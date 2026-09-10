"""Conversion orchestration (sync until Celery in Phase 6)."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from uuid import UUID

from app.converters.registry import ConverterRegistry, get_default_registry
from app.core.exceptions import ConversionAppError, ValidationAppError
from app.models.schemas import ConversionResponse, DocumentMeta
from app.storage.local import LocalStorage

logger = logging.getLogger(__name__)


class ConversionService:
    def __init__(
        self,
        storage: LocalStorage,
        registry: ConverterRegistry | None = None,
    ) -> None:
        self._storage = storage
        self._registry = registry or get_default_registry()

    def convert(
        self,
        *,
        source_document_id: UUID,
        target_format: str,
    ) -> ConversionResponse:
        target = target_format.strip().lower()
        source_meta = self._storage.get_meta(source_document_id)
        source_path = self._storage.get_path(source_document_id)
        source_format = _infer_source_format(source_meta, source_path)

        try:
            converter = self._registry.get(source_format, target)
        except KeyError as exc:
            raise ValidationAppError(
                f"No converter for {source_format!r} → {target!r}",
                code="unsupported_conversion",
            ) from exc

        suffix = f".{target}"
        with tempfile.TemporaryDirectory(prefix="convert-") as tmp:
            dest = Path(tmp) / f"output{suffix}"
            result = converter.convert(source_path, dest)
            if not result.success or result.output_path is None:
                raise ConversionAppError(
                    result.error or "Conversion failed",
                    code="conversion_failed",
                )
            output_bytes = result.output_path.read_bytes()
            assets_dir = result.output_path.parent / "assets"
            out_name = _output_filename(source_meta.original_filename, target)
            output_meta = self._storage.save_output(
                filename=out_name,
                content_type=_content_type_for(target),
                data=output_bytes,
                page_count=result.page_count,
                title=result.title,
                assets_dir=assets_dir if assets_dir.is_dir() else None,
            )

        logger.info(
            "Converted %s (%s→%s) to %s pages=%s",
            source_document_id,
            source_format,
            target,
            output_meta.id,
            result.page_count,
        )

        return ConversionResponse(
            source_document_id=source_document_id,
            output_document_id=output_meta.id,
            target_format=target,
            filename=output_meta.original_filename,
            content_type=output_meta.content_type,
            size=output_meta.size,
            page_count=result.page_count,
            title=result.title,
            warnings=result.warnings,
            download_url=f"/api/v1/documents/{output_meta.id}/download",
        )


def _infer_source_format(meta: DocumentMeta, path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".html", ".htm"} or meta.content_type.startswith("text/html"):
        return "html"
    if ext == ".pdf" or meta.content_type == "application/pdf":
        return "pdf"
    raise ValidationAppError(
        f"Cannot infer source format for {meta.original_filename!r}",
        code="unsupported_source",
    )


def _output_filename(original: str, target: str) -> str:
    stem = Path(original).stem or "document"
    return f"{stem}.{target}"


def _content_type_for(target: str) -> str:
    if target == "pdf":
        return "application/pdf"
    if target == "html":
        return "text/html"
    return "application/octet-stream"
