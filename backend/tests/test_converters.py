"""TDD: converter protocol, result, and registry."""

from pathlib import Path

import pytest

from app.converters.base import ConversionResult, Converter
from app.converters.html_to_pdf import HtmlToPdfConverter
from app.converters.pdf_to_html import PdfToHtmlConverter
from app.converters.registry import ConverterRegistry, get_default_registry


class _EchoConverter:
    source_format = "txt"
    target_format = "txt"

    def convert(self, source_path: Path, destination_path: Path) -> ConversionResult:
        destination_path.write_bytes(source_path.read_bytes())
        return ConversionResult(success=True, output_path=destination_path)


def test_conversion_result_success() -> None:
    path = Path("out.pdf")
    result = ConversionResult(success=True, output_path=path, warnings=["soft"])
    assert result.success is True
    assert result.output_path == path
    assert result.warnings == ["soft"]
    assert result.error is None


def test_conversion_result_failure() -> None:
    result = ConversionResult(success=False, error="boom")
    assert result.success is False
    assert result.output_path is None
    assert result.error == "boom"


def test_registry_register_and_get(tmp_path: Path) -> None:
    registry = ConverterRegistry()
    converter: Converter = _EchoConverter()
    registry.register(converter)
    found = registry.get("txt", "txt")
    assert found is converter

    src = tmp_path / "in.txt"
    dst = tmp_path / "out.txt"
    src.write_text("hi", encoding="utf-8")
    result = found.convert(src, dst)
    assert result.success is True
    assert dst.read_text(encoding="utf-8") == "hi"


def test_registry_missing_raises() -> None:
    registry = ConverterRegistry()
    with pytest.raises(KeyError):
        registry.get("html", "pdf")


def test_default_registry_has_placeholders() -> None:
    registry = get_default_registry()
    html = registry.get("html", "pdf")
    pdf = registry.get("pdf", "html")
    assert isinstance(html, HtmlToPdfConverter)
    assert isinstance(pdf, PdfToHtmlConverter)


def test_placeholder_converters_not_implemented(tmp_path: Path) -> None:
    src = tmp_path / "a.html"
    dst = tmp_path / "a.pdf"
    src.write_text("<html></html>", encoding="utf-8")
    with pytest.raises(NotImplementedError):
        HtmlToPdfConverter().convert(src, dst)
    with pytest.raises(NotImplementedError):
        PdfToHtmlConverter().convert(src, dst)
