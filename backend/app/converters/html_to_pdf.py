"""HTML → PDF converter using WeasyPrint (local assets only)."""

from __future__ import annotations

import logging
import mimetypes
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from bs4 import BeautifulSoup

from app.converters.base import ConversionResult
from app.core.exceptions import ConversionAppError, ValidationAppError

logger = logging.getLogger(__name__)

_HTML_SUFFIXES = {".html", ".htm"}

# 1x1 transparent PNG used when remote images are blocked (no network fetch).
_PLACEHOLDER_PNG = bytes(
    [
        0x89,
        0x50,
        0x4E,
        0x47,
        0x0D,
        0x0A,
        0x1A,
        0x0A,
        0x00,
        0x00,
        0x00,
        0x0D,
        0x49,
        0x48,
        0x44,
        0x52,
        0x00,
        0x00,
        0x00,
        0x01,
        0x00,
        0x00,
        0x00,
        0x01,
        0x08,
        0x06,
        0x00,
        0x00,
        0x00,
        0x1F,
        0x15,
        0xC4,
        0x89,
        0x00,
        0x00,
        0x00,
        0x0A,
        0x49,
        0x44,
        0x41,
        0x54,
        0x78,
        0x9C,
        0x63,
        0x00,
        0x01,
        0x00,
        0x00,
        0x05,
        0x00,
        0x01,
        0x0D,
        0x0A,
        0x2D,
        0xB4,
        0x00,
        0x00,
        0x00,
        0x00,
        0x49,
        0x45,
        0x4E,
        0x44,
        0xAE,
        0x42,
        0x60,
        0x82,
    ]
)


class LocalOnlyUrlFetcher:
    """Allow file:// reads only under a document asset root; block remote URLs.

    Remote http(s) URLs never hit the network. By default they are replaced with a
    tiny placeholder image so conversion can continue; set ``strict_remote=True``
    to raise instead. Host allowlisting can be added later.
    """

    def __init__(self, asset_root: Path, *, strict_remote: bool = False) -> None:
        self._root = asset_root.resolve()
        self.strict_remote = strict_remote
        self.blocked_urls: list[str] = []

    def __call__(self, url: str, timeout: int = 10, ssl_context=None) -> dict:
        parsed = urlparse(url)
        scheme = (parsed.scheme or "").lower()

        if scheme == "data":
            from weasyprint import default_url_fetcher

            return default_url_fetcher(url, timeout=timeout, ssl_context=ssl_context)

        if scheme in {"http", "https", "ftp", "ftps"}:
            self.blocked_urls.append(url)
            logger.warning("Blocked remote asset URL during HTML→PDF: %s", url)
            if self.strict_remote:
                raise ConversionAppError(
                    "Remote URL fetching is disabled for HTML conversion",
                    code="remote_url_blocked",
                    details={"url": url},
                )
            return {
                "string": _PLACEHOLDER_PNG,
                "mime_type": "image/png",
                "encoding": None,
                "redirected_url": url,
            }

        if scheme not in {"", "file"}:
            raise ConversionAppError(
                f"URL scheme {scheme!r} is not allowed",
                code="remote_url_blocked",
                details={"url": url},
            )

        path = self._file_url_to_path(url)
        try:
            path.relative_to(self._root)
        except ValueError as exc:
            raise ConversionAppError(
                "Asset path is outside the document directory",
                code="asset_path_denied",
                details={"url": url},
            ) from exc

        if not path.is_file():
            raise ConversionAppError(
                "Referenced asset was not found",
                code="asset_not_found",
                details={"url": url},
            )

        mime, _ = mimetypes.guess_type(str(path))
        return {
            "string": path.read_bytes(),
            "mime_type": mime or "application/octet-stream",
            "encoding": None,
            "redirected_url": path.as_uri(),
        }

    @staticmethod
    def _file_url_to_path(url: str) -> Path:
        parsed = urlparse(url)
        if parsed.scheme == "file":
            return Path(url2pathname(unquote(parsed.path))).resolve()
        return Path(unquote(parsed.path)).resolve()


class HtmlToPdfConverter:
    source_format = "html"
    target_format = "pdf"

    def convert(self, source_path: Path, destination_path: Path) -> ConversionResult:
        source_path = source_path.resolve()
        if source_path.suffix.lower() not in _HTML_SUFFIXES:
            raise ValidationAppError(
                "HTML → PDF converter requires an .html/.htm source",
                code="unsupported_source",
            )
        if not source_path.is_file():
            raise ValidationAppError(
                "Source HTML file does not exist",
                code="unsupported_source",
            )

        asset_root = source_path.parent
        html_text = source_path.read_text(encoding="utf-8")
        title, author = _extract_metadata(html_text)

        try:
            from weasyprint import HTML
        except ImportError as exc:
            raise ConversionAppError(
                "WeasyPrint is not installed",
                code="conversion_dependency_missing",
            ) from exc

        destination_path.parent.mkdir(parents=True, exist_ok=True)
        fetcher = LocalOnlyUrlFetcher(asset_root)
        warnings: list[str] = []

        try:
            document = HTML(
                filename=str(source_path),
                base_url=asset_root.as_uri() + "/",
                url_fetcher=fetcher,
            ).render()
            if title:
                document.metadata.title = title
            if author:
                document.metadata.authors = [author]
            document.metadata.generator = "document-processing-service"
            document.write_pdf(destination_path)
            page_count = len(document.pages)
        except ConversionAppError:
            raise
        except Exception as exc:
            logger.exception("WeasyPrint conversion failed for %s", source_path)
            raise ConversionAppError(
                "HTML to PDF conversion failed",
                code="conversion_failed",
                details={"reason": str(exc)},
            ) from exc

        if not destination_path.is_file() or destination_path.stat().st_size == 0:
            raise ConversionAppError(
                "Conversion produced an empty PDF",
                code="conversion_failed",
            )

        if fetcher.blocked_urls:
            warnings.append(
                "Remote http(s) asset URLs were blocked; only local files under the "
                "document directory are loaded. Host allowlisting may be added later."
            )

        return ConversionResult(
            success=True,
            output_path=destination_path,
            warnings=warnings,
            page_count=page_count,
            title=title,
        )


def _extract_metadata(html_text: str) -> tuple[str | None, str | None]:
    soup = BeautifulSoup(html_text, "lxml")
    title = soup.title.string.strip() if soup.title and soup.title.string else None
    author_meta = soup.find("meta", attrs={"name": "author"})
    author = None
    if author_meta and author_meta.get("content"):
        author = str(author_meta["content"]).strip() or None
    return title, author
