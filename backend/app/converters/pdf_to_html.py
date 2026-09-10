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
_SAFE_URI_SCHEMES = {"http", "https", "mailto"}
_LINK_OVERLAP_PAD = 1.0
_MIN_DRAWING_SIZE = 0.15  # pt — skip degenerate fragments
_PAGE_BG_COVERAGE = 0.9


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
            "(tables, lists) and complex vector paths are limited."
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

    # Drawings first (z-index 0) so text/images paint above section rules / shapes.
    drawing_parts, drawing_warnings = _drawings_to_html(page)
    parts.extend(drawing_parts)
    warnings.extend(drawing_warnings)

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
    scheme = parsed.scheme.lower()
    if scheme not in _SAFE_URI_SCHEMES:
        return False
    if scheme == "mailto":
        # mailto:user@host — path or netloc may hold the address
        address = (parsed.path or parsed.netloc or "").strip()
        return "@" in address and " " not in address
    return bool(parsed.netloc)


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
        "z-index:1",
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


def _rgb_tuple_to_css(rgb: object) -> str | None:
    if not rgb or not isinstance(rgb, (tuple, list)) or len(rgb) < 3:
        return None
    try:
        r, g, b = (float(rgb[0]), float(rgb[1]), float(rgb[2]))
    except (TypeError, ValueError):
        return None
    # PyMuPDF drawing colors are 0..1; tolerate 0..255
    if r > 1 or g > 1 or b > 1:
        return f"rgb({int(r)},{int(g)},{int(b)})"
    return f"rgb({int(round(r * 255))},{int(round(g * 255))},{int(round(b * 255))})"


def _drawings_to_html(page) -> tuple[list[str], list[str]]:
    """Render vector drawings (section rules, filled boxes, stroked lines)."""
    parts: list[str] = []
    warnings: list[str] = []
    try:
        drawings = page.get_drawings()
    except Exception as exc:
        logger.warning("Drawing extraction failed: %s", exc)
        return [], ["Drawing extraction failed on a page"]

    page_rect = page.rect
    for drawing in drawings:
        try:
            parts.extend(_drawing_to_elements(drawing, page_rect))
        except Exception as exc:
            logger.warning("Skipping drawing: %s", exc)
            warnings.append("Skipped a vector drawing on a page")
    return parts, warnings


def _drawing_to_elements(drawing: dict, page_rect) -> list[str]:
    fill = drawing.get("fill")
    stroke = drawing.get("color")
    fill_css = _rgb_tuple_to_css(fill)
    stroke_css = _rgb_tuple_to_css(stroke)
    opacity = drawing.get("fill_opacity")
    if opacity is None:
        opacity = 1.0

    items = drawing.get("items") or []
    rect_items = [it[1] for it in items if it and it[0] == "re" and len(it) >= 2]
    line_items = [it for it in items if it and it[0] == "l"]

    visible_rects: list[tuple[float, float, float, float]] = []

    if rect_items:
        aa_rects = [_normalize_rect(r) for r in rect_items]
        aa_rects = [r for r in aa_rects if r is not None]
        if drawing.get("even_odd") and len(aa_rects) >= 2:
            # WeasyPrint section underlines: two overlapping rects with even-odd
            # fill → thin visible band (XOR), not a solid heading background.
            visible_rects = _even_odd_union_xor(aa_rects)
        else:
            visible_rects = aa_rects

    elements: list[str] = []
    for rect in visible_rects:
        if _is_page_background(rect, page_rect, fill):
            continue
        x0, y0, x1, y1 = rect
        w, h = x1 - x0, y1 - y0
        if w < _MIN_DRAWING_SIZE or h < _MIN_DRAWING_SIZE:
            continue
        bg = fill_css or stroke_css
        if not bg:
            continue
        style = (
            f"position:absolute;left:{round(x0, 2):g}pt;top:{round(y0, 2):g}pt;"
            f"width:{round(w, 2):g}pt;height:{round(h, 2):g}pt;"
            f"background:{bg};z-index:0"
        )
        if opacity < 1.0:
            style += f";opacity:{opacity:g}"
        elements.append(f'<div class="pdf-drawing" style="{style}"></div>')

    # Stroked line segments (type "l")
    stroke_width = float(drawing.get("width") or 1.0)
    if stroke_css and line_items:
        for item in line_items:
            if len(item) < 3:
                continue
            p1, p2 = item[1], item[2]
            line_el = _stroke_line_to_html(p1, p2, stroke_css, stroke_width)
            if line_el:
                elements.append(line_el)

    return elements


def _normalize_rect(rect) -> tuple[float, float, float, float] | None:
    try:
        x0, y0, x1, y1 = float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1)
    except Exception:
        try:
            x0, y0, x1, y1 = (float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3]))
        except Exception:
            return None
    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0
    return (x0, y0, x1, y1)


def _is_page_background(
    rect: tuple[float, float, float, float],
    page_rect,
    fill: object,
) -> bool:
    x0, y0, x1, y1 = rect
    pw, ph = float(page_rect.width), float(page_rect.height)
    if pw <= 0 or ph <= 0:
        return False
    covers = ((x1 - x0) / pw) >= _PAGE_BG_COVERAGE and ((y1 - y0) / ph) >= _PAGE_BG_COVERAGE
    if not covers:
        return False
    # Near-white / empty fill page wash
    if not fill:
        return True
    try:
        r, g, b = float(fill[0]), float(fill[1]), float(fill[2])
        if r > 1:
            r, g, b = r / 255.0, g / 255.0, b / 255.0
        return r >= 0.95 and g >= 0.95 and b >= 0.95
    except Exception:
        return True


def _even_odd_union_xor(
    rects: list[tuple[float, float, float, float]],
) -> list[tuple[float, float, float, float]]:
    """Visible bands for even-odd fill of axis-aligned rectangles (pairwise XOR fold)."""
    if not rects:
        return []
    result: list[tuple[float, float, float, float]] = [rects[0]]
    for nxt in rects[1:]:
        updated: list[tuple[float, float, float, float]] = []
        for cur in result:
            updated.extend(_rect_xor(cur, nxt))
        # Also parts of nxt not in any previous — handled by xor with each; for
        # sequential fold of nested WeasyPrint pairs, pairwise xor is enough.
        result = _merge_adjacent_rects(updated)
        if not result:
            # First xor emptied; treat nxt as seed if odd count remaining — rare.
            result = [nxt]
    return result


def _rect_xor(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> list[tuple[float, float, float, float]]:
    return _rect_subtract(a, b) + _rect_subtract(b, a)


def _rect_subtract(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> list[tuple[float, float, float, float]]:
    """Axis-aligned A − B as up to four rectangles."""
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    if ix1 <= ix0 or iy1 <= iy0:
        return [a]
    out: list[tuple[float, float, float, float]] = []
    if ay0 < iy0:
        out.append((ax0, ay0, ax1, iy0))
    if iy1 < ay1:
        out.append((ax0, iy1, ax1, ay1))
    if ax0 < ix0:
        out.append((ax0, iy0, ix0, iy1))
    if ix1 < ax1:
        out.append((ix1, iy0, ax1, iy1))
    return out


def _merge_adjacent_rects(
    rects: list[tuple[float, float, float, float]],
) -> list[tuple[float, float, float, float]]:
    """Light cleanup: drop empties; keep fragments (no heavy merge needed)."""
    cleaned: list[tuple[float, float, float, float]] = []
    for x0, y0, x1, y1 in rects:
        if (x1 - x0) >= _MIN_DRAWING_SIZE and (y1 - y0) >= _MIN_DRAWING_SIZE:
            cleaned.append((x0, y0, x1, y1))
    return cleaned


def _stroke_line_to_html(p1, p2, color_css: str, width: float) -> str | None:
    try:
        x1, y1 = float(p1.x), float(p1.y)
        x2, y2 = float(p2.x), float(p2.y)
    except Exception:
        try:
            x1, y1 = float(p1[0]), float(p1[1])
            x2, y2 = float(p2[0]), float(p2[1])
        except Exception:
            return None

    # Axis-aligned lines → thin div; diagonals skipped for now.
    if abs(y1 - y2) <= 0.5:
        x0, x1b = min(x1, x2), max(x1, x2)
        y = min(y1, y2)
        h = max(width, 0.5)
        return (
            f'<div class="pdf-drawing" style="position:absolute;left:{round(x0, 2):g}pt;'
            f"top:{round(y - h / 2, 2):g}pt;width:{round(x1b - x0, 2):g}pt;"
            f'height:{round(h, 2):g}pt;background:{color_css};z-index:0"></div>'
        )
    if abs(x1 - x2) <= 0.5:
        y0, y1b = min(y1, y2), max(y1, y2)
        x = min(x1, x2)
        w = max(width, 0.5)
        return (
            f'<div class="pdf-drawing" style="position:absolute;left:{round(x - w / 2, 2):g}pt;'
            f"top:{round(y0, 2):g}pt;width:{round(w, 2):g}pt;"
            f'height:{round(y1b - y0, 2):g}pt;background:{color_css};z-index:0"></div>'
        )
    return None


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

    style_parts = ["position:absolute", "z-index:1"]
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
                        f"width:{float(r.width):g}pt;height:{float(r.height):g}pt;z-index:1"
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
    .pdf-drawing {{
      pointer-events: none;
    }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""
