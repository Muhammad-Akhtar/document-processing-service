"""TDD: sync conversion API (HTML → PDF)."""

from pathlib import Path

import pytest

from tests.weasyprint_utils import weasyprint_works

FIXTURES = Path(__file__).parent / "fixtures" / "html_to_pdf"

requires_weasyprint = pytest.mark.skipif(
    not weasyprint_works(),
    reason="WeasyPrint native libraries not available",
)


@requires_weasyprint
def test_convert_html_document_to_pdf_and_download(client) -> None:
    html = (FIXTURES / "sample.html").read_bytes()
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("sample.html", html, "text/html")},
    )
    assert upload.status_code == 201
    source_id = upload.json()["document_id"]

    convert = client.post(
        "/api/v1/conversions",
        json={"source_document_id": source_id, "target_format": "pdf"},
    )
    assert convert.status_code == 201, convert.text
    body = convert.json()
    assert body["source_document_id"] == source_id
    assert body["target_format"] == "pdf"
    assert body["output_document_id"]
    assert body["size"] > 0
    assert body["page_count"] >= 1
    assert body["download_url"].endswith(
        f"/api/v1/documents/{body['output_document_id']}/download"
    )

    download = client.get(body["download_url"])
    assert download.status_code == 200
    assert download.content.startswith(b"%PDF")
    assert "application/pdf" in download.headers["content-type"]


def test_convert_rejects_unsupported_target(client) -> None:
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("a.html", b"<html><body>x</body></html>", "text/html")},
    )
    source_id = upload.json()["document_id"]
    response = client.post(
        "/api/v1/conversions",
        json={"source_document_id": source_id, "target_format": "docx"},
    )
    assert response.status_code == 400
    assert response.json()["code"] in {
        "unsupported_conversion",
        "unsupported_target",
        "validation_error",
    }


def test_convert_rejects_pdf_source_for_html_to_pdf(client) -> None:
    pdf = b"%PDF-1.4\nfake\n%%EOF\n"
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("a.pdf", pdf, "application/pdf")},
    )
    source_id = upload.json()["document_id"]
    response = client.post(
        "/api/v1/conversions",
        json={"source_document_id": source_id, "target_format": "pdf"},
    )
    assert response.status_code == 400
    assert response.json()["code"] in {
        "unsupported_source",
        "unsupported_conversion",
        "validation_error",
    }


def test_convert_missing_document_404(client) -> None:
    from uuid import uuid4

    response = client.post(
        "/api/v1/conversions",
        json={"source_document_id": str(uuid4()), "target_format": "pdf"},
    )
    assert response.status_code == 404
