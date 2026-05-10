from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_markdown_export_requires_ready_report() -> None:
    response = client.get("/api/v1/report/00000000-0000-0000-0000-000000000000/export.md")
    assert response.status_code in {404, 409}


def test_html_export_requires_ready_report() -> None:
    response = client.get("/api/v1/report/00000000-0000-0000-0000-000000000000/export.html")
    assert response.status_code in {404, 409}
