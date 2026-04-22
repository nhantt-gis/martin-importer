FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        gdal-bin \
        libgdal-dev \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY app /workspace/app
COPY sql /workspace/sql

RUN uv sync --project /workspace/app --no-dev

ENV PATH="/workspace/app/.venv/bin:${PATH}" \
    PYTHONPATH="/workspace/app/src"

CMD ["uv", "run", "--project", "/workspace/app", "uvicorn", "martin_importer.api:app", "--host", "0.0.0.0", "--port", "8000"]
