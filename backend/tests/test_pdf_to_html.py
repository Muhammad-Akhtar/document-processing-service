"""TDD: PDF → HTML converter (PyMuPDF, flow layout)."""

from pathlib import Path

import fitz
import pytest

from app.converters.pdf_to_html import PdfToHtmlConverter
from app.converters.registry import get_default_registry
from app.core.exceptions import ConversionAppError, ValidationAppError


def _write_simple_pdf(path: Path, text: str = "Hello Phase 3 PDF") -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text, fontsize=16)
    doc.save(path)
    doc.close()


def _write_multipage_pdf(path: Path) -> None:
    doc = fitz.open()
    for i, label in enumerate(("Page One Content", "Page Two Content"), start=1):
        page = doc.new_page()
        page.insert_text((72, 72), label, fontsize=14)
        page.insert_text((72, 100), f"Marker {i}", fontsize=11)
    doc.save(path)
    doc.close()


def _write_pdf_with_image(path: Path, png_bytes: Path) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "PDF with image", fontsize=14)
    rect = fitz.Rect(72, 100, 136, 164)
    page.insert_image(rect, filename=str(png_bytes))
    doc.save(path)
    doc.close()


@pytest.fixture
def simple_pdf(tmp_path: Path) -> Path:
    path = tmp_path / "simple.pdf"
    _write_simple_pdf(path)
    return path


def test_registry_returns_pdf_to_html() -> None:
    converter = get_default_registry().get("pdf", "html")
    assert isinstance(converter, PdfToHtmlConverter)


def test_pdf_to_html_contains_known_text(simple_pdf: Path, tmp_path: Path) -> None:
    dst = tmp_path / "out.html"
    result = PdfToHtmlConverter().convert(simple_pdf, dst)
    assert result.success is True
    html = dst.read_text(encoding="utf-8")
    assert "Hello Phase 3 PDF" in html
    assert 'data-page="1"' in html
    assert result.page_count == 1


def test_pdf_to_html_multipage_sections(tmp_path: Path) -> None:
    src = tmp_path / "multi.pdf"
    _write_multipage_pdf(src)
    dst = tmp_path / "out.html"
    result = PdfToHtmlConverter().convert(src, dst)
    html = dst.read_text(encoding="utf-8")
    assert 'data-page="1"' in html
    assert 'data-page="2"' in html
    assert "Page One Content" in html
    assert "Page Two Content" in html
    assert result.page_count == 2


def test_pdf_to_html_extracts_image(tmp_path: Path) -> None:
    png = Path(__file__).parent / "fixtures" / "html_to_pdf" / "logo.png"
    src = tmp_path / "with_img.pdf"
    _write_pdf_with_image(src, png)
    dst = tmp_path / "out.html"
    result = PdfToHtmlConverter().convert(src, dst)
    html = dst.read_text(encoding="utf-8")
    assets = dst.parent / "assets"
    assert assets.is_dir()
    assert any(assets.iterdir())
    assert "assets/" in html
    assert result.warnings is not None


def test_pdf_to_html_rejects_non_pdf(tmp_path: Path) -> None:
    src = tmp_path / "x.html"
    src.write_text("<html></html>", encoding="utf-8")
    dst = tmp_path / "out.html"
    with pytest.raises(ValidationAppError) as exc:
        PdfToHtmlConverter().convert(src, dst)
    assert exc.value.code == "unsupported_source"


def test_pdf_to_html_corrupt_file(tmp_path: Path) -> None:
    src = tmp_path / "bad.pdf"
    src.write_bytes(b"not-a-real-pdf")
    dst = tmp_path / "out.html"
    with pytest.raises(ConversionAppError) as exc:
        PdfToHtmlConverter().convert(src, dst)
    assert exc.value.code in {"pdf_unreadable", "conversion_failed"}


def test_pdf_to_html_encrypted(tmp_path: Path) -> None:
    src = tmp_path / "locked.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "secret", fontsize=12)
    doc.save(
        src,
        encryption=fitz.PDF_ENCRYPT_AES_256,
        user_pw="user",
        owner_pw="owner",
    )
    doc.close()

    dst = tmp_path / "out.html"
    with pytest.raises(ConversionAppError) as exc:
        PdfToHtmlConverter().convert(src, dst)
    assert exc.value.code == "pdf_encrypted"
