"""TDD: local storage service."""

from uuid import uuid4

import pytest

from app.core.config import Settings
from app.core.exceptions import NotFoundAppError, StorageAppError
from app.storage.local import LocalStorage


@pytest.fixture
def storage(tmp_path) -> LocalStorage:
    root = tmp_path / "storage"
    (root / "uploads").mkdir(parents=True)
    settings = Settings(storage_root=root, _env_file=None)  # type: ignore[call-arg]
    return LocalStorage(settings)


def test_save_upload_writes_file_and_metadata(storage: LocalStorage) -> None:
    meta = storage.save_upload(
        filename="hello.html",
        content_type="text/html",
        data=b"<html>hi</html>",
    )
    assert meta.original_filename == "hello.html"
    assert meta.size == len(b"<html>hi</html>")
    assert storage.exists(meta.id)
    path = storage.get_path(meta.id)
    assert path.read_bytes() == b"<html>hi</html>"
    loaded = storage.get_meta(meta.id)
    assert loaded.id == meta.id
    assert loaded.content_type == "text/html"


def test_get_missing_raises(storage: LocalStorage) -> None:
    missing = uuid4()
    with pytest.raises(NotFoundAppError):
        storage.get_meta(missing)
    with pytest.raises(NotFoundAppError):
        storage.get_path(missing)


def test_delete_removes_document(storage: LocalStorage) -> None:
    meta = storage.save_upload(
        filename="gone.html",
        content_type="text/html",
        data=b"<html>x</html>",
    )
    storage.delete(meta.id)
    assert storage.exists(meta.id) is False
    with pytest.raises(NotFoundAppError):
        storage.get_meta(meta.id)


def test_rejects_path_escape_via_document_id(storage: LocalStorage, tmp_path) -> None:
    # Document IDs are UUIDs; non-UUID / traversal must not escape storage root.
    with pytest.raises((NotFoundAppError, StorageAppError, ValueError)):
        storage.get_path("../../../etc/passwd")  # type: ignore[arg-type]
