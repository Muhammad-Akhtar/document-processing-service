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
        self._outputs = settings.outputs_dir
        self._uploads.mkdir(parents=True, exist_ok=True)
        self._outputs.mkdir(parents=True, exist_ok=True)

    def _doc_dir(self, document_id: UUID, *, kind: str = "uploads") -> Path:
        root = self._uploads if kind == "uploads" else self._outputs
        return self._safe_join(root, str(document_id))

    def _locate_doc_dir(self, document_id: UUID) -> Path:
        for kind in ("uploads", "outputs"):
            candidate = self._doc_dir(document_id, kind=kind)
            if (candidate / "meta.json").is_file():
                return candidate
        raise NotFoundAppError(f"Document {document_id} not found")

    def _meta_path(self, document_id: UUID) -> Path:
        return self._locate_doc_dir(document_id) / "meta.json"

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
        return self._save(
            kind="uploads",
            filename=filename,
            content_type=content_type,
            data=data,
            document_id=document_id,
        )

    def save_output(
        self,
        *,
        filename: str,
        content_type: str,
        data: bytes,
        document_id: UUID | None = None,
        page_count: int | None = None,
        title: str | None = None,
        assets_dir: Path | None = None,
    ) -> DocumentMeta:
        return self._save(
            kind="outputs",
            filename=filename,
            content_type=content_type,
            data=data,
            document_id=document_id,
            page_count=page_count,
            title=title,
            assets_dir=assets_dir,
        )

    def _save(
        self,
        *,
        kind: str,
        filename: str,
        content_type: str,
        data: bytes,
        document_id: UUID | None = None,
        page_count: int | None = None,
        title: str | None = None,
        assets_dir: Path | None = None,
    ) -> DocumentMeta:
        doc_id = document_id or uuid4()
        doc_dir = self._doc_dir(doc_id, kind=kind)
        doc_dir.mkdir(parents=True, exist_ok=False)

        file_path = self._safe_join(doc_dir, filename)
        file_path.write_bytes(data)

        if assets_dir is not None and assets_dir.is_dir() and any(assets_dir.iterdir()):
            dest_assets = doc_dir / "assets"
            shutil.copytree(assets_dir, dest_assets)

        created_at = datetime.now(UTC)
        relative = file_path.relative_to(self._settings.storage_root.resolve()).as_posix()
        meta = DocumentMeta(
            id=doc_id,
            original_filename=filename,
            content_type=content_type,
            size=len(data),
            stored_path=relative,
            created_at=created_at,
            page_count=page_count,
            title=title,
        )
        (doc_dir / "meta.json").write_text(
            meta.model_dump_json(),
            encoding="utf-8",
        )
        return meta

    def exists(self, document_id: UUID) -> bool:
        try:
            self._locate_doc_dir(document_id)
            return True
        except NotFoundAppError:
            return False

    def get_meta(self, document_id: UUID) -> DocumentMeta:
        path = self._meta_path(document_id)
        payload = json.loads(path.read_text(encoding="utf-8"))
        return DocumentMeta.model_validate(payload)

    def get_path(self, document_id: UUID | str) -> Path:
        doc_id = self._parse_document_id(document_id)
        meta = self.get_meta(doc_id)
        path = self._safe_join(self._settings.storage_root, *meta.stored_path.split("/"))
        if not path.is_file():
            raise NotFoundAppError(f"Document file for {doc_id} not found")
        return path

    def get_asset_path(self, document_id: UUID, asset_name: str) -> Path:
        if (
            not asset_name
            or asset_name != Path(asset_name).name
            or "/" in asset_name
            or "\\" in asset_name
            or asset_name in {".", ".."}
        ):
            raise StorageAppError("Invalid asset name")

        doc_dir = self._locate_doc_dir(document_id)
        assets_root = doc_dir / "assets"
        if not assets_root.is_dir():
            raise NotFoundAppError(f"No assets for document {document_id}")
        path = self._safe_join(assets_root, asset_name)
        if not path.is_file():
            raise NotFoundAppError(f"Asset {asset_name!r} not found")
        return path

    def delete(self, document_id: UUID) -> None:
        doc_dir = self._locate_doc_dir(document_id)
        shutil.rmtree(doc_dir)

    @staticmethod
    def _parse_document_id(document_id: UUID | str) -> UUID:
        if isinstance(document_id, UUID):
            return document_id
        try:
            return UUID(str(document_id))
        except (ValueError, TypeError) as exc:
            raise StorageAppError("Invalid document id") from exc
