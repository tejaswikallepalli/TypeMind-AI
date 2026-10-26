"""Deterministic AST and semantic feature extraction for TypeMind ML pipeline."""

from __future__ import annotations
import ast
from typing import Any, Dict, List, Optional
from app.semantic.inference import infer_expr_type
from app.semantic.symbol_table import SymbolTable
from app.semantic.types import UNKNOWN, parse_type_annotation


class CodePatternFeatureExtractor:
    """Extracts abstract, structural, and semantic features from Python code snippets.

    Does not depend on specific variable names, file paths, or line numbers.
    """

    def __init__(self) -> None:
        pass

    def extract_features(self, source_code: str) -> Dict[str, Any]:
        """Extract a fixed dictionary of structural and semantic features from source code.

        Returns a dictionary suitable for vectorization in an ML pipeline.
        """
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return self._default_malformed_features()

        # Build symbol table for the snippet
        symbol_table = SymbolTable()
        self._populate_declarations(tree, symbol_table)

        # Locate focal target node (e.g. Call, Return, BinOp, AnnAssign, Assign)
        focal_node, context = self._find_focal_node(tree, symbol_table)

        features: Dict[str, Any] = {
            "node_type": focal_node.__class__.__name__ if focal_node else "None",
            "operator": "None",
            "left_type": "n/a",
            "right_type": "n/a",
            "expected_type": "n/a",
            "observed_type": "n/a",
            "has_type_mismatch": 0,
            "has_unknown_type": 0,
            "is_in_function": 1 if context.get("in_function") else 0,
            "has_return_annotation": 1 if context.get("has_return_annotation") else 0,
            "has_param_annotations": 1 if context.get("has_param_annotations") else 0,
            "args_count": 0,
            "expected_args_count": 0,
            "args_count_diff": 0,
            "has_defaults": 1 if context.get("has_defaults") else 0,
            "is_constant_literal": 0,
            "num_lines": len([l for l in source_code.splitlines() if l.strip()]),
            "ast_depth": self._compute_ast_depth(tree),
            "is_malformed": 0,
        }

        if focal_node is None:
            return features

        # 1. Binary Operations Features
        if isinstance(focal_node, ast.BinOp):
            features["operator"] = focal_node.op.__class__.__name__
            left_t = infer_expr_type(focal_node.left, symbol_table)
            right_t = infer_expr_type(focal_node.right, symbol_table)

            features["left_type"] = left_t.name
            features["right_type"] = right_t.name

            if left_t.is_unknown or right_t.is_unknown:
                features["has_unknown_type"] = 1
            elif not left_t.is_compatible_with(right_t):
                features["has_type_mismatch"] = 1

            if isinstance(focal_node.left, ast.Constant) or isinstance(focal_node.right, ast.Constant):
                features["is_constant_literal"] = 1

        # 2. Function Call Features
        elif isinstance(focal_node, ast.Call):
            features["args_count"] = len(focal_node.args) + len(focal_node.keywords)
            func_name = None
            if isinstance(focal_node.func, ast.Name):
                func_name = focal_node.func.id
            elif isinstance(focal_node.func, ast.Attribute):
                func_name = focal_node.func.attr

            if func_name:
                sym = symbol_table.lookup(func_name)
                if sym and sym.is_function:
                    features["expected_args_count"] = len(sym.param_names)
                    features["args_count_diff"] = features["args_count"] - features["expected_args_count"]
                    features["has_defaults"] = 1 if any(sym.param_has_default.values()) else 0

                    # Check argument type mismatch on first arg
                    if focal_node.args and sym.param_names:
                        p_name = sym.param_names[0]
                        expected_p_t = sym.param_types.get(p_name, UNKNOWN)
                        observed_arg_t = infer_expr_type(focal_node.args[0], symbol_table)

                        features["expected_type"] = expected_p_t.name
                        features["observed_type"] = observed_arg_t.name

                        if not expected_p_t.is_unknown and not observed_arg_t.is_unknown:
                            if not observed_arg_t.is_compatible_with(expected_p_t):
                                features["has_type_mismatch"] = 1

        # 3. Return Statement Features
        elif isinstance(focal_node, ast.Return):
            expected_ret_t = symbol_table.get_enclosing_function_return_type()
            if expected_ret_t:
                features["expected_type"] = expected_ret_t.name
                features["has_return_annotation"] = 1

            observed_ret_t = (
                infer_expr_type(focal_node.value, symbol_table)
                if focal_node.value is not None
                else parse_type_annotation(None)
            )
            features["observed_type"] = observed_ret_t.name

            if expected_ret_t and not expected_ret_t.is_unknown and not observed_ret_t.is_unknown:
                if not observed_ret_t.is_compatible_with(expected_ret_t):
                    features["has_type_mismatch"] = 1

        # 4. Annotated Assignment Features
        elif isinstance(focal_node, ast.AnnAssign):
            annotated_t = parse_type_annotation(focal_node.annotation)
            features["expected_type"] = annotated_t.name
            if focal_node.value is not None:
                val_t = infer_expr_type(focal_node.value, symbol_table)
                features["observed_type"] = val_t.name
                if not annotated_t.is_unknown and not val_t.is_unknown:
                    if not val_t.is_compatible_with(annotated_t):
                        features["has_type_mismatch"] = 1
                if isinstance(focal_node.value, ast.Constant):
                    features["is_constant_literal"] = 1

        # 5. Regular Assignment Features
        elif isinstance(focal_node, ast.Assign):
            val_t = infer_expr_type(focal_node.value, symbol_table)
            features["observed_type"] = val_t.name
            if isinstance(focal_node.value, ast.Constant):
                features["is_constant_literal"] = 1

        return features

    def _default_malformed_features(self) -> Dict[str, Any]:
        """Return safe fallback feature representation for unparseable input."""
        return {
            "node_type": "Malformed",
            "operator": "None",
            "left_type": "n/a",
            "right_type": "n/a",
            "expected_type": "n/a",
            "observed_type": "n/a",
            "has_type_mismatch": 0,
            "has_unknown_type": 1,
            "is_in_function": 0,
            "has_return_annotation": 0,
            "has_param_annotations": 0,
            "args_count": 0,
            "expected_args_count": 0,
            "args_count_diff": 0,
            "has_defaults": 0,
            "is_constant_literal": 0,
            "num_lines": 0,
            "ast_depth": 0,
            "is_malformed": 1,
        }

    def _populate_declarations(self, tree: ast.AST, symbol_table: SymbolTable) -> None:
        """Register top-level functions and annotations into symbol table."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                ret_t = parse_type_annotation(node.returns)
                param_names = [arg.arg for arg in node.args.args]
                param_types = {arg.arg: parse_type_annotation(arg.annotation) for arg in node.args.args}

                num_defaults = len(node.args.defaults)
                first_default_idx = len(param_names) - num_defaults
                param_has_default = {name: (i >= first_default_idx) for i, name in enumerate(param_names)}

                symbol_table.define(
                    name=node.name,
                    type=ret_t,
                    is_annotated=node.returns is not None,
                    is_function=True,
                    param_names=param_names,
                    param_types=param_types,
                    param_has_default=param_has_default,
                    return_type=ret_t,
                )

    def _find_focal_node(self, tree: ast.AST, symbol_table: SymbolTable) -> tuple[Optional[ast.AST], Dict[str, Any]]:
        """Identify the primary statement or operation node representing the snippet pattern."""
        context: Dict[str, Any] = {
            "in_function": False,
            "has_return_annotation": False,
            "has_param_annotations": False,
            "has_defaults": False,
        }

        # Check for function context
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                context["in_function"] = True
                context["has_return_annotation"] = node.returns is not None
                context["has_param_annotations"] = any(arg.annotation is not None for arg in node.args.args)
                context["has_defaults"] = len(node.args.defaults) > 0
                symbol_table.enter_scope(node.name, "function", return_type=parse_type_annotation(node.returns))
                for arg in node.args.args:
                    symbol_table.define(arg.arg, parse_type_annotation(arg.annotation), is_annotated=True)

        # Priority 1: Top-level or trailing function calls: e.g. foo(1, 2)
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
        if calls:
            # Prefer calls that appear outside function definitions if present
            top_level_calls = [c for c in calls if not any(isinstance(p, ast.FunctionDef) for p in ast.walk(c))]
            return (top_level_calls[-1] if top_level_calls else calls[-1]), context

        # Priority 2: Annotated assignments: e.g. x: int = "val"
        ann_assigns = [n for n in ast.walk(tree) if isinstance(n, ast.AnnAssign)]
        if ann_assigns:
            return ann_assigns[0], context

        # Priority 3: Return statements
        returns = [n for n in ast.walk(tree) if isinstance(n, ast.Return) and n.value is not None]
        if returns:
            # If the return value is a binary op, check if the binary op itself is focal
            ret_val = returns[0].value
            if isinstance(ret_val, ast.BinOp):
                left_t = infer_expr_type(ret_val.left, symbol_table)
                right_t = infer_expr_type(ret_val.right, symbol_table)
                # If binary op has a mismatch, focal is BinOp; else Return
                if not left_t.is_unknown and not right_t.is_unknown and not left_t.is_compatible_with(right_t):
                    return ret_val, context
            return returns[0], context

        # Priority 4: Binary operations: e.g. a + b
        bin_ops = [n for n in ast.walk(tree) if isinstance(n, ast.BinOp)]
        if bin_ops:
            return bin_ops[0], context

        # Priority 5: Plain assignments
        assigns = [n for n in ast.walk(tree) if isinstance(n, ast.Assign)]
        if assigns:
            return assigns[0], context

        # Fallback to first body node
        if hasattr(tree, "body") and tree.body:
            return tree.body[0], context

        return None, context

    def _compute_ast_depth(self, node: ast.AST) -> int:
        """Compute the maximum depth of the AST hierarchy."""
        children = list(ast.iter_child_nodes(node))
        if not children:
            return 1
        return 1 + max(self._compute_ast_depth(child) for child in children)
