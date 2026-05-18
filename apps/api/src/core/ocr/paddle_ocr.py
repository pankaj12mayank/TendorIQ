"""PaddleOCR Service - Document Text Extraction"""

import io
import logging
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

logger = logging.getLogger('ocr_service')


@dataclass
class OCRResult:
    text: str
    confidence: float
    language: str
    word_count: int
    blocks: list[dict]
    is_low_quality: bool
    processing_time_ms: int


@dataclass
class OCRJobResult:
    success: bool
    document_id: str
    job_id: str
    status: str
    result: Optional[OCRResult] = None
    error: Optional[str] = None
    retry_count: int = 0


class PaddleOCRService:
    _instance: Optional['PaddleOCRService'] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.ocr = None
        self._initialized = True

    def _lazy_init(self, lang: str = 'en'):
        if self.ocr is not None:
            return

        try:
            from paddleocr import PaddleOCR

            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang=lang,
                show_log=False,
                use_gpu=False,
                det_db_thresh=0.3,
                det_db_box_thresh=0.5,
                rec_batch_num=16,
                max_batch_size=32,
            )
            logger.info(f'PaddleOCR initialized with lang={lang}')
        except ImportError:
            logger.warning('PaddleOCR not installed, using fallback OCR')
            self.ocr = None

    def process_image(
        self,
        image_bytes: bytes,
        language: str = 'en',
        min_confidence: float = 0.5,
    ) -> OCRResult:
        from PIL import Image
        import numpy as np
        import cv2
        import time

        start_time = time.time()
        self._lazy_init(lang=language)

        image = Image.open(io.BytesIO(image_bytes))
        image_array = np.array(image)

        if len(image_array.shape) == 2:
            image_array = cv2.cvtColor(image_array, cv2.COLOR_GRAY2RGB)
        elif image_array.shape[2] == 4:
            image_array = cv2.cvtColor(image_array, cv2.COLOR_RGBA2RGB)

        preprocessed = self._preprocess_image(image_array)

        if self.ocr is None:
            return self._fallback_ocr(preprocessed, start_time)

        try:
            result = self.ocr.ocr(preprocessed, cls=True)

            if not result or not result[0]:
                return OCRResult(
                    text='',
                    confidence=0.0,
                    language=language,
                    word_count=0,
                    blocks=[],
                    is_low_quality=True,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                )

            full_text = []
            blocks = []
            confidences = []
            low_conf_count = 0

            for line in result[0]:
                if len(line) >= 2:
                    box = line[0]
                    text_info = line[1]
                    text = text_info[0]
                    conf = text_info[1] if len(text_info) > 1 else 0.5

                    confidences.append(conf)

                    if conf < min_confidence:
                        low_conf_count += 1

                    blocks.append({
                        'text': text,
                        'confidence': float(conf),
                        'bbox': box,
                        'low_quality': conf < min_confidence,
                    })

                    full_text.append(text)

            combined_text = '\n'.join(full_text)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            low_quality_ratio = low_conf_count / len(blocks) if blocks else 0

            is_low_quality = (
                avg_confidence < 0.7 or
                low_quality_ratio > 0.3 or
                len(combined_text.strip()) < 20
            )

            word_count = len(combined_text.split())

            return OCRResult(
                text=combined_text,
                confidence=float(avg_confidence),
                language=language,
                word_count=word_count,
                blocks=blocks,
                is_low_quality=is_low_quality,
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

        except Exception as e:
            logger.error(f'OCR processing error: {e}')
            return OCRResult(
                text='',
                confidence=0.0,
                language=language,
                word_count=0,
                blocks=[],
                is_low_quality=True,
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

    def process_pdf(
        self,
        pdf_bytes: bytes,
        language: str = 'en',
        min_confidence: float = 0.5,
        max_pages: int = 50,
    ) -> list[OCRResult]:
        from pdf2image import convert_from_bytes
        import time

        start_time = time.time()
        results = []

        try:
            images = convert_from_bytes(
                pdf_bytes,
                fmt='png',
                dpi=200,
                first_page=1,
                last_page=min(max_pages, 100),
            )

            logger.info(f'PDF converted to {len(images)} pages')

            for i, image in enumerate(images[:max_pages]):
                img_bytes = io.BytesIO()
                image.save(img_bytes, format='PNG')
                img_bytes.seek(0)

                result = self.process_image(
                    img_bytes.read(),
                    language=language,
                    min_confidence=min_confidence,
                )
                result.page_number = i + 1
                results.append(result)

            return results

        except Exception as e:
            logger.error(f'PDF processing error: {e}')
            return []

    def _preprocess_image(self, image: 'np.ndarray') -> 'np.ndarray':
        import cv2
        import numpy as np

        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        sigma = 0.5
        blurred = cv2.GaussianBlur(enhanced, (0, 0), sigma)

        unsharp_mask = cv2.addWeighted(enhanced, 1.5, blurred, -0.5, 0)
        denoised = cv2.fastNlMeansDenoising(unsharp_mask, None, h=10, templateWindowSize=7, searchWindowSize=21)

        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        if np.mean(binary) > 200:
            binary = cv2.bitwise_not(binary)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        return cleaned

    def _fallback_ocr(self, image: 'np.ndarray', start_time: float) -> OCRResult:
        from PIL import Image
        import pytesseract

        try:
            pil_image = Image.fromarray(image)
            text = pytesseract.image_to_string(pil_image, lang='eng')

            return OCRResult(
                text=text,
                confidence=0.6,
                language='en',
                word_count=len(text.split()),
                blocks=[],
                is_low_quality=False,
                processing_time_ms=int((datetime.now().timestamp() - start_time) * 1000),
            )
        except Exception as e:
            logger.error(f'Fallback OCR failed: {e}')
            return OCRResult(
                text='',
                confidence=0.0,
                language='en',
                word_count=0,
                blocks=[],
                is_low_quality=True,
                processing_time_ms=int((datetime.now().timestamp() - start_time) * 1000),
            )

    def detect_language(self, image_bytes: bytes) -> str:
        try:
            import langdetect
            from PIL import Image
            import pytesseract

            image = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(image)

            if len(text.strip()) < 10:
                return 'en'

            lang = langdetect.detect(text)
            return lang if lang else 'en'
        except Exception:
            return 'en'

    def estimate_quality(self, image_bytes: bytes) -> dict:
        import cv2
        import numpy as np
        from PIL import Image

        image = Image.open(io.BytesIO(image_bytes))
        image_array = np.array(image)

        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_array

        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        blur_score = min(1.0, laplacian_var / 500)

        brightness = np.mean(gray)
        brightness_score = 1.0 if 60 < brightness < 200 else max(0, 1.0 - abs(brightness - 130) / 130)

        contrast = np.std(gray)
        contrast_score = min(1.0, contrast / 60)

        overall_quality = (blur_score * 0.4 + brightness_score * 0.3 + contrast_score * 0.3)

        return {
            'blur_score': round(blur_score, 2),
            'brightness_score': round(brightness_score, 2),
            'contrast_score': round(contrast_score, 2),
            'overall_quality': round(overall_quality, 2),
            'is_blurry': blur_score < 0.5,
            'is_too_dark': brightness < 40,
            'is_too_bright': brightness > 220,
            'needs_enhancement': overall_quality < 0.6,
        }


paddle_ocr_service = PaddleOCRService()