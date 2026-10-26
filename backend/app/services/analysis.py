"""Service layer orchestrating multi-language semantic analysis, ML inference, and diagnostic intelligence."""

import logging
from typing import Optional
from app.core.config import get_settings
from app.diagnostics.service import DiagnosticIntelligenceService, get_diagnostic_service
from app.languages.registry import LanguageRegistry, get_language_registry
from app.ml.predictor import MLPredictionResult, TypePatternPredictor
from app.schemas.analysis import AnalysisRequest, AnalysisResponse, AnalysisSummary
from app.schemas.common import ErrorCategory, FindingOrigin, Severity, SourceLocation
from app.schemas.diagnostics import DiagnosticFinding
from app.schemas.languages import LanguageSupportLevel
from app.semantic.analyzer import SemanticAnalyzer

logger = logging.getLogger("typemind.service.analysis")


class AnalysisService:
    """Orchestrates source code parsing across multiple languages, deterministic rules, ML predictions, and diagnostics."""

    def __init__(
        self,
        analyzer: Optional[SemanticAnalyzer] = None,
        predictor: Optional[TypePatternPredictor] = None,
        diagnostic_service: Optional[DiagnosticIntelligenceService] = None,
        registry: Optional[LanguageRegistry] = None,
    ) -> None:
        self.analyzer = analyzer or SemanticAnalyzer()
        self.predictor = predictor or TypePatternPredictor()
        self.diagnostic_service = diagnostic_service or get_diagnostic_service()
        self.registry = registry or get_language_registry()
        self.settings = get_settings()

    def analyze_code(self, request: AnalysisRequest) -> AnalysisResponse:
        """Route and execute analysis through appropriate language adapter."""
        # 1. Resolve target language
        target_lang = "python"
        if request.language and request.language.strip():
            target_lang = request.language.strip().lower()
        elif request.file_path:
            inferred = self.registry.detect_language_from_path(request.file_path)
            if inferred:
                target_lang = inferred

        # 2. Check if language is registered
        adapter = self.registry.get_adapter(target_lang)
        if not adapter:
            logger.warning("Requested unsupported language: %s", target_lang)
            return self._create_unsupported_language_response(target_lang, request)

        # 3. Handle Python: AST analysis + ML prediction + diagnostic intelligence
        if target_lang == "python":
            base_response = self.analyzer.analyze(
                source_code=request.source_code,
                file_path=request.file_path,
            )

            # Ensure multi-language fields are set
            base_response = base_response.model_copy(
                update={
                    "language": "python",
                    "analyzer_id": "python_ast_semantic",
                    "support_level": LanguageSupportLevel.SUPPORTED.value,
                    "status_message": "Python semantic AST analysis completed.",
                }
            )

            # Syntax errors halt semantic analysis
            if base_response.status == "syntax_error":
                return base_response

            # Machine Learning inference (Python only)
            ml_result: Optional[MLPredictionResult] = None
            if request.enable_ml_analysis:
                ml_result = self.predictor.predict(
                    source_code=request.source_code,
                    min_confidence=request.min_confidence,
                )

            # Diagnostic intelligence processing
            return self.diagnostic_service.process_diagnostics(
                base_response=base_response,
                source_code=request.source_code,
                ml_result=ml_result,
                file_path=request.file_path,
            )

        # 4. Handle Non-Python Languages
        # NEVER pass non-python source code to Python AST parser or ML classifier
        logger.info(
            "Routing [%s] analysis to adapter '%s' (tool: %s)",
            target_lang,
            adapter.analyzer_id,
            adapter.tool_name,
        )
        return adapter.analyze(
            source_code=request.source_code,
            file_path=request.file_path,
        )

    def _create_unsupported_language_response(
        self,
        language: str,
        request: AnalysisRequest,
    ) -> AnalysisResponse:
        """Create structured response when an unknown/unsupported language is requested."""
        registered = ", ".join(sorted(self.registry._adapters.keys()))
        msg = f"Language '{language}' is not recognized or supported by TypeMind AI."
        lines_count = len([line for line in request.source_code.splitlines() if line.strip()])

        finding = DiagnosticFinding(
            id=f"TM_UNSUPPORTED_LANG_{language.upper()}",
            message=msg,
            category=ErrorCategory.SYNTAX_ERROR,
            severity=Severity.ERROR,
            location=SourceLocation(file_path=request.file_path, line=1, column=1),
            origin=FindingOrigin.RULE_BASED,
            is_confirmed=True,
            rule_id="TM_LANG_UNSUPPORTED",
            explanation=f"TypeMind AI currently supports the following registered languages: {registered}.",
        )

        summary = AnalysisSummary(
            total_findings=1,
            rule_based_findings=1,
            ml_predicted_findings=0,
            errors_count=1,
            warnings_count=0,
            syntax_errors_count=0,
            category_counts={"syntax_error": 1},
            severity_counts={"error": 1},
            execution_time_ms=0.1,
            lines_analyzed=lines_count,
        )

        return AnalysisResponse(
            status="error",
            language=language,
            analyzer_id="unknown",
            support_level="unsupported",
            status_message=f"{msg} Available: {registered}.",
            syntax_error=None,
            findings=[finding],
            summary=summary,
            server_version=self.settings.app_version,
        )


_analysis_service = AnalysisService()


def get_analysis_service() -> AnalysisService:
    """Return singleton analysis service instance."""
    return _analysis_service

