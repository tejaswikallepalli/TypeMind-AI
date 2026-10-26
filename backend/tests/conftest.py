"""Pytest configuration and shared test fixtures."""

import sys
from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
backend_path = Path(__file__).resolve().parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.main import create_app


@pytest.fixture(scope="session")
def app():
    """Create and return a test FastAPI instance."""
    return create_app()


@pytest.fixture(scope="session")
def client(app) -> Generator[TestClient, None, None]:
    """Provide a TestClient instance for synchronous endpoint testing without network access."""
    with TestClient(app) as test_client:
        yield test_client
