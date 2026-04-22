from __future__ import annotations

import json
from pathlib import Path

import typer
from psycopg import sql

from .config import get_settings
from .db import connect, wait_for_database
from .importer import ImportMode, ImporterError, import_dataset, import_manifest, list_tables, truncate_table
from .sql import iter_sql_files


app = typer.Typer(no_args_is_help=True, pretty_exceptions_show_locals=False)
db_app = typer.Typer(no_args_is_help=True)
data_app = typer.Typer(no_args_is_help=True)
app.add_typer(db_app, name="db")
app.add_typer(data_app, name="data")


def run_migrations(*, wait_timeout: int = 60) -> list[str]:
    settings = get_settings()
    wait_for_database(settings.database_url, timeout=wait_timeout)

    executed_files: list[str] = []
    with connect(settings.database_url) as conn:
        for sql_file in iter_sql_files(settings.sql_dir):
            conn.execute(sql_file.read_text(encoding="utf-8"))
            executed_files.append(str(sql_file))
        conn.commit()

    return executed_files


@db_app.command("migrate")
def migrate_command(wait_timeout: int = typer.Option(60, min=1)) -> None:
    executed_files = run_migrations(wait_timeout=wait_timeout)
    typer.echo(json.dumps({"applied": executed_files}, indent=2))


@data_app.command("import-file")
def import_file_command(
    source: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    table: str = typer.Option(..., "--table", prompt=False),
    mode: ImportMode = typer.Option(ImportMode.REPLACE, case_sensitive=False),
    source_layer: str | None = typer.Option(None),
) -> None:
    settings = get_settings()
    try:
        rows_loaded = import_dataset(settings.database_url, source, table, mode, source_layer)
    except ImporterError as exc:
        raise typer.BadParameter(str(exc)) from exc

    typer.echo(
        json.dumps(
            {
                "table": table,
                "source": str(source.resolve()),
                "mode": mode.value,
                "rows_loaded": rows_loaded,
            },
            indent=2,
        )
    )


@data_app.command("import-manifest")
def import_manifest_command(
    manifest: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
) -> None:
    settings = get_settings()
    typer.echo(json.dumps(import_manifest(settings.database_url, manifest), indent=2))


@data_app.command("truncate-table")
def truncate_table_command(table: str = typer.Argument(...)) -> None:
    settings = get_settings()
    truncate_table(settings.database_url, table)
    typer.echo(json.dumps({"table": table, "status": "truncated"}, indent=2))


@data_app.command("list-tables")
def list_tables_command() -> None:
    settings = get_settings()
    typer.echo(json.dumps(list_tables(settings.database_url), indent=2))