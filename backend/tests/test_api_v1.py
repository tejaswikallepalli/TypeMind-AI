"""Comprehensive integration tests for TypeMind AI API v1 endpoints.

Covers:
- GET /health and GET /api/v1/health
- GET /api/v1/info
- GET /api/v1/diagnostics/categories
- GET /api/v1/model/info (loaded & gracefully unavailable)
- POST /api/v1/analyze:
  - valid clean code
  - syntax errors
  - type errors (with explanations, provenance, and suggested fixes)
  - empty input
  - oversized input (>500KB)
  - malformed JSON
  - fallback behavior when model is missing/unloaded
  - request tracing (X-Request-ID header propagation)
"""

from unittest.mock import MagicMock, patch
from fastapi import status
from app.ml.predictor import MLPredictionResult


def test_health_root_and_v1(client):
    """Verify both /health and /api/v1/health return healthy status and version."""
    for path in ["/health", "/api/v1/health"]:
        response = client.get(path)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data
        assert "X-Request-ID" in response.headers


def test_api_v1_info(client):
    """Verify /api/v1/info returns system metadata and supported Python target."""
    response = client.get("/api/v1/info")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["project_name"] == "TypeMind AI"
    assert data["api_version"] == "v1"
    assert data["supported_language"] == "Python"
    assert "3.12" in data["supported_python_version"]
    assert "ast_semantic_analysis" in data["features"]
    assert "X-Request-ID" in response.headers


def test_diagnostics_categories_endpoint(client):
    """Verify /api/v1/diagnostics/categories returns registered categories, rules, and fix support."""
    response = client.get("/api/v1/diagnostics/categories")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "categories" in data
    assert "total_categories" in data
    assert data["total_categories"] >= 7

    cat_map = {c["code"]: c for c in data["categories"]}

    # Verify key categories are properly cataloged
    assert "type_mismatch" in cat_map
    assert cat_map["type_mismatch"]["fix_support"] is True
    assert "TM001_STRING_NUMBER_CONCAT" in cat_map["type_mismatch"]["rule_ids"]

    assert "syntax_error" in cat_map
    assert "TM000_SYNTAX_ERROR" in cat_map["syntax_error"]["rule_ids"]

    assert "incompatible_return" in cat_map
    assert "invalid_assignment" in cat_map
    assert "unsupported_operand" in cat_map
    assert "argument_count_mismatch" in cat_map
    assert "argument_type_mismatch" in cat_map


def test_model_info_endpoint_loaded(client):
    """Verify /api/v1/model/info returns model architecture and evaluation metrics when loaded."""
    response = client.get("/api/v1/model/info")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # If the artifact is present, status should be loaded
    assert data["status"] in ("loaded", "unavailable")
    if data["status"] == "loaded":
        assert data["model_architecture"] == "RandomForestClassifier"
        assert len(data["classes"]) >= 5
        assert data["features_count"] > 0
        assert data["evaluation_summary"] is not None


def test_model_info_endpoint_missing_artifact(client):
    """Verify /api/v1/model/info degrades gracefully to 'unavailable' without crashing."""
    from app.services.model import get_model_service

    service = get_model_service()
    with patch.object(service.predictor, "pipeline", None):
        response = client.get("/api/v1/model/info")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "unavailable"
        assert data["features_count"] == 0
        assert data["classes"] == []
        assert data["model_architecture"] is None


def test_analyze_valid_clean_code(client):
    """Verify valid clean Python code returns 200 OK and 0 findings."""
    code = (
        "def compute_total(items: list, tax_rate: float) -> float:\n"
        "    subtotal: float = sum(items)\n"
        "    return subtotal * (1.0 + tax_rate)\n"
    )
    response = client.post("/api/v1/analyze", json={"source_code": code, "file_path": "total.py"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "success"
    assert data["syntax_error"] is None
    assert len(data["findings"]) == 0
    assert data["summary"]["total_findings"] == 0
    assert data["summary"]["errors_count"] == 0
    assert data["summary"]["lines_analyzed"] >= 3


def test_analyze_syntax_error(client):
    """Verify syntax error returns 200 OK with status='syntax_error' and structured syntax finding."""
    code = "def malformed_syntax(:\n    pass\n"
    response = client.post("/api/v1/analyze", json={"source_code": code})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "syntax_error"
    assert data["syntax_error"] is not None
    assert data["syntax_error"]["rule_id"] == "TM000_SYNTAX_ERROR"
    assert data["syntax_error"]["location"]["line"] == 1
    assert data["summary"]["syntax_errors_count"] == 1
    assert len(data["findings"]) == 0


def test_analyze_type_error_with_explanations_and_fixes(client):
    """Verify type error returns rich findings with location, severity, explanation, and fixes."""
    code = 'def greet(name: str) -> str:\n    return name + 42\n'
    response = client.post("/api/v1/analyze", json={"source_code": code, "file_path": "greet.py"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "success"
    assert len(data["findings"]) >= 1

    finding = data["findings"][0]
    assert finding["category"] == "type_mismatch"
    assert finding["severity"] == "error"
    assert finding["location"]["line"] == 2
    assert finding["location"]["column"] >= 1
    assert finding["rule_id"] == "TM001_STRING_NUMBER_CONCAT"
    assert finding["origin"] in ("rule_based", "hybrid")
    assert finding["is_confirmed"] is True
    assert finding["explanation"] is not None
    assert len(finding["suggested_fixes"]) >= 1

    fix = finding["suggested_fixes"][0]
    assert "str(" in fix["title"] or "str(" in fix["description"]
    assert fix["diff_preview"] is not None


def test_analyze_empty_input(client):
    """Verify empty source_code is rejected with HTTP 422 Unprocessable Content."""
    response = client.post("/api/v1/analyze", json={"source_code": ""})
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"
    assert data["error_type"] == "ValidationError"
    assert "source_code" in str(data["details"])


def test_analyze_oversized_input(client):
    """Verify source code exceeding size limit (500,000 characters) is rejected with 422."""
    oversized_code = "# dummy comment\n" * 35_000  # ~560,000 characters
    assert len(oversized_code) > 500_000

    response = client.post("/api/v1/analyze", json={"source_code": oversized_code})
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"
    assert data["error_type"] == "ValidationError"
    assert "source_code" in str(data["details"])


def test_analyze_malformed_json_body(client):
    """Verify invalid JSON payload returns HTTP 422 with structured error body."""
    response = client.post(
        "/api/v1/analyze",
        content="not a valid json payload",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"
    assert data["error_type"] == "ValidationError"
    assert "X-Request-ID" in response.headers


def test_request_id_tracing_and_propagation(client):
    """Verify client-supplied X-Request-ID is echoed back on the response headers."""
    custom_id = "test-custom-trace-uuid-12345"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("X-Request-ID") == custom_id


def test_analyze_with_ml_model_unavailable_fallback(client):
    """Verify analyzer continues to detect rule-based errors even when ML predictor is unavailable."""
    from app.services.analysis import get_analysis_service

    code = 'def compute() -> int:\n    return "string_not_int"\n'
    service = get_analysis_service()

    with patch.object(service.predictor, "predict") as mock_predict:
        # Mock predictor returning model_unavailable
        mock_predict.return_value = MLPredictionResult(
            status="model_unavailable",
            reason="Model weights artifact missing",
        )
        response = client.post(
            "/api/v1/analyze",
            json={"source_code": code, "enable_ml_analysis": True},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert len(data["findings"]) == 1
        f = data["findings"][0]
        assert f["rule_id"] == "TM005_INCOMPATIBLE_RETURN"
        assert f["origin"] == "rule_based"
        assert f["is_confirmed"] is True
