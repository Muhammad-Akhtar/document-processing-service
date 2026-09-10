"""Conversion endpoints (sync HTML → PDF in Phase 2)."""

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.models.schemas import ConversionRequest, ConversionResponse
from app.services.conversion import ConversionService
from app.storage.local import LocalStorage

router = APIRouter(prefix="/api/v1/conversions", tags=["conversions"])


def get_storage(settings: Settings = Depends(get_settings)) -> LocalStorage:
    return LocalStorage(settings)


def get_conversion_service(
    storage: LocalStorage = Depends(get_storage),
) -> ConversionService:
    return ConversionService(storage)


@router.post(
    "",
    response_model=ConversionResponse,
    status_code=201,
    summary="Convert a document (sync)",
    description=(
        "Runs conversion in-process via a converter plugin. "
        "HTML → PDF uses WeasyPrint. Async jobs arrive in Phase 6."
    ),
)
def convert_document(
    body: ConversionRequest,
    service: ConversionService = Depends(get_conversion_service),
) -> ConversionResponse:
    return service.convert(
        source_document_id=body.source_document_id,
        target_format=body.target_format,
    )
