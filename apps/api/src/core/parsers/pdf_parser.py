"""PDF Parser using PyMuPDF (fitz)"""

import io
import logging
import re
from datetime import datetime
from typing import Optional

import fitz

from .base import (
    BaseParser, ParsedDocument, DocumentMetadata,
    PageSegment, Section, ParsingError
)
from ..logging import get_logger

logger = get_logger('pdf_parser')


class PDFParser(BaseParser):
    supported_extensions = ['pdf', 'pdf/a']

    HEADING_PATTERNS = [
        (r'^(#{1,6})\s+(.+)', 1),
        (r'^([IVXLCDM]+\.\s+.+)', 1),
        (r'^(\d+\.\d+\.?\s+.+)', 1),
        (r'^(\d+\s+(?!.*\d+\.)\S.+)', 1),
        (r'^([A-Z][A-Z\s]{2,})$', 1),
    ]

    MIN_HEADING_LENGTH = 4
    MAX_HEADING_LENGTH = 200

    def __init__(self):
        self.fitz_module = fitz

    async def parse(self, file_bytes: bytes, file_name: str, document_id: str) -> ParsedDocument:
        try:
            doc = fitz.open(stream=file_bytes, filetype='pdf')
        except Exception as e:
            raise ParsingError(f'Failed to open PDF: {str(e)}')

        metadata = await self.extract_metadata(doc, file_bytes)
        full_text, pages = await self._extract_pages(doc)
        full_text = self.normalize_text(full_text)

        sections = self._detect_sections(full_text, pages)
        headings = self._detect_headings_fast(full_text)

        links = await self._extract_links(doc)
        images = await self._extract_images(doc)
        tables = await self._extract_tables(doc, pages)

        doc.close()

        return ParsedDocument(
            document_id=document_id,
            file_name=file_name,
            file_type='pdf',
            metadata=metadata,
            full_text=full_text,
            pages=pages,
            sections=sections,
            tables=tables,
            images=images,
            links=links,
            confidence_score=self._calculate_confidence(full_text, pages),
        )

    async def extract_metadata(self, file_bytes: bytes) -> DocumentMetadata:
        try:
            doc = fitz.open(stream=file_bytes, filetype='pdf')
        except Exception:
            return DocumentMetadata()

        try:
            meta = doc.metadata

            creation_str = meta.get('creationDate', '')
            mod_str = meta.get('modDate', '')

            creation_date = None
            if creation_str:
                try:
                    creation_date = datetime.strptime(creation_str[2:16], '%Y%m%d%H%M%S')
                except:
                    pass

            mod_date = None
            if mod_str:
                try:
                    mod_date = datetime.strptime(mod_str[2:16], '%Y%m%d%H%M%S')
                except:
                    pass

            keywords_str = meta.get('keywords', '')
            keywords = [k.strip() for k in keywords_str.split(',') if k.strip()] if keywords_str else []

            return DocumentMetadata(
                title=meta.get('title') or None,
                author=meta.get('author') or None,
                creator=meta.get('creator') or None,
                producer=meta.get('producer') or None,
                subject=meta.get('subject') or None,
                description=meta.get('subject') or None,
                keywords=keywords,
                creation_date=creation_date,
                modification_date=mod_date,
                page_count=len(doc),
                language='en',
                file_size=len(file_bytes),
                is_encrypted=doc.is_encrypted,
                is_form=doc.is_form,
            )
        finally:
            doc.close()

    async def extract_text(self, file_bytes: bytes) -> str:
        doc = fitz.open(stream=file_bytes, filetype='pdf')
        text_parts = []

        for page in doc:
            page_text = page.get_text()
            if page_text:
                text_parts.append(page_text)

        doc.close()
        return self.normalize_text('\n'.join(text_parts))

    async def _extract_pages(self, doc) -> tuple[str, list[PageSegment]]:
        all_text = []
        pages = []
        global_char_pos = 0

        for page_num, page in enumerate(doc):
            page_text = page.get_text('text')
            all_text.append(page_text)

            cleaned = self.normalize_text(page_text)
            start_char = global_char_pos
            end_char = global_char_pos + len(cleaned)
            global_char_pos = end_char + 1

            headings = self._detect_headings_fast(cleaned)

            page_segments = self._segment_page(
                cleaned,
                page_num + 1,
                start_char,
                headings,
                page,
            )
            pages.extend(page_segments)

        return '\n'.join(all_text), pages

    def _segment_page(
        self,
        text: str,
        page_num: int,
        global_start: int,
        headings: list[tuple[int, int, str, int]],
        page,
    ) -> list[PageSegment]:
        segments = []

        lines = text.split('\n')
        current_pos = global_start
        in_heading = False

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                current_pos += 1
                continue

            is_heading = False
            heading_level = None
            section_title = None

            for start, end, heading_text, level in headings:
                if line == heading_text.strip():
                    is_heading = True
                    heading_level = level
                    section_title = heading_text.strip()
                    break

            seg = PageSegment(
                page_number=page_num,
                text=line,
                start_char=current_pos,
                end_char=current_pos + len(line),
                bbox=None,
                is_heading=is_heading,
                heading_level=heading_level,
                section_title=section_title,
                confidence=1.0,
                font_info=None,
            )

            try:
                text_dict = page.get_text('dict')
                for block in text_dict.get('blocks', []):
                    if block.get('type') == 0:
                        for span in block.get('spans', []):
                            if span.get('text', '').strip() == line.strip():
                                seg.bbox = span.get('bbox')
                                seg.font_info = {
                                    'size': span.get('size'),
                                    'font': span.get('font'),
                                    'flags': span.get('flags'),
                                }
                                if span.get('size', 0) > 12:
                                    seg.is_heading = True
                                    seg.heading_level = 1 if span.get('size', 0) > 16 else 2
                                break
            except:
                pass

            segments.append(seg)
            current_pos += len(line) + 1

        return segments

    def _detect_headings_fast(self, text: str) -> list[tuple[int, int, str, int]]:
        headings = []
        lines = text.split('\n')
        prev_was_short = False

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                prev_was_short = False
                continue

            is_heading = False
            level = 1
            char_pos = sum(len(l) + 1 for l in lines[:i])

            if re.match(r'^[A-Z][A-Z\s]{3,}$', line_stripped) and len(line_stripped) <= self.MAX_HEADING_LENGTH:
                if len(line_stripped) >= self.MIN_HEADING_LENGTH:
                    is_heading = True
                    level = 1

            if re.match(r'^\d+\.\s+\S', line_stripped) and not re.search(r'\.{2,}$', line_stripped):
                if len(line_stripped) <= self.MAX_HEADING_LENGTH:
                    is_heading = True
                    level = 2

            if re.match(r'^\d+\.\d+\.?\s+\S', line_stripped):
                if len(line_stripped) <= self.MAX_HEADING_LENGTH:
                    is_heading = True
                    level = 2

            if re.match(r'^[IVX]+\.\s+', line_stripped):
                if len(line_stripped) <= self.MAX_HEADING_LENGTH:
                    is_heading = True
                    level = 1

            if is_heading:
                headings.append((char_pos, char_pos + len(line_stripped), line_stripped, level))

            prev_was_short = len(line_stripped) < 50

        return headings

    def _detect_sections(self, full_text: str, pages: list[PageSegment]) -> list[Section]:
        sections = []
        lines = full_text.split('\n')

        current_section = None
        current_content = []
        current_pages = set()

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue

            is_heading = False
            heading_level = 1
            char_pos = sum(len(l) + 1 for l in lines[:i])

            if re.match(r'^[A-Z][A-Z\s]{3,}$', line_stripped) and len(line_stripped) <= 100:
                is_heading = True
                heading_level = 1
            elif re.match(r'^\d+\.\s+\S', line_stripped) and len(line_stripped) <= 100:
                is_heading = True
                heading_level = 2

            if is_heading:
                if current_section:
                    current_section.content = '\n'.join(current_content).strip()
                    current_section.word_count = len(current_section.content.split())
                    sections.append(current_section)

                current_section = Section(
                    title=line_stripped,
                    level=heading_level,
                    start_page=i // 50 + 1,
                    end_page=i // 50 + 1,
                    content='',
                )
                current_content = []
            else:
                if current_section:
                    current_content.append(line_stripped)

            page_num = i // 50 + 1
            if page_num <= len(pages) if pages else True:
                current_pages.add(page_num)

        if current_section:
            current_section.content = '\n'.join(current_content).strip()
            current_section.word_count = len(current_section.content.split())
            current_section.page_numbers = sorted(list(current_pages))
            sections.append(current_section)

        return sections

    def _calculate_confidence(self, full_text: str, pages: list[PageSegment]) -> float:
        if not full_text:
            return 0.0

        text_ratio = min(1.0, len(full_text) / 100)

        heading_ratio = 0.5
        if pages:
            heading_count = sum(1 for p in pages if p.is_heading)
            heading_ratio = min(1.0, heading_count / max(1, len(pages) * 0.3))

        avg_word_len = sum(len(w) for w in full_text.split()) / max(1, len(full_text.split()))
        quality_ratio = min(1.0, avg_word_len / 4)

        confidence = (text_ratio * 0.3 + heading_ratio * 0.4 + quality_ratio * 0.3)

        return round(confidence, 3)

    async def _extract_links(self, doc) -> list[dict]:
        links = []
        for page_num, page in enumerate(doc):
            for link in page.get_links():
                if link.get('uri'):
                    links.append({
                        'page': page_num + 1,
                        'uri': link['uri'],
                        'bbox': link.get('from'),
                    })
        return links

    async def _extract_images(self, doc) -> list[dict]:
        images = []
        for page_num, page in enumerate(doc):
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                images.append({
                    'page': page_num + 1,
                    'xref': xref,
                    'width': img[1],
                    'height': img[2],
                    'colorspace': img[5],
                })
        return images

    async def _extract_tables(self, doc, pages: list[PageSegment]) -> list[dict]:
        tables = []
        for page_num, page in enumerate(doc):
            tables_on_page = page.find_tables()
            if tables_on_page:
                for table in tables_on_page.tables:
                    tables.append({
                        'page': page_num + 1,
                        'rows': len(table.extract()),
                        'bbox': table.bbox,
                    })
        return tables


pdf_parser = PDFParser()