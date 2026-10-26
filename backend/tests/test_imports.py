"""Test that all packages and modules import cleanly without starting a server or network calls."""

import importlib
import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "app",
        "app.main",
        "app.core",
        "app.core.config",
        "app.core.logging",
        "app.core.errors",
        "app.api",
        "app.api.v1",
        "app.api.v1.router",
        "app.api.v1.endpoints.health",
        "app.api.v1.endpoints.info",
        "app.api.v1.endpoints.analyze",
        "app.api.v1.endpoints.categories",
        "app.api.v1.endpoints.model",
        "app.schemas",
        "app.schemas.common",
        "app.schemas.fixes",
        "app.schemas.ml",
        "app.schemas.diagnostics",
        "app.schemas.analysis",
        "app.models",
        "app.services",
        "app.services.analysis",
        "app.services.diagnostics",
        "app.services.model",
        "app.semantic",
        "app.semantic.types",
        "app.semantic.symbol_table",
        "app.semantic.inference",
        "app.semantic.rules",
        "app.semantic.rules.binary_ops",
        "app.semantic.rules.calls",
        "app.semantic.rules.returns",
        "app.semantic.rules.assignments",
        "app.semantic.analyzer",
        "app.ml",
        "app.ml.features",
        "app.ml.predictor",
        "app.ml.train",
        "app.diagnostics",
        "app.diagnostics.aggregator",
        "app.diagnostics.explainer",
        "app.diagnostics.fix_generator",
        "app.diagnostics.service",
        "app.utils",
    ],
)
def test_module_imports_without_side_effects(module_name: str):
    """Verify each module can be imported cleanly without requiring a running server."""
    mod = importlib.import_module(module_name)
    assert mod is not None
