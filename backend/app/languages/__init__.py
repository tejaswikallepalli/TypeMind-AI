"""Multi-language semantic analysis package for TypeMind AI."""

from app.languages.base import BaseLanguageAdapter
from app.languages.registry import LanguageRegistry, get_language_registry

__all__ = [
    "BaseLanguageAdapter",
    "LanguageRegistry",
    "get_language_registry",
]
