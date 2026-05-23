import { useState, useCallback } from 'react';

import { UPLOAD_API_TIMEOUT_MS } from '@/lib/api-config';
import { authenticatedFetch } from '@/lib/api-fetch';
import { parseApiErrorMessage } from '@/lib/api-envelope';

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

export interface UseFileUploadOptions {
  maxSizeMB?: number;
  allowedExtensions?: string[];
  onProgress?: (progress: UploadProgress) => void;
  onComplete?: (result: UploadResult) => void;
  onError?: (error: string) => void;
}

const DEFAULT_MAX_SIZE_MB = 50;
const DEFAULT_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg', '.gif', '.txt', '.csv'];

export function useFileUpload(options: UseFileUploadOptions = {}) {
  const {
    maxSizeMB = DEFAULT_MAX_SIZE_MB,
    allowedExtensions = DEFAULT_EXTENSIONS,
    onProgress,
    onComplete,
    onError,
  } = options;

  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState<UploadProgress | null>(null);
  const [error, setError] = useState<string | null>(null);

  const validateFile = useCallback((file: File): string | null => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
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
  }, [allowedExtensions, maxSizeMB]);

  const uploadFile = useCallback(async (
    file: File,
    tenderId?: string,
    category: string = 'documents'
  ): Promise<UploadResult> => {
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

      const params = new URLSearchParams({ category });
      if (tenderId) params.set('tender_id', tenderId);

      const formData = new FormData();
      formData.append('file', file);

      const directResponse = await authenticatedFetch(
        `/api/v1/files/upload/direct?${params.toString()}`,
        {
          method: 'POST',
          body: formData,
          timeout: UPLOAD_API_TIMEOUT_MS,
        }
      );

      if (directResponse.ok) {
        const directData = await directResponse.json();
        setProgress({ loaded: file.size, total: file.size, percent: 100 });
        const result: UploadResult = {
          success: true,
          document_id: directData.document_id,
          storage_key: directData.storage_key,
        };
        onComplete?.(result);
        setUploading(false);
        return result;
      }

      if (directResponse.status === 400) {
        const errBody = (await directResponse.json().catch(() => ({}))) as Record<string, unknown>;
        throw new Error(parseApiErrorMessage(errBody) || 'Upload rejected');
      }

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

      const initData = await initResponse.json();

      const uploadResponse = await fetch(initData.upload_url, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': file.type || 'application/octet-stream',
        },
      });

      if (!uploadResponse.ok) {
        throw new Error('Failed to upload file to storage');
      }

      setProgress({ loaded: file.size, total: file.size, percent: 100 });

      const completeResponse = await authenticatedFetch(
        `/api/v1/files/upload/complete/${initData.document_id}`,
        { method: 'POST', timeout: UPLOAD_API_TIMEOUT_MS }
      );

      if (!completeResponse.ok) {
        throw new Error('Failed to complete upload');
      }

      const result: UploadResult = {
        success: true,
        document_id: initData.document_id,
        storage_key: initData.storage_key,
      };

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
  }, [validateFile, onComplete, onError]);

  const uploadFiles = useCallback(async (
    files: File[],
    tenderId?: string,
    category: string = 'documents'
  ): Promise<UploadResult[]> => {
    const results: UploadResult[] = [];

    for (const file of files) {
      const result = await uploadFile(file, tenderId, category);
      results.push(result);
    }

    return results;
  }, [uploadFile]);

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
  };
}
