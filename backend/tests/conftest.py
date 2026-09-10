"""Shared pytest fixtures for Phase 1+."""

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import create_app


@pytest.fixture
def storage_root(tmp_path: Path) -> Path:
    root = tmp_path / "storage"
    (root / "uploads").mkdir(parents=True)
    (root / "outputs").mkdir(parents=True)
    (root / "previews").mkdir(parents=True)
    return root


@pytest.fixture
def test_settings(storage_root: Path) -> Settings:
    return Settings(
        storage_root=storage_root,
        max_upload_bytes=256 * 1024,
        debug=True,
        cors_origins="http://testclient.local",
        _env_file=None,  # type: ignore[call-arg]
    )


@pytest.fixture
def client(test_settings: Settings) -> Generator[TestClient, None, None]:
    get_settings.cache_clear()

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    get_settings.cache_clear()
