"""TDD: PDF → HTML via conversions API."""

from pathlib import Path

import fitz


def _make_pdf_bytes(text: str = "API Converted PDF Text") -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text, fontsize=14)
    data = doc.tobytes()
    doc.close()
    return data


def test_convert_pdf_to_html_download_and_preview(client) -> None:
    pdf = _make_pdf_bytes()
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("sample.pdf", pdf, "application/pdf")},
    )
    assert upload.status_code == 201
    source_id = upload.json()["document_id"]

    convert = client.post(
        "/api/v1/conversions",
        json={"source_document_id": source_id, "target_format": "html"},
    )
    assert convert.status_code == 201, convert.text
    body = convert.json()
    assert body["target_format"] == "html"
    assert body["page_count"] == 1
    assert body["content_type"] == "text/html"

    download = client.get(body["download_url"])
    assert download.status_code == 200
    html = download.content.decode("utf-8")
    assert "API Converted PDF Text" in html
    assert 'data-page="1"' in html

    preview = client.get(f"/api/v1/documents/{body['output_document_id']}/preview")
    assert preview.status_code == 200
    assert "API Converted PDF Text" in preview.text
    assert "content-security-policy" in {k.lower() for k in preview.headers}


def test_convert_pdf_with_image_serves_asset(client) -> None:
    png = (
        Path(__file__).parent / "fixtures" / "html_to_pdf" / "logo.png"
    ).read_bytes()
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Has image", fontsize=12)
    page.insert_image(fitz.Rect(72, 90, 120, 138), stream=png)
    pdf = doc.tobytes()
    doc.close()

    upload = client.post(
        "/api/v1/documents",
        files={"file": ("img.pdf", pdf, "application/pdf")},
    )
    source_id = upload.json()["document_id"]
    convert = client.post(
        "/api/v1/conversions",
        json={"source_document_id": source_id, "target_format": "html"},
    )
    assert convert.status_code == 201, convert.text
    out_id = convert.json()["output_document_id"]
    html = client.get(f"/api/v1/documents/{out_id}/download").text
    assert "assets/" in html

    marker = 'src="assets/'
    assert marker in html
    start = html.index(marker) + len(marker)
    end = html.index('"', start)
    asset_name = html[start:end]
    asset = client.get(f"/api/v1/documents/{out_id}/assets/{asset_name}")
    assert asset.status_code == 200
    assert len(asset.content) > 0


def test_asset_path_traversal_rejected(client) -> None:
    pdf = _make_pdf_bytes("asset guard")
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("a.pdf", pdf, "application/pdf")},
    )
    source_id = upload.json()["document_id"]
    convert = client.post(
        "/api/v1/conversions",
        json={"source_document_id": source_id, "target_format": "html"},
    )
    out_id = convert.json()["output_document_id"]
    response = client.get(f"/api/v1/documents/{out_id}/assets/../meta.json")
    assert response.status_code in {400, 404}
