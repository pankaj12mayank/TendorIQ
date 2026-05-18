import { useCallback, useState } from 'react';
import { api } from '@/lib/api';

export interface OCRStatus {
  document_id: string;
  ocr_status: string;
  has_result: boolean;
  result?: {
    id: string;
    text: string;
    confidence: number;
    word_count: number;
    language: string;
    is_low_quality: boolean;
    quality_scores: {
      blur: number;
      brightness: number;
      contrast: number;
      overall: number;
    };
    status: string;
    completed_at: string;
  };
  job?: {
    id: string;
    status: string;
    retry_count: number;
  };
}

export interface QualityAssessment {
  blur_score: number;
  brightness_score: number;
  contrast_score: number;
  overall_quality: number;
  is_blurry: boolean;
  is_too_dark: boolean;
  is_too_bright: boolean;
  needs_enhancement: boolean;
  recommended_dpi: number;
  estimated_ocr_accuracy: string;
}

export function useOCRApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const processDocument = useCallback(async (documentId: string, language = 'en') => {
    setLoading(true);
    setError(null);

    try {
      const res = await api.post<{
        success: boolean;
        job_id: string;
        document_id: string;
        status: string;
      }>(`/api/v1/ocr/process/${documentId}`, { language });

      return res;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to process OCR';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getStatus = useCallback(async (documentId: string): Promise<OCRStatus> => {
    try {
      const res = await api.get<OCRStatus>(`/api/v1/ocr/status/${documentId}`);
      return res;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to get OCR status';
      setError(msg);
      throw err;
    }
  }, []);

  const getResult = useCallback(async (documentId: string) => {
    try {
      const res = await api.get<{
        success: boolean;
        result: {
          id: string;
          text: string;
          confidence: number;
          word_count: number;
          is_low_quality: boolean;
          quality_scores: {
            blur: number;
            brightness: number;
            contrast: number;
            overall: number;
          };
        };
      }>(`/api/v1/ocr/result/${documentId}`);
      return res.result;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to get OCR result';
      setError(msg);
      throw err;
    }
  }, []);

  const assessQuality = useCallback(async (documentId: string): Promise<QualityAssessment> => {
    try {
      const res = await api.get<QualityAssessment>(`/api/v1/ocr/quality/${documentId}`);
      return res;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to assess quality';
      setError(msg);
      throw err;
    }
  }, []);

  const retryOCR = useCallback(async (documentIds: string[]) => {
    setLoading(true);
    setError(null);

    try {
      const res = await api.post<{
        retried_count: number;
        skipped_count: number;
        errors: string[];
      }>('/api/v1/ocr/retry', { document_ids: documentIds });
      return res;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to retry OCR';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const pollStatus = useCallback(async (documentId: string, maxAttempts = 60, intervalMs = 5000) => {
    let attempts = 0;

    const poll = async (): Promise<OCRStatus> => {
      if (attempts >= maxAttempts) {
        throw new Error('OCR polling timeout');
      }

      try {
        const status = await getStatus(documentId);
        attempts++;

        if (status.ocr_status === 'completed' || status.ocr_status === 'failed' || status.ocr_status === 'needs_review') {
          return status;
        }

        await new Promise((resolve) => setTimeout(resolve, intervalMs));
        return poll();
      } catch (err) {
        attempts++;
        if (attempts >= maxAttempts) throw err;
        await new Promise((resolve) => setTimeout(resolve, intervalMs));
        return poll();
      }
    };

    return poll();
  }, [getStatus]);

  return {
    loading,
    error,
    processDocument,
    getStatus,
    getResult,
    assessQuality,
    retryOCR,
    pollStatus,
  };
}