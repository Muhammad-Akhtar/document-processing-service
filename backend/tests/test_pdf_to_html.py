"""TDD: PDF → HTML converter (PyMuPDF, layout-aware v2)."""

from pathlib import Path

import fitz
import pytest

from app.converters.pdf_to_html import PdfToHtmlConverter
from app.converters.registry import get_default_registry
from app.core.exceptions import ConversionAppError, ValidationAppError

_SAMPLE_PDF = Path(__file__).parent / "fixtures" / "pdf_to_html" / "sample.pdf"
_SAMPLE_2_PDF = Path(__file__).parent / "fixtures" / "pdf_to_html" / "sample_2.pdf"


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


def _write_styled_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((40, 80), "Bold Title", fontsize=18, fontname="helv")
    # helv is regular; use bold/italic fonts for style detection
    page.insert_text((40, 120), "Bold Word", fontsize=12, fontname="hebo")
    page.insert_text((40, 150), "Italic Word", fontsize=11, fontname="heit")
    page.insert_text((40, 180), "Plain Word", fontsize=9.5, fontname="helv")
    doc.save(path)
    doc.close()


def _write_linked_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((40, 100), "LinkedIn", fontsize=12, fontname="helv")
    # Link rect roughly covering the text (PDF y grows downward from top in PyMuPDF)
    rect = fitz.Rect(40, 88, 100, 108)
    page.insert_link(
        {
            "kind": fitz.LINK_URI,
            "from": rect,
            "uri": "https://example.com/profile",
        }
    )
    doc.save(path)
    doc.close()


def _write_underline_drawing_pdf(path: Path) -> None:
    """WeasyPrint-style even-odd double rect → thin horizontal rule."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((40, 100), "SECTION HEADING", fontsize=14, fontname="hebo")
    shape = page.new_shape()
    shape.draw_rect(fitz.Rect(40, 90, 560, 118))
    shape.draw_rect(fitz.Rect(40, 90, 560, 120))
    shape.finish(fill=(0.1, 0.2, 0.35), even_odd=True)
    shape.commit()
    doc.save(path)
    doc.close()


def _write_mailto_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((40, 100), "user@example.com", fontsize=11, fontname="helv")
    page.insert_link(
        {
            "kind": fitz.LINK_URI,
            "from": fitz.Rect(40, 88, 160, 110),
            "uri": "mailto:user@example.com",
        }
    )
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
    assert "position:absolute" in html
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


def test_pdf_to_html_preserves_font_size_and_styles(tmp_path: Path) -> None:
    src = tmp_path / "styled.pdf"
    _write_styled_pdf(src)
    dst = tmp_path / "out.html"
    PdfToHtmlConverter().convert(src, dst)
    html = dst.read_text(encoding="utf-8")
    assert "font-size:18pt" in html or "font-size:18.0pt" in html
    assert "9.5pt" in html
    assert "<strong>" in html
    assert "<em>" in html
    assert "position:absolute" in html
    assert "left:" in html and "top:" in html


def test_pdf_to_html_preserves_hyperlinks(tmp_path: Path) -> None:
    src = tmp_path / "linked.pdf"
    _write_linked_pdf(src)
    dst = tmp_path / "out.html"
    PdfToHtmlConverter().convert(src, dst)
    html = dst.read_text(encoding="utf-8")
    assert 'href="https://example.com/profile"' in html
    assert "<a " in html
    assert "LinkedIn" in html


def test_pdf_to_html_even_odd_section_rule(tmp_path: Path) -> None:
    src = tmp_path / "rule.pdf"
    _write_underline_drawing_pdf(src)
    dst = tmp_path / "out.html"
    PdfToHtmlConverter().convert(src, dst)
    html = dst.read_text(encoding="utf-8")
    assert "pdf-drawing" in html
    assert "SECTION HEADING" in html
    # Thin band (~2pt), not a solid ~30pt heading background.
    assert "height:2pt" in html or "height:2.0pt" in html


def test_pdf_to_html_mailto_links(tmp_path: Path) -> None:
    src = tmp_path / "mail.pdf"
    _write_mailto_pdf(src)
    dst = tmp_path / "out.html"
    PdfToHtmlConverter().convert(src, dst)
    html = dst.read_text(encoding="utf-8")
    assert 'href="mailto:user@example.com"' in html


def test_pdf_to_html_sample_2_drawings_and_mailto(tmp_path: Path) -> None:
    assert _SAMPLE_2_PDF.is_file(), "sample_2.pdf fixture missing"
    dst = tmp_path / "sample2_out.html"
    result = PdfToHtmlConverter().convert(_SAMPLE_2_PDF, dst)
    html = dst.read_text(encoding="utf-8")
    assert result.success is True
    assert "PROFESSIONAL SUMMARY" in html
    assert "TECHNICAL SKILLS" in html
    assert html.count('class="pdf-drawing"') >= 3
    assert "rgb(26,54,93)" in html.replace(" ", "")
    assert 'href="mailto:akhtarm821@gmail.com"' in html
    assert "linkedin.com/in/muhammad-akhtar-47b1a4102" in html


def test_pdf_to_html_sample_fixture_layout(tmp_path: Path) -> None:
    assert _SAMPLE_PDF.is_file(), "sample.pdf fixture missing"
    dst = tmp_path / "sample_out.html"
    result = PdfToHtmlConverter().convert(_SAMPLE_PDF, dst)
    html = dst.read_text(encoding="utf-8")
    assert result.success is True
    assert result.page_count == 2
    assert "MUHAMMAD AKHTAR" in html
    assert "PROFESSIONAL SUMMARY" in html
    assert 'href="https://linkedin.com/in/muhammad-akhtar-web-developer"' in html
    assert "muhammad-akhtar-folio.lovable.app" in html
    assert "612pt" in html and "792pt" in html
    assert "position:absolute" in html
    assert "18pt" in html
    assert "9.5pt" in html
    assert 'data-page="1"' in html
    assert 'data-page="2"' in html


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
