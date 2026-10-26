"""Semantic analysis package.

Exports the core SemanticAnalyzer, symbol tables, and type systems.
"""

from app.semantic.analyzer import SemanticAnalyzer
from app.semantic.symbol_table import Symbol, SymbolTable
from app.semantic.types import (
    ANY,
    BOOL,
    FLOAT,
    INT,
    NONE,
    STR,
    UNKNOWN,
    PyType,
    parse_type_annotation,
)

__all__ = [
    "SemanticAnalyzer",
    "SymbolTable",
    "Symbol",
    "PyType",
    "INT",
    "FLOAT",
    "STR",
    "BOOL",
    "NONE",
    "ANY",
    "UNKNOWN",
    "parse_type_annotation",
]
