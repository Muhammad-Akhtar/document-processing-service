"""Local filesystem storage under STORAGE_ROOT (no path traversal)."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from app.core.config import Settings
from app.core.exceptions import NotFoundAppError, StorageAppError
from app.models.schemas import DocumentMeta


class LocalStorage:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._uploads = settings.uploads_dir
        self._uploads.mkdir(parents=True, exist_ok=True)

    def _doc_dir(self, document_id: UUID) -> Path:
        return self._safe_join(self._uploads, str(document_id))

    def _meta_path(self, document_id: UUID) -> Path:
        return self._doc_dir(document_id) / "meta.json"

    def _safe_join(self, root: Path, *parts: str) -> Path:
        candidate = (root.joinpath(*parts)).resolve()
        root_resolved = root.resolve()
        try:
            candidate.relative_to(root_resolved)
        except ValueError as exc:
            raise StorageAppError("Path escapes storage root") from exc
        return candidate

    def save_upload(
        self,
        *,
        filename: str,
        content_type: str,
        data: bytes,
        document_id: UUID | None = None,
    ) -> DocumentMeta:
        doc_id = document_id or uuid4()
        doc_dir = self._doc_dir(doc_id)
        doc_dir.mkdir(parents=True, exist_ok=False)

        file_path = self._safe_join(doc_dir, filename)
        file_path.write_bytes(data)

        created_at = datetime.now(UTC)
        relative = file_path.relative_to(self._settings.storage_root.resolve()).as_posix()
        meta = DocumentMeta(
            id=doc_id,
            original_filename=filename,
            content_type=content_type,
            size=len(data),
            stored_path=relative,
            created_at=created_at,
        )
        self._meta_path(doc_id).write_text(
            meta.model_dump_json(),
            encoding="utf-8",
        )
        return meta

    def exists(self, document_id: UUID) -> bool:
        return self._meta_path(document_id).is_file()

    def get_meta(self, document_id: UUID) -> DocumentMeta:
        path = self._meta_path(document_id)
        if not path.is_file():
            raise NotFoundAppError(f"Document {document_id} not found")
        payload = json.loads(path.read_text(encoding="utf-8"))
        return DocumentMeta.model_validate(payload)

    def get_path(self, document_id: UUID | str) -> Path:
        doc_id = self._parse_document_id(document_id)
        meta = self.get_meta(doc_id)
        path = self._safe_join(self._settings.storage_root, *meta.stored_path.split("/"))
        if not path.is_file():
            raise NotFoundAppError(f"Document file for {doc_id} not found")
        return path

    def delete(self, document_id: UUID) -> None:
        if not self.exists(document_id):
            raise NotFoundAppError(f"Document {document_id} not found")
        shutil.rmtree(self._doc_dir(document_id))

    @staticmethod
    def _parse_document_id(document_id: UUID | str) -> UUID:
        if isinstance(document_id, UUID):
            return document_id
        try:
            return UUID(str(document_id))
        except (ValueError, TypeError) as exc:
            raise StorageAppError("Invalid document id") from exc
