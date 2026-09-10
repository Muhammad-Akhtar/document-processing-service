"""PDF → HTML converter using PyMuPDF (layout-aware absolute positioning, v2)."""

from __future__ import annotations

import html
import logging
from pathlib import Path
from urllib.parse import urlparse

from app.converters.base import ConversionResult
from app.core.exceptions import ConversionAppError, ValidationAppError

logger = logging.getLogger(__name__)

_PDF_SUFFIXES = {".pdf"}
_SAFE_URI_SCHEMES = {"http", "https"}
_LINK_OVERLAP_PAD = 1.0


class PdfToHtmlConverter:
    """Convert PDF to layout-aware HTML preserving spans, styles, links, and coords.

    v2 approach: page-sized containers with absolute-positioned elements.
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
            "PDF → HTML v2 uses absolute visual layout; semantic structure "
            "(tables, lists) is not reconstructed."
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
    rect = page.rect
    width = float(rect.width)
    height = float(rect.height)

    parts: list[str] = [
        (
            f'<section data-page="{page_number}" class="pdf-page" '
            f'style="width:{width:g}pt;height:{height:g}pt;">'
        )
    ]

    uri_links = _uri_links(page)

    try:
        data = page.get_text("dict", flags=0)
    except Exception as exc:
        logger.warning("Text extraction failed on page %s: %s", page_number, exc)
        warnings.append(f"Text extraction failed on page {page_number}")
        data = {"blocks": []}

    image_index = 0
    for block in data.get("blocks", []):
        block_type = block.get("type")
        if block_type == 0:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    element = _span_to_html(span, uri_links)
                    if element:
                        parts.append(element)
        elif block_type == 1:
            img_html, img_warn, image_index = _image_block_to_html(
                doc, block, page_number, assets_dir, image_index
            )
            if img_html:
                parts.append(img_html)
            if img_warn:
                warnings.append(img_warn)

    # Fallback: images listed by get_images but missing as dict type-1 blocks.
    if image_index == 0:
        fallback_parts, fallback_warnings = _fallback_images(
            doc, page, page_number, assets_dir
        )
        parts.extend(fallback_parts)
        warnings.extend(fallback_warnings)

    parts.append("</section>")
    return "\n".join(parts), warnings


def _uri_links(page) -> list[tuple[tuple[float, float, float, float], str]]:
    import fitz

    links: list[tuple[tuple[float, float, float, float], str]] = []
    try:
        raw_links = page.get_links()
    except Exception:
        return links

    uri_kind = getattr(fitz, "LINK_URI", 2)
    for link in raw_links:
        uri = link.get("uri")
        if not uri or not isinstance(uri, str):
            continue
        kind = link.get("kind")
        if kind is not None and kind != uri_kind:
            continue
        if not _safe_http_uri(uri):
            continue
        from_rect = link.get("from")
        if from_rect is None:
            continue
        try:
            r = fitz.Rect(from_rect)
            links.append(((float(r.x0), float(r.y0), float(r.x1), float(r.y1)), uri))
        except Exception:
            continue
    return links


def _safe_http_uri(uri: str) -> bool:
    try:
        parsed = urlparse(uri.strip())
    except Exception:
        return False
    return parsed.scheme.lower() in _SAFE_URI_SCHEMES and bool(parsed.netloc)


def _find_uri_for_bbox(
    bbox: tuple[float, float, float, float],
    uri_links: list[tuple[tuple[float, float, float, float], str]],
) -> str | None:
    x0, y0, x1, y1 = bbox
    pad = _LINK_OVERLAP_PAD
    sx0, sy0, sx1, sy1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
    best_uri: str | None = None
    best_area = 0.0
    for (lx0, ly0, lx1, ly1), uri in uri_links:
        ix0 = max(sx0, lx0)
        iy0 = max(sy0, ly0)
        ix1 = min(sx1, lx1)
        iy1 = min(sy1, ly1)
        if ix1 <= ix0 or iy1 <= iy0:
            continue
        area = (ix1 - ix0) * (iy1 - iy0)
        if area > best_area:
            best_area = area
            best_uri = uri
    return best_uri


def _span_to_html(
    span: dict,
    uri_links: list[tuple[tuple[float, float, float, float], str]],
) -> str | None:
    text = span.get("text") or ""
    if not text.strip():
        return None

    bbox = span.get("bbox")
    if not bbox or len(bbox) < 4:
        return None

    x0, y0 = float(bbox[0]), float(bbox[1])
    size = float(span.get("size") or 12.0)
    font = str(span.get("font") or "")
    flags = int(span.get("flags") or 0)
    color = span.get("color")

    size_css = f"{round(size, 1):g}pt"
    left_css = f"{round(x0, 2):g}pt"
    top_css = f"{round(y0, 2):g}pt"

    styles = [
        "position:absolute",
        f"left:{left_css}",
        f"top:{top_css}",
        f"font-size:{size_css}",
        "white-space:pre",
        "line-height:1.15",
    ]
    color_css = _color_to_css(color)
    if color_css:
        styles.append(f"color:{color_css}")

    font_family = _css_font_family(font)
    if font_family:
        styles.append(f"font-family:{font_family}")

    content = html.escape(text)
    bold = _is_bold(font, flags)
    italic = _is_italic(font, flags)
    if bold:
        content = f"<strong>{content}</strong>"
    if italic:
        content = f"<em>{content}</em>"

    uri = _find_uri_for_bbox(
        (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])),
        uri_links,
    )
    if uri:
        content = f'<a href="{html.escape(uri, quote=True)}">{content}</a>'

    style_attr = ";".join(styles)
    return f'<span class="pdf-span" style="{style_attr}">{content}</span>'


def _is_bold(font: str, flags: int) -> bool:
    name = font.lower()
    if flags & 2**4:  # PyMuPDF bit 4 = bold
        return True
    return "bold" in name


def _is_italic(font: str, flags: int) -> bool:
    name = font.lower()
    if flags & 2**1:  # PyMuPDF bit 1 = italic
        return True
    return "italic" in name or "oblique" in name


def _css_font_family(font: str) -> str | None:
    if not font:
        return "Arial, Helvetica, sans-serif"
    lower = font.lower()
    if "times" in lower or "roman" in lower:
        return '"Times New Roman", Times, serif'
    if "courier" in lower:
        return '"Courier New", Courier, monospace'
    # Arial / Helvetica / default sans
    return "Arial, Helvetica, sans-serif"


def _color_to_css(color: object) -> str | None:
    if color is None:
        return None
    try:
        value = int(color)
    except (TypeError, ValueError):
        return None
    r = (value >> 16) & 0xFF
    g = (value >> 8) & 0xFF
    b = value & 0xFF
    return f"#{r:02x}{g:02x}{b:02x}"


def _image_block_to_html(
    doc,
    block: dict,
    page_number: int,
    assets_dir: Path,
    image_index: int,
) -> tuple[str | None, str | None, int]:
    bbox = block.get("bbox")
    image_bytes = block.get("image")
    ext = (block.get("ext") or "png").lstrip(".")
    xref = block.get("xref")

    if not image_bytes and xref:
        try:
            extracted = doc.extract_image(int(xref))
            image_bytes = extracted.get("image")
            ext = (extracted.get("ext") or ext).lstrip(".")
        except Exception as exc:
            logger.warning(
                "Skipping image xref=%s on page %s: %s", xref, page_number, exc
            )
            return None, f"Skipped image on page {page_number}", image_index

    if not image_bytes:
        return None, f"Skipped image on page {page_number}", image_index

    name = f"p{page_number}_img{image_index}.{ext}"
    try:
        (assets_dir / name).write_bytes(image_bytes)
    except Exception as exc:
        logger.warning("Failed writing image %s: %s", name, exc)
        return None, f"Skipped image on page {page_number}", image_index

    style_parts = ["position:absolute"]
    if bbox and len(bbox) >= 4:
        x0, y0, x1, y1 = (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
        style_parts.extend(
            [
                f"left:{x0:g}pt",
                f"top:{y0:g}pt",
                f"width:{(x1 - x0):g}pt",
                f"height:{(y1 - y0):g}pt",
            ]
        )
    style = ";".join(style_parts)
    tag = (
        f'<img class="pdf-image" src="assets/{html.escape(name)}" alt="" '
        f'style="{style}" />'
    )
    return tag, None, image_index + 1


def _fallback_images(
    doc,
    page,
    page_number: int,
    assets_dir: Path,
) -> tuple[list[str], list[str]]:
    """Extract images via get_images when dict had no type-1 image blocks."""
    parts: list[str] = []
    warnings: list[str] = []
    try:
        images = page.get_images(full=True)
    except Exception as exc:
        logger.warning("Image list failed on page %s: %s", page_number, exc)
        return [], [f"Image enumeration failed on page {page_number}"]

    for img_index, img in enumerate(images):
        xref = img[0]
        try:
            extracted = doc.extract_image(xref)
            image_bytes = extracted["image"]
            ext = extracted.get("ext") or "png"
            name = f"p{page_number}_img{img_index}.{ext}"
            (assets_dir / name).write_bytes(image_bytes)

            # Best-effort position from first rect for this xref.
            style = "position:absolute;left:0;top:0;max-width:100%"
            try:
                rects = page.get_image_rects(xref)
                if rects:
                    r = rects[0]
                    style = (
                        f"position:absolute;left:{float(r.x0):g}pt;top:{float(r.y0):g}pt;"
                        f"width:{float(r.width):g}pt;height:{float(r.height):g}pt"
                    )
            except Exception:
                pass

            parts.append(
                f'<img class="pdf-image" src="assets/{html.escape(name)}" alt="" '
                f'style="{style}" />'
            )
        except Exception as exc:
            logger.warning(
                "Skipping image xref=%s on page %s: %s", xref, page_number, exc
            )
            warnings.append(f"Skipped image on page {page_number}")
    return parts, warnings


def _wrap_document(*, title: str, body: str) -> str:
    safe_title = html.escape(title or "Converted PDF")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>{safe_title}</title>
  <style>
    body {{
      margin: 0;
      padding: 1rem;
      background: #e8e8e8;
      color: #1a1a1a;
    }}
    .pdf-page {{
      position: relative;
      margin: 0 auto 1.5rem;
      background: #fff;
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.12);
      overflow: hidden;
    }}
    .pdf-span {{
      margin: 0;
      padding: 0;
    }}
    .pdf-span a {{
      color: inherit;
      text-decoration: underline;
    }}
    .pdf-image {{
      display: block;
    }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""
