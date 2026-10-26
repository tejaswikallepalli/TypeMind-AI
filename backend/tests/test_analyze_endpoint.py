"""Tests for POST /api/v1/analyze endpoint."""

from fastapi import status


def test_analyze_endpoint_clean_code(client):
    """Verify clean code returns 0 findings and success status."""
    payload = {
        "source_code": "def add(a: int, b: int) -> int:\n    return a + b\n",
        "file_path": "clean.py",
        "python_version": "3.12",
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["status"] == "success"
    assert data["syntax_error"] is None
    assert len(data["findings"]) == 0
    assert data["summary"]["total_findings"] == 0
    assert data["summary"]["errors_count"] == 0


def test_analyze_endpoint_type_error(client):
    """Verify type error code returns populated findings with line and column coordinates."""
    payload = {
        "source_code": 'def greet(name: str) -> str:\n    return "User: " + 100\n',
        "file_path": "error.py",
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["status"] == "success"
    assert len(data["findings"]) == 1
    f = data["findings"][0]
    assert f["rule_id"] == "TM001_STRING_NUMBER_CONCAT"
    assert f["origin"] in ("rule_based", "hybrid")
    assert f["is_confirmed"] is True
    assert f["location"]["line"] == 2
    assert f["location"]["column"] >= 1
    assert data["summary"]["errors_count"] == 1


def test_analyze_endpoint_syntax_error(client):
    """Verify syntax errors return status='syntax_error' and syntax_error object."""
    payload = {
        "source_code": "def broken(\n",
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["status"] == "syntax_error"
    assert data["syntax_error"] is not None
    assert data["syntax_error"]["rule_id"] == "TM000_SYNTAX_ERROR"
    assert len(data["findings"]) == 0
    assert data["summary"]["syntax_errors_count"] == 1
