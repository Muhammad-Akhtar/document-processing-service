"""Pydantic API / domain schemas (DB models arrive in Phase 5)."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class DocumentMeta(BaseModel):
    id: UUID
    original_filename: str
    content_type: str
    size: int = Field(ge=0)
    stored_path: str
    created_at: datetime
    page_count: int | None = None
    title: str | None = None


class UploadResponse(BaseModel):
    document_id: UUID
    filename: str
    content_type: str
    size: int = Field(ge=0)


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Any = None


class ConversionRequest(BaseModel):
    source_document_id: UUID
    target_format: str


class ConversionResponse(BaseModel):
    source_document_id: UUID
    output_document_id: UUID
    target_format: str
    filename: str
    content_type: str
    size: int = Field(ge=0)
    page_count: int | None = None
    title: str | None = None
    warnings: list[str] = Field(default_factory=list)
    download_url: str
