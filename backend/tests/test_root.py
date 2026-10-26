"""Tests for root application information endpoint."""

from fastapi import status


def test_root_endpoint(client):
    """Verify GET / returns application information and docs URL."""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["name"] == "TypeMind AI"
    assert "description" in data
    assert data["version"] == "0.1.0"
    assert data["docs_url"] == "/docs"
    assert data["api_v1_prefix"] == "/api/v1"
