CREATE OR REPLACE FUNCTION layer_wld_boundary_pg(z integer, x integer, y integer)
RETURNS bytea AS $$
DECLARE
    mvt bytea;
BEGIN
    SELECT INTO mvt ST_AsMVT(tile, 'wld_boundary_pg', 4096, 'geom')
    FROM (
        SELECT
            ST_AsMVTGeom(geometry, ST_TileEnvelope(z, x, y), 4096, 64, true) AS geom,
            code,
            name,
            name_en
        FROM (
            SELECT geometry, code, name, name_en
            FROM wld_boundary_pg_view_country
            WHERE z < 6
                AND geometry && ST_TileEnvelope(z, x, y)

            UNION ALL

            SELECT geometry, code, name, name_en
            FROM wld_boundary_pg_view_province
            WHERE z >= 6
                AND z < 10
                AND geometry && ST_TileEnvelope(z, x, y)

            UNION ALL

            SELECT geometry, code, name, name_en
            FROM wld_boundary_pg_view_ward
            WHERE z >= 10
                AND z < 12
                AND geometry && ST_TileEnvelope(z, x, y)

            UNION ALL

            SELECT geometry, code, name, name_en
            FROM wld_boundary_pg_view_street
            WHERE z >= 12
                AND geometry && ST_TileEnvelope(z, x, y)
        ) AS source_rows
        WHERE ST_IsValid(geometry)
    ) AS tile
    WHERE geom IS NOT NULL;

    RETURN COALESCE(mvt, ''::bytea);
END
$$ LANGUAGE plpgsql STABLE STRICT PARALLEL SAFE;

DO $do$ BEGIN
    EXECUTE 'COMMENT ON FUNCTION layer_wld_boundary_pg(integer, integer, integer) IS $tj$' || $$
    {
        "description": "World boundary polygons for Martin vector tiles",
        "minzoom": 0,
        "maxzoom": 22,
        "vector_layers": [
            {
                "id": "wld_boundary_pg",
                "fields": {
                    "code": "String",
                    "name": "String",
                    "name_en": "String"
                }
            }
        ]
    }
    $$::json || '$tj$';
END $do$;
