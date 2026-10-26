"""Python language adapter wrapping the core AST semantic analyzer."""

from typing import Optional
from app.languages.base import BaseLanguageAdapter
from app.schemas.analysis import AnalysisResponse
from app.schemas.languages import LanguageSupportLevel
from app.semantic.analyzer import SemanticAnalyzer


class PythonLanguageAdapter(BaseLanguageAdapter):
    """Adapter for Python source code using AST parsing, symbol tables, and static type inference."""

    def __init__(self, analyzer: Optional[SemanticAnalyzer] = None) -> None:
        super().__init__(
            language_id="python",
            display_name="Python",
            extensions=[".py", ".pyi", ".pyw"],
            analyzer_id="python_ast_semantic",
            tool_name="Built-in AST + Symbol Table",
            description="Static AST semantic analysis with symbol table inference, rule verification, and ML pattern classification.",
            install_instructions="Python 3.11+ standard library runtime (built-in).",
            is_ml_supported=True,
        )
        self.analyzer = analyzer or SemanticAnalyzer()

    def is_tool_available(self) -> bool:
        """Python AST parser is always available within the Python runtime."""
        return True

    def get_support_level(self) -> LanguageSupportLevel:
        return LanguageSupportLevel.SUPPORTED

    def analyze(
        self,
        source_code: str,
        file_path: Optional[str] = None,
    ) -> AnalysisResponse:
        """Analyze Python source code using deterministic AST rules."""
        base_resp = self.analyzer.analyze(source_code=source_code, file_path=file_path)
        return base_resp.model_copy(
            update={
                "language": self.language_id,
                "analyzer_id": self.analyzer_id,
                "support_level": LanguageSupportLevel.SUPPORTED.value,
                "status_message": "Python semantic analysis completed via AST rules.",
            }
        )
