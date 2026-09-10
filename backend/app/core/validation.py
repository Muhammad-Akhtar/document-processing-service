"""Upload validation: size, extension, content checks, filename sanitization."""

from dataclasses import dataclass
from pathlib import PurePosixPath, PureWindowsPath

from app.core.config import Settings
from app.core.exceptions import ValidationAppError

ALLOWED_EXTENSIONS = {".html", ".htm", ".pdf"}

# HTML remote URL fetching must stay disabled / allowlisted in Phase 2 converters.
HTML_REMOTE_FETCH_POLICY = "disabled_until_allowlisted"


@dataclass(slots=True, frozen=True)
class ValidatedUpload:
    safe_filename: str
    content_type: str
    size: int
    extension: str


def sanitize_filename(filename: str) -> str:
    if not filename or not filename.strip():
        raise ValidationAppError("Filename is required", code="invalid_filename")

    name = filename.replace("\\", "/")
    # Drop any directory components (path traversal / absolute paths).
    posix_name = PurePosixPath(name).name
    win_name = PureWindowsPath(posix_name).name
    safe = win_name.strip()

    if not safe or safe in {".", ".."} or set(safe) <= {"."}:
        raise ValidationAppError("Filename is invalid", code="invalid_filename")

    return safe


def _extension(filename: str) -> str:
    return PurePosixPath(filename).suffix.lower()


def _detect_content_type(extension: str, declared: str | None, data: bytes) -> str:
    declared_norm = (declared or "").split(";")[0].strip().lower()

    if extension == ".pdf":
        if not data.startswith(b"%PDF"):
            raise ValidationAppError(
                "File content is not a valid PDF",
                code="invalid_content",
            )
        return "application/pdf"

    if extension in {".html", ".htm"}:
        # Soft check: reject obvious binary payloads for HTML.
        if b"\x00" in data[:1024]:
            raise ValidationAppError(
                "File content is not valid HTML",
                code="invalid_content",
            )
        if declared_norm in {"text/html", "application/xhtml+xml", "text/plain", ""}:
            return "text/html"
        return "text/html"

    raise ValidationAppError("Unsupported file type", code="invalid_extension")


def validate_upload(
    *,
    filename: str,
    content_type: str | None,
    data: bytes,
    settings: Settings,
) -> ValidatedUpload:
    if not data:
        raise ValidationAppError("Empty files are not allowed", code="empty_file")

    if len(data) > settings.max_upload_bytes:
        raise ValidationAppError(
            f"File exceeds max size of {settings.max_upload_bytes} bytes",
            code="file_too_large",
            status_code=413,
        )

    safe_filename = sanitize_filename(filename)
    extension = _extension(safe_filename)
    if extension not in ALLOWED_EXTENSIONS:
        raise ValidationAppError(
            f"Extension {extension!r} is not allowed",
            code="invalid_extension",
        )

    resolved_type = _detect_content_type(extension, content_type, data)
    return ValidatedUpload(
        safe_filename=safe_filename,
        content_type=resolved_type,
        size=len(data),
        extension=extension,
    )
