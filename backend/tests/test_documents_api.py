"""TDD: documents API endpoints."""

from uuid import uuid4


def test_health_still_works(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_html_happy_path(client) -> None:
    response = client.post(
        "/api/v1/documents",
        files={"file": ("note.html", b"<html><body>hi</body></html>", "text/html")},
    )
    assert response.status_code == 201
    body = response.json()
    assert "document_id" in body
    assert body["filename"] == "note.html"
    assert body["content_type"] == "text/html"
    assert body["size"] == len(b"<html><body>hi</body></html>")


def test_upload_pdf_happy_path(client) -> None:
    pdf = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"
    response = client.post(
        "/api/v1/documents",
        files={"file": ("doc.pdf", pdf, "application/pdf")},
    )
    assert response.status_code == 201
    assert response.json()["filename"] == "doc.pdf"


def test_upload_rejects_bad_extension(client) -> None:
    response = client.post(
        "/api/v1/documents",
        files={"file": ("x.exe", b"MZ", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_extension"


def test_upload_rejects_oversized(client) -> None:
    # conftest max_upload_bytes = 1024
    response = client.post(
        "/api/v1/documents",
        files={"file": ("big.html", b"a" * 1025, "text/html")},
    )
    assert response.status_code == 413
    assert response.json()["code"] == "file_too_large"


def test_get_metadata_download_preview_delete(client) -> None:
    html = b"<html><body>preview</body></html>"
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("page.html", html, "text/html")},
    )
    doc_id = upload.json()["document_id"]

    meta = client.get(f"/api/v1/documents/{doc_id}")
    assert meta.status_code == 200
    assert meta.json()["original_filename"] == "page.html"

    download = client.get(f"/api/v1/documents/{doc_id}/download")
    assert download.status_code == 200
    assert download.content == html
    assert "text/html" in download.headers["content-type"]

    preview = client.get(f"/api/v1/documents/{doc_id}/preview")
    assert preview.status_code == 200
    assert preview.content == html
    assert "content-security-policy" in {k.lower() for k in preview.headers}

    deleted = client.delete(f"/api/v1/documents/{doc_id}")
    assert deleted.status_code == 204

    missing = client.get(f"/api/v1/documents/{doc_id}")
    assert missing.status_code == 404


def test_pdf_preview_returns_pdf_bytes(client) -> None:
    pdf = b"%PDF-1.4\nfake pdf content for preview\n%%EOF\n"
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("a.pdf", pdf, "application/pdf")},
    )
    doc_id = upload.json()["document_id"]
    preview = client.get(f"/api/v1/documents/{doc_id}/preview")
    assert preview.status_code == 200
    assert preview.content == pdf
    assert "application/pdf" in preview.headers["content-type"]


def test_missing_document_404(client) -> None:
    missing = uuid4()
    assert client.get(f"/api/v1/documents/{missing}").status_code == 404
    assert client.get(f"/api/v1/documents/{missing}/download").status_code == 404
    assert client.delete(f"/api/v1/documents/{missing}").status_code == 404


def test_conversions_router_stub_listed(client) -> None:
    # Empty conversions router should still mount under /api/v1
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/documents" in paths
    assert "/health" in paths
