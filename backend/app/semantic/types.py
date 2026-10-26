"""Internal type representation and type compatibility engine for static analysis."""

from __future__ import annotations
import ast
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Set, Tuple, Union


class TypeKind(str, Enum):
    """Categorization of static types."""

    PRIMITIVE = "primitive"
    COLLECTION = "collection"
    CALLABLE = "callable"
    UNION = "union"
    ANY = "any"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PyType:
    """Immutable representation of a Python type in the TypeMind static analysis engine."""

    name: str
    kind: TypeKind = TypeKind.PRIMITIVE
    args: Tuple[PyType, ...] = field(default_factory=tuple)
    is_optional: bool = False

    def __str__(self) -> str:
        if self.kind == TypeKind.UNKNOWN:
            return "Unknown"
        if self.kind == TypeKind.ANY:
            return "Any"
        if self.kind == TypeKind.UNION:
            non_none = [str(arg) for arg in self.args if arg.name != "None"]
            has_none = any(arg.name == "None" for arg in self.args)
            joined = " | ".join(non_none)
            if has_none:
                return f"{joined} | None" if len(non_none) > 1 else f"Optional[{non_none[0]}]"
            return joined
        if self.args:
            args_str = ", ".join(str(arg) for arg in self.args)
            return f"{self.name}[{args_str}]"
        return self.name

    @property
    def is_unknown(self) -> bool:
        """True if the type is completely unknown or unresolvable."""
        return self.kind == TypeKind.UNKNOWN

    @property
    def is_any(self) -> bool:
        """True if type is explicitly typing.Any."""
        return self.kind == TypeKind.ANY

    @property
    def is_numeric(self) -> bool:
        """True if type represents a numeric value (int, float, bool)."""
        return self.name in ("int", "float", "bool")

    @property
    def is_strict_numeric(self) -> bool:
        """True for int and float (excluding bool)."""
        return self.name in ("int", "float")

    @property
    def is_collection(self) -> bool:
        """True if type is list, tuple, set, dict, or str."""
        return self.name in ("list", "tuple", "set", "dict", "str")

    def is_compatible_with(self, target: PyType) -> bool:
        """Check if this type can be used where `target` is expected.

        Conservative rule: If either type is Unknown or Any, we assume compatible
        to prevent false positive errors.
        """
        # Unknown or Any is conservatively compatible with anything
        if self.is_unknown or target.is_unknown or self.is_any or target.is_any:
            return True

        # Exact match
        if self.name == target.name:
            if not self.args or not target.args:
                return True
            if len(self.args) != len(target.args):
                return False
            return all(s.is_compatible_with(t) for s, t in zip(self.args, target.args))

        # Target is a Union: compatible if self matches any variant
        if target.kind == TypeKind.UNION:
            return any(self.is_compatible_with(variant) for variant in target.args)

        # Self is a Union: compatible only if all variants match target
        if self.kind == TypeKind.UNION:
            return all(variant.is_compatible_with(target) for variant in self.args)

        # Numeric widening: int is compatible with float
        if target.name == "float" and self.name in ("int", "bool"):
            return True

        # Python bool is an int subclass
        if target.name == "int" and self.name == "bool":
            return True

        return False


# Singleton definitions for standard primitive types
INT = PyType(name="int", kind=TypeKind.PRIMITIVE)
FLOAT = PyType(name="float", kind=TypeKind.PRIMITIVE)
STR = PyType(name="str", kind=TypeKind.PRIMITIVE)
BOOL = PyType(name="bool", kind=TypeKind.PRIMITIVE)
NONE = PyType(name="None", kind=TypeKind.PRIMITIVE)
ANY = PyType(name="Any", kind=TypeKind.ANY)
UNKNOWN = PyType(name="Unknown", kind=TypeKind.UNKNOWN)


def make_list(elem_type: PyType = UNKNOWN) -> PyType:
    """Create a list type with element type."""
    return PyType(name="list", kind=TypeKind.COLLECTION, args=(elem_type,))


def make_tuple(*elem_types: PyType) -> PyType:
    """Create a tuple type with element types."""
    return PyType(name="tuple", kind=TypeKind.COLLECTION, args=elem_types if elem_types else (UNKNOWN,))


def make_set(elem_type: PyType = UNKNOWN) -> PyType:
    """Create a set type with element type."""
    return PyType(name="set", kind=TypeKind.COLLECTION, args=(elem_type,))


def make_dict(key_type: PyType = UNKNOWN, val_type: PyType = UNKNOWN) -> PyType:
    """Create a dict type with key and value types."""
    return PyType(name="dict", kind=TypeKind.COLLECTION, args=(key_type, val_type))


def make_union(*types: PyType) -> PyType:
    """Create a union type from unique non-unknown types."""
    flat_types: List[PyType] = []
    for t in types:
        if t.kind == TypeKind.UNION:
            flat_types.extend(t.args)
        elif t.kind != TypeKind.UNKNOWN:
            if t not in flat_types:
                flat_types.append(t)
    if not flat_types:
        return UNKNOWN
    if len(flat_types) == 1:
        return flat_types[0]
    return PyType(name="Union", kind=TypeKind.UNION, args=tuple(flat_types))


def make_optional(base_type: PyType) -> PyType:
    """Create Optional[T] = Union[T, None]."""
    return make_union(base_type, NONE)


def parse_type_annotation(node: Optional[ast.AST]) -> PyType:
    """Parse an AST type annotation node into a PyType object.

    Supports:
    - Primitive names: int, float, str, bool, None
    - Collections: list[T], tuple[T], set[T], dict[K, V]
    - typing generics: List, Dict, Tuple, Set, Optional, Union, Any
    - PEP 604 union syntax: T1 | T2
    """
    if node is None:
        return UNKNOWN

    # Simple name: int, str, float, bool, list, dict, None, Any
    if isinstance(node, ast.Name):
        name = node.id
        mapping = {
            "int": INT,
            "float": FLOAT,
            "str": STR,
            "bool": BOOL,
            "None": NONE,
            "NoneType": NONE,
            "list": make_list(),
            "tuple": make_tuple(),
            "set": make_set(),
            "dict": make_dict(),
            "Any": ANY,
            "List": make_list(),
            "Tuple": make_tuple(),
            "Set": make_set(),
            "Dict": make_dict(),
        }
        return mapping.get(name, UNKNOWN)

    # Constant None: None
    if isinstance(node, ast.Constant):
        if node.value is None or node.value == "None":
            return NONE
        if isinstance(node.value, str):
            # Forward references / stringified annotations: e.g. "int"
            try:
                parsed = ast.parse(node.value, mode="eval")
                return parse_type_annotation(parsed.body)
            except Exception:
                return UNKNOWN
        return UNKNOWN

    # Subscript: list[int], Dict[str, int], Optional[int], Union[int, str]
    if isinstance(node, ast.Subscript):
        base_name = ""
        if isinstance(node.value, ast.Name):
            base_name = node.value.id
        elif isinstance(node.value, ast.Attribute):
            base_name = node.value.attr

        # Unpack slice elements
        slice_nodes: List[ast.AST] = []
        if isinstance(node.slice, ast.Tuple):
            slice_nodes = list(node.slice.elts)
        else:
            slice_nodes = [node.slice]

        parsed_args = tuple(parse_type_annotation(arg) for arg in slice_nodes)

        if base_name in ("list", "List"):
            elem = parsed_args[0] if parsed_args else UNKNOWN
            return make_list(elem)
        if base_name in ("tuple", "Tuple"):
            return make_tuple(*parsed_args)
        if base_name in ("set", "Set"):
            elem = parsed_args[0] if parsed_args else UNKNOWN
            return make_set(elem)
        if base_name in ("dict", "Dict"):
            k = parsed_args[0] if len(parsed_args) > 0 else UNKNOWN
            v = parsed_args[1] if len(parsed_args) > 1 else UNKNOWN
            return make_dict(k, v)
        if base_name in ("Optional", "optional"):
            elem = parsed_args[0] if parsed_args else UNKNOWN
            return make_optional(elem)
        if base_name in ("Union", "union"):
            return make_union(*parsed_args)

        return UNKNOWN

    # PEP 604 union syntax: T1 | T2
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left_t = parse_type_annotation(node.left)
        right_t = parse_type_annotation(node.right)
        return make_union(left_t, right_t)

    # Attribute: typing.List, typing.Optional
    if isinstance(node, ast.Attribute):
        attr_name = node.attr
        if attr_name == "Any":
            return ANY
        if attr_name in ("List", "list"):
            return make_list()
        if attr_name in ("Dict", "dict"):
            return make_dict()
        if attr_name in ("Tuple", "tuple"):
            return make_tuple()
        if attr_name in ("Set", "set"):
            return make_set()

    return UNKNOWN
