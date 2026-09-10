"""Converter discovery registry: (source_format, target_format) → Converter."""

from app.converters.base import Converter
from app.converters.html_to_pdf import HtmlToPdfConverter
from app.converters.pdf_to_html import PdfToHtmlConverter


class ConverterRegistry:
    def __init__(self) -> None:
        self._converters: dict[tuple[str, str], Converter] = {}

    def register(self, converter: Converter) -> None:
        key = (converter.source_format.lower(), converter.target_format.lower())
        self._converters[key] = converter

    def get(self, source_format: str, target_format: str) -> Converter:
        key = (source_format.lower(), target_format.lower())
        try:
            return self._converters[key]
        except KeyError as exc:
            raise KeyError(
                f"No converter registered for {source_format!r} → {target_format!r}"
            ) from exc

    def list_pairs(self) -> list[tuple[str, str]]:
        return list(self._converters.keys())


def get_default_registry() -> ConverterRegistry:
    registry = ConverterRegistry()
    registry.register(HtmlToPdfConverter())
    registry.register(PdfToHtmlConverter())
    return registry
