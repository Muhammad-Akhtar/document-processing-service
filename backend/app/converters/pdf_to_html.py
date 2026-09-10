"""PDF → HTML converter using PyMuPDF (flow layout, best-effort v1)."""

from __future__ import annotations

import html
import logging
from pathlib import Path

from app.converters.base import ConversionResult
from app.core.exceptions import ConversionAppError, ValidationAppError

logger = logging.getLogger(__name__)

_PDF_SUFFIXES = {".pdf"}
_HEADING_SIZE_THRESHOLD = 14.0


class PdfToHtmlConverter:
    """Convert PDF to simple flow-layout HTML.

    v1 approach: stacked paragraphs/sections (not absolute positioning).
    See ``backend/docs/pdf-to-html-limitations.md``.
    """

    source_format = "pdf"
    target_format = "html"

    def convert(self, source_path: Path, destination_path: Path) -> ConversionResult:
        source_path = source_path.resolve()
        if source_path.suffix.lower() not in _PDF_SUFFIXES:
            raise ValidationAppError(
                "PDF → HTML converter requires a .pdf source",
                code="unsupported_source",
            )
        if not source_path.is_file():
            raise ValidationAppError(
                "Source PDF file does not exist",
                code="unsupported_source",
            )

        try:
            import fitz
        except ImportError as exc:
            raise ConversionAppError(
                "PyMuPDF is not installed",
                code="conversion_dependency_missing",
            ) from exc

        warnings: list[str] = []
        try:
            doc = fitz.open(source_path)
        except Exception as exc:
            logger.exception("Failed to open PDF %s", source_path)
            raise ConversionAppError(
                "PDF could not be opened",
                code="pdf_unreadable",
                details={"reason": str(exc)},
            ) from exc

        try:
            if doc.is_encrypted and not doc.authenticate(""):
                raise ConversionAppError(
                    "Encrypted PDFs are not supported without a password",
                    code="pdf_encrypted",
                )

            destination_path.parent.mkdir(parents=True, exist_ok=True)
            assets_dir = destination_path.parent / "assets"
            assets_dir.mkdir(parents=True, exist_ok=True)

            title = (doc.metadata or {}).get("title") or source_path.stem
            page_sections: list[str] = []

            for page_index in range(doc.page_count):
                page = doc.load_page(page_index)
                section_html, page_warnings = _page_to_html(
                    doc, page, page_index + 1, assets_dir
                )
                page_sections.append(section_html)
                warnings.extend(page_warnings)

            body = "\n".join(page_sections)
            document_html = _wrap_document(title=title, body=body)
            destination_path.write_text(document_html, encoding="utf-8")
            page_count = doc.page_count
        finally:
            doc.close()

        if not destination_path.is_file() or destination_path.stat().st_size == 0:
            raise ConversionAppError(
                "Conversion produced empty HTML",
                code="conversion_failed",
            )

        warnings.append(
            "PDF → HTML v1 uses best-effort flow layout; complex layouts may degrade."
        )

        return ConversionResult(
            success=True,
            output_path=destination_path,
            warnings=warnings,
            page_count=page_count,
            title=title if isinstance(title, str) else None,
        )


def _page_to_html(
    doc,
    page,
    page_number: int,
    assets_dir: Path,
) -> tuple[str, list[str]]:
    warnings: list[str] = []
    parts: list[str] = [f'<section data-page="{page_number}">']

    # Text blocks (dict preserves reading-order blocks/lines/spans).
    try:
        data = page.get_text("dict", flags=0)
    except Exception as exc:
        logger.warning("Text extraction failed on page %s: %s", page_number, exc)
        warnings.append(f"Text extraction failed on page {page_number}")
        data = {"blocks": []}

    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        line_texts: list[str] = []
        max_size = 0.0
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            text = "".join(span.get("text", "") for span in spans).strip()
            if not text:
                continue
            line_texts.append(text)
            for span in spans:
                max_size = max(max_size, float(span.get("size") or 0))
        if not line_texts:
            continue
        joined = " ".join(line_texts)
        escaped = html.escape(joined)
        if max_size >= _HEADING_SIZE_THRESHOLD:
            parts.append(f'<h2 class="pdf-heading">{escaped}</h2>')
        else:
            parts.append(f'<p class="pdf-block">{escaped}</p>')

    # Embedded images
    try:
        images = page.get_images(full=True)
    except Exception as exc:
        logger.warning("Image list failed on page %s: %s", page_number, exc)
        warnings.append(f"Image enumeration failed on page {page_number}")
        images = []

    for img_index, img in enumerate(images):
        xref = img[0]
        try:
            extracted = doc.extract_image(xref)
            image_bytes = extracted["image"]
            ext = extracted.get("ext") or "png"
            name = f"p{page_number}_img{img_index}.{ext}"
            (assets_dir / name).write_bytes(image_bytes)
            parts.append(
                f'<img class="pdf-image" src="assets/{html.escape(name)}" alt="" />'
            )
        except Exception as exc:
            logger.warning(
                "Skipping image xref=%s on page %s: %s", xref, page_number, exc
            )
            warnings.append(f"Skipped image on page {page_number}")

    parts.append("</section>")
    return "\n".join(parts), warnings


def _wrap_document(*, title: str, body: str) -> str:
    safe_title = html.escape(title or "Converted PDF")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>{safe_title}</title>
  <style>
    body {{
      font-family: system-ui, sans-serif;
      max-width: 48rem;
      margin: 1.5rem auto;
      padding: 0 1rem;
      line-height: 1.5;
      color: #1a1a1a;
    }}
    section[data-page] {{
      margin-bottom: 2rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid #ddd;
    }}
    .pdf-heading {{ font-size: 1.35rem; margin: 0.75rem 0 0.35rem; }}
    .pdf-block {{ margin: 0.4rem 0; }}
    .pdf-image {{ max-width: 100%; height: auto; display: block; margin: 0.75rem 0; }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""
