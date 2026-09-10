"""Unit tests for application settings."""

from pathlib import Path

from app.core.config import Settings


def test_settings_defaults() -> None:
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
    )
    assert settings.app_name == "document-processing-service"
    assert settings.max_upload_bytes == 10 * 1024 * 1024
    assert settings.uploads_dir == settings.storage_root / "uploads"
    assert settings.outputs_dir == settings.storage_root / "outputs"
    assert settings.previews_dir == settings.storage_root / "previews"


def test_cors_origin_list_parses_csv() -> None:
    settings = Settings(
        cors_origins="http://a.example, http://b.example",
        _env_file=None,  # type: ignore[call-arg]
    )
    assert settings.cors_origin_list == [
        "http://a.example",
        "http://b.example",
    ]


def test_storage_root_accepts_path(tmp_path: Path) -> None:
    settings = Settings(
        storage_root=tmp_path,
        _env_file=None,  # type: ignore[call-arg]
    )
    assert settings.storage_root == tmp_path
    assert settings.uploads_dir == tmp_path / "uploads"
