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
