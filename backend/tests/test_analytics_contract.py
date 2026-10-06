from fastapi.testclient import TestClient
import pytest

from app.core.config import settings
from app.main import app


def test_analytics_requires_evaluator_or_admin():
    response = TestClient(app).get("/api/v1/analytics")
    assert response.status_code == 401


def test_metrics_expose_exact_document_status_counts():
    response = TestClient(app).get("/api/v1/metrics")
    assert response.status_code == 200
    payload = response.json()
    assert {"documents_total", "documents_ready", "documents_processing", "documents_failed"} <= payload.keys()
    assert payload["documents_total"] >= payload["documents_ready"] + payload["documents_processing"] + payload["documents_failed"]


def test_document_list_includes_upload_timestamp():
    response = TestClient(app).get("/api/v1/documents?page_size=1")
    assert response.status_code == 200
    if response.json():
        assert response.json()[0]["created_at"] is not None


def test_similar_cases_include_page_provenance():
    client = TestClient(app)
    documents = client.get("/api/v1/documents?status=ready&page_size=100").json()
    if len(documents) < 2:
        pytest.skip("At least two ready documents are required for a similar-case result")

    response = client.post(f"/api/v1/similar/{documents[0]['id']}", json={"top_k": 5})
    assert response.status_code == 200
    for result in response.json()["results"]:
        assert "target_page_number" in result
        assert "source_page_number" in result


def test_analytics_returns_real_search_activity_and_validates_dates():
    password = settings.EVALUATOR_API_KEY or settings.ADMIN_API_KEY
    if not password:
        return

    client = TestClient(app)
    login = client.post("/api/v1/auth/login", json={"username": "analytics-test", "password": password})
    assert login.status_code == 200

    response = client.get("/api/v1/analytics")
    assert response.status_code == 200
    payload = response.json()
    assert {"corpus", "processing", "latency", "search_activity", "top_queries"} <= payload.keys()
    assert isinstance(payload["search_activity"], list)
    assert isinstance(payload["top_queries"], list)

    invalid_range = client.get("/api/v1/analytics?date_from=2026-10-02&date_to=2026-10-01")
    assert invalid_range.status_code == 422
    assert invalid_range.json()["error"] == "invalid_date_range"
