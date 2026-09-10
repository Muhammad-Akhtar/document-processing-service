"""TDD: upload validation rules."""

import pytest

from app.core.config import Settings
from app.core.exceptions import ValidationAppError
from app.core.validation import sanitize_filename, validate_upload


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        storage_root=tmp_path,
        max_upload_bytes=100,
        _env_file=None,  # type: ignore[call-arg]
    )


def test_sanitize_filename_strips_path_parts() -> None:
    assert sanitize_filename("../evil.html") == "evil.html"
    assert sanitize_filename("C:\\\\temp\\\\doc.pdf") == "doc.pdf"
    assert sanitize_filename("nested/folder/file.htm") == "file.htm"


def test_sanitize_filename_rejects_empty() -> None:
    with pytest.raises(ValidationAppError):
        sanitize_filename("...")
    with pytest.raises(ValidationAppError):
        sanitize_filename("")


def test_validate_upload_accepts_html(settings: Settings) -> None:
    data = b"<html><body>hi</body></html>"
    result = validate_upload(
        filename="page.html",
        content_type="text/html",
        data=data,
        settings=settings,
    )
    assert result.safe_filename == "page.html"
    assert result.content_type == "text/html"
    assert result.size == len(data)


def test_validate_upload_accepts_pdf_magic(settings: Settings) -> None:
    data = b"%PDF-1.4\n%fake"
    result = validate_upload(
        filename="doc.pdf",
        content_type="application/pdf",
        data=data,
        settings=settings,
    )
    assert result.safe_filename == "doc.pdf"
    assert result.content_type == "application/pdf"


def test_reject_empty_file(settings: Settings) -> None:
    with pytest.raises(ValidationAppError) as exc:
        validate_upload(
            filename="empty.html",
            content_type="text/html",
            data=b"",
            settings=settings,
        )
    assert exc.value.code == "empty_file"


def test_reject_oversized(settings: Settings) -> None:
    with pytest.raises(ValidationAppError) as exc:
        validate_upload(
            filename="big.html",
            content_type="text/html",
            data=b"x" * 101,
            settings=settings,
        )
    assert exc.value.code == "file_too_large"


def test_reject_bad_extension(settings: Settings) -> None:
    with pytest.raises(ValidationAppError) as exc:
        validate_upload(
            filename="virus.exe",
            content_type="application/octet-stream",
            data=b"MZ",
            settings=settings,
        )
    assert exc.value.code == "invalid_extension"


def test_reject_pdf_without_magic(settings: Settings) -> None:
    with pytest.raises(ValidationAppError) as exc:
        validate_upload(
            filename="fake.pdf",
            content_type="application/pdf",
            data=b"not a pdf",
            settings=settings,
        )
    assert exc.value.code == "invalid_content"


def test_reject_path_traversal_filename(settings: Settings) -> None:
    data = b"<html>ok</html>"
    result = validate_upload(
        filename="../../etc/passwd.html",
        content_type="text/html",
        data=data,
        settings=settings,
    )
    assert result.safe_filename == "passwd.html"
    assert ".." not in result.safe_filename
