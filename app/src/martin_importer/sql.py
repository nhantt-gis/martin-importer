from __future__ import annotations

from pathlib import Path


def iter_sql_files(sql_dir: Path) -> list[Path]:
    schema_file = sql_dir / "schema.sql"
    function_files = sorted((sql_dir / "functions").glob("*.sql"))
    return [schema_file, *function_files]