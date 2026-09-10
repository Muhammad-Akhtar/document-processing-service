"""Application-level errors mapped to HTTP responses."""

from typing import Any


class AppError(Exception):
    """Base application error."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "app_error",
        status_code: int = 400,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class ValidationAppError(AppError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "validation_error",
        status_code: int = 400,
        details: Any = None,
    ) -> None:
        super().__init__(
            message, code=code, status_code=status_code, details=details
        )


class NotFoundAppError(AppError):
    def __init__(self, message: str = "Resource not found", *, details: Any = None) -> None:
        super().__init__(
            message, code="not_found", status_code=404, details=details
        )


class StorageAppError(AppError):
    def __init__(self, message: str, *, details: Any = None) -> None:
        super().__init__(
            message, code="storage_error", status_code=400, details=details
        )
