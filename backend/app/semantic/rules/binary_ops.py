"""Rule checks for binary operations: concatenation and arithmetic compatibility."""

from __future__ import annotations
import ast
import uuid
from typing import List, Optional
from app.schemas.common import ErrorCategory, FindingOrigin, Severity, SourceLocation, TypeInfo
from app.schemas.diagnostics import DiagnosticFinding
from app.schemas.fixes import CodeReplacement, SuggestedFix
from app.semantic.inference import get_node_location, infer_expr_type
from app.semantic.symbol_table import SymbolTable
from app.semantic.types import BOOL, FLOAT, INT, NONE, STR, UNKNOWN, PyType


OP_SYMBOLS = {
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.Div: "/",
    ast.FloorDiv: "//",
    ast.Mod: "%",
    ast.Pow: "**",
    ast.LShift: "<<",
    ast.RShift: ">>",
    ast.BitOr: "|",
    ast.BitXor: "^",
    ast.BitAnd: "&",
}


def check_binary_op(
    node: ast.BinOp,
    symbol_table: SymbolTable,
    file_path: Optional[str] = None,
) -> List[DiagnosticFinding]:
    """Check binary operations for type compatibility."""
    findings: List[DiagnosticFinding] = []

    left_t = infer_expr_type(node.left, symbol_table)
    right_t = infer_expr_type(node.right, symbol_table)

    # Conservative rule: If either operand is unknown, do not emit errors
    if left_t.is_unknown or right_t.is_unknown:
        return findings

    loc = get_node_location(node, file_path)
    op_type = type(node.op)
    op_symbol = OP_SYMBOLS.get(op_type, "operation")

    # 1. String-number concatenation: "hello" + 5 or 5 + "hello"
    if isinstance(node.op, ast.Add):
        is_str_num = (left_t == STR and right_t.is_numeric) or (right_t == STR and left_t.is_numeric)
        if is_str_num:
            non_str_node = node.right if left_t == STR else node.left
            non_str_t = right_t if left_t == STR else left_t
            non_str_loc = get_node_location(non_str_node, file_path)

            fixes = [
                SuggestedFix(
                    id=f"fix-concat-{uuid.uuid4().hex[:8]}",
                    title=f"Convert {non_str_t} operand to str",
                    description=f"Wrap expression with str() to allow string concatenation.",
                    replacements=[
                        CodeReplacement(
                            location=non_str_loc,
                            new_text=f"str({ast.unparse(non_str_node)})",
                            description="Convert operand to string",
                        )
                    ],
                    diff_preview=f"- {ast.unparse(non_str_node)}\n+ str({ast.unparse(non_str_node)})",
                    confidence=0.98,
                    is_auto_applicable=True,
                )
            ]

            findings.append(
                DiagnosticFinding(
                    id=f"TM001-{uuid.uuid4().hex[:8]}",
                    message=f"Cannot concatenate 'str' and '{right_t}' using the '+' operator.",
                    category=ErrorCategory.TYPE_MISMATCH,
                    severity=Severity.ERROR,
                    location=loc,
                    origin=FindingOrigin.RULE_BASED,
                    is_confirmed=True,
                    rule_id="TM001_STRING_NUMBER_CONCAT",
                    expected_type=TypeInfo(raw_type="str"),
                    observed_type=TypeInfo(raw_type=str(right_t if left_t == STR else left_t)),
                    suggested_fixes=fixes,
                    explanation=(
                        f"In Python, the '+' operator does not automatically convert numbers to strings. "
                        f"Use explicit str() conversion or f-strings instead."
                    ),
                )
            )
            return findings

    # 2. Unsupported arithmetic: None with any arithmetic operator
    if left_t == NONE or right_t == NONE:
        findings.append(
            DiagnosticFinding(
                id=f"TM002-{uuid.uuid4().hex[:8]}",
                message=f"Unsupported operand types for {op_symbol}: '{left_t}' and '{right_t}'.",
                category=ErrorCategory.UNSUPPORTED_OPERAND,
                severity=Severity.ERROR,
                location=loc,
                origin=FindingOrigin.RULE_BASED,
                is_confirmed=True,
                rule_id="TM002_UNSUPPORTED_ARITHMETIC",
                expected_type=TypeInfo(raw_type="numeric"),
                observed_type=TypeInfo(raw_type="None"),
                explanation=f"Values of type None cannot be used in arithmetic operations.",
            )
        )
        return findings

    # 3. Operations on collections and sequences
    # Subtraction, Division, FloorDiv, Mod, Pow on str
    if left_t == STR or right_t == STR:
        if isinstance(node.op, (ast.Sub, ast.Div, ast.FloorDiv, ast.Pow)):
            findings.append(
                DiagnosticFinding(
                    id=f"TM002-{uuid.uuid4().hex[:8]}",
                    message=f"Unsupported operand types for {op_symbol}: '{left_t}' and '{right_t}'.",
                    category=ErrorCategory.UNSUPPORTED_OPERAND,
                    severity=Severity.ERROR,
                    location=loc,
                    origin=FindingOrigin.RULE_BASED,
                    is_confirmed=True,
                    rule_id="TM002_UNSUPPORTED_ARITHMETIC",
                    expected_type=TypeInfo(raw_type="numeric"),
                    observed_type=TypeInfo(raw_type="str"),
                    explanation=f"String objects do not support arithmetic '{op_symbol}'.",
                )
            )
            return findings

        # str * str is invalid
        if isinstance(node.op, ast.Mult) and left_t == STR and right_t == STR:
            findings.append(
                DiagnosticFinding(
                    id=f"TM002-{uuid.uuid4().hex[:8]}",
                    message=f"Cannot multiply sequence of non-int of type 'str'.",
                    category=ErrorCategory.UNSUPPORTED_OPERAND,
                    severity=Severity.ERROR,
                    location=loc,
                    origin=FindingOrigin.RULE_BASED,
                    is_confirmed=True,
                    rule_id="TM002_UNSUPPORTED_ARITHMETIC",
                    expected_type=TypeInfo(raw_type="int"),
                    observed_type=TypeInfo(raw_type="str"),
                    explanation=f"Strings can only be multiplied by integers for repetition.",
                )
            )
            return findings

    # Operations on list, tuple, set, dict
    left_name = left_t.name
    right_name = right_t.name
    coll_names = {"list", "tuple", "set", "dict"}

    if left_name in coll_names or right_name in coll_names:
        # List/tuple addition with different type: e.g. list + int, list + tuple
        if isinstance(node.op, ast.Add):
            if left_name in coll_names and right_name in coll_names and left_name != right_name:
                findings.append(
                    DiagnosticFinding(
                        id=f"TM002-{uuid.uuid4().hex[:8]}",
                        message=f"Cannot concatenate '{left_name}' and '{right_name}'.",
                        category=ErrorCategory.TYPE_MISMATCH,
                        severity=Severity.ERROR,
                        location=loc,
                        origin=FindingOrigin.RULE_BASED,
                        is_confirmed=True,
                        rule_id="TM002_UNSUPPORTED_ARITHMETIC",
                        expected_type=TypeInfo(raw_type=left_name),
                        observed_type=TypeInfo(raw_type=right_name),
                        explanation=f"Cannot concatenate incompatible collection types '{left_name}' and '{right_name}'.",
                    )
                )
                return findings

            if (left_name in coll_names and right_t.is_numeric) or (right_name in coll_names and left_t.is_numeric):
                findings.append(
                    DiagnosticFinding(
                        id=f"TM002-{uuid.uuid4().hex[:8]}",
                        message=f"Cannot concatenate '{left_name}' and '{right_t}'.",
                        category=ErrorCategory.TYPE_MISMATCH,
                        severity=Severity.ERROR,
                        location=loc,
                        origin=FindingOrigin.RULE_BASED,
                        is_confirmed=True,
                        rule_id="TM002_UNSUPPORTED_ARITHMETIC",
                        expected_type=TypeInfo(raw_type=left_name if left_name in coll_names else right_name),
                        observed_type=TypeInfo(raw_type=str(right_t if left_name in coll_names else left_t)),
                        explanation=f"Collections can only be concatenated with objects of the same collection type.",
                    )
                )
                return findings

            if left_name in ("dict", "set") or right_name in ("dict", "set"):
                findings.append(
                    DiagnosticFinding(
                        id=f"TM002-{uuid.uuid4().hex[:8]}",
                        message=f"Unsupported operand types for +: '{left_name}' and '{right_name}'.",
                        category=ErrorCategory.UNSUPPORTED_OPERAND,
                        severity=Severity.ERROR,
                        location=loc,
                        origin=FindingOrigin.RULE_BASED,
                        is_confirmed=True,
                        rule_id="TM002_UNSUPPORTED_ARITHMETIC",
                        expected_type=TypeInfo(raw_type="list | tuple"),
                        observed_type=TypeInfo(raw_type=left_name),
                        explanation=f"Sets and dictionaries do not support '+' operator. Use union (|) or update() instead.",
                    )
                )
                return findings

        # Subtraction, Division on lists, dicts, tuples
        if isinstance(node.op, (ast.Sub, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)):
            # Note: set - set is valid set difference, so only flag non-sets
            if left_name in ("list", "tuple", "dict") or right_name in ("list", "tuple", "dict"):
                findings.append(
                    DiagnosticFinding(
                        id=f"TM002-{uuid.uuid4().hex[:8]}",
                        message=f"Unsupported operand types for {op_symbol}: '{left_t}' and '{right_t}'.",
                        category=ErrorCategory.UNSUPPORTED_OPERAND,
                        severity=Severity.ERROR,
                        location=loc,
                        origin=FindingOrigin.RULE_BASED,
                        is_confirmed=True,
                        rule_id="TM002_UNSUPPORTED_ARITHMETIC",
                        expected_type=TypeInfo(raw_type="numeric"),
                        observed_type=TypeInfo(raw_type=left_name),
                        explanation=f"Collection type '{left_name}' does not support '{op_symbol}' arithmetic.",
                    )
                )
                return findings

        # Multiplication: list * non-int or dict * anything
        if isinstance(node.op, ast.Mult):
            if left_name in coll_names and right_name in coll_names:
                findings.append(
                    DiagnosticFinding(
                        id=f"TM002-{uuid.uuid4().hex[:8]}",
                        message=f"Cannot multiply sequence of non-int of type '{right_name}'.",
                        category=ErrorCategory.UNSUPPORTED_OPERAND,
                        severity=Severity.ERROR,
                        location=loc,
                        origin=FindingOrigin.RULE_BASED,
                        is_confirmed=True,
                        rule_id="TM002_UNSUPPORTED_ARITHMETIC",
                        expected_type=TypeInfo(raw_type="int"),
                        observed_type=TypeInfo(raw_type=right_name),
                        explanation=f"Collections can only be multiplied by integers.",
                    )
                )
                return findings

    return findings
