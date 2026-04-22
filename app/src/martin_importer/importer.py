from __future__ import annotations

import re
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml
from psycopg import sql

from .db import build_ogr_connection_string, connect


class ImporterError(RuntimeError):
    pass


class ImportMode(StrEnum):
    APPEND = "append"
    REPLACE = "replace"


@dataclass(frozen=True)
class TargetTableMetadata:
    name: str
    columns: list[str]
    column_types: dict[str, str]
    geometry_column: str
    geometry_type: str
    srid: int


GEOMETRY_DIMENSIONS = {
    "MULTIPOINT": 1,
    "MULTILINESTRING": 2,
    "MULTIPOLYGON": 3,
}

OGR_GEOMETRY_TYPES = {
    "MULTIPOINT": "MULTIPOINT",
    "MULTILINESTRING": "MULTILINESTRING",
    "MULTIPOLYGON": "MULTIPOLYGON",
}


def validate_table_name(table_name: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table_name):
        raise ImporterError(f"Invalid table name: {table_name}")
    return table_name.lower()


def run_command(command: list[str]) -> str:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        details = completed.stderr.strip() or completed.stdout.strip() or "Unknown command failure"
        raise ImporterError(details)
    return completed.stdout


def list_tables(database_url: str) -> list[dict[str, Any]]:
    query = """
        SELECT
            tables.table_name,
            geometry_columns.type AS geometry_type,
            geometry_columns.srid
        FROM information_schema.tables AS tables
        LEFT JOIN geometry_columns
            ON geometry_columns.f_table_schema = tables.table_schema
           AND geometry_columns.f_table_name = tables.table_name
        WHERE tables.table_schema = 'public'
          AND tables.table_type = 'BASE TABLE'
        ORDER BY tables.table_name
    """

    with connect(database_url) as conn:
        return [dict(row) for row in conn.execute(query).fetchall()]


def get_target_table_metadata(database_url: str, table_name: str) -> TargetTableMetadata:
    table_name = validate_table_name(table_name)
    columns_query = """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
    """
    geometry_query = """
        SELECT f_geometry_column AS geometry_column, type AS geometry_type, srid
        FROM geometry_columns
        WHERE f_table_schema = 'public' AND f_table_name = %s
    """

    with connect(database_url) as conn:
        column_rows = conn.execute(columns_query, (table_name,)).fetchall()
        columns = [row["column_name"] for row in column_rows]
        if not columns:
            raise ImporterError(f"Table public.{table_name} does not exist")

        geometry = conn.execute(geometry_query, (table_name,)).fetchone()
        if geometry is None:
            raise ImporterError(f"Table public.{table_name} does not have a PostGIS geometry column")

    geometry_type = geometry["geometry_type"].upper()
    if geometry_type not in GEOMETRY_DIMENSIONS:
        raise ImporterError(
            f"Table public.{table_name} uses unsupported geometry type {geometry_type}. "
            "Supported types: MULTIPOINT, MULTILINESTRING, MULTIPOLYGON."
        )

    return TargetTableMetadata(
        name=table_name,
        columns=columns,
        column_types={row["column_name"]: row["data_type"] for row in column_rows},
        geometry_column=geometry["geometry_column"],
        geometry_type=geometry_type,
        srid=int(geometry["srid"]),
    )


def get_table_columns(database_url: str, table_name: str) -> list[str]:
    query = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
    """

    with connect(database_url) as conn:
        return [row["column_name"] for row in conn.execute(query, (table_name,)).fetchall()]


def list_layers(dataset_path: Path) -> list[str]:
    output = run_command(["ogrinfo", "-ro", "-so", str(dataset_path)])
    return re.findall(r"^\s*\d+:\s+(.*?)\s+\(", output, flags=re.MULTILINE)


def resolve_source(dataset_path: Path, source_layer: str | None) -> tuple[Path, str | None, tempfile.TemporaryDirectory[str] | None]:
    suffix = dataset_path.suffix.lower()

    if suffix in {".geojson", ".json", ".shp"}:
        return dataset_path, None, None

    if suffix == ".gpkg":
        layers = list_layers(dataset_path)
        if source_layer:
            if source_layer not in layers:
                raise ImporterError(f"Layer {source_layer} was not found in {dataset_path.name}")
            return dataset_path, source_layer, None
        if len(layers) != 1:
            raise ImporterError(
                f"Geopackage {dataset_path.name} contains {len(layers)} layers. Provide source_layer explicitly."
            )
        return dataset_path, layers[0], None

    if suffix == ".zip":
        temp_dir = tempfile.TemporaryDirectory(prefix="shp-")
        with zipfile.ZipFile(dataset_path) as archive:
            archive.extractall(temp_dir.name)

        shapefiles = sorted(Path(temp_dir.name).rglob("*.shp"))
        if not shapefiles:
            temp_dir.cleanup()
            raise ImporterError("Zip upload does not contain any .shp file")

        if source_layer:
            for shapefile in shapefiles:
                if shapefile.stem == source_layer or shapefile.name == source_layer:
                    return shapefile, None, temp_dir
            temp_dir.cleanup()
            raise ImporterError(f"Layer {source_layer} was not found inside the uploaded zip archive")

        if len(shapefiles) != 1:
            temp_dir.cleanup()
            raise ImporterError(
                "Zip upload contains multiple shapefiles. Provide source_layer to choose one explicitly."
            )
        return shapefiles[0], None, temp_dir

    raise ImporterError(
        f"Unsupported file format {dataset_path.suffix}. Supported inputs: .geojson, .json, .gpkg, .shp, .zip"
    )


def build_stage_table_name(target_table: str) -> str:
    return f"_stage_{target_table}_{uuid4().hex[:12]}"


def import_into_stage(
    database_url: str,
    source_path: Path,
    source_layer: str | None,
    target_metadata: TargetTableMetadata,
    stage_table: str,
) -> None:
    command = [
        "ogr2ogr",
        "-f",
        "PostgreSQL",
        build_ogr_connection_string(database_url),
        str(source_path),
        "-overwrite",
        "-t_srs",
        f"EPSG:{target_metadata.srid}",
        "-nlt",
        OGR_GEOMETRY_TYPES[target_metadata.geometry_type],
        "-nln",
        stage_table,
        "-lco",
        "SCHEMA=public",
        "-lco",
        f"GEOMETRY_NAME={target_metadata.geometry_column}",
        "-lco",
        "PRECISION=NO",
    ]

    if source_layer:
        command.append(source_layer)

    run_command(command)


def geometry_transform_expression(geometry_column: str, geometry_type: str, srid: int) -> sql.SQL:
    normalized_geometry = sql.SQL(
        "CASE "
        "WHEN ST_SRID({column}) = {srid} THEN {column} "
        "WHEN ST_SRID({column}) = 0 THEN ST_SetSRID({column}, {srid}) "
        "ELSE ST_Transform({column}, {srid}) END"
    ).format(
        column=sql.Identifier(geometry_column),
        srid=sql.Literal(srid),
    )

    return sql.SQL("ST_Multi(ST_CollectionExtract(ST_MakeValid({geom}), {dimension}))").format(
        geom=normalized_geometry,
        dimension=sql.Literal(GEOMETRY_DIMENSIONS[geometry_type]),
    )


INTEGER_TYPES = {"smallint", "integer", "bigint"}
FLOAT_TYPES = {"real", "double precision"}
DECIMAL_TYPES = {"numeric", "decimal"}


def cast_stage_value_expression(stage_column: str, target_data_type: str) -> sql.SQL:
    column_ref = sql.Identifier(stage_column)
    column_text = sql.SQL("{}::text").format(column_ref)
    trimmed_text = sql.SQL("NULLIF(BTRIM({}), '')").format(column_text)

    if target_data_type in INTEGER_TYPES:
        return sql.SQL(
            "CASE "
            "WHEN {value} ~ '^[+-]?[0-9]+$' THEN ({value})::{type} "
            "ELSE NULL END"
        ).format(
            value=trimmed_text,
            type=sql.SQL(target_data_type),
        )

    if target_data_type in FLOAT_TYPES | DECIMAL_TYPES:
        return sql.SQL(
            "CASE "
            "WHEN {value} ~ '^[+-]?(?:[0-9]+(?:\\.[0-9]*)?|\\.[0-9]+)$' THEN ({value})::{type} "
            "ELSE NULL END"
        ).format(
            value=trimmed_text,
            type=sql.SQL(target_data_type),
        )

    if target_data_type == "boolean":
        return sql.SQL(
            "CASE "
            "WHEN {value} IS NULL THEN NULL "
            "WHEN LOWER({value}) IN ('true', 't', '1', 'yes', 'y', 'on') THEN TRUE "
            "WHEN LOWER({value}) IN ('false', 'f', '0', 'no', 'n', 'off') THEN FALSE "
            "ELSE NULL END"
        ).format(value=trimmed_text)

    return column_ref


def load_stage_into_target(
    database_url: str,
    target_metadata: TargetTableMetadata,
    stage_table: str,
    mode: ImportMode,
) -> int:
    stage_columns = get_table_columns(database_url, stage_table)
    stage_lookup = {column.lower(): column for column in stage_columns}
    target_columns = [
        column
        for column in target_metadata.columns
        if column not in {"id", target_metadata.geometry_column}
    ]

    matched_columns = [
        (target_column, stage_lookup[target_column.lower()])
        for target_column in target_columns
        if target_column.lower() in stage_lookup
    ]

    insert_columns = [sql.Identifier(column) for column, _ in matched_columns]
    insert_columns.append(sql.Identifier(target_metadata.geometry_column))

    inner_select_parts = [
        cast_stage_value_expression(stage_column, target_metadata.column_types[target_column])
        + sql.SQL(" AS ")
        + sql.Identifier(stage_column)
        for target_column, stage_column in matched_columns
    ]
    inner_select_parts.append(
        geometry_transform_expression(
            target_metadata.geometry_column,
            target_metadata.geometry_type,
            target_metadata.srid,
        )
        + sql.SQL(" AS prepared_geom")
    )

    outer_select_parts = [sql.Identifier(stage_column) for _, stage_column in matched_columns]
    outer_select_parts.append(sql.Identifier("prepared_geom"))

    insert_query = sql.SQL(
        "INSERT INTO {}.{} ({}) "
        "SELECT {} FROM (SELECT {} FROM {}.{}) AS prepared "
        "WHERE prepared_geom IS NOT NULL AND NOT ST_IsEmpty(prepared_geom)"
    ).format(
        sql.Identifier("public"),
        sql.Identifier(target_metadata.name),
        sql.SQL(", ").join(insert_columns),
        sql.SQL(", ").join(outer_select_parts),
        sql.SQL(", ").join(inner_select_parts),
        sql.Identifier("public"),
        sql.Identifier(stage_table),
    )

    with connect(database_url) as conn:
        if mode is ImportMode.REPLACE:
            conn.execute(
                sql.SQL("TRUNCATE TABLE {}.{} RESTART IDENTITY").format(
                    sql.Identifier("public"),
                    sql.Identifier(target_metadata.name),
                )
            )

        cursor = conn.execute(insert_query)
        conn.commit()
        return cursor.rowcount or 0


def drop_table(database_url: str, table_name: str) -> None:
    with connect(database_url) as conn:
        conn.execute(
            sql.SQL("DROP TABLE IF EXISTS {}.{}").format(
                sql.Identifier("public"),
                sql.Identifier(table_name),
            )
        )
        conn.commit()


def import_dataset(
    database_url: str,
    source_path: Path,
    table_name: str,
    mode: ImportMode,
    source_layer: str | None = None,
) -> int:
    source_path = source_path.resolve()
    if not source_path.exists():
        raise ImporterError(f"Source file does not exist: {source_path}")

    target_metadata = get_target_table_metadata(database_url, table_name)
    stage_table = build_stage_table_name(target_metadata.name)
    working_dir: tempfile.TemporaryDirectory[str] | None = None

    try:
        resolved_source, resolved_layer, working_dir = resolve_source(source_path, source_layer)
        import_into_stage(database_url, resolved_source, resolved_layer, target_metadata, stage_table)
        return load_stage_into_target(database_url, target_metadata, stage_table, mode)
    finally:
        drop_table(database_url, stage_table)
        if working_dir is not None:
            working_dir.cleanup()


def truncate_table(database_url: str, table_name: str) -> None:
    target_metadata = get_target_table_metadata(database_url, table_name)
    with connect(database_url) as conn:
        conn.execute(
            sql.SQL("TRUNCATE TABLE {}.{} RESTART IDENTITY").format(
                sql.Identifier("public"),
                sql.Identifier(target_metadata.name),
            )
        )
        conn.commit()


def import_manifest(database_url: str, manifest_path: Path) -> list[dict[str, Any]]:
    manifest_path = manifest_path.resolve()
    if not manifest_path.exists():
        raise ImporterError(f"Manifest file does not exist: {manifest_path}")

    raw_manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    datasets = raw_manifest.get("datasets")
    if not isinstance(datasets, list):
        raise ImporterError("Manifest must define a top-level 'datasets' array")

    results: list[dict[str, Any]] = []
    for dataset in datasets:
        source = manifest_path.parent / dataset["source"]
        table_name = dataset["table"]
        mode = ImportMode(dataset.get("mode", ImportMode.REPLACE))
        rows_loaded = import_dataset(
            database_url=database_url,
            source_path=source,
            table_name=table_name,
            mode=mode,
            source_layer=dataset.get("source_layer"),
        )
        results.append(
            {
                "table": table_name,
                "source": str(source.resolve()),
                "mode": mode.value,
                "rows_loaded": rows_loaded,
            }
        )

    return results