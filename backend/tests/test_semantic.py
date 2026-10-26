"""Comprehensive test suite for the TypeMind AI AST-based semantic analyzer."""

import pytest
from app.schemas.common import ErrorCategory, FindingOrigin, Severity
from app.semantic.analyzer import SemanticAnalyzer
from app.semantic.symbol_table import SymbolTable
from app.semantic.types import (
    BOOL,
    FLOAT,
    INT,
    NONE,
    STR,
    UNKNOWN,
    make_dict,
    make_list,
    make_tuple,
    make_union,
    parse_type_annotation,
)


@pytest.fixture
def analyzer() -> SemanticAnalyzer:
    return SemanticAnalyzer()


# =====================================================================
# 1. Type System and Annotation Parsing Tests
# =====================================================================

class TestTypeSystem:
    def test_primitive_compatibility(self):
        assert INT.is_compatible_with(INT)
        assert INT.is_compatible_with(FLOAT)  # Int widens to float
        assert not FLOAT.is_compatible_with(INT)  # Float does not narrow to int
        assert not STR.is_compatible_with(INT)
        assert not NONE.is_compatible_with(INT)

    def test_unknown_and_any_are_conservatively_compatible(self):
        assert UNKNOWN.is_compatible_with(INT)
        assert INT.is_compatible_with(UNKNOWN)
        assert UNKNOWN.is_compatible_with(UNKNOWN)

    def test_union_compatibility(self):
        union_int_str = make_union(INT, STR)
        assert INT.is_compatible_with(union_int_str)
        assert STR.is_compatible_with(union_int_str)
        assert not FLOAT.is_compatible_with(union_int_str)

    def test_pep604_and_generic_annotation_parsing(self):
        import ast
        tree = ast.parse("x: int | str = 1\ny: list[float] = [1.0]\nz: dict[str, int] = {'a': 1}")
        ann1 = tree.body[0].annotation  # int | str
        ann2 = tree.body[1].annotation  # list[float]
        ann3 = tree.body[2].annotation  # dict[str, int]

        t1 = parse_type_annotation(ann1)
        t2 = parse_type_annotation(ann2)
        t3 = parse_type_annotation(ann3)

        assert t1.kind.value == "union"
        assert t2.name == "list"
        assert t2.args[0] == FLOAT
        assert t3.name == "dict"
        assert t3.args[0] == STR
        assert t3.args[1] == INT


# =====================================================================
# 2. Syntax Error Handling
# =====================================================================

class TestSyntaxErrors:
    def test_syntax_error_reported_separately(self, analyzer):
        code = "def broken_func(\n    x = 10"  # unclosed parenthesis
        result = analyzer.analyze(code, file_path="broken.py")

        assert result.status == "syntax_error"
        assert result.syntax_error is not None
        assert result.syntax_error.category == ErrorCategory.SYNTAX_ERROR
        assert result.syntax_error.severity == Severity.ERROR
        assert result.syntax_error.rule_id == "TM000_SYNTAX_ERROR"
        assert result.syntax_error.location.file_path == "broken.py"
        assert result.syntax_error.location.line >= 1
        assert result.syntax_error.location.column >= 1
        assert len(result.findings) == 0  # Semantic findings empty when syntax invalid
        assert result.summary.syntax_errors_count == 1


# =====================================================================
# 3. Binary Operations & String-Number Concatenation
# =====================================================================

class TestBinaryOperations:
    def test_string_number_concatenation_detected(self, analyzer):
        code = 'msg = "Count: " + 42\n'
        result = analyzer.analyze(code)

        assert result.status == "success"
        assert len(result.findings) == 1
        f = result.findings[0]
        assert f.rule_id == "TM001_STRING_NUMBER_CONCAT"
        assert f.category == ErrorCategory.TYPE_MISMATCH
        assert f.severity == Severity.ERROR
        assert "Cannot concatenate 'str' and 'int'" in f.message
        assert f.location.line == 1
        assert len(f.suggested_fixes) == 1
        assert "str(42)" in f.suggested_fixes[0].replacements[0].new_text

    def test_number_string_concatenation_detected(self, analyzer):
        code = 'val = 10.5 + " units"\n'
        result = analyzer.analyze(code)

        assert len(result.findings) == 1
        assert result.findings[0].rule_id == "TM001_STRING_NUMBER_CONCAT"

    def test_unsupported_subtraction_on_strings(self, analyzer):
        code = 'res = "hello" - "world"\n'
        result = analyzer.analyze(code)

        assert len(result.findings) == 1
        f = result.findings[0]
        assert f.rule_id == "TM002_UNSUPPORTED_ARITHMETIC"
        assert f.category == ErrorCategory.UNSUPPORTED_OPERAND
        assert "Unsupported operand types for -" in f.message

    def test_none_arithmetic_detected(self, analyzer):
        code = "res = None + 5\n"
        result = analyzer.analyze(code)

        assert len(result.findings) == 1
        assert result.findings[0].rule_id == "TM002_UNSUPPORTED_ARITHMETIC"

    def test_collection_arithmetic_mismatches(self, analyzer):
        code = """
a = [1, 2] + (3, 4)
b = [1, 2] - [1]
c = {"a": 1} + {"b": 2}
"""
        result = analyzer.analyze(code)
        assert len(result.findings) == 3
        for f in result.findings:
            assert f.rule_id == "TM002_UNSUPPORTED_ARITHMETIC"

    def test_valid_binary_operations_produce_no_errors(self, analyzer):
        code = """
num = 10 + 20
flt = 10 + 3.14
text = "hello " + "world"
rep_str = "abc" * 3
seq = [1, 2] + [3, 4]
tup = (1,) + (2,)
diff = 100 - 50
prod = 5 * 5
div = 10 / 2
fdiv = 10 // 3
"""
        result = analyzer.analyze(code)
        assert result.status == "success"
        assert len(result.findings) == 0


# =====================================================================
# 4. Function Call Arguments & Signatures
# =====================================================================

class TestFunctionCalls:
    def test_too_few_arguments(self, analyzer):
        code = """
def calculate(a: int, b: int) -> int:
    return a + b

res = calculate(10)
"""
        result = analyzer.analyze(code)
        assert len(result.findings) == 1
        f = result.findings[0]
        assert f.rule_id == "TM003_ARGUMENT_COUNT_MISMATCH"
        assert "expects at least 2 arguments" in f.message

    def test_too_many_arguments(self, analyzer):
        code = """
def greet(name: str) -> str:
    return "Hello " + name

res = greet("Alice", 123)
"""
        result = analyzer.analyze(code)
        assert len(result.findings) == 1
        assert result.findings[0].rule_id == "TM003_ARGUMENT_COUNT_MISMATCH"
        assert "takes 1 positional arguments, but 2 were given" in result.findings[0].message

    def test_default_arguments_respected(self, analyzer):
        code = """
def power(base: int, exp: int = 2) -> int:
    return base ** exp

res1 = power(5)
res2 = power(5, 3)
"""
        result = analyzer.analyze(code)
        assert len(result.findings) == 0

    def test_annotated_argument_type_mismatch(self, analyzer):
        code = """
def double_number(x: int) -> int:
    return x * 2

val = double_number("hello")
"""
        result = analyzer.analyze(code)
        assert len(result.findings) == 1
        f = result.findings[0]
        assert f.rule_id == "TM004_ARGUMENT_TYPE_MISMATCH"
        assert f.category == ErrorCategory.ARGUMENT_TYPE_MISMATCH
        assert f.expected_type.raw_type == "int"
        assert f.observed_type.raw_type == "str"


# =====================================================================
# 5. Return Statement Type Compatibility
# =====================================================================

class TestReturnTypes:
    def test_incompatible_return_type_detected(self, analyzer):
        code = """
def calculate_price(discount: float) -> float:
    if discount < 0:
        return "invalid discount"
    return 100.0 * (1.0 - discount)
"""
        result = analyzer.analyze(code)
        assert len(result.findings) == 1
        f = result.findings[0]
        assert f.rule_id == "TM005_INCOMPATIBLE_RETURN"
        assert f.expected_type.raw_type == "float"
        assert f.observed_type.raw_type == "str"

    def test_numeric_widening_return_is_valid(self, analyzer):
        code = """
def get_ratio() -> float:
    return 10  # int is valid float
"""
        result = analyzer.analyze(code)
        assert len(result.findings) == 0


# =====================================================================
# 6. Assignment and Reassignment Inconsistencies
# =====================================================================

class TestAssignments:
    def test_annotated_assignment_mismatch(self, analyzer):
        code = 'user_id: int = "12345"\n'
        result = analyzer.analyze(code)

        assert len(result.findings) == 1
        f = result.findings[0]
        assert f.rule_id == "TM006_INVALID_ANNOTATED_ASSIGNMENT"
        assert f.expected_type.raw_type == "int"
        assert f.observed_type.raw_type == "str"

    def test_reassignment_to_annotated_variable_mismatch(self, analyzer):
        code = """
x: int = 10
x = "incompatible string"
"""
        result = analyzer.analyze(code)
        assert len(result.findings) == 1
        f = result.findings[0]
        assert f.rule_id == "TM006_INVALID_ANNOTATED_ASSIGNMENT"

    def test_incompatible_unannotated_reassignment_warning(self, analyzer):
        code = """
count = 10
count = "ten"
"""
        result = analyzer.analyze(code)
        assert len(result.findings) == 1
        f = result.findings[0]
        assert f.rule_id == "TM007_INCOMPATIBLE_REASSIGNMENT"
        assert f.severity == Severity.WARNING


# =====================================================================
# 7. Nested Scopes and Conservative Typing (No False Positives)
# =====================================================================

class TestScopesAndConservativeTyping:
    def test_nested_functions_isolated_scopes(self, analyzer):
        code = """
def outer() -> int:
    x: int = 10
    def inner() -> str:
        x: str = "nested string"
        return x
    return x
"""
        result = analyzer.analyze(code)
        assert len(result.findings) == 0  # Scopes are isolated, no collision

    def test_unannotated_parameters_produce_no_false_positives(self, analyzer):
        code = """
def process(data):
    # 'data' has unknown type, must NOT report false positive
    return data + 10
"""
        result = analyzer.analyze(code)
        assert len(result.findings) == 0

    def test_unknown_function_call_produces_no_false_positives(self, analyzer):
        code = """
import random
val = random.choice([1, 2, 3])
res = val + 5
"""
        result = analyzer.analyze(code)
        assert len(result.findings) == 0
