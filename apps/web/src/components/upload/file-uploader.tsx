'use client';

import { useCallback, useState } from 'react';
import { Upload, X, FileIcon, CheckCircle2, AlertCircle, Loader2, CloudUpload } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useFileUpload, UploadResult } from '@/hooks/use-file-upload';
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
  onUploadComplete?: (results: UploadResult[]) => void;
  className?: string;
}

export function FileUploader({
  tenderId,
  category = 'documents',
  maxFiles = 10,
  onUploadComplete,
  className,
}: FileUploaderProps) {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const { uploadFile, validateFile, formatFileSize, uploading } = useFileUpload({
    maxSizeMB: 50,
    onProgress: (progress) => {
      // Progress tracked per-file in state
    },
  });

  const addFiles = useCallback((newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles);
    const remaining = maxFiles - files.length;
    const toAdd = fileArray.slice(0, remaining);

    const newUploadFiles: UploadedFile[] = toAdd.map((file) => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      name: file.name,
      size: file.size,
      status: 'pending' as const,
      progress: 0,
    }));

    setFiles((prev) => [...prev, ...newUploadFiles]);
  }, [files.length, maxFiles]);

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

  const uploadAll = useCallback(async () => {
    const pendingFiles = files.filter((f) => f.status === 'pending');
    const results: UploadResult[] = [];

    for (const file of pendingFiles) {
      setFiles((prev) =>
        prev.map((f) => (f.id === file.id ? { ...f, status: 'uploading' as const, progress: 0 } : f))
      );

      const result = await uploadFile(file.file, tenderId, category);

      if (result.success) {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === file.id ? { ...f, status: 'completed' as const, progress: 100, documentId: result.document_id } : f
          )
        );
      } else {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === file.id ? { ...f, status: 'error' as const, error: result.error } : f
          )
        );
      }

      results.push(result);
    }

    onUploadComplete?.(results);
  }, [files, uploadFile, tenderId, category, onUploadComplete]);

  const uploadSingle = useCallback(async (fileId: string) => {
    const file = files.find((f) => f.id === fileId);
    if (!file) return;

    setFiles((prev) =>
      prev.map((f) => (f.id === fileId ? { ...f, status: 'uploading' as const, progress: 0 } : f))
    );

    const result = await uploadFile(file.file, tenderId, category);

    if (result.success) {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === fileId ? { ...f, status: 'completed' as const, progress: 100, documentId: result.document_id } : f
        )
      );
    } else {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === fileId ? { ...f, status: 'error' as const, error: result.error } : f
        )
      );
    }
  }, [files, uploadFile, tenderId, category]);

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
          Max 50MB per file. Supported: PDF, DOC, XLS, PNG, JPG, CSV
        </p>
        <input
          type="file"
          multiple
          onChange={handleInputChange}
          className="absolute inset-0 cursor-pointer opacity-0"
          accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg,.gif,.txt,.csv"
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
              disabled={uploading || files.filter((f) => f.status === 'pending').length === 0}
              className="flex-1"
            >
              {uploading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload {files.filter((f) => f.status === 'pending').length} file(s)
                </>
              )}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

function getMimeType(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase();
  const mimeTypes: Record<string, string> = {
    pdf: 'application/pdf',
    doc: 'application/msword',
    docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    xls: 'application/vnd.ms-excel',
    xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    png: 'image/png',
    jpg: 'image/jpeg',
    jpeg: 'image/jpeg',
    gif: 'image/gif',
    txt: 'text/plain',
    csv: 'text/csv',
  };
  return mimeTypes[ext || ''] || 'application/octet-stream';
}