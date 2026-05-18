"""Document Parsing Schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ParsedDocumentMetadata(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    keywords: list[str] = Field(default_factory=list)
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    page_count: int = 0
    word_count: int = 0
    language: str = 'en'
    file_size: int = 0
    is_encrypted: bool = False
    is_form: bool = False


class PageSegmentSchema(BaseModel):
    page_number: int
    text: str
    start_char: int
    end_char: int
    bbox: Optional[list[float]] = None
    is_heading: bool = False
    heading_level: Optional[int] = None
    section_title: Optional[str] = None
    confidence: float = 1.0


class SectionSchema(BaseModel):
    title: str
    level: int
    start_page: int
    end_page: int
    content: str
    word_count: int = 0
    page_numbers: list[int] = Field(default_factory=list)


class ParsedDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    file_name: str
    file_type: str
    metadata: ParsedDocumentMetadata
    full_text: str
    page_count: int
    word_count: int
    confidence_score: float
    sections: list[SectionSchema]
    parsing_errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class TextChunkSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    metadata: dict = Field(default_factory=dict)


class ChunkingResultResponse(BaseModel):
    chunks: list[TextChunkSchema]
    total_tokens: int
    strategy: str
    chunk_count: int
    sections_preserved: int


class ParsingRequest(BaseModel):
    document_id: str
    chunk: bool = True
    chunking_strategy: str = Field(default='hybrid', pattern=r'^(raw|sentence|paragraph|section|hybrid)$')


class ParsingStatusResponse(BaseModel):
    success: bool = True
    document_id: str
    status: str
    has_parsed: bool
    has_chunks: bool
    word_count: int = 0
    chunk_count: int = 0
    confidence_score: float = 0.0


class ParsePreviewRequest(BaseModel):
    file_bytes: Optional[str] = None
    file_name: str


class ParsePreviewResponse(BaseModel):
    success: bool = True
    preview_text: str
    word_count: int
    estimated_pages: int
    confidence: float
    warnings: list[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: Optional[dict] = None