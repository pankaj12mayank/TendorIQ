/** TenderIQ Lite upload policy — keep in sync with api/src/core/upload_policy.py */

export const LITE_MAX_FILE_SIZE_MB = 25;
export const LITE_ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx'] as const;
export const LITE_ACCEPT_ATTR = '.pdf,.doc,.docx';

export interface UploadConfig {
  provider: 'local' | 'r2' | 's3';
  max_file_size_mb: number;
  max_file_size_bytes: number;
  allowed_extensions: string[];
  use_presigned: boolean;
  mime_types?: Record<string, string>;
}

export const DEFAULT_UPLOAD_CONFIG: UploadConfig = {
  provider: 'local',
  max_file_size_mb: LITE_MAX_FILE_SIZE_MB,
  max_file_size_bytes: LITE_MAX_FILE_SIZE_MB * 1024 * 1024,
  allowed_extensions: [...LITE_ALLOWED_EXTENSIONS],
  use_presigned: false,
};
