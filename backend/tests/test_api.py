from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_url_analysis_flow() -> None:
    response = client.post(
        "/api/v1/analyze",
        json={"url": "https://example.com/video.mp4", "platform": "TikTok"},
    )
    assert response.status_code == 202
    task_id = response.json()["id"]

    report = client.get(f"/api/v1/report/{task_id}")
    assert report.status_code == 200
    body = report.json()
    assert body["status"] in {"queued", "processing", "completed"}
    report_body = body.get("report")
    if report_body:
        assert isinstance(report_body.get("timeline"), list)


def test_tasks_endpoint_lists_history() -> None:
    response = client.get("/api/v1/tasks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
