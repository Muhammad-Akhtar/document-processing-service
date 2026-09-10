"""Helpers for WeasyPrint availability in tests."""

from __future__ import annotations

import functools


@functools.lru_cache(maxsize=1)
def weasyprint_works() -> bool:
    """Return True if WeasyPrint can render a tiny PDF (native libs present)."""
    try:
        from weasyprint import HTML

        pdf = HTML(string="<html><body>ok</body></html>").write_pdf()
        return bool(pdf) and pdf.startswith(b"%PDF")
    except Exception:  # noqa: BLE001 — native lib failures vary widely
        return False
