"""Tests for service health check endpoints."""

from fastapi import status


def test_root_health_endpoint(client):
    """Verify GET /health returns 200 with proper health status and version."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data
    assert data["version"] == "0.1.0"


def test_api_v1_health_endpoint(client):
    """Verify GET /api/v1/health is also reachable and consistent."""
    response = client.get("/api/v1/health")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
