"""Expression type inference engine and AST location utilities."""

from __future__ import annotations
import ast
from typing import Optional
from app.schemas.common import SourceLocation
from app.semantic.symbol_table import SymbolTable
from app.semantic.types import (
    ANY,
    BOOL,
    FLOAT,
    INT,
    NONE,
    STR,
    UNKNOWN,
    PyType,
    TypeKind,
    make_dict,
    make_list,
    make_set,
    make_tuple,
    make_union,
)


def get_node_location(node: ast.AST, file_path: Optional[str] = None) -> SourceLocation:
    """Extract a 1-indexed SourceLocation from an AST node."""
    line = getattr(node, "lineno", 1)
    col = getattr(node, "col_offset", 0) + 1  # ast col_offset is 0-indexed
    end_line = getattr(node, "end_lineno", line)
    end_col_raw = getattr(node, "end_col_offset", None)
    end_col = (end_col_raw + 1) if end_col_raw is not None else col

    # Safeguard against end location being prior to start location
    if end_line < line:
        end_line = line
    if end_line == line and end_col < col:
        end_col = col

    return SourceLocation(
        file_path=file_path,
        line=line,
        column=col,
        end_line=end_line,
        end_column=end_col,
    )


def infer_expr_type(node: Optional[ast.AST], symbol_table: SymbolTable) -> PyType:
    """Statically infer the PyType of an AST expression node.

    Conservatively returns UNKNOWN if the expression cannot be inferred
    with static certainty.
    """
    if node is None:
        return UNKNOWN

    # 1. Constant literals: int, float, str, bool, None
    if isinstance(node, ast.Constant):
        val = node.value
        if val is None:
            return NONE
        if isinstance(val, bool):
            return BOOL
        if isinstance(val, int):
            return INT
        if isinstance(val, float):
            return FLOAT
        if isinstance(val, str):
            return STR
        return UNKNOWN

    # 2. Variable references: Name
    if isinstance(node, ast.Name):
        sym = symbol_table.lookup(node.id)
        if sym is not None:
            return sym.type
        return UNKNOWN

    # 3. Collections: list, tuple, set, dict
    if isinstance(node, ast.List):
        if not node.elts:
            return make_list(UNKNOWN)
        elem_types = [infer_expr_type(e, symbol_table) for e in node.elts]
        first_t = elem_types[0]
        # If all elements have uniform known type, record it
        if all(t == first_t for t in elem_types):
            return make_list(first_t)
        return make_list(UNKNOWN)

    if isinstance(node, ast.Tuple):
        elem_types = tuple(infer_expr_type(e, symbol_table) for e in node.elts)
        return make_tuple(*elem_types)

    if isinstance(node, ast.Set):
        if not node.elts:
            return make_set(UNKNOWN)
        elem_types = [infer_expr_type(e, symbol_table) for e in node.elts]
        first_t = elem_types[0]
        if all(t == first_t for t in elem_types):
            return make_set(first_t)
        return make_set(UNKNOWN)

    if isinstance(node, ast.Dict):
        k_type = UNKNOWN
        v_type = UNKNOWN
        if node.keys and node.values:
            key_types = [infer_expr_type(k, symbol_table) for k in node.keys if k is not None]
            val_types = [infer_expr_type(v, symbol_table) for v in node.values]
            if key_types and all(t == key_types[0] for t in key_types):
                k_type = key_types[0]
            if val_types and all(t == val_types[0] for t in val_types):
                v_type = val_types[0]
        return make_dict(k_type, v_type)

    # 4. Formatted values (f-strings)
    if isinstance(node, ast.JoinedStr):
        return STR

    # 5. Comprehensions
    if isinstance(node, ast.ListComp):
        return make_list(UNKNOWN)
    if isinstance(node, ast.SetComp):
        return make_set(UNKNOWN)
    if isinstance(node, ast.DictComp):
        return make_dict(UNKNOWN, UNKNOWN)

    # 6. Comparisons (always bool)
    if isinstance(node, ast.Compare):
        return BOOL

    # 7. Unary Operations
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.Not):
            return BOOL
        operand_t = infer_expr_type(node.operand, symbol_table)
        if isinstance(node.op, (ast.UAdd, ast.USub)):
            if operand_t.is_numeric:
                return operand_t
        return UNKNOWN

    # 8. Binary Operations
    if isinstance(node, ast.BinOp):
        left_t = infer_expr_type(node.left, symbol_table)
        right_t = infer_expr_type(node.right, symbol_table)

        if left_t.is_unknown or right_t.is_unknown:
            return UNKNOWN

        # Addition / Concatenation
        if isinstance(node.op, ast.Add):
            if left_t == STR and right_t == STR:
                return STR
            if left_t == INT and right_t == INT:
                return INT
            if (left_t == FLOAT and right_t.is_numeric) or (right_t == FLOAT and left_t.is_numeric):
                return FLOAT
            if left_t.name == "list" and right_t.name == "list":
                return make_list(UNKNOWN)
            if left_t.name == "tuple" and right_t.name == "tuple":
                return make_tuple(UNKNOWN)

        # Subtraction, Modulo, Power
        if isinstance(node.op, (ast.Sub, ast.Mod, ast.Pow)):
            if left_t == INT and right_t == INT:
                return INT
            if (left_t == FLOAT and right_t.is_numeric) or (right_t == FLOAT and left_t.is_numeric):
                return FLOAT

        # Multiplication
        if isinstance(node.op, ast.Mult):
            if left_t == INT and right_t == INT:
                return INT
            if (left_t == FLOAT and right_t.is_numeric) or (right_t == FLOAT and left_t.is_numeric):
                return FLOAT
            # Sequence repetition: str * int or list * int
            if (left_t == STR and right_t == INT) or (left_t == INT and right_t == STR):
                return STR
            if (left_t.name == "list" and right_t == INT) or (left_t == INT and right_t.name == "list"):
                return make_list(UNKNOWN)

        # True Division always produces float
        if isinstance(node.op, ast.Div):
            if left_t.is_numeric and right_t.is_numeric:
                return FLOAT

        # Floor division
        if isinstance(node.op, ast.FloorDiv):
            if left_t == INT and right_t == INT:
                return INT
            if left_t.is_numeric and right_t.is_numeric:
                return FLOAT

        return UNKNOWN

    # 9. Function Calls
    if isinstance(node, ast.Call):
        # Direct function name call: e.g. str(x), my_func(a, b)
        if isinstance(node.func, ast.Name):
            sym = symbol_table.lookup(node.func.id)
            if sym is not None and sym.return_type is not None:
                return sym.return_type

        # Attribute method calls: e.g. x.upper(), x.split()
        if isinstance(node.func, ast.Attribute):
            target_t = infer_expr_type(node.func.value, symbol_table)
            method_name = node.func.attr
            if target_t == STR:
                if method_name in ("upper", "lower", "title", "strip", "lstrip", "rstrip", "replace"):
                    return STR
                if method_name in ("split", "rsplit", "splitlines"):
                    return make_list(STR)
                if method_name.startswith("is"):
                    return BOOL
                if method_name in ("find", "rfind", "index", "count"):
                    return INT

        return UNKNOWN

    # 10. Conditional Expression: x if cond else y
    if isinstance(node, ast.IfExp):
        body_t = infer_expr_type(node.body, symbol_table)
        orelse_t = infer_expr_type(node.orelse, symbol_table)
        if body_t == orelse_t:
            return body_t
        if not body_t.is_unknown and not orelse_t.is_unknown:
            return make_union(body_t, orelse_t)
        return UNKNOWN

    return UNKNOWN
