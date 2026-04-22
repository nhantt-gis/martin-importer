CREATE OR REPLACE FUNCTION layer_vn_admin_pt(z integer, x integer, y integer)
RETURNS bytea AS $$
DECLARE
    mvt bytea;
BEGIN
    SELECT INTO mvt ST_AsMVT(tile, 'vn_admin_pt', 4096, 'geom')
    FROM (
        SELECT
            ST_AsMVTGeom(geometry, ST_TileEnvelope(z, x, y), 4096, 64, true) AS geom,
            code,
            name,
            name_en,
            level,
            region,
            admin_level,
            level_num,
            label,
            rank
        FROM (
            SELECT geometry, code, name, name_en, level, region, admin_level, level_num, label, rank
            FROM vn_admin_pt
            WHERE z >= 4
                AND level_num = 4
                AND geometry && ST_TileEnvelope(z, x, y)

            UNION ALL

            SELECT geometry, code, name, name_en, level, region, admin_level, level_num, label, rank
            FROM vn_admin_pt
            WHERE z >= 8
                AND level_num = 8
                AND geometry && ST_TileEnvelope(z, x, y)
        ) AS source_rows
        WHERE ST_IsValid(geometry)
    ) AS tile
    WHERE geom IS NOT NULL;

    RETURN COALESCE(mvt, ''::bytea);
END
$$ LANGUAGE plpgsql STABLE STRICT PARALLEL SAFE;

DO $do$ BEGIN
    EXECUTE 'COMMENT ON FUNCTION layer_vn_admin_pt(integer, integer, integer) IS $tj$' || $$
    {
        "description": "Vietnam administrative label points for Martin vector tiles",
        "minzoom": 4,
        "maxzoom": 22,
        "vector_layers": [
            {
                "id": "vn_admin_pt",
                "fields": {
                    "code": "String",
                    "name": "String",
                    "name_en": "String",
                    "level": "String",
                    "region": "String",
                    "admin_level": "Number",
                    "level_num": "Number",
                    "label": "String",
                    "rank": "Number"
                }
            }
        ]
    }
    $$::json || '$tj$';
END $do$;

