"""Tests for domain exceptions and global error handlers."""

from app.core.errors import (
    ModelInferenceError,
    SemanticAnalysisError,
    TypeMindException,
    ValidationError,
)


def test_typemind_exception_attributes():
    exc = TypeMindException("General engine failure", status_code=500, details={"code": "ERR_001"})
    assert exc.message == "General engine failure"
    assert exc.status_code == 500
    assert exc.details == {"code": "ERR_001"}


def test_semantic_analysis_error():
    exc = SemanticAnalysisError("Syntax error parsing AST", details={"line": 42})
    assert exc.status_code == 422
    assert "Syntax error" in exc.message
    assert exc.details["line"] == 42


def test_model_inference_error():
    exc = ModelInferenceError("ML classifier weights unavailable")
    assert exc.status_code == 503
    assert "classifier weights unavailable" in exc.message


def test_validation_error():
    exc = ValidationError("Invalid Python code snippet")
    assert exc.status_code == 400
