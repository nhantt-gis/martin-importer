# Admin Martin Stack

This workspace now contains a Docker-based stack for:

- creating a fresh PostGIS database,
- migrating `sql/schema.sql` and all SQL functions,
- importing `geojson`, `gpkg`, `shapefile` data into PostGIS,
- exposing Martin-compatible PostgreSQL functions as vector tile APIs,
- serving the demo `index.html` via Nginx.

## Services

- `db`: PostgreSQL 17 + PostGIS 3.5
- `app`: FastAPI + Typer service for imports and table maintenance
- `martin`: Martin tile server exposing SQL functions as MVT endpoints
- `nginx`: static web server for the MapLibre demo page

## Start the stack:

```bash
# Start all services
docker compose up -d

# Start App/Postgres/Martin service
docker compose up -d app
docker compose up -d db
docker compose up -d martin
docker compose up -d nginx
```

Useful checks:

```bash
# Demo map
curl http://172.16.9.53:8484/

# Martin
curl http://172.16.9.53:3444/
curl http://172.16.9.53:3444/catalog

# API
curl http://172.16.9.53:8444/healthz
curl http://172.16.9.53:8444/tables
```

## Migrations

Run inside the app image:

```bash
docker compose run --rm app uv run --project /workspace/app martin-importer db migrate
```

## Import API

FastAPI docs are available at `http://172.16.9.53:8444/docs`.

Examples:

```bash
# Truncate existing data before import
curl -X POST http://172.16.9.53:8444/tables/vn_admin_pt/truncate

# Import data with auto-creating table if it doesn't exist
curl -X POST http://172.16.9.53:8444/imports \
  -F table=vn_admin_pt \
  -F mode=replace \
  -F file=@/path/to/new_data.gpkg \
  -F source_layer=layer_name

# Append new data to existing table
curl -X POST http://172.16.9.53:8444/tables/vn_admin_pt/append \
  -F file=@/path/to/new_data.gpkg \
  -F source_layer=layer_name

# Replace entire table with new data from a layer
curl -X POST http://172.16.9.53:8444/tables/vn_admin_pt/replace \
  -F file=@/path/to/new_data.gpkg \
  -F source_layer=layer_name
```

For Shapefile uploads, send a `.zip` bundle containing the `.shp`, `.shx`, `.dbf`, and related sidecar files.

## Martin sources

Martin is configured via `martin/config.yaml` and auto-publishes functions in `public` with source ids matching the SQL function names.

Current published sources after migration:

- `layer_vn_admin_ln`
- `layer_vn_admin_pt`
- `layer_vn_islands_pg`
- `layer_vn_islands_pt`
- `layer_wld_boundary_ln`
- `layer_wld_boundary_pg`

Each function now returns `bytea` MVT payloads using the Martin-friendly `(z, x, y)` signature.

## Demo map

Open `http://172.16.9.53:8484/` after `docker compose up -d` to load the bundled `index.html` through Nginx. The page proxies Martin style and `layer_*` tile requests through the same origin, so you do not need to edit host/IP values in the HTML anymore.