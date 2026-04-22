from __future__ import annotations

import time
from dataclasses import dataclass
from urllib.parse import parse_qsl, unquote, urlparse

import psycopg
from psycopg.rows import dict_row


def connect(database_url: str, *, autocommit: bool = False) -> psycopg.Connection:
    return psycopg.connect(database_url, autocommit=autocommit, row_factory=dict_row)


def wait_for_database(database_url: str, *, timeout: float = 60.0, interval: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            with connect(database_url):
                return
        except Exception as exc:  # pragma: no cover - depends on container state
            last_error = exc
            time.sleep(interval)

    message = f"Database did not become ready within {timeout:.0f}s"
    if last_error is not None:
        raise RuntimeError(message) from last_error
    raise RuntimeError(message)


@dataclass(frozen=True)
class PgConnectionParts:
    host: str | None
    port: int | None
    user: str | None
    password: str | None
    dbname: str
    query_params: dict[str, str]


def parse_postgres_url(database_url: str) -> PgConnectionParts:
    parsed = urlparse(database_url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ValueError("Only postgres:// and postgresql:// URLs are supported")

    database_name = parsed.path.lstrip("/")
    if not database_name:
        raise ValueError("Database URL must include a database name")

    return PgConnectionParts(
        host=parsed.hostname,
        port=parsed.port,
        user=unquote(parsed.username) if parsed.username else None,
        password=unquote(parsed.password) if parsed.password else None,
        dbname=unquote(database_name),
        query_params=dict(parse_qsl(parsed.query, keep_blank_values=True)),
    )


def build_ogr_connection_string(database_url: str) -> str:
    parts = parse_postgres_url(database_url)
    segments = [f"dbname={parts.dbname}"]

    if parts.host:
        segments.append(f"host={parts.host}")
    if parts.port:
        segments.append(f"port={parts.port}")
    if parts.user:
        segments.append(f"user={parts.user}")
    if parts.password:
        segments.append(f"password={parts.password}")

    for key in ("sslmode", "sslrootcert", "sslcert", "sslkey"):
        value = parts.query_params.get(key)
        if value:
            segments.append(f"{key}={value}")

    return "PG:" + " ".join(segments)