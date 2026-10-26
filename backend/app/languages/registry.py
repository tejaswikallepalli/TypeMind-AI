"""Central registry managing language adapters, file extension routing, and tool availability."""

from __future__ import annotations
import logging
import os
from typing import Dict, List, Optional

from app.languages.base import BaseLanguageAdapter
from app.languages.c_cpp import CLanguageAdapter, CppLanguageAdapter
from app.languages.csharp import CSharpLanguageAdapter
from app.languages.go import GoLanguageAdapter
from app.languages.java import JavaLanguageAdapter
from app.languages.javascript import JavaScriptLanguageAdapter
from app.languages.php import PhpLanguageAdapter
from app.languages.python import PythonLanguageAdapter
from app.languages.ruby import RubyLanguageAdapter
from app.languages.rust import RustLanguageAdapter
from app.languages.typescript import TypeScriptLanguageAdapter
from app.schemas.languages import LanguageInfo, LanguagesResponse

logger = logging.getLogger("typemind.languages.registry")


class LanguageRegistry:
    """Central registry and dispatch hub for all supported programming language adapters."""

    def __init__(self) -> None:
        self._adapters: Dict[str, BaseLanguageAdapter] = {}
        self._extension_map: Dict[str, str] = {}
        self._register_default_adapters()

    def _register_default_adapters(self) -> None:
        """Register the built-in language adapters."""
        defaults: List[BaseLanguageAdapter] = [
            PythonLanguageAdapter(),
            TypeScriptLanguageAdapter(),
            JavaScriptLanguageAdapter(),
            JavaLanguageAdapter(),
            CLanguageAdapter(),
            CppLanguageAdapter(),
            CSharpLanguageAdapter(),
            GoLanguageAdapter(),
            RustLanguageAdapter(),
            PhpLanguageAdapter(),
            RubyLanguageAdapter(),
        ]
        for adapter in defaults:
            self.register(adapter)

    def register(self, adapter: BaseLanguageAdapter) -> None:
        """Register a new language adapter and index its supported file extensions."""
        lang_id = adapter.language_id.lower()
        self._adapters[lang_id] = adapter
        for ext in adapter.extensions:
            self._extension_map[ext.lower()] = lang_id
        logger.debug("Registered adapter '%s' for extensions: %s", lang_id, adapter.extensions)

    def get_adapter(self, language_id: str) -> Optional[BaseLanguageAdapter]:
        """Look up adapter by canonical language identifier."""
        return self._adapters.get(language_id.lower())

    def detect_language_from_path(self, file_path: str) -> Optional[str]:
        """Detect language identifier from a file's extension."""
        if not file_path:
            return None
        _, ext = os.path.splitext(file_path.strip())
        if not ext:
            return None
        return self._extension_map.get(ext.lower())

    def is_language_supported(self, language_id: str) -> bool:
        """Check if language identifier exists in the registry."""
        return language_id.lower() in self._adapters

    def list_languages(self) -> List[LanguageInfo]:
        """Return standardized capability descriptions for all registered languages."""
        return [adapter.get_info() for adapter in self._adapters.values()]

    def get_languages_response(self) -> LanguagesResponse:
        """Return full LanguagesResponse object for API capabilities endpoint."""
        langs = self.list_languages()
        return LanguagesResponse(
            languages=langs,
            total=len(langs),
            default_language="python",
        )


# Global singleton registry instance
_language_registry = LanguageRegistry()


def get_language_registry() -> LanguageRegistry:
    """Return the global LanguageRegistry instance."""
    return _language_registry
