"""Helpers for WeasyPrint availability in tests."""

from __future__ import annotations

import functools
import os

import pytest


@functools.lru_cache(maxsize=1)
def weasyprint_works() -> bool:
    """Return True if WeasyPrint can render a tiny PDF (native libs present)."""
    try:
        from weasyprint import HTML

        pdf = HTML(string="<html><body>ok</body></html>").write_pdf()
        return bool(pdf) and pdf.startswith(b"%PDF")
    except Exception:
        return False


def _weasyprint_required() -> bool:
    return os.environ.get("WEASYPRINT_REQUIRED", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def require_weasyprint() -> None:
    """Skip on bare Windows without GTK; fail in Docker/CI when required."""
    if weasyprint_works():
        return
    if _weasyprint_required():
        pytest.fail(
            "WeasyPrint native libraries are required in this environment "
            "(Docker/CI) but rendering failed"
        )
    pytest.skip("WeasyPrint native libraries not available")
