"""Schemas for multi-language registry, capabilities, and tool status."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class LanguageSupportLevel(str, Enum):
    """Categorization of analysis support level for a programming language."""

    SUPPORTED = "supported"          # Full semantic type analysis available
    PARTIAL = "partial"              # Syntax checking or partial static typing
    TOOL_UNAVAILABLE = "tool_unavailable"  # Compiler/toolchain required but not found on system PATH


class LanguageInfo(BaseModel):
    """Metadata describing a supported programming language, its toolchain, and status."""

    id: str = Field(..., description="Canonical identifier (e.g. 'python', 'typescript', 'java')")
    name: str = Field(..., description="Human-readable display name (e.g. 'Python', 'TypeScript')")
    extensions: List[str] = Field(..., description="Supported file extensions (e.g. ['.ts', '.tsx'])")
    support_level: LanguageSupportLevel = Field(..., description="Current support level")
    tool_name: str = Field(..., description="Name of the underlying parser/compiler/analyzer tool")
    tool_available: bool = Field(..., description="Whether the required tool is installed and executable")
    ml_supported: bool = Field(default=False, description="Whether ML-assisted classification is supported")
    description: str = Field(..., description="Summary of analysis capabilities for this language")
    setup_instructions: Optional[str] = Field(
        default=None,
        description="Installation and configuration instructions if the tool is unavailable"
    )

    model_config = ConfigDict(frozen=True)


class LanguagesResponse(BaseModel):
    """Response returned by the /api/v1/languages capabilities endpoint."""

    languages: List[LanguageInfo] = Field(..., description="List of configured languages and their capabilities")
    total: int = Field(..., ge=0, description="Total number of registered languages")
    default_language: str = Field(default="python", description="Default language identifier")

    model_config = ConfigDict(frozen=True)
