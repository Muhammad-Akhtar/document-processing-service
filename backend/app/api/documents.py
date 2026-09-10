"""Document upload, metadata, download, preview, and delete APIs."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse, Response

from app.core.config import Settings, get_settings
from app.core.validation import validate_upload
from app.models.schemas import DocumentMeta, UploadResponse
from app.storage.local import LocalStorage

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# Preview strategy A (default): return original bytes for browser built-in viewers.
# Optional first-page PNG rendering remains available as a future enhancement.
PREVIEW_STRATEGY = "original_bytes"


def get_storage(settings: Settings = Depends(get_settings)) -> LocalStorage:
    return LocalStorage(settings)


@router.post(
    "",
    response_model=UploadResponse,
    status_code=201,
    summary="Upload a document",
)
async def upload_document(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    storage: LocalStorage = Depends(get_storage),
) -> UploadResponse:
    data = await file.read()
    validated = validate_upload(
        filename=file.filename or "upload.bin",
        content_type=file.content_type,
        data=data,
        settings=settings,
    )
    meta = storage.save_upload(
        filename=validated.safe_filename,
        content_type=validated.content_type,
        data=data,
    )
    return UploadResponse(
        document_id=meta.id,
        filename=meta.original_filename,
        content_type=meta.content_type,
        size=meta.size,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentMeta,
    summary="Get document metadata",
)
def get_document(
    document_id: UUID,
    storage: LocalStorage = Depends(get_storage),
) -> DocumentMeta:
    return storage.get_meta(document_id)


@router.get(
    "/{document_id}/download",
    summary="Download original document",
    responses={200: {"content": {"application/octet-stream": {}}}},
)
def download_document(
    document_id: UUID,
    storage: LocalStorage = Depends(get_storage),
) -> FileResponse:
    meta = storage.get_meta(document_id)
    path = storage.get_path(document_id)
    return FileResponse(
        path,
        media_type=meta.content_type,
        filename=meta.original_filename,
    )


@router.get(
    "/{document_id}/preview",
    summary="Preview document (original bytes; browser PDF/HTML viewers)",
    description=(
        "Default preview strategy: return original file bytes "
        f"(`{PREVIEW_STRATEGY}`). HTML previews may load sibling "
        "`/assets/{{name}}` for extracted images."
    ),
)
def preview_document(
    document_id: UUID,
    storage: LocalStorage = Depends(get_storage),
) -> Response:
    meta = storage.get_meta(document_id)
    path = storage.get_path(document_id)
    headers = {
        "Content-Security-Policy": (
            "default-src 'none'; img-src 'self' data:; "
            "style-src 'unsafe-inline'; sandbox allow-same-origin"
        ),
        "X-Content-Type-Options": "nosniff",
    }
    return Response(
        content=path.read_bytes(),
        media_type=meta.content_type,
        headers=headers,
    )


@router.get(
    "/{document_id}/assets/{asset_name}",
    summary="Fetch an asset belonging to a document (e.g. PDF→HTML images)",
)
def get_document_asset(
    document_id: UUID,
    asset_name: str,
    storage: LocalStorage = Depends(get_storage),
) -> FileResponse:
    path = storage.get_asset_path(document_id, asset_name)
    return FileResponse(path)


@router.delete(
    "/{document_id}",
    status_code=204,
    summary="Delete a document",
)
def delete_document(
    document_id: UUID,
    storage: LocalStorage = Depends(get_storage),
) -> Response:
    storage.delete(document_id)
    return Response(status_code=204)
