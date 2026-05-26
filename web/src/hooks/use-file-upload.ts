import { useState, useCallback } from 'react';

import { UPLOAD_API_TIMEOUT_MS } from '@/lib/api-config';
import { authenticatedFetch } from '@/lib/api-fetch';
import { parseApiErrorMessage, unwrapData } from '@/lib/api-envelope';
import {
  DEFAULT_UPLOAD_CONFIG,
  LITE_ALLOWED_EXTENSIONS,
  LITE_MAX_FILE_SIZE_MB,
  type UploadConfig,
} from '@/shared/upload-policy';

export interface UploadFile {
  name: string;
  size: number;
  type: string;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percent: number;
}

export interface UploadResult {
  success: boolean;
  document_id?: string;
  storage_key?: string;
  error?: string;
}

export interface AiUploadSelection {
  provider?: string;
  model?: string;
}

export interface UseFileUploadOptions {
  uploadConfig?: UploadConfig;
  maxSizeMB?: number;
  allowedExtensions?: string[];
  aiSelection?: AiUploadSelection;
  onProgress?: (progress: UploadProgress) => void;
  onComplete?: (result: UploadResult) => void;
  onError?: (error: string) => void;
}

function aiQueryParams(selection?: AiUploadSelection): string {
  if (!selection?.provider && !selection?.model) return '';
  const params = new URLSearchParams();
  if (selection.provider) params.set('provider', selection.provider);
  if (selection.model) params.set('model', selection.model);
  const q = params.toString();
  return q ? `?${q}` : '';
}

interface InitiatePayload {
  document_id: string;
  storage_key: string;
  upload_url: string;
}

function parseInitiateResponse(json: unknown): InitiatePayload {
  const body = unwrapData(json as { data?: InitiatePayload }) as InitiatePayload;
  if (!body?.document_id || !body?.upload_url) {
    const flat = json as InitiatePayload;
    if (flat.document_id && flat.upload_url) return flat;
    throw new Error('Invalid upload initiate response');
  }
  return body;
}

function parseDirectResponse(json: unknown): { document_id?: string; storage_key?: string } {
  const body = unwrapData(json as { document_id?: string; storage_key?: string });
  return (body && typeof body === 'object' ? body : json) as {
    document_id?: string;
    storage_key?: string;
  };
}

export function useFileUpload(options: UseFileUploadOptions = {}) {
  const config = options.uploadConfig ?? DEFAULT_UPLOAD_CONFIG;
  const aiSelection = options.aiSelection;
  const maxSizeMB = options.maxSizeMB ?? config.max_file_size_mb ?? LITE_MAX_FILE_SIZE_MB;
  const allowedExtensions =
    options.allowedExtensions ?? config.allowed_extensions ?? [...LITE_ALLOWED_EXTENSIONS];
  const usePresigned = config.use_presigned ?? config.provider !== 'local';

  const {
    onProgress,
    onComplete,
    onError,
  } = options;

  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState<UploadProgress | null>(null);
  const [error, setError] = useState<string | null>(null);

  const validateFile = useCallback(
    (file: File): string | null => {
      const ext = '.' + (file.name.split('.').pop()?.toLowerCase() ?? '');
      if (!allowedExtensions.includes(ext)) {
        return `File type ${ext} is not allowed. Allowed: ${allowedExtensions.join(', ')}`;
      }

      const maxBytes = maxSizeMB * 1024 * 1024;
      if (file.size > maxBytes) {
        return `File size exceeds ${maxSizeMB}MB limit`;
      }

      if (file.size === 0) {
        return 'File is empty';
      }

      return null;
    },
    [allowedExtensions, maxSizeMB]
  );

  const uploadViaPresigned = useCallback(
    async (file: File, tenderId?: string, category: string = 'documents'): Promise<UploadResult> => {
      const initResponse = await authenticatedFetch('/api/v1/files/upload/initiate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_name: file.name,
          file_size: file.size,
          content_type: file.type,
          tender_id: tenderId,
          category,
        }),
        timeout: UPLOAD_API_TIMEOUT_MS,
      });

      if (!initResponse.ok) {
        const err = (await initResponse.json().catch(() => ({}))) as Record<string, unknown>;
        throw new Error(parseApiErrorMessage(err) || 'Failed to initiate upload');
      }

      const initData = parseInitiateResponse(await initResponse.json());

      const uploadResponse = await fetch(initData.upload_url, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': file.type || 'application/octet-stream',
        },
      });

      if (!uploadResponse.ok) {
        throw new Error('Failed to upload file to storage (check R2 CORS if using Cloudflare R2)');
      }

      setProgress({ loaded: file.size, total: file.size, percent: 100 });

      const completeResponse = await authenticatedFetch(
        `/api/v1/files/upload/complete/${initData.document_id}${aiQueryParams(aiSelection)}`,
        { method: 'POST', timeout: UPLOAD_API_TIMEOUT_MS }
      );

      if (!completeResponse.ok) {
        throw new Error('Failed to complete upload');
      }

      return {
        success: true,
        document_id: initData.document_id,
        storage_key: initData.storage_key,
      };
    },
    [aiSelection]
  );

  const uploadViaDirect = useCallback(
    async (file: File, tenderId?: string, category: string = 'documents'): Promise<UploadResult> => {
      const params = new URLSearchParams({ category });
      if (tenderId) params.set('tender_id', tenderId);

      const formData = new FormData();
      formData.append('file', file);

      const aiParams = aiSelection?.provider || aiSelection?.model
        ? new URLSearchParams({
            ...(aiSelection.provider ? { provider: aiSelection.provider } : {}),
            ...(aiSelection.model ? { model: aiSelection.model } : {}),
          })
        : null;
      if (aiParams) {
        aiParams.forEach((v, k) => params.set(k, v));
      }

      const directResponse = await authenticatedFetch(
        `/api/v1/files/upload/direct?${params.toString()}`,
        {
          method: 'POST',
          body: formData,
          timeout: UPLOAD_API_TIMEOUT_MS,
        }
      );

      if (!directResponse.ok) {
        const errBody = (await directResponse.json().catch(() => ({}))) as Record<string, unknown>;
        throw new Error(parseApiErrorMessage(errBody) || 'Upload rejected');
      }

      const directData = parseDirectResponse(await directResponse.json());
      setProgress({ loaded: file.size, total: file.size, percent: 100 });
      return {
        success: true,
        document_id: directData.document_id,
        storage_key: directData.storage_key,
      };
    },
    [aiSelection]
  );

  const uploadFile = useCallback(
    async (file: File, tenderId?: string, category: string = 'documents'): Promise<UploadResult> => {
      setUploading(true);
      setError(null);
      setProgress({ loaded: 0, total: file.size, percent: 0 });

      try {
        const validationError = validateFile(file);
        if (validationError) {
          setError(validationError);
          onError?.(validationError);
          setUploading(false);
          return { success: false, error: validationError };
        }

        let result: UploadResult;

        if (usePresigned) {
          result = await uploadViaPresigned(file, tenderId, category);
        } else {
          try {
            result = await uploadViaDirect(file, tenderId, category);
          } catch (directErr) {
            const message = directErr instanceof Error ? directErr.message : 'Direct upload failed';
            if (message.includes('presigned')) {
              result = await uploadViaPresigned(file, tenderId, category);
            } else {
              throw directErr;
            }
          }
        }

        onComplete?.(result);
        setUploading(false);
        return result;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Upload failed';
        setError(errorMessage);
        onError?.(errorMessage);
        setUploading(false);
        return { success: false, error: errorMessage };
      }
    },
    [validateFile, usePresigned, uploadViaDirect, uploadViaPresigned, onComplete, onError]
  );

  const uploadFiles = useCallback(
    async (files: File[], tenderId?: string, category: string = 'documents'): Promise<UploadResult[]> => {
      const results: UploadResult[] = [];
      for (const file of files) {
        results.push(await uploadFile(file, tenderId, category));
      }
      return results;
    },
    [uploadFile]
  );

  const formatFileSize = useCallback((bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }, []);

  const reset = useCallback(() => {
    setUploading(false);
    setProgress(null);
    setError(null);
  }, []);

  return {
    uploading,
    progress,
    error,
    validateFile,
    uploadFile,
    uploadFiles,
    formatFileSize,
    reset,
    maxSizeMB,
    allowedExtensions,
    usePresigned,
  };
}
