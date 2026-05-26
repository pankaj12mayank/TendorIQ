"""Document Parser Service - Unified Interface"""

import logging
from typing import Optional
from uuid import UUID

from .base import (
    BaseParser, ParsedDocument, ParsingError, UnsupportedFormatError
)
from .pdf_parser import pdf_parser
from .docx_parser import docx_parser
from .chunking import document_chunker, ChunkingResult, ChunkingStrategy
from ..logging import get_logger

logger = get_logger('parser_service')

PARSER_BY_EXT = {
    'pdf': pdf_parser,
    'pdf/a': pdf_parser,
    'docx': docx_parser,
    'docm': docx_parser,
}


class DocumentParserService:
    def __init__(self):
        self.parsers = {
            'pdf': pdf_parser,
            'pdf/a': pdf_parser,
            'docx': docx_parser,
            'docm': docx_parser,
        }

    async def parse(
        self,
        file_bytes: bytes,
        file_name: str,
        document_id: str,
        chunk: bool = True,
        chunking_strategy: str = ChunkingStrategy.HYBRID,
    ) -> tuple[ParsedDocument, Optional[ChunkingResult]]:
        ext = self._get_extension(file_name)

        parser = self.parsers.get(ext)
        if not parser:
            raise UnsupportedFormatError(f'No parser for file type: {ext}')

        try:
            logger.info(f'Parsing document {document_id}', file_type=ext)

            parsed = await parser.parse(file_bytes, file_name, document_id)

            if parsed.parsing_errors:
                logger.warning(
                    f'Document {document_id} had parsing errors',
                    errors=parsed.parsing_errors,
                )

            chunking_result = None
            if chunk and parsed.full_text:
                chunking_result = document_chunker.chunk_document(
                    parsed, chunking_strategy
                )
                logger.info(
                    f'Document {document_id} chunked into {chunking_result.chunk_count} chunks',
                    strategy=chunking_strategy,
                )

            return parsed, chunking_result

        except Exception as e:
            logger.error(f'Failed to parse document {document_id}: {e}')
            raise ParsingError(f'Parsing failed: {str(e)}')

    async def parse_only(
        self,
        file_bytes: bytes,
        file_name: str,
        document_id: str,
    ) -> ParsedDocument:
        parsed, _ = await self.parse(
            file_bytes, file_name, document_id, chunk=False
        )
        return parsed

    async def chunk_existing(
        self,
        document: ParsedDocument,
        strategy: str = ChunkingStrategy.HYBRID,
    ) -> ChunkingResult:
        return document_chunker.chunk_document(document, strategy)

    async def extract_text_only(
        self,
        file_bytes: bytes,
        file_name: str,
    ) -> str:
        ext = self._get_extension(file_name)
        parser = self.parsers.get(ext)

        if not parser:
            raise UnsupportedFormatError(f'No parser for file type: {ext}')

        return await parser.extract_text(file_bytes)

    async def extract_metadata_only(
        self,
        file_bytes: bytes,
        file_name: str,
    ):
        ext = self._get_extension(file_name)
        parser = self.parsers.get(ext)

        if not parser:
            raise UnsupportedFormatError(f'No parser for file type: {ext}')

        return await parser.extract_metadata(file_bytes)

    def can_parse(self, file_name: str) -> bool:
        ext = self._get_extension(file_name)
        return ext in self.parsers

    def _get_extension(self, file_name: str) -> str:
        parts = file_name.lower().rsplit('.', 1)
        if len(parts) == 2:
            return parts[1]
        return ''

    def get_supported_formats(self) -> list[str]:
        return list(self.parsers.keys())


parser_service = DocumentParserService()