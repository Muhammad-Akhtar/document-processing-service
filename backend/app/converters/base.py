"""Converter plugin protocol and result type."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(slots=True)
class ConversionResult:
    success: bool
    output_path: Path | None = None
    warnings: list[str] = field(default_factory=list)
    error: str | None = None


@runtime_checkable
class Converter(Protocol):
    source_format: str
    target_format: str

    def convert(self, source_path: Path, destination_path: Path) -> ConversionResult:
        """Convert source file to destination path."""
        ...
