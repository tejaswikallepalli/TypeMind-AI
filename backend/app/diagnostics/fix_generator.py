"""Automated fix generator providing safe, structured code repair suggestions."""

from __future__ import annotations
import uuid
from typing import List, Optional
from app.schemas.common import SourceLocation, TypeInfo
from app.schemas.fixes import CodeReplacement, SuggestedFix


class FixGenerator:
    """Generates structured fix recommendations and diff previews for recognized patterns."""

    def generate_fixes(
        self,
        rule_id: Optional[str],
        location: SourceLocation,
        source_code: str,
        expected_type: Optional[TypeInfo] = None,
        observed_type: Optional[TypeInfo] = None,
        context: Optional[dict] = None,
    ) -> List[SuggestedFix]:
        """Generate candidate fixes for a diagnostic finding.

        Fixes require developer review before applying and do not automatically mutate code.
        """
        fixes: List[SuggestedFix] = []
        if not rule_id:
            return fixes

        # 1. String-Number Concatenation Fixes
        if rule_id == "TM001_STRING_NUMBER_CONCAT":
            snippet = self._extract_snippet(source_code, location)
            fix_id = f"fix-concat-{uuid.uuid4().hex[:8]}"

            # Fix Option A: Explicit str() cast
            wrap_text = f"str({snippet})" if snippet else "str(value)"
            fixes.append(
                SuggestedFix(
                    id=fix_id,
                    title="Explicitly convert operand with str()",
                    description=(
                        "Convert non-string operand to string using str(). "
                        "Python requires explicit string conversion for concatenation."
                    ),
                    replacements=[
                        CodeReplacement(
                            location=location,
                            new_text=wrap_text,
                            description=f"Wrap expression with str()",
                        )
                    ],
                    diff_preview=f"- {snippet}\n+ {wrap_text}" if snippet else None,
                    confidence=0.98,
                    is_auto_applicable=False,
                    requires_user_review=True,
                )
            )

        # 2. Incompatible Return Type Fixes
        elif rule_id == "TM005_INCOMPATIBLE_RETURN":
            snippet = self._extract_snippet(source_code, location)
            exp_t = expected_type.raw_type if expected_type else "Any"
            obs_t = observed_type.raw_type if observed_type else "Any"

            # Suggestion: Cast expression if numeric conversion is valid
            if exp_t in ("float", "int") and obs_t in ("int", "float", "str"):
                cast_text = f"{exp_t}({snippet})"
                fixes.append(
                    SuggestedFix(
                        id=f"fix-return-cast-{uuid.uuid4().hex[:8]}",
                        title=f"Cast return expression to {exp_t}",
                        description=f"Cast returned value to match declared return annotation '{exp_t}'.",
                        replacements=[
                            CodeReplacement(
                                location=location,
                                new_text=cast_text,
                                description=f"Cast value to {exp_t}",
                            )
                        ],
                        diff_preview=f"- {snippet}\n+ {cast_text}" if snippet else None,
                        confidence=0.85,
                        is_auto_applicable=False,
                        requires_user_review=True,
                    )
                )

        # 3. Invalid Annotated Assignment Fixes
        elif rule_id == "TM006_INVALID_ANNOTATED_ASSIGNMENT":
            exp_t = expected_type.raw_type if expected_type else "Any"
            obs_t = observed_type.raw_type if observed_type else "Any"
            fixes.append(
                SuggestedFix(
                    id=f"fix-ann-update-{uuid.uuid4().hex[:8]}",
                    title=f"Update type annotation to {obs_t} or Union",
                    description=(
                        f"Align the variable annotation with assigned expression type '{obs_t}' "
                        f"or use Union[{exp_t}, {obs_t}] if multiple types are intended."
                    ),
                    replacements=[],
                    confidence=0.90,
                    is_auto_applicable=False,
                    requires_user_review=True,
                )
            )

        return fixes

    def _extract_snippet(self, source_code: str, loc: SourceLocation) -> str:
        """Extract the exact substring of code at the given SourceLocation."""
        lines = source_code.splitlines()
        if loc.line > len(lines):
            return ""

        target_line = lines[loc.line - 1]
        start_col = max(0, loc.column - 1)
        end_col = loc.end_column if loc.end_column is not None else len(target_line)

        # Handle multi-line spans safely
        if loc.end_line and loc.end_line > loc.line:
            return target_line[start_col:].strip()

        return target_line[start_col:end_col].strip()
