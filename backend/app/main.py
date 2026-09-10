"""FastAPI application entrypoint (Phase 0 smoke app)."""

from fastapi import FastAPI

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
