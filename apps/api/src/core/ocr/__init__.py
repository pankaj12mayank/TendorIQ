from .paddle_ocr import paddle_ocr_service, PaddleOCRService, OCRResult
from .worker import process_ocr_job, queue_ocr_job, OCRWorkerSettings

__all__ = [
    'paddle_ocr_service',
    'PaddleOCRService',
    'OCRResult',
    'process_ocr_job',
    'queue_ocr_job',
    'OCRWorkerSettings',
]