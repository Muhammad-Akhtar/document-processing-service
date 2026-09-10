# Document processing API — WeasyPrint (Cairo/Pango) + PyMuPDF ready.
# Targets:
#   runtime (default) — uvicorn API
#   test              — pytest + ruff with native libs (Linux; no Windows skips)

FROM python:3.13-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STORAGE_ROOT=/storage

RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi8 \
    libglib2.0-0 \
    shared-mime-info \
    libharfbuzz0b \
    libharfbuzz-subset0 \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN mkdir -p /storage/uploads /storage/outputs /storage/previews

FROM base AS runtime

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS test

COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY tests ./tests
COPY pytest.ini ruff.toml ./

# Inside Docker/Linux, WeasyPrint native libs are present — do not skip those tests.
ENV WEASYPRINT_REQUIRED=1 \
    STORAGE_ROOT=/tmp/test-storage

CMD ["pytest", "-q"]
