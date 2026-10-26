"""Rule checks for function return statements: annotated return type compatibility."""

from __future__ import annotations
import ast
import uuid
from typing import List, Optional
from app.schemas.common import ErrorCategory, FindingOrigin, Severity, SourceLocation, TypeInfo
from app.schemas.diagnostics import DiagnosticFinding
from app.semantic.inference import get_node_location, infer_expr_type
from app.semantic.symbol_table import SymbolTable
from app.semantic.types import NONE


def check_return(
    node: ast.Return,
    symbol_table: SymbolTable,
    file_path: Optional[str] = None,
) -> List[DiagnosticFinding]:
    """Check return statement against the enclosing function's annotated return type."""
    findings: List[DiagnosticFinding] = []

    expected_return_t = symbol_table.get_enclosing_function_return_type()
    if expected_return_t is None or expected_return_t.is_unknown or expected_return_t.is_any:
        return findings

    func_name = symbol_table.get_enclosing_function_name() or "<function>"

    # Bare return is equivalent to returning None
    if node.value is None:
        observed_t = NONE
    else:
        observed_t = infer_expr_type(node.value, symbol_table)

    if observed_t.is_unknown or observed_t.is_any:
        return findings

    if not observed_t.is_compatible_with(expected_return_t):
        loc = get_node_location(node, file_path)
        findings.append(
            DiagnosticFinding(
                id=f"TM005-{uuid.uuid4().hex[:8]}",
                message=(
                    f"Function '{func_name}' has return type annotation '{expected_return_t}', "
                    f"but returns incompatible type '{observed_t}'."
                ),
                category=ErrorCategory.INCOMPATIBLE_RETURN,
                severity=Severity.ERROR,
                location=loc,
                origin=FindingOrigin.RULE_BASED,
                is_confirmed=True,
                rule_id="TM005_INCOMPATIBLE_RETURN",
                expected_type=TypeInfo(raw_type=str(expected_return_t)),
                observed_type=TypeInfo(raw_type=str(observed_t)),
                explanation=(
                    f"Function signature declares return type '{expected_return_t}', "
                    f"but the returned expression evaluates to '{observed_t}'."
                ),
            )
        )

    return findings
