import { useCallback, useState, useRef, useEffect } from 'react';
import { api } from '@/lib/api-client';

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
  const cancelledRef = useRef(false);

  useEffect(() => {
    return () => { cancelledRef.current = true; };
  }, []);

  const processDocument = useCallback(async (documentId: string, language = 'en') => {
    setLoading(true);
    setError(null);

    try {
      const res = await api.post<{
        success: boolean;
        job_id: string;
        document_id: string;
        status: string;
      }>(`/api/v1/ocr/process/${documentId}?language=${encodeURIComponent(language)}`, {});

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

  const delay = useCallback((ms: number) => {
    return new Promise<void>((resolve) => {
      if (cancelledRef.current) { resolve(); return; }
      const timer = setTimeout(() => {
        if (!cancelledRef.current) resolve();
      }, ms);
      const interval = setInterval(() => {
        if (cancelledRef.current) {
          clearTimeout(timer);
          clearInterval(interval);
          resolve();
        }
      }, 100);
    });
  }, []);

  const pollStatus = useCallback(async (documentId: string, maxAttempts = 60, intervalMs = 5000) => {
    const poll = async (attempt = 0): Promise<OCRStatus> => {
      if (cancelledRef.current || attempt >= maxAttempts) {
        throw new Error(cancelledRef.current ? 'Polling cancelled' : 'OCR polling timeout');
      }

      try {
        const status = await getStatus(documentId);

        if (status.ocr_status === 'completed' || status.ocr_status === 'failed' || status.ocr_status === 'needs_review') {
          return status;
        }

        await delay(intervalMs);
        return poll(attempt + 1);
      } catch (err) {
        if (cancelledRef.current) throw new Error('Polling cancelled');
        if (attempt + 1 >= maxAttempts) throw err;
        await delay(intervalMs);
        return poll(attempt + 1);
      }
    };

    return poll();
  }, [getStatus, delay]);

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