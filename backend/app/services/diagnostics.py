"""Diagnostic category catalog and service."""

from typing import List
from app.schemas.common import ErrorCategory, Severity
from app.schemas.diagnostics import CategoriesResponse, CategoryDetail


CATEGORY_CATALOG: List[CategoryDetail] = [
    CategoryDetail(
        code=ErrorCategory.TYPE_MISMATCH.value,
        title="Type Mismatch",
        description="Incompatible types used in an expression, such as string-number concatenation or invalid operations.",
        default_severity=Severity.ERROR,
        rule_ids=["TM001_STRING_NUMBER_CONCAT"],
        fix_support=True,
    ),
    CategoryDetail(
        code=ErrorCategory.UNSUPPORTED_OPERAND.value,
        title="Unsupported Operand",
        description="Binary or arithmetic operator applied to operands of unsupported or incompatible types.",
        default_severity=Severity.ERROR,
        rule_ids=["TM002_UNSUPPORTED_ARITHMETIC"],
        fix_support=False,
    ),
    CategoryDetail(
        code=ErrorCategory.ARGUMENT_COUNT_MISMATCH.value,
        title="Argument Count Mismatch",
        description="Function called with fewer or more positional arguments than accepted by its signature.",
        default_severity=Severity.ERROR,
        rule_ids=["TM003_ARGUMENT_COUNT_MISMATCH"],
        fix_support=False,
    ),
    CategoryDetail(
        code=ErrorCategory.ARGUMENT_TYPE_MISMATCH.value,
        title="Argument Type Mismatch",
        description="Argument passed to a function call does not conform to the declared parameter type annotation.",
        default_severity=Severity.ERROR,
        rule_ids=["TM004_ARGUMENT_TYPE_MISMATCH"],
        fix_support=False,
    ),
    CategoryDetail(
        code=ErrorCategory.INCOMPATIBLE_RETURN.value,
        title="Incompatible Return Type",
        description="Expression returned by a function is incompatible with its declared return type annotation.",
        default_severity=Severity.ERROR,
        rule_ids=["TM005_INCOMPATIBLE_RETURN"],
        fix_support=True,
    ),
    CategoryDetail(
        code=ErrorCategory.INVALID_ASSIGNMENT.value,
        title="Invalid Assignment",
        description="Variable assigned a value incompatible with its declared type annotation or reassigned an inconsistent type.",
        default_severity=Severity.ERROR,
        rule_ids=["TM006_INVALID_ANNOTATED_ASSIGNMENT", "TM007_INCOMPATIBLE_REASSIGNMENT"],
        fix_support=True,
    ),
    CategoryDetail(
        code=ErrorCategory.SYNTAX_ERROR.value,
        title="Syntax Error",
        description="Source code fails Python AST grammar parsing, preventing further semantic analysis.",
        default_severity=Severity.ERROR,
        rule_ids=["TM000_SYNTAX_ERROR"],
        fix_support=False,
    ),
    CategoryDetail(
        code=ErrorCategory.NONE_SAFETY.value,
        title="None Safety",
        description="Potential NoneType dereference, arithmetic, or attribute access without prior guard checks.",
        default_severity=Severity.WARNING,
        rule_ids=[],
        fix_support=False,
    ),
    CategoryDetail(
        code=ErrorCategory.ATTRIBUTE_NOT_FOUND.value,
        title="Attribute Not Found",
        description="Accessing an attribute or method not defined on the statically inferred receiver type.",
        default_severity=Severity.ERROR,
        rule_ids=[],
        fix_support=False,
    ),
    CategoryDetail(
        code=ErrorCategory.UNDEFINED_NAME.value,
        title="Undefined Name",
        description="Reference to a variable, function, or symbol that has not been defined in any reachable scope.",
        default_severity=Severity.ERROR,
        rule_ids=[],
        fix_support=False,
    ),
]


class CategoryService:
    """Service providing catalog of recognized diagnostic categories."""

    def __init__(self, catalog: List[CategoryDetail] = CATEGORY_CATALOG) -> None:
        self._catalog = catalog

    def get_categories(self) -> CategoriesResponse:
        """Return all supported diagnostic categories and total count."""
        return CategoriesResponse(
            categories=self._catalog,
            total_categories=len(self._catalog),
        )


_category_service = CategoryService()


def get_category_service() -> CategoryService:
    """Dependency provider returning singleton CategoryService."""
    return _category_service
