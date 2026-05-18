"""Document Chunking System with Overlap"""

import re
import uuid
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

from .base import ParsedDocument, TextChunk, Section


@dataclass
class ChunkConfig:
    chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_size: int = 100
    max_chunk_size: int = 2000
    semantic_splitting: bool = True
    preserve_sections: bool = True
    min_section_words: int = 50


class ChunkingStrategy:
    RAW = 'raw'
    SENTENCE = 'sentence'
    PARAGRAPH = 'paragraph'
    SECTION = 'section'
    HYBRID = 'hybrid'


@dataclass
class ChunkingResult:
    chunks: list[TextChunk]
    total_tokens: int
    strategy: str
    chunk_count: int
    sections_preserved: int
    metadata: dict = field(default_factory=dict)


class DocumentChunker:
    def __init__(self, config: Optional[ChunkConfig] = None):
        self.config = config or ChunkConfig()

    def chunk_document(self, document: ParsedDocument, strategy: str = ChunkingStrategy.HYBRID) -> ChunkingResult:
        if strategy == ChunkingStrategy.RAW:
            return self._chunk_raw(document)
        elif strategy == ChunkingStrategy.SECTION:
            return self._chunk_by_section(document)
        elif strategy == ChunkingStrategy.PARAGRAPH:
            return self._chunk_by_paragraph(document)
        elif strategy == ChunkingStrategy.SENTENCE:
            return self._chunk_by_sentence(document)
        else:
            return self._chunk_hybrid(document)

    def _chunk_raw(self, document: ParsedDocument) -> ChunkingResult:
        text = document.full_text
        chunks = []
        tokens_so_far = 0
        sections_preserved = 0

        start = 0
        chunk_index = 0

        while start < len(text):
            end = min(start + self.config.chunk_size, len(text))

            if end < len(text):
                sentence_end = max(text.rfind(s) for s in '.!?\n' if s in text[start:end] and end - text.rfind(s, start, end) < 100)
                if sentence_end > start + self.config.min_chunk_size:
                    end = sentence_end + 1

            chunk_text = text[start:end].strip()
            if len(chunk_text) < self.config.min_chunk_size and start > 0:
                start = end - self.config.chunk_overlap
                continue

            chunk = self._create_chunk(
                document.document_id,
                chunk_text,
                chunk_index,
                start,
                end,
                1,
                1,
                '',
                tokens_so_far,
            )
            chunks.append(chunk)

            tokens_so_far += len(chunk_text.split())
            start = end - self.config.chunk_overlap
            chunk_index += 1

        return ChunkingResult(
            chunks=chunks,
            total_tokens=tokens_so_far,
            strategy=ChunkingStrategy.RAW,
            chunk_count=len(chunks),
            sections_preserved=0,
        )

    def _chunk_by_section(self, document: ParsedDocument) -> ChunkingResult:
        chunks = []
        tokens_so_far = 0
        chunk_index = 0
        sections_preserved = 0

        for section in document.sections:
            sections_preserved += 1
            section_text = section.content.strip()
            section_path = f"{section.title}"

            if not section_text:
                continue

            if len(section_text) <= self.config.chunk_size:
                chunk = self._create_chunk(
                    document.document_id,
                    section_text,
                    chunk_index,
                    0,
                    len(section_text),
                    section.start_page,
                    section.end_page,
                    section_path,
                    tokens_so_far,
                    {'section_title': section.title, 'level': section.level},
                )
                chunks.append(chunk)
                tokens_so_far += len(section_text.split())
                chunk_index += 1
            else:
                sub_chunks = self._split_large_text(section_text, section_path, chunk_index, tokens_so_far, section)
                chunks.extend(sub_chunks)
                tokens_so_far += sum(len(c.text.split()) for c in sub_chunks)
                chunk_index += len(sub_chunks)

        return ChunkingResult(
            chunks=chunks,
            total_tokens=tokens_so_far,
            strategy=ChunkingStrategy.SECTION,
            chunk_count=len(chunks),
            sections_preserved=sections_preserved,
        )

    def _chunk_by_paragraph(self, document: ParsedDocument) -> ChunkingResult:
        text = document.full_text
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        chunks = []
        tokens_so_far = 0
        chunk_index = 0
        sections_preserved = 0

        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para)

            if current_size + para_size <= self.config.chunk_size:
                current_chunk.append(para)
                current_size += para_size
            else:
                if current_chunk:
                    chunk_text = '\n\n'.join(current_chunk)
                    chunk = self._create_chunk(
                        document.document_id,
                        chunk_text,
                        chunk_index,
                        0,
                        len(chunk_text),
                        1,
                        1,
                        '',
                        tokens_so_far,
                    )
                    chunks.append(chunk)
                    tokens_so_far += len(chunk_text.split())
                    chunk_index += 1

                if para_size > self.config.max_chunk_size:
                    sub_chunks = self._split_large_text(para, '', chunk_index, tokens_so_far)
                    chunks.extend(sub_chunks)
                    tokens_so_far += sum(len(c.text.split()) for c in sub_chunks)
                    chunk_index += len(sub_chunks)
                    current_chunk = []
                    current_size = 0
                else:
                    current_chunk = [para]
                    current_size = para_size

        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunk = self._create_chunk(
                document.document_id,
                chunk_text,
                chunk_index,
                0,
                len(chunk_text),
                1,
                1,
                '',
                tokens_so_far,
            )
            chunks.append(chunk)

        return ChunkingResult(
            chunks=chunks,
            total_tokens=tokens_so_far,
            strategy=ChunkingStrategy.PARAGRAPH,
            chunk_count=len(chunks),
            sections_preserved=sections_preserved,
        )

    def _chunk_by_sentence(self, document: ParsedDocument) -> ChunkingResult:
        text = document.full_text

        sentence_endings = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_endings, text)

        chunks = []
        tokens_so_far = 0
        chunk_index = 0

        current_sentences = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            if current_size + sentence_size <= self.config.chunk_size:
                current_sentences.append(sentence)
                current_size += sentence_size
            else:
                if current_sentences:
                    chunk_text = ' '.join(current_sentences)
                    chunk = self._create_chunk(
                        document.document_id,
                        chunk_text,
                        chunk_index,
                        0,
                        len(chunk_text),
                        1,
                        1,
                        '',
                        tokens_so_far,
                    )
                    chunks.append(chunk)
                    tokens_so_far += len(chunk_text.split())
                    chunk_index += 1

                    overlap_sentences = current_sentences[-2:] if len(current_sentences) >= 2 else current_sentences[-1:]
                    current_sentences = overlap_sentences
                    current_size = sum(len(s) for s in current_sentences)

            if sentence_size > self.config.max_chunk_size:
                sub_chunks = self._split_large_text(sentence, '', chunk_index, tokens_so_far)
                chunks.extend(sub_chunks)
                tokens_so_far += sum(len(c.text.split()) for c in sub_chunks)
                chunk_index += len(sub_chunks)
                current_sentences = []
                current_size = 0

        if current_sentences:
            chunk_text = ' '.join(current_sentences)
            chunk = self._create_chunk(
                document.document_id,
                chunk_text,
                chunk_index,
                0,
                len(chunk_text),
                1,
                1,
                '',
                tokens_so_far,
            )
            chunks.append(chunk)

        return ChunkingResult(
            chunks=chunks,
            total_tokens=tokens_so_far,
            strategy=ChunkingStrategy.SENTENCE,
            chunk_count=len(chunks),
            sections_preserved=0,
        )

    def _chunk_hybrid(self, document: ParsedDocument) -> ChunkingResult:
        chunks = []
        tokens_so_far = 0
        chunk_index = 0
        sections_preserved = 0

        for section in document.sections:
            sections_preserved += 1
            section_text = section.content.strip()
            section_path = f"{section.title}"

            if not section_text:
                continue

            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', section_text) if p.strip()]

            current_paras = []
            current_size = 0

            for para in paragraphs:
                para_size = len(para)

                if current_size + para_size <= self.config.chunk_size:
                    current_paras.append(para)
                    current_size += para_size
                else:
                    if current_paras:
                        chunk_text = '\n\n'.join(current_paras)
                        chunk = self._create_chunk(
                            document.document_id,
                            chunk_text,
                            chunk_index,
                            0,
                            len(chunk_text),
                            section.start_page,
                            section.end_page,
                            section_path,
                            tokens_so_far,
                            {
                                'section_title': section.title,
                                'level': section.level,
                                'word_count': section.word_count,
                            },
                        )
                        chunks.append(chunk)
                        tokens_so_far += len(chunk_text.split())
                        chunk_index += 1

                        if len(current_paras) >= 2:
                            current_paras = current_paras[-1:]
                            current_size = len(current_paras[0]) if current_paras else 0
                        else:
                            current_paras = []
                            current_size = 0

                if para_size > self.config.max_chunk_size:
                    sub_chunks = self._split_large_text(para, section_path, chunk_index, tokens_so_far, section)
                    chunks.extend(sub_chunks)
                    tokens_so_far += sum(len(c.text.split()) for c in sub_chunks)
                    chunk_index += len(sub_chunks)
                    current_paras = []
                    current_size = 0

            if current_paras:
                chunk_text = '\n\n'.join(current_paras)
                chunk = self._create_chunk(
                    document.document_id,
                    chunk_text,
                    chunk_index,
                    0,
                    len(chunk_text),
                    section.start_page,
                    section.end_page,
                    section_path,
                    tokens_so_far,
                    {
                        'section_title': section.title,
                        'level': section.level,
                        'word_count': section.word_count,
                    },
                )
                chunks.append(chunk)
                tokens_so_far += len(chunk_text.split())
                chunk_index += 1

        return ChunkingResult(
            chunks=chunks,
            total_tokens=tokens_so_far,
            strategy=ChunkingStrategy.HYBRID,
            chunk_count=len(chunks),
            sections_preserved=sections_preserved,
        )

    def _split_large_text(
        self,
        text: str,
        section_path: str,
        start_index: int,
        tokens_offset: int,
        section: Optional[Section] = None,
    ) -> list[TextChunk]:
        chunks = []
        start = 0
        chunk_index = start_index
        tokens_so_far = tokens_offset

        while start < len(text):
            end = min(start + self.config.chunk_size, len(text))

            if end < len(text):
                sentence_break = max(
                    (text.rfind(s, start, end) for s in '.!?\n' if s in text[start:end]),
                    default=start + self.config.min_chunk_size,
                )
                if sentence_break > start + self.config.min_chunk_size:
                    end = sentence_break + 1

            chunk_text = text[start:end].strip()
            if len(chunk_text) < self.config.min_chunk_size and start > 0:
                start = end - self.config.chunk_overlap
                continue

            chunk = self._create_chunk(
                text[:20] + '...' if len(text) > 20 else text,
                chunk_text,
                chunk_index,
                start,
                end,
                section.start_page if section else 1,
                section.end_page if section else 1,
                section_path,
                tokens_so_far,
                {'section_title': section.title if section else None},
            )
            chunks.append(chunk)

            tokens_so_far += len(chunk_text.split())
            start = end - self.config.chunk_overlap
            chunk_index += 1

        return chunks

    def _create_chunk(
        self,
        document_id: str,
        text: str,
        chunk_index: int,
        start_char: int,
        end_char: int,
        start_page: int,
        end_page: int,
        section_path: str,
        tokens: int,
        metadata: Optional[dict] = None,
    ) -> TextChunk:
        return TextChunk(
            chunk_id=str(uuid.uuid4()),
            document_id=document_id,
            text=text,
            chunk_index=chunk_index,
            start_char=start_char,
            end_char=end_char,
            start_page=start_page,
            end_page=end_page,
            section_path=section_path,
            tokens=tokens,
            metadata=metadata or {},
        )


document_chunker = DocumentChunker()