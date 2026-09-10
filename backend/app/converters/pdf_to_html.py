"""PDF → HTML converter placeholder (implemented in Phase 3)."""

from pathlib import Path

from app.converters.base import ConversionResult


class PdfToHtmlConverter:
    source_format = "pdf"
    target_format = "html"

    def convert(self, source_path: Path, destination_path: Path) -> ConversionResult:
        raise NotImplementedError("PDF → HTML conversion lands in Phase 3 (PyMuPDF)")
