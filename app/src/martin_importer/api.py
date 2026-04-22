from __future__ import annotations

import shutil
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from .config import get_settings
from .db import wait_for_database
from .importer import ImportMode, ImporterError, import_dataset, list_tables, truncate_table


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    wait_for_database(settings.database_url, timeout=120)
    yield


app = FastAPI(
    title="Admin Martin Import API",
    version="0.1.0",
    lifespan=lifespan,
)


def persist_upload(upload: UploadFile) -> Path:
    filename = upload.filename or "upload.bin"
    suffix = Path(filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
        shutil.copyfileobj(upload.file, handle)
        temp_path = Path(handle.name)
    upload.file.close()
    return temp_path


def execute_import(
    *,
    table: str,
    mode: ImportMode,
    upload: UploadFile,
    source_layer: str | None,
) -> dict[str, object]:
    temp_path = persist_upload(upload)
    try:
        rows_loaded = import_dataset(settings.database_url, temp_path, table, mode, source_layer)
    except ImporterError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        temp_path.unlink(missing_ok=True)

    return {
        "table": table,
        "mode": mode.value,
        "filename": upload.filename,
        "rows_loaded": rows_loaded,
    }


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {
        "status": "ok",
        "database": settings.database_name,
    }


@app.get("/tables")
def tables() -> dict[str, object]:
    return {"tables": list_tables(settings.database_url)}


@app.post("/imports")
async def import_file(
    table: str = Form(...),
    mode: ImportMode = Form(ImportMode.REPLACE),
    source_layer: str | None = Form(None),
    file: UploadFile = File(...),
) -> dict[str, object]:
    return execute_import(table=table, mode=mode, upload=file, source_layer=source_layer)


@app.post("/tables/{table}/replace")
async def replace_table(
    table: str,
    file: UploadFile = File(...),
    source_layer: str | None = Form(None),
) -> dict[str, object]:
    return execute_import(table=table, mode=ImportMode.REPLACE, upload=file, source_layer=source_layer)


@app.post("/tables/{table}/append")
async def append_table(
    table: str,
    file: UploadFile = File(...),
    source_layer: str | None = Form(None),
) -> dict[str, object]:
    return execute_import(table=table, mode=ImportMode.APPEND, upload=file, source_layer=source_layer)


@app.post("/tables/{table}/truncate")
def truncate_table_endpoint(table: str) -> dict[str, str]:
    try:
        truncate_table(settings.database_url, table)
    except ImporterError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "table": table,
        "status": "truncated",
    }