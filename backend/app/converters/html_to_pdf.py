"""HTML → PDF converter placeholder (implemented in Phase 2)."""

from pathlib import Path

from app.converters.base import ConversionResult


class HtmlToPdfConverter:
    source_format = "html"
    target_format = "pdf"

    def convert(self, source_path: Path, destination_path: Path) -> ConversionResult:
        raise NotImplementedError("HTML → PDF conversion lands in Phase 2 (WeasyPrint)")
