'use client';

import { useCallback, useRef, useState } from 'react';
import { Upload, X, FileIcon, CheckCircle2, AlertCircle, Loader2, CloudUpload } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useFileUpload, UploadResult, type AiUploadSelection, type UploadProgress } from '@/hooks/use-file-upload';
import { useUploadConfig } from '@/hooks/use-upload-config';
import { LITE_ACCEPT_ATTR } from '@/shared/upload-policy';
import { Button } from '@/components/ui/button';

interface UploadedFile {
  id: string;
  file: File;
  name: string;
  size: number;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  progress: number;
  error?: string;
  documentId?: string;
}

interface FileUploaderProps {
  tenderId?: string;
  category?: string;
  maxFiles?: number;
  aiSelection?: AiUploadSelection;
  onUploadComplete?: (results: UploadResult[]) => void;
  className?: string;
}

export function FileUploader({
  tenderId,
  category = 'documents',
  maxFiles = 10,
  aiSelection,
  onUploadComplete,
  className,
}: FileUploaderProps) {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const uploadingIds = useRef<Set<string>>(new Set());
  const { data: uploadConfig } = useUploadConfig();
  const { uploadFile, validateFile, formatFileSize } = useFileUpload({
    uploadConfig,
    aiSelection,
  });
  const maxSizeMB = uploadConfig?.max_file_size_mb ?? 25;

  const updateFileProgress = useCallback((fileId: string, p: UploadProgress) => {
    setFiles((prev) =>
      prev.map((f) => (f.id === fileId ? { ...f, progress: p.percent } : f))
    );
  }, []);

  const addFiles = useCallback((newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles);
    setFiles((prev) => {
      const remaining = maxFiles - prev.length;
      const toAdd = fileArray.slice(0, remaining);
      const newUploadFiles: UploadedFile[] = toAdd.map((file) => ({
        id: Math.random().toString(36).substr(2, 9),
        file,
        name: file.name,
        size: file.size,
        status: 'pending' as const,
        progress: 0,
      }));
      return [...prev, ...newUploadFiles];
    });
  }, [maxFiles]);

  const removeFile = useCallback((id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files.length > 0) {
      addFiles(e.dataTransfer.files);
    }
  }, [addFiles]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(e.target.files);
    }
  }, [addFiles]);

  const uploadSingle = useCallback(async (fileId: string) => {
    if (uploadingIds.current.has(fileId)) return;
    const file = files.find((f) => f.id === fileId);
    if (!file || file.status !== 'pending') return;

    uploadingIds.current.add(fileId);
    setFiles((prev) =>
      prev.map((f) => (f.id === fileId ? { ...f, status: 'uploading' as const, progress: 0 } : f))
    );

    const result = await uploadFile(file.file, tenderId, category, {
      onProgress: (p) => updateFileProgress(fileId, p),
    });

    uploadingIds.current.delete(fileId);
    setFiles((prev) =>
      prev.map((f) =>
        f.id === fileId
          ? result.success
            ? { ...f, status: 'completed' as const, progress: 100, documentId: result.document_id }
            : { ...f, status: 'error' as const, error: result.error }
          : f
      )
    );
    return result;
  }, [files, uploadFile, tenderId, category, updateFileProgress]);

  const uploadAll = useCallback(async () => {
    const pending = files.filter((f) => f.status === 'pending');
    const results: UploadResult[] = [];
    for (const f of pending) {
      const r = await uploadSingle(f.id);
      if (r) results.push(r);
    }
    onUploadComplete?.(results);
  }, [files, uploadSingle, onUploadComplete]);

  const anyUploading = uploadingIds.current.size > 0;
  const pendingCount = files.filter((f) => f.status === 'pending').length;

  return (
    <div className={cn('space-y-4', className)}>
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={cn(
          'relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors',
          isDragging
            ? 'border-primary bg-primary/5'
            : 'border-muted-foreground/25 hover:border-muted-foreground/50'
        )}
      >
        <CloudUpload className="mb-4 h-12 w-12 text-muted-foreground" />
        <p className="mb-2 text-sm font-medium">
          Drag & drop files here, or click to browse
        </p>
        <p className="mb-4 text-xs text-muted-foreground">
          Max {maxSizeMB}MB per file. PDF, DOC, and DOCX only.
          {uploadConfig?.use_presigned ? ' Uploads go directly to cloud storage.' : ''}
        </p>
        <input
          type="file"
          multiple
          onChange={handleInputChange}
          className="absolute inset-0 cursor-pointer opacity-0"
          accept={LITE_ACCEPT_ATTR}
        />
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((file) => (
            <div
              key={file.id}
              className="flex items-center gap-3 rounded-lg border bg-card p-3"
            >
              <FileIcon className="h-8 w-8 text-muted-foreground" />

              <div className="flex-1 min-w-0">
                <p className="truncate text-sm font-medium">{file.name}</p>
                <p className="text-xs text-muted-foreground">
                  {formatFileSize(file.size)}
                </p>

                {file.status === 'uploading' && (
                  <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full bg-primary transition-all duration-300"
                      style={{ width: `${file.progress}%` }}
                    />
                  </div>
                )}

                {file.status === 'error' && file.error && (
                  <p className="mt-1 text-xs text-destructive">{file.error}</p>
                )}
              </div>

              <div className="flex items-center gap-2">
                {file.status === 'pending' && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => uploadSingle(file.id)}
                  >
                    <Upload className="h-4 w-4" />
                  </Button>
                )}

                {file.status === 'uploading' && (
                  <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                )}

                {file.status === 'completed' && (
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                )}

                {file.status === 'error' && (
                  <AlertCircle className="h-5 w-5 text-destructive" />
                )}

                <button
                  onClick={() => removeFile(file.id)}
                  className="rounded p-1 hover:bg-muted"
                >
                  <X className="h-4 w-4 text-muted-foreground" />
                </button>
              </div>
            </div>
          ))}

          <div className="flex items-center gap-3">
            <Button
              onClick={uploadAll}
              disabled={anyUploading || pendingCount === 0}
              className="flex-1"
            >
              {anyUploading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload {pendingCount} file(s)
                </>
              )}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}