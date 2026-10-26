"""Symbol table and hierarchical scope tracking for TypeMind semantic analysis."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from app.schemas.common import SourceLocation
from app.semantic.types import (
    ANY,
    BOOL,
    FLOAT,
    INT,
    NONE,
    STR,
    UNKNOWN,
    PyType,
    make_dict,
    make_list,
    make_set,
    make_tuple,
)


@dataclass
class Symbol:
    """A declared or inferred named identifier within a scope."""

    name: str
    type: PyType
    is_annotated: bool = False
    location: Optional[SourceLocation] = None

    # Function metadata if this symbol is a callable function
    is_function: bool = False
    param_names: List[str] = field(default_factory=list)
    param_types: Dict[str, PyType] = field(default_factory=dict)
    param_has_default: Dict[str, bool] = field(default_factory=dict)
    has_varargs: bool = False
    has_kwargs: bool = False
    return_type: Optional[PyType] = None


class Scope:
    """A lexical scope (global, function, class, or block) holding symbols."""

    def __init__(
        self,
        name: str,
        scope_type: str = "function",
        parent: Optional[Scope] = None,
        return_type: Optional[PyType] = None,
    ) -> None:
        self.name = name
        self.scope_type = scope_type
        self.parent = parent
        self.return_type = return_type
        self.symbols: Dict[str, Symbol] = {}
        self.children: List[Scope] = []

    def define(self, symbol: Symbol) -> None:
        """Bind or update a symbol in this scope."""
        self.symbols[symbol.name] = symbol

    def lookup_local(self, name: str) -> Optional[Symbol]:
        """Look up symbol strictly within this local scope."""
        return self.symbols.get(name)

    def lookup(self, name: str, recursive: bool = True) -> Optional[Symbol]:
        """Look up symbol in this scope or enclosing parent scopes."""
        sym = self.symbols.get(name)
        if sym is not None:
            return sym
        if recursive and self.parent is not None:
            return self.parent.lookup(name, recursive=True)
        return None


class SymbolTable:
    """Manages the hierarchical stack of active scopes during AST traversal."""

    def __init__(self) -> None:
        self.global_scope = Scope(name="<global>", scope_type="global")
        self.current_scope = self.global_scope
        self._populate_builtins()

    def _populate_builtins(self) -> None:
        """Register common Python builtins with signatures and return types."""
        builtins: Dict[str, Symbol] = {
            "True": Symbol(name="True", type=BOOL, is_annotated=True),
            "False": Symbol(name="False", type=BOOL, is_annotated=True),
            "None": Symbol(name="None", type=NONE, is_annotated=True),
            # Type casting functions
            "str": Symbol(
                name="str",
                type=STR,
                is_function=True,
                param_names=["object"],
                param_types={"object": ANY},
                param_has_default={"object": True},
                return_type=STR,
            ),
            "int": Symbol(
                name="int",
                type=INT,
                is_function=True,
                param_names=["x"],
                param_types={"x": ANY},
                param_has_default={"x": True},
                return_type=INT,
            ),
            "float": Symbol(
                name="float",
                type=FLOAT,
                is_function=True,
                param_names=["x"],
                param_types={"x": ANY},
                param_has_default={"x": True},
                return_type=FLOAT,
            ),
            "bool": Symbol(
                name="bool",
                type=BOOL,
                is_function=True,
                param_names=["x"],
                param_types={"x": ANY},
                param_has_default={"x": True},
                return_type=BOOL,
            ),
            "len": Symbol(
                name="len",
                type=INT,
                is_function=True,
                param_names=["obj"],
                param_types={"obj": ANY},
                param_has_default={"obj": False},
                return_type=INT,
            ),
            "print": Symbol(
                name="print",
                type=NONE,
                is_function=True,
                param_names=[],
                has_varargs=True,
                return_type=NONE,
            ),
            "list": Symbol(
                name="list",
                type=make_list(ANY),
                is_function=True,
                param_names=["iterable"],
                param_has_default={"iterable": True},
                return_type=make_list(ANY),
            ),
            "dict": Symbol(
                name="dict",
                type=make_dict(ANY, ANY),
                is_function=True,
                param_names=[],
                has_kwargs=True,
                return_type=make_dict(ANY, ANY),
            ),
            "set": Symbol(
                name="set",
                type=make_set(ANY),
                is_function=True,
                param_names=["iterable"],
                param_has_default={"iterable": True},
                return_type=make_set(ANY),
            ),
            "tuple": Symbol(
                name="tuple",
                type=make_tuple(ANY),
                is_function=True,
                param_names=["iterable"],
                param_has_default={"iterable": True},
                return_type=make_tuple(ANY),
            ),
        }
        for name, sym in builtins.items():
            self.global_scope.define(sym)

    def enter_scope(
        self,
        name: str,
        scope_type: str = "function",
        return_type: Optional[PyType] = None,
    ) -> Scope:
        """Create and enter a new child scope."""
        new_scope = Scope(
            name=name,
            scope_type=scope_type,
            parent=self.current_scope,
            return_type=return_type,
        )
        self.current_scope.children.append(new_scope)
        self.current_scope = new_scope
        return self.current_scope

    def exit_scope(self) -> Scope:
        """Exit the current scope and return to the parent scope."""
        if self.current_scope.parent is not None:
            self.current_scope = self.current_scope.parent
        return self.current_scope

    def lookup(self, name: str) -> Optional[Symbol]:
        """Look up a symbol in current or enclosing scopes."""
        return self.current_scope.lookup(name, recursive=True)

    def lookup_local(self, name: str) -> Optional[Symbol]:
        """Look up a symbol in the active local scope only."""
        return self.current_scope.lookup_local(name)

    def define(
        self,
        name: str,
        type: PyType,
        is_annotated: bool = False,
        location: Optional[SourceLocation] = None,
        **kwargs,
    ) -> Symbol:
        """Define a symbol in the current scope."""
        sym = Symbol(
            name=name,
            type=type,
            is_annotated=is_annotated,
            location=location,
            **kwargs,
        )
        self.current_scope.define(sym)
        return sym

    def get_enclosing_function_return_type(self) -> Optional[PyType]:
        """Ascend scopes to find the expected return type of the enclosing function."""
        s: Optional[Scope] = self.current_scope
        while s is not None:
            if s.scope_type == "function":
                return s.return_type
            s = s.parent
        return None

    def get_enclosing_function_name(self) -> Optional[str]:
        """Return the name of the nearest enclosing function scope."""
        s: Optional[Scope] = self.current_scope
        while s is not None:
            if s.scope_type == "function":
                return s.name
            s = s.parent
        return None
