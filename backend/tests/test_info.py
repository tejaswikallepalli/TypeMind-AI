"""Tests for project info and metadata endpoint."""

from fastapi import status


def test_api_v1_info_endpoint(client):
    """Verify GET /api/v1/info returns project name, API version, and supported language."""
    response = client.get("/api/v1/info")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["project_name"] == "TypeMind AI"
    assert data["api_version"] == "v1"
    assert data["app_version"] == "0.1.0"
    assert data["supported_language"] == "Python"
    assert "supported_python_version" in data
    assert isinstance(data["features"], list)
    assert len(data["features"]) > 0
    assert "ast_semantic_analysis" in data["features"]
