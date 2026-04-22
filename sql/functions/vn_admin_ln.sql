CREATE OR REPLACE FUNCTION layer_vn_admin_ln(z integer, x integer, y integer)
RETURNS bytea AS $$
DECLARE
    mvt bytea;
BEGIN
    SELECT INTO mvt ST_AsMVT(tile, 'vn_admin_ln', 4096, 'geom')
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
            admin_left,
            admin_right,
            is_overlap
        FROM (
            SELECT geometry, code, name, name_en, level, region, admin_level, level_num, admin_left, admin_right, is_overlap
            FROM vn_admin_ln_view_country
            WHERE z < 6
                AND level_num = 4
                AND geometry && ST_TileEnvelope(z, x, y)

            UNION ALL

            SELECT geometry, code, name, name_en, level, region, admin_level, level_num, admin_left, admin_right, is_overlap
            FROM vn_admin_ln_view_province
            WHERE z >= 6
                AND z < 10
                AND level_num = 4
                AND geometry && ST_TileEnvelope(z, x, y)

            UNION ALL

            SELECT geometry, code, name, name_en, level, region, admin_level, level_num, admin_left, admin_right, is_overlap
            FROM vn_admin_ln_view_ward
            WHERE z >= 10
                AND z < 12
                AND level_num IN (4, 8)
                AND geometry && ST_TileEnvelope(z, x, y)

            UNION ALL

            SELECT geometry, code, name, name_en, level, region, admin_level, level_num, admin_left, admin_right, is_overlap
            FROM vn_admin_ln_view_street
            WHERE z >= 12
                AND level_num IN (4, 8)
                AND geometry && ST_TileEnvelope(z, x, y)
        ) AS source_rows
        WHERE ST_IsValid(geometry)
    ) AS tile
    WHERE geom IS NOT NULL;

    RETURN COALESCE(mvt, ''::bytea);
END
$$ LANGUAGE plpgsql STABLE STRICT PARALLEL SAFE;

DO $do$ BEGIN
    EXECUTE 'COMMENT ON FUNCTION layer_vn_admin_ln(integer, integer, integer) IS $tj$' || $$
    {
        "description": "Vietnam administrative linework for Martin vector tiles",
        "minzoom": 0,
        "maxzoom": 22,
        "vector_layers": [
            {
                "id": "vn_admin_ln",
                "fields": {
                    "code": "String",
                    "name": "String",
                    "name_en": "String",
                    "level": "String",
                    "region": "String",
                    "admin_level": "Number",
                    "level_num": "Number",
                    "admin_left": "String",
                    "admin_right": "String",
                    "is_overlap": "Boolean"
                }
            }
        ]
    }
    $$::json || '$tj$';
END $do$;
