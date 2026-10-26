"""Modular AST-based semantic analyzer for Python source code."""

from __future__ import annotations
import ast
import time
import uuid
from typing import List, Optional
from app.core.config import get_settings
from app.schemas.analysis import AnalysisResponse, AnalysisSummary
from app.schemas.common import ErrorCategory, FindingOrigin, Severity, SourceLocation, TypeInfo
from app.schemas.diagnostics import DiagnosticFinding
from app.semantic.inference import get_node_location, infer_expr_type
from app.semantic.rules.assignments import check_annotated_assignment, check_reassignment
from app.semantic.rules.binary_ops import check_binary_op
from app.semantic.rules.calls import check_call
from app.semantic.rules.returns import check_return
from app.semantic.symbol_table import Symbol, SymbolTable
from app.semantic.types import UNKNOWN, parse_type_annotation


class DeclarationCollector(ast.NodeVisitor):
    """First-pass visitor: collects functions, parameters, and global annotations."""

    def __init__(self, symbol_table: SymbolTable, file_path: Optional[str] = None) -> None:
        self.symbol_table = symbol_table
        self.file_path = file_path

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._register_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._register_function(node)

    def _register_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        ret_type = parse_type_annotation(node.returns)
        param_names: List[str] = []
        param_types = {}
        param_has_default = {}

        # Compute default values mapping
        total_args = len(node.args.args)
        num_defaults = len(node.args.defaults)
        first_default_idx = total_args - num_defaults

        for i, arg in enumerate(node.args.args):
            p_name = arg.arg
            param_names.append(p_name)
            param_types[p_name] = parse_type_annotation(arg.annotation)
            param_has_default[p_name] = (i >= first_default_idx)

        has_varargs = node.args.vararg is not None
        has_kwargs = node.args.kwarg is not None

        loc = get_node_location(node, self.file_path)
        self.symbol_table.define(
            name=node.name,
            type=ret_type,
            is_annotated=node.returns is not None,
            location=loc,
            is_function=True,
            param_names=param_names,
            param_types=param_types,
            param_has_default=param_has_default,
            has_varargs=has_varargs,
            has_kwargs=has_kwargs,
            return_type=ret_type,
        )


class SemanticCheckVisitor(ast.NodeVisitor):
    """Second-pass visitor: scope-aware semantic type checker."""

    def __init__(self, symbol_table: SymbolTable, file_path: Optional[str] = None) -> None:
        self.symbol_table = symbol_table
        self.file_path = file_path
        self.findings: List[DiagnosticFinding] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._enter_and_check_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._enter_and_check_function(node)

    def _enter_and_check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        # Retrieve function signature from symbol table
        sym = self.symbol_table.lookup(node.name)
        ret_type = sym.return_type if sym else parse_type_annotation(node.returns)

        # Enter function scope
        self.symbol_table.enter_scope(name=node.name, scope_type="function", return_type=ret_type)

        # Register parameters into local scope
        if sym:
            for p_name in sym.param_names:
                p_type = sym.param_types.get(p_name, UNKNOWN)
                self.symbol_table.define(
                    name=p_name,
                    type=p_type,
                    is_annotated=p_type != UNKNOWN,
                )

        # Recurse into function statements
        for stmt in node.body:
            self.visit(stmt)

        # Exit function scope
        self.symbol_table.exit_scope()

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        # First check expression children (RHS)
        if node.value is not None:
            self.visit(node.value)

        # Check for annotated assignment mismatch: e.g. x: int = "str"
        rule_findings = check_annotated_assignment(node, self.symbol_table, self.file_path)
        self.findings.extend(rule_findings)

        # Register target symbol in symbol table
        if isinstance(node.target, ast.Name):
            annotated_t = parse_type_annotation(node.annotation)
            self.symbol_table.define(
                name=node.target.id,
                type=annotated_t,
                is_annotated=True,
                location=get_node_location(node, self.file_path),
            )

    def visit_Assign(self, node: ast.Assign) -> None:
        # Visit value expression
        self.visit(node.value)

        # Check for reassignment inconsistencies
        rule_findings = check_reassignment(node, self.symbol_table, self.file_path)
        self.findings.extend(rule_findings)

        # Infer value type and update symbol table
        inferred_t = infer_expr_type(node.value, self.symbol_table)
        for target in node.targets:
            if isinstance(target, ast.Name):
                existing = self.symbol_table.lookup_local(target.id)
                if existing is None or not existing.is_annotated:
                    self.symbol_table.define(
                        name=target.id,
                        type=inferred_t,
                        is_annotated=False,
                        location=get_node_location(node, self.file_path),
                    )

    def visit_BinOp(self, node: ast.BinOp) -> None:
        # Visit children first to catch nested operations
        self.generic_visit(node)
        rule_findings = check_binary_op(node, self.symbol_table, self.file_path)
        self.findings.extend(rule_findings)

    def visit_Call(self, node: ast.Call) -> None:
        # Visit children first
        self.generic_visit(node)
        rule_findings = check_call(node, self.symbol_table, self.file_path)
        self.findings.extend(rule_findings)

    def visit_Return(self, node: ast.Return) -> None:
        # Visit return expression
        if node.value is not None:
            self.visit(node.value)
        rule_findings = check_return(node, self.symbol_table, self.file_path)
        self.findings.extend(rule_findings)


class SemanticAnalyzer:
    """Production AST-based semantic analyzer for Python source code."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def analyze(self, source_code: str, file_path: Optional[str] = None) -> AnalysisResponse:
        """Parse and semantically analyze Python source code.

        Returns a structured AnalysisResponse adhering to Phase 1 data contracts.
        """
        start_time = time.perf_counter()
        lines_count = len([line for line in source_code.splitlines() if line.strip()])

        # 1. Parsing Phase with Syntax Error Handling
        try:
            tree = ast.parse(source_code, filename=file_path or "<string>")
        except SyntaxError as e:
            execution_time = (time.perf_counter() - start_time) * 1000.0
            error_line = e.lineno or 1
            error_col = e.offset or 1
            end_line = getattr(e, "end_lineno", error_line) or error_line
            end_col = getattr(e, "end_offset", error_col) or error_col

            syntax_finding = DiagnosticFinding(
                id=f"TM000-{uuid.uuid4().hex[:8]}",
                message=f"Syntax Error: {e.msg}",
                category=ErrorCategory.SYNTAX_ERROR,
                severity=Severity.ERROR,
                location=SourceLocation(
                    file_path=file_path,
                    line=error_line,
                    column=error_col,
                    end_line=end_line,
                    end_column=end_col,
                ),
                origin=FindingOrigin.RULE_BASED,
                is_confirmed=True,
                rule_id="TM000_SYNTAX_ERROR",
                explanation=f"Source code could not be parsed: {e.msg} at line {error_line}, column {error_col}.",
            )

            summary = AnalysisSummary(
                total_findings=1,
                rule_based_findings=1,
                ml_predicted_findings=0,
                errors_count=1,
                warnings_count=0,
                syntax_errors_count=1,
                execution_time_ms=round(execution_time, 2),
                lines_analyzed=lines_count,
            )

            return AnalysisResponse(
                status="syntax_error",
                syntax_error=syntax_finding,
                findings=[],
                summary=summary,
                server_version=self.settings.app_version,
            )

        # 2. Semantic Analysis Phase
        symbol_table = SymbolTable()

        # Pass 1: Declaration collection
        collector = DeclarationCollector(symbol_table, file_path=file_path)
        collector.visit(tree)

        # Pass 2: Semantic rules traversal
        checker = SemanticCheckVisitor(symbol_table, file_path=file_path)
        checker.visit(tree)

        execution_time = (time.perf_counter() - start_time) * 1000.0

        errors_count = sum(1 for f in checker.findings if f.severity == Severity.ERROR)
        warnings_count = sum(1 for f in checker.findings if f.severity == Severity.WARNING)

        summary = AnalysisSummary(
            total_findings=len(checker.findings),
            rule_based_findings=len(checker.findings),
            ml_predicted_findings=0,
            errors_count=errors_count,
            warnings_count=warnings_count,
            syntax_errors_count=0,
            execution_time_ms=round(execution_time, 2),
            lines_analyzed=lines_count,
        )

        return AnalysisResponse(
            status="success",
            syntax_error=None,
            findings=checker.findings,
            summary=summary,
            server_version=self.settings.app_version,
        )
