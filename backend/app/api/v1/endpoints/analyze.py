"""Semantic source code analysis API endpoint."""

import logging
from fastapi import APIRouter, Depends, Request, status

from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.analysis import AnalysisService, get_analysis_service

logger = logging.getLogger("typemind.api.analyze")
router = APIRouter()


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Python Source Code",
    description=(
        "Performs AST-based semantic analysis on Python source code without executing it. "
        "Detects type mismatches, incompatible return statements, argument mismatches, "
        "and reassignment inconsistencies."
    ),
)
async def analyze_source_code(
    request: AnalysisRequest,
    http_request: Request,
    service: AnalysisService = Depends(get_analysis_service),
) -> AnalysisResponse:
    """Analyze submitted Python source code and return structured diagnostic findings."""
    request_id = getattr(http_request.state, "request_id", "unknown")
    line_count = len(request.source_code.splitlines())
    char_count = len(request.source_code)
    logger.info(
        "Analysis request [%s]: lang=%s, %d chars, %d lines (file=%s, ml=%s, min_conf=%.2f)",
        request_id,
        request.language or "python",
        char_count,
        line_count,
        request.file_path or "<stdin>",
        request.enable_ml_analysis,
        request.min_confidence,
    )

    response = service.analyze_code(request)

    logger.info(
        "Analysis completed [%s]: status=%s, findings=%d, exec_time=%.2fms",
        request_id,
        response.status,
        response.summary.total_findings,
        response.summary.execution_time_ms,
    )
    return response
