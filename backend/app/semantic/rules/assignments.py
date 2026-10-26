"""Rule checks for variable assignments and reassignment type inconsistencies."""

from __future__ import annotations
import ast
import uuid
from typing import List, Optional
from app.schemas.common import ErrorCategory, FindingOrigin, Severity, SourceLocation, TypeInfo
from app.schemas.diagnostics import DiagnosticFinding
from app.semantic.inference import get_node_location, infer_expr_type
from app.semantic.symbol_table import SymbolTable
from app.semantic.types import parse_type_annotation


def check_annotated_assignment(
    node: ast.AnnAssign,
    symbol_table: SymbolTable,
    file_path: Optional[str] = None,
) -> List[DiagnosticFinding]:
    """Check annotated assignment: e.g. x: int = 'hello'."""
    findings: List[DiagnosticFinding] = []

    if not isinstance(node.target, ast.Name):
        return findings

    var_name = node.target.id
    annotated_t = parse_type_annotation(node.annotation)

    if annotated_t.is_unknown or annotated_t.is_any:
        return findings

    if node.value is None:
        # Declaration without assignment: e.g. x: int
        return findings

    observed_t = infer_expr_type(node.value, symbol_table)
    if observed_t.is_unknown or observed_t.is_any:
        return findings

    if not observed_t.is_compatible_with(annotated_t):
        loc = get_node_location(node, file_path)
        findings.append(
            DiagnosticFinding(
                id=f"TM006-{uuid.uuid4().hex[:8]}",
                message=(
                    f"Cannot assign value of type '{observed_t}' to variable '{var_name}' "
                    f"annotated as '{annotated_t}'."
                ),
                category=ErrorCategory.INVALID_ASSIGNMENT,
                severity=Severity.ERROR,
                location=loc,
                origin=FindingOrigin.RULE_BASED,
                is_confirmed=True,
                rule_id="TM006_INVALID_ANNOTATED_ASSIGNMENT",
                expected_type=TypeInfo(raw_type=str(annotated_t)),
                observed_type=TypeInfo(raw_type=str(observed_t)),
                explanation=(
                    f"Variable '{var_name}' is explicitly annotated as '{annotated_t}', "
                    f"but assigned an incompatible expression of type '{observed_t}'."
                ),
            )
        )

    return findings


def check_reassignment(
    node: ast.Assign,
    symbol_table: SymbolTable,
    file_path: Optional[str] = None,
) -> List[DiagnosticFinding]:
    """Check unannotated assignment for type inconsistency with existing local symbol."""
    findings: List[DiagnosticFinding] = []

    for target in node.targets:
        if not isinstance(target, ast.Name):
            continue

        var_name = target.id
        existing_sym = symbol_table.lookup_local(var_name)

        # If symbol does not exist yet in local scope, this is initial definition
        if existing_sym is None or existing_sym.type.is_unknown or existing_sym.type.is_any:
            continue

        new_t = infer_expr_type(node.value, symbol_table)
        if new_t.is_unknown or new_t.is_any:
            continue

        if not new_t.is_compatible_with(existing_sym.type):
            loc = get_node_location(node, file_path)
            if existing_sym.is_annotated:
                findings.append(
                    DiagnosticFinding(
                        id=f"TM006-{uuid.uuid4().hex[:8]}",
                        message=(
                            f"Cannot assign value of type '{new_t}' to variable '{var_name}' "
                            f"annotated as '{existing_sym.type}'."
                        ),
                        category=ErrorCategory.INVALID_ASSIGNMENT,
                        severity=Severity.ERROR,
                        location=loc,
                        origin=FindingOrigin.RULE_BASED,
                        is_confirmed=True,
                        rule_id="TM006_INVALID_ANNOTATED_ASSIGNMENT",
                        expected_type=TypeInfo(raw_type=str(existing_sym.type)),
                        observed_type=TypeInfo(raw_type=str(new_t)),
                        explanation=(
                            f"Variable '{var_name}' was previously annotated as '{existing_sym.type}'. "
                            f"Reassigning it to '{new_t}' violates its type contract."
                        ),
                    )
                )
            else:
                findings.append(
                    DiagnosticFinding(
                        id=f"TM007-{uuid.uuid4().hex[:8]}",
                        message=(
                            f"Variable '{var_name}' previously established as type '{existing_sym.type}' "
                            f"reassigned to incompatible type '{new_t}'."
                        ),
                        category=ErrorCategory.TYPE_MISMATCH,
                        severity=Severity.WARNING,
                        location=loc,
                        origin=FindingOrigin.RULE_BASED,
                        is_confirmed=True,
                        rule_id="TM007_INCOMPATIBLE_REASSIGNMENT",
                        expected_type=TypeInfo(raw_type=str(existing_sym.type)),
                        observed_type=TypeInfo(raw_type=str(new_t)),
                        explanation=(
                            f"Reassigning variable '{var_name}' from '{existing_sym.type}' to '{new_t}' "
                            f"creates a type inconsistency within scope '{symbol_table.current_scope.name}'."
                        ),
                    )
                )

    return findings
