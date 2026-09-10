"""TDD: HTML → PDF converter (WeasyPrint) and URL security."""

from pathlib import Path

import pytest

from app.converters.html_to_pdf import HtmlToPdfConverter, LocalOnlyUrlFetcher
from app.core.exceptions import ConversionAppError, ValidationAppError
from tests.weasyprint_utils import weasyprint_works

FIXTURES = Path(__file__).parent / "fixtures" / "html_to_pdf"

requires_weasyprint = pytest.mark.skipif(
    not weasyprint_works(),
    reason="WeasyPrint native libraries not available",
)


def test_url_fetcher_allows_local_file(tmp_path: Path) -> None:
    asset = tmp_path / "a.txt"
    asset.write_text("hello", encoding="utf-8")
    fetcher = LocalOnlyUrlFetcher(tmp_path)
    result = fetcher(asset.resolve().as_uri())
    assert result["string"] == b"hello"


def test_url_fetcher_blocks_http_strict() -> None:
    fetcher = LocalOnlyUrlFetcher(Path("."), strict_remote=True)
    with pytest.raises(ConversionAppError) as exc:
        fetcher("https://example.invalid/x.png")
    assert exc.value.code == "remote_url_blocked"


def test_url_fetcher_soft_blocks_http_with_placeholder() -> None:
    fetcher = LocalOnlyUrlFetcher(Path("."), strict_remote=False)
    result = fetcher("https://example.invalid/x.png")
    assert result["mime_type"] == "image/png"
    assert result["string"].startswith(b"\x89PNG")
    assert fetcher.blocked_urls == ["https://example.invalid/x.png"]


def test_url_fetcher_blocks_path_escape(tmp_path: Path) -> None:
    root = tmp_path / "doc"
    root.mkdir()
    outside = tmp_path / "secret.txt"
    outside.write_text("nope", encoding="utf-8")
    fetcher = LocalOnlyUrlFetcher(root)
    with pytest.raises(ConversionAppError) as exc:
        fetcher(outside.resolve().as_uri())
    assert exc.value.code == "asset_path_denied"


@requires_weasyprint
def test_html_to_pdf_produces_non_empty_pdf(tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    # Copy fixture bundle so relative CSS/image resolve locally.
    for name in ("sample.html", "extra.css", "logo.png"):
        (work / name).write_bytes((FIXTURES / name).read_bytes())

    dst = tmp_path / "out.pdf"
    result = HtmlToPdfConverter().convert(work / "sample.html", dst)
    assert result.success is True
    assert dst.is_file()
    assert dst.stat().st_size > 0
    assert dst.read_bytes().startswith(b"%PDF")
    assert result.page_count is not None and result.page_count >= 1
    assert result.title == "Phase 2 Sample"


def test_html_to_pdf_rejects_non_html_source(tmp_path: Path) -> None:
    src = tmp_path / "x.pdf"
    src.write_bytes(b"%PDF-1.4\n")
    dst = tmp_path / "out.pdf"
    with pytest.raises(ValidationAppError) as exc:
        HtmlToPdfConverter().convert(src, dst)
    assert exc.value.code == "unsupported_source"
