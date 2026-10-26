"""Unit and integration tests for multi-language semantic analysis and registry."""

from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from app.languages.base import BaseLanguageAdapter, safe_subprocess_run
from app.languages.c_cpp import CLanguageAdapter, CppLanguageAdapter
from app.languages.csharp import CSharpLanguageAdapter
from app.languages.go import GoLanguageAdapter
from app.languages.java import JavaLanguageAdapter
from app.languages.javascript import JavaScriptLanguageAdapter
from app.languages.php import PhpLanguageAdapter
from app.languages.python import PythonLanguageAdapter
from app.languages.registry import LanguageRegistry, get_language_registry
from app.languages.ruby import RubyLanguageAdapter
from app.languages.rust import RustLanguageAdapter
from app.languages.typescript import TypeScriptLanguageAdapter
from app.main import create_app
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.schemas.common import ErrorCategory, Severity
from app.schemas.languages import LanguageSupportLevel, LanguagesResponse


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def registry():
    return get_language_registry()


class TestLanguageRegistry:
    """Tests for language registration, extensions, and resolution."""

    def test_all_11_languages_registered(self, registry: LanguageRegistry):
        expected_langs = [
            "python", "typescript", "javascript", "java",
            "c", "cpp", "csharp", "go", "rust", "php", "ruby"
        ]
        for lang_id in expected_langs:
            adapter = registry.get_adapter(lang_id)
            assert adapter is not None, f"Language '{lang_id}' should be registered in LanguageRegistry"
            assert adapter.language_id == lang_id

    def test_extension_detection(self, registry: LanguageRegistry):
        test_cases = [
            ("test.py", "python"),
            ("test.pyi", "python"),
            ("app.ts", "typescript"),
            ("Component.tsx", "typescript"),
            ("index.js", "javascript"),
            ("Component.jsx", "javascript"),
            ("Main.java", "java"),
            ("code.c", "c"),
            ("header.h", "c"),
            ("engine.cpp", "cpp"),
            ("header.hpp", "cpp"),
            ("Program.cs", "csharp"),
            ("main.go", "go"),
            ("lib.rs", "rust"),
            ("index.php", "php"),
            ("script.rb", "ruby"),
        ]
        for file_path, expected_lang in test_cases:
            detected = registry.detect_language_from_path(file_path)
            assert detected == expected_lang, f"Failed for {file_path}: expected {expected_lang}, got {detected}"

    def test_extension_detection_unknown(self, registry: LanguageRegistry):
        assert registry.detect_language_from_path("README.md") is None
        assert registry.detect_language_from_path("styles.css") is None
        assert registry.detect_language_from_path("") is None

    def test_get_languages_response(self, registry: LanguageRegistry):
        resp = registry.get_languages_response()
        assert isinstance(resp, LanguagesResponse)
        assert resp.total >= 11
        assert resp.default_language == "python"

        python_info = next((l for l in resp.languages if l.id == "python"), None)
        assert python_info is not None
        assert python_info.tool_available is True
        assert python_info.support_level == LanguageSupportLevel.SUPPORTED
        assert python_info.ml_supported is True


class TestLanguageAdapters:
    """Tests for language adapter execution and diagnostic normalization."""

    def test_python_adapter(self):
        adapter = PythonLanguageAdapter()
        assert adapter.is_tool_available() is True
        resp = adapter.analyze("x: int = 'hello'\n")
        assert resp.language == "python"
        assert resp.analyzer_id == "python_ast_semantic"
        assert resp.support_level == "supported"
        assert resp.summary.total_findings > 0

    def test_non_python_never_sent_to_ast_parser(self):
        """Ensures that Java code is analyzed by Java adapter and never reaches ast.parse()."""
        from app.services.analysis import get_analysis_service
        service = get_analysis_service()

        with patch("ast.parse") as mock_ast:
            java_code = "public class Main { public static void main(String[] args) { int x = \"bad\"; } }"
            req = AnalysisRequest(
                source_code=java_code,
                language="java",
                file_path="Main.java",
            )
            resp = service.analyze_code(req)
            # ast.parse must NOT be called for Java code
            mock_ast.assert_not_called()
            assert resp.language == "java"

    def test_typescript_adapter_with_tsc(self):
        adapter = TypeScriptLanguageAdapter()
        if not adapter.is_tool_available():
            pytest.skip("TypeScript compiler runner not available in this test environment")

        ts_code = 'let x: number = "string_value";\n'
        resp = adapter.analyze(ts_code, "test.ts")
        assert resp.language == "typescript"
        assert resp.analyzer_id == "typescript_tsc_compiler"
        assert resp.status in ("success", "partial")
        assert len(resp.findings) > 0
        finding = resp.findings[0]
        assert "TS2322" in finding.message or "not assignable" in finding.message.lower()
        assert finding.category == ErrorCategory.TYPE_MISMATCH
        assert finding.is_confirmed is True

    def test_typescript_adapter_mocked(self):
        adapter = TypeScriptLanguageAdapter()
        mock_output = "test.ts(3,5): error TS2322: Type 'string' is not assignable to type 'number'."

        with patch("app.languages.typescript.find_tsc_runner", return_value=["mock_tsc"]), \
             patch("app.languages.typescript.safe_subprocess_run", return_value=(2, mock_output, "")):
            resp = adapter.analyze("let x: number = 'hello';", "test.ts")
            assert resp.language == "typescript"
            assert len(resp.findings) == 1
            f = resp.findings[0]
            assert f.location.line == 3
            assert f.location.column == 5
            assert f.severity == Severity.ERROR
            assert f.category == ErrorCategory.TYPE_MISMATCH
            assert f.expected_type is not None
            assert f.expected_type.raw_type == "number"
            assert f.observed_type is not None
            assert f.observed_type.raw_type == "string"

    def test_java_adapter_tool_unavailable(self):
        adapter = JavaLanguageAdapter()
        with patch.object(adapter, "is_tool_available", return_value=False):
            resp = adapter.analyze("public class Main {}", "Main.java")
            assert resp.status == "tool_unavailable"
            assert resp.support_level == "tool_unavailable"
            assert len(resp.findings) == 1
            assert "javac" in resp.findings[0].message
            assert "Adoptium" in resp.findings[0].explanation

    def test_java_adapter_mocked_output(self):
        adapter = JavaLanguageAdapter()
        mock_stderr = "Main.java:5: error: incompatible types: java.lang.String cannot be converted to int\n    int x = \"test\";"

        with patch.object(adapter, "is_tool_available", return_value=True), \
             patch("app.languages.java.safe_subprocess_run", return_value=(1, "", mock_stderr)):
            resp = adapter.analyze("public class Main { int x = \"test\"; }", "Main.java")
            assert resp.language == "java"
            assert len(resp.findings) == 1
            f = resp.findings[0]
            assert f.location.line == 5
            assert f.category == ErrorCategory.TYPE_MISMATCH
            assert f.expected_type is not None
            assert f.expected_type.raw_type == "int"
            assert f.observed_type is not None
            assert f.observed_type.raw_type == "java.lang.String"

    def test_c_adapter_mocked(self):
        adapter = CLanguageAdapter()
        mock_stderr = "source.c:8:5: error: assigning to 'int' from incompatible type 'char *'\n    int a = \"bad\";"

        with patch("app.languages.c_cpp.find_c_compiler", return_value=("gcc", "gnu")), \
             patch("app.languages.c_cpp.safe_subprocess_run", return_value=(1, "", mock_stderr)):
            resp = adapter.analyze("int main() { int a = \"bad\"; }", "source.c")
            assert resp.language == "c"
            assert len(resp.findings) == 1
            f = resp.findings[0]
            assert f.location.line == 8
            assert f.category == ErrorCategory.TYPE_MISMATCH

    def test_rust_adapter_mocked_json(self):
        adapter = RustLanguageAdapter()
        json_diag = (
            '{"message": "mismatched types", "code": {"code": "E0308"}, '
            '"level": "error", "spans": [{"is_primary": true, "line_start": 4, "column_start": 9}]}'
        )

        with patch.object(adapter, "is_tool_available", return_value=True), \
             patch("app.languages.rust.safe_subprocess_run", return_value=(1, "", json_diag)):
            resp = adapter.analyze("fn main() { let x: i32 = \"hi\"; }", "main.rs")
            assert resp.language == "rust"
            assert len(resp.findings) == 1
            f = resp.findings[0]
            assert f.location.line == 4
            assert f.rule_id == "TM_RUST_E0308"
            assert f.category == ErrorCategory.TYPE_MISMATCH


class TestMultiLanguageAPI:
    """Integration tests for FastAPI endpoints with multi-language support."""

    def test_get_languages_endpoint(self, client: TestClient):
        response = client.get("/api/v1/languages")
        assert response.status_code == 200
        data = response.json()
        assert "languages" in data
        assert data["total"] >= 11
        ids = [l["id"] for l in data["languages"]]
        assert "python" in ids
        assert "typescript" in ids
        assert "java" in ids
        assert "c" in ids
        assert "cpp" in ids
        assert "rust" in ids

    def test_analyze_python_by_default(self, client: TestClient):
        payload = {"source_code": "x: int = 42\n"}
        resp = client.post("/api/v1/analyze", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["language"] == "python"
        assert data["analyzer_id"] == "python_ast_semantic"
        assert data["support_level"] == "supported"

    def test_analyze_unsupported_language(self, client: TestClient):
        payload = {"source_code": "code", "language": "brainfuck"}
        resp = client.post("/api/v1/analyze", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "error"
        assert data["support_level"] == "unsupported"
        assert len(data["findings"]) == 1
        assert "not recognized" in data["findings"][0]["message"]

    def test_analyze_infer_from_file_path(self, client: TestClient):
        payload = {
            "source_code": "let x: number = 123;\n",
            "file_path": "example.ts",
        }
        resp = client.post("/api/v1/analyze", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["language"] == "typescript"
