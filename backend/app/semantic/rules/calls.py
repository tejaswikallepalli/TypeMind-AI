"""Rule checks for function calls: argument count and annotated argument type compatibility."""

from __future__ import annotations
import ast
import uuid
from typing import List, Optional
from app.schemas.common import ErrorCategory, FindingOrigin, Severity, SourceLocation, TypeInfo
from app.schemas.diagnostics import DiagnosticFinding
from app.semantic.inference import get_node_location, infer_expr_type
from app.semantic.symbol_table import SymbolTable
from app.semantic.types import UNKNOWN


def check_call(
    node: ast.Call,
    symbol_table: SymbolTable,
    file_path: Optional[str] = None,
) -> List[DiagnosticFinding]:
    """Check function call against resolvable parameter definitions."""
    findings: List[DiagnosticFinding] = []

    func_name: Optional[str] = None
    if isinstance(node.func, ast.Name):
        func_name = node.func.id
    elif isinstance(node.func, ast.Attribute):
        # Attribute calls like obj.method() - skip if object/method not in static symbol table
        return findings

    if not func_name:
        return findings

    sym = symbol_table.lookup(func_name)
    if sym is None or not sym.is_function:
        return findings

    loc = get_node_location(node, file_path)

    # 1. Argument Count Checks (only if function does not accept *args or **kwargs)
    if not sym.has_varargs and not sym.has_kwargs:
        total_params = len(sym.param_names)
        required_params = sum(
            1 for p in sym.param_names if not sym.param_has_default.get(p, False)
        )

        provided_positional = len(node.args)
        provided_keyword_names = {kw.arg for kw in node.keywords if kw.arg is not None}
        total_provided = provided_positional + len(provided_keyword_names)

        # Check for missing required arguments
        if total_provided < required_params:
            findings.append(
                DiagnosticFinding(
                    id=f"TM003-{uuid.uuid4().hex[:8]}",
                    message=(
                        f"Function '{func_name}' expects at least {required_params} arguments, "
                        f"but only {total_provided} were provided."
                    ),
                    category=ErrorCategory.ARGUMENT_COUNT_MISMATCH,
                    severity=Severity.ERROR,
                    location=loc,
                    origin=FindingOrigin.RULE_BASED,
                    is_confirmed=True,
                    rule_id="TM003_ARGUMENT_COUNT_MISMATCH",
                    explanation=f"Required parameters for '{func_name}': {sym.param_names[:required_params]}.",
                )
            )
            return findings

        # Check for too many positional arguments
        if provided_positional > total_params:
            findings.append(
                DiagnosticFinding(
                    id=f"TM003-{uuid.uuid4().hex[:8]}",
                    message=(
                        f"Function '{func_name}' takes {total_params} positional arguments, "
                        f"but {provided_positional} were given."
                    ),
                    category=ErrorCategory.ARGUMENT_COUNT_MISMATCH,
                    severity=Severity.ERROR,
                    location=loc,
                    origin=FindingOrigin.RULE_BASED,
                    is_confirmed=True,
                    rule_id="TM003_ARGUMENT_COUNT_MISMATCH",
                    explanation=f"Function was defined with {total_params} parameters: {sym.param_names}.",
                )
            )
            return findings

    # 2. Argument Type Checks (Positional Arguments)
    for i, arg_expr in enumerate(node.args):
        if i >= len(sym.param_names):
            break
        param_name = sym.param_names[i]
        expected_t = sym.param_types.get(param_name, UNKNOWN)

        if expected_t.is_unknown or expected_t.is_any:
            continue

        observed_t = infer_expr_type(arg_expr, symbol_table)
        if observed_t.is_unknown or observed_t.is_any:
            continue

        if not observed_t.is_compatible_with(expected_t):
            arg_loc = get_node_location(arg_expr, file_path)
            findings.append(
                DiagnosticFinding(
                    id=f"TM004-{uuid.uuid4().hex[:8]}",
                    message=(
                        f"Argument '{param_name}' of function '{func_name}' expected type '{expected_t}', "
                        f"but received incompatible type '{observed_t}'."
                    ),
                    category=ErrorCategory.ARGUMENT_TYPE_MISMATCH,
                    severity=Severity.ERROR,
                    location=arg_loc,
                    origin=FindingOrigin.RULE_BASED,
                    is_confirmed=True,
                    rule_id="TM004_ARGUMENT_TYPE_MISMATCH",
                    expected_type=TypeInfo(raw_type=str(expected_t)),
                    observed_type=TypeInfo(raw_type=str(observed_t)),
                    explanation=(
                        f"Parameter '{param_name}' is annotated with type '{expected_t}'. "
                        f"The provided expression evaluates to '{observed_t}'."
                    ),
                )
            )

    # 3. Argument Type Checks (Keyword Arguments)
    for kw in node.keywords:
        if kw.arg is None or kw.arg not in sym.param_types:
            continue
        param_name = kw.arg
        expected_t = sym.param_types[param_name]

        if expected_t.is_unknown or expected_t.is_any:
            continue

        observed_t = infer_expr_type(kw.value, symbol_table)
        if observed_t.is_unknown or observed_t.is_any:
            continue

        if not observed_t.is_compatible_with(expected_t):
            kw_loc = get_node_location(kw.value, file_path)
            findings.append(
                DiagnosticFinding(
                    id=f"TM004-{uuid.uuid4().hex[:8]}",
                    message=(
                        f"Keyword argument '{param_name}' of function '{func_name}' expected type '{expected_t}', "
                        f"but received incompatible type '{observed_t}'."
                    ),
                    category=ErrorCategory.ARGUMENT_TYPE_MISMATCH,
                    severity=Severity.ERROR,
                    location=kw_loc,
                    origin=FindingOrigin.RULE_BASED,
                    is_confirmed=True,
                    rule_id="TM004_ARGUMENT_TYPE_MISMATCH",
                    expected_type=TypeInfo(raw_type=str(expected_t)),
                    observed_type=TypeInfo(raw_type=str(observed_t)),
                    explanation=f"Parameter '{param_name}' expects '{expected_t}'.",
                )
            )

    return findings
