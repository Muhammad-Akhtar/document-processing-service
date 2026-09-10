"""TDD: API / domain schema construction."""

from datetime import UTC, datetime
from uuid import uuid4

from app.models.schemas import (
    ConversionRequest,
    DocumentMeta,
    ErrorResponse,
    JobStatus,
    UploadResponse,
)


def test_document_meta_fields() -> None:
    doc_id = uuid4()
    created = datetime.now(UTC)
    meta = DocumentMeta(
        id=doc_id,
        original_filename="sample.html",
        content_type="text/html",
        size=42,
        stored_path="uploads/abc/sample.html",
        created_at=created,
    )
    assert meta.id == doc_id
    assert meta.original_filename == "sample.html"
    assert meta.size == 42


def test_upload_response_fields() -> None:
    doc_id = uuid4()
    response = UploadResponse(
        document_id=doc_id,
        filename="a.pdf",
        content_type="application/pdf",
        size=100,
    )
    assert response.document_id == doc_id
    assert response.filename == "a.pdf"


def test_error_response_optional_details() -> None:
    err = ErrorResponse(code="validation_error", message="bad file")
    assert err.details is None


def test_conversion_request_stub() -> None:
    req = ConversionRequest(source_document_id=uuid4(), target_format="pdf")
    assert req.target_format == "pdf"


def test_job_status_enum_values() -> None:
    assert JobStatus.pending.value == "pending"
    assert JobStatus.processing.value == "processing"
    assert JobStatus.completed.value == "completed"
    assert JobStatus.failed.value == "failed"
