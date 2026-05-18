"""Document Parser Base Interfaces"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class DocumentMetadata:
    title: Optional[str] = None
    author: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    keywords: list[str] = field(default_factory=list)
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    page_count: int = 0
    word_count: int = 0
    language: str = 'en'
    file_size: int = 0
    is_encrypted: bool = False
    is_form: bool = False
    custom: dict = field(default_factory=dict)


@dataclass
class PageSegment:
    page_number: int
    text: str
    start_char: int
    end_char: int
    bbox: Optional[tuple[float, float, float, float]] = None
    is_heading: bool = False
    heading_level: Optional[int] = None
    section_title: Optional[str] = None
    confidence: float = 1.0
    font_info: Optional[dict] = None


@dataclass
class Section:
    title: str
    level: int
    start_page: int
    end_page: int
    content: str
    subsections: list['Section'] = field(default_factory=list)
    page_numbers: list[int] = field(default_factory=list)
    word_count: int = 0


@dataclass
class ParsedDocument:
    document_id: str
    file_name: str
    file_type: str
    metadata: DocumentMetadata
    full_text: str
    pages: list[PageSegment]
    sections: list[Section]
    tables: list[dict] = field(default_factory=list)
    images: list[dict] = field(default_factory=list)
    links: list[dict] = field(default_factory=list)
    parsed_at: datetime = field(default_factory=datetime.utcnow)
    parsing_errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    confidence_score: float = 1.0


@dataclass
class TextChunk:
    chunk_id: str
    document_id: str
    text: str
    chunk_index: int
    start_char: int
    end_char: int
    start_page: int
    end_page: int
    section_path: str
    tokens: int = 0
    embedding: Optional[list[float]] = None
    metadata: dict = field(default_factory=dict)


class BaseParser(ABC):
    supported_extensions: list[str] = []

    @abstractmethod
    async def parse(self, file_bytes: bytes, file_name: str, document_id: str) -> ParsedDocument:
        """Parse document and return structured output"""
        pass

    @abstractmethod
    async def extract_metadata(self, file_bytes: bytes) -> DocumentMetadata:
        """Extract document metadata"""
        pass

    @abstractmethod
    async def extract_text(self, file_bytes: bytes) -> str:
        """Extract raw text from document"""
        pass

    def can_parse(self, file_name: str) -> bool:
        """Check if this parser can handle the file"""
        ext = file_name.lower().split('.')[-1]
        return ext in self.supported_extensions

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize extracted text"""
        import re

        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\r', '\n', text)

        text = re.sub(r'[ \t]+', ' ', text)

        text = re.sub(r'\n{3,}', '\n\n', text)

        lines = text.split('\n')
        normalized_lines = []
        for line in lines:
            line = line.strip()
            if line or (normalized_lines and normalized_lines[-1]):
                normalized_lines.append(line)

        return '\n'.join(normalized_lines).strip()


class ParsingError(Exception):
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(ParsingError):
    pass


class UnsupportedFormatError(ParsingError):
    pass