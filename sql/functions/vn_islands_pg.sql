CREATE OR REPLACE FUNCTION layer_vn_islands_pg(z integer, x integer, y integer)
RETURNS bytea AS $$
DECLARE
    mvt bytea;
BEGIN
    SELECT INTO mvt ST_AsMVT(tile, 'vn_islands_pg', 4096, 'geom')
    FROM (
        SELECT
            ST_AsMVTGeom(geometry, ST_TileEnvelope(z, x, y), 4096, 64, true) AS geom,
            code,
            name,
            name_en
        FROM vn_islands_pg
        WHERE z >= 3
            AND geometry && ST_TileEnvelope(z, x, y)
            AND ST_IsValid(geometry)
    ) AS tile
    WHERE geom IS NOT NULL;

    RETURN COALESCE(mvt, ''::bytea);
END
$$ LANGUAGE plpgsql STABLE STRICT PARALLEL SAFE;

DO $do$ BEGIN
    EXECUTE 'COMMENT ON FUNCTION layer_vn_islands_pg(integer, integer, integer) IS $tj$' || $$
    {
        "description": "Vietnam island polygons for Martin vector tiles",
        "minzoom": 3,
        "maxzoom": 22,
        "vector_layers": [
            {
                "id": "vn_islands_pg",
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