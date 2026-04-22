CREATE OR REPLACE FUNCTION layer_vn_islands_pt(z integer, x integer, y integer)
RETURNS bytea AS $$
DECLARE
    mvt bytea;
BEGIN
    SELECT INTO mvt ST_AsMVT(tile, 'vn_islands_pt', 4096, 'geom')
    FROM (
        SELECT
            ST_AsMVTGeom(geometry, ST_TileEnvelope(z, x, y), 4096, 64, true) AS geom,
            code,
            name,
            name_en,
            type,
            rank,
            size,
            archipelago,
            name_arch
        FROM vn_islands_pt
        WHERE geometry && ST_TileEnvelope(z, x, y)
            AND ST_IsValid(geometry)
    ) AS tile
    WHERE geom IS NOT NULL;

    RETURN COALESCE(mvt, ''::bytea);
END
$$ LANGUAGE plpgsql STABLE STRICT PARALLEL SAFE;

DO $do$ BEGIN
    EXECUTE 'COMMENT ON FUNCTION layer_vn_islands_pt(integer, integer, integer) IS $tj$' || $$
    {
        "description": "Vietnam island points for Martin vector tiles",
        "minzoom": 0,
        "maxzoom": 22,
        "vector_layers": [
            {
                "id": "vn_islands_pt",
                "fields": {
                    "code": "String",
                    "name": "String",
                    "name_en": "String",
                    "type": "String",
                    "rank": "Number",
                    "size": "String",
                    "archipelago": "String",
                    "name_arch": "String"
                }
            }
        ]
    }
    $$::json || '$tj$';
END $do$;