-- =============================================================================
-- EXTENSIONS
-- =============================================================================
CREATE EXTENSION IF NOT EXISTS postgis;

-- =============================================================================
-- ADMIN VIEW: COUNTRY LEVEL
-- =============================================================================

CREATE TABLE IF NOT EXISTS wld_boundary_pg_view_country (
    id       SERIAL PRIMARY KEY,
    code     VARCHAR(50),
    name     VARCHAR(255),
    name_en  VARCHAR(255),
    geometry GEOMETRY(MultiPolygon, 3857)
);

CREATE INDEX IF NOT EXISTS idx_wld_boundary_pg_view_country_geom ON wld_boundary_pg_view_country USING GIST (geometry);

-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS wld_boundary_ln_view_country (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(255),
    name_en    VARCHAR(255),
    adm0_left  VARCHAR(255),
    adm0_right VARCHAR(255),
    adm0_a3_l  VARCHAR(255),
    adm0_a3_r  VARCHAR(255),
    labelrank  INTEGER,
    scalerank  INTEGER,
    geometry GEOMETRY(MultiLineString, 3857)
);

CREATE INDEX IF NOT EXISTS idx_wld_boundary_ln_view_country_geom ON wld_boundary_ln_view_country USING GIST (geometry);

-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS vn_admin_ln_view_country (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(50),
    name        VARCHAR(255),
    name_en     VARCHAR(255),
    level       VARCHAR(50),
    region      VARCHAR(100),
    admin_level INTEGER,
    level_num   INTEGER,
    admin_left  VARCHAR(100),
    admin_right VARCHAR(100),
    is_overlap  BOOLEAN DEFAULT FALSE,
    geometry    GEOMETRY(MultiLineString, 3857)
);

CREATE INDEX IF NOT EXISTS idx_vn_admin_ln_view_country_geom ON vn_admin_ln_view_country USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_vn_admin_ln_view_country_code ON vn_admin_ln_view_country (code);


-- =============================================================================
-- ADMIN VIEW: PROVINCE LEVEL
-- =============================================================================

CREATE TABLE IF NOT EXISTS wld_boundary_pg_view_province (
    id       SERIAL PRIMARY KEY,
    code     VARCHAR(50),
    name     VARCHAR(255),
    name_en  VARCHAR(255),
    geometry GEOMETRY(MultiPolygon, 3857)
);

CREATE INDEX IF NOT EXISTS idx_wld_boundary_pg_view_province_geom ON wld_boundary_pg_view_province USING GIST (geometry);

-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS wld_boundary_ln_view_province (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(255),
    name_en    VARCHAR(255),
    adm0_left  VARCHAR(255),
    adm0_right VARCHAR(255),
    adm0_a3_l  VARCHAR(255),
    adm0_a3_r  VARCHAR(255),
    labelrank  INTEGER,
    scalerank  INTEGER,
    geometry GEOMETRY(MultiLineString, 3857)
);

CREATE INDEX IF NOT EXISTS idx_wld_boundary_ln_view_province_geom ON wld_boundary_ln_view_province USING GIST (geometry);

-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS vn_admin_ln_view_province (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(50),
    name        VARCHAR(255),
    name_en     VARCHAR(255),
    level       VARCHAR(50),
    region      VARCHAR(100),
    admin_level INTEGER,
    level_num   INTEGER,
    admin_left  VARCHAR(100),
    admin_right VARCHAR(100),
    is_overlap  BOOLEAN DEFAULT FALSE,
    geometry    GEOMETRY(MultiLineString, 3857)
);

CREATE INDEX IF NOT EXISTS idx_vn_admin_ln_view_province_geom ON vn_admin_ln_view_province USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_vn_admin_ln_view_province_code ON vn_admin_ln_view_province (code);


-- =============================================================================
-- ADMIN VIEW: WARD LEVEL
-- =============================================================================

CREATE TABLE IF NOT EXISTS wld_boundary_pg_view_ward (
    id       SERIAL PRIMARY KEY,
    code     VARCHAR(50),
    name     VARCHAR(255),
    name_en  VARCHAR(255),
    geometry GEOMETRY(MultiPolygon, 3857)
);

CREATE INDEX IF NOT EXISTS idx_wld_boundary_pg_view_ward_geom ON wld_boundary_pg_view_ward USING GIST (geometry);

-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS wld_boundary_ln_view_ward (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(255),
    name_en    VARCHAR(255),
    adm0_left  VARCHAR(255),
    adm0_right VARCHAR(255),
    adm0_a3_l  VARCHAR(255),
    adm0_a3_r  VARCHAR(255),
    labelrank  INTEGER,
    scalerank  INTEGER,
    geometry GEOMETRY(MultiLineString, 3857)
);

CREATE INDEX IF NOT EXISTS idx_wld_boundary_ln_view_ward_geom ON wld_boundary_ln_view_ward USING GIST (geometry);

-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS vn_admin_ln_view_ward (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(50),
    name        VARCHAR(255),
    name_en     VARCHAR(255),
    level       VARCHAR(50),
    region      VARCHAR(100),
    admin_level INTEGER,
    level_num   INTEGER,
    admin_left  VARCHAR(100),
    admin_right VARCHAR(100),
    is_overlap  BOOLEAN DEFAULT FALSE,
    geometry    GEOMETRY(MultiLineString, 3857)
);

CREATE INDEX IF NOT EXISTS idx_vn_admin_ln_view_ward_geom ON vn_admin_ln_view_ward USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_vn_admin_ln_view_ward_code ON vn_admin_ln_view_ward (code);


-- =============================================================================
-- ADMIN VIEW: STREET LEVEL
-- =============================================================================

CREATE TABLE IF NOT EXISTS wld_boundary_pg_view_street (
    id       SERIAL PRIMARY KEY,
    code     VARCHAR(50),
    name     VARCHAR(255),
    name_en  VARCHAR(255),
    geometry GEOMETRY(MultiPolygon, 3857)
);

CREATE INDEX IF NOT EXISTS idx_wld_boundary_pg_view_street_geom ON wld_boundary_pg_view_street USING GIST (geometry);

-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS wld_boundary_ln_view_street (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(255),
    name_en    VARCHAR(255),
    adm0_left  VARCHAR(255),
    adm0_right VARCHAR(255),
    adm0_a3_l  VARCHAR(255),
    adm0_a3_r  VARCHAR(255),
    labelrank  INTEGER,
    scalerank  INTEGER,
    geometry GEOMETRY(MultiLineString, 3857)
);

CREATE INDEX IF NOT EXISTS idx_wld_boundary_ln_view_street_geom ON wld_boundary_ln_view_street USING GIST (geometry);

-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS vn_admin_ln_view_street (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(50),
    name        VARCHAR(255),
    name_en     VARCHAR(255),
    level       VARCHAR(50),
    region      VARCHAR(100),
    admin_level INTEGER,
    level_num   INTEGER,
    admin_left  VARCHAR(100),
    admin_right VARCHAR(100),
    is_overlap  BOOLEAN DEFAULT FALSE,
    geometry    GEOMETRY(MultiLineString, 3857)
);

CREATE INDEX IF NOT EXISTS idx_vn_admin_ln_view_street_geom ON vn_admin_ln_view_street USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_vn_admin_ln_view_street_code ON vn_admin_ln_view_street (code);


-- =============================================================================
-- ADMIN LABEL POINTS
-- =============================================================================

CREATE TABLE IF NOT EXISTS vn_admin_pt (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(50),
    name        VARCHAR(255),
    name_en     VARCHAR(255),
    level       VARCHAR(50),
    region      VARCHAR(100),
    admin_level INTEGER,
    level_num   INTEGER,
    label       VARCHAR(255),
    rank        INTEGER,
    geometry    GEOMETRY(MultiPoint, 3857)
);

CREATE INDEX IF NOT EXISTS idx_vn_admin_pt_geom ON vn_admin_pt USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_vn_admin_pt_code ON vn_admin_pt (code);


-- =============================================================================
-- ISLANDS
-- =============================================================================

CREATE TABLE IF NOT EXISTS vn_islands_pg (
    id       SERIAL PRIMARY KEY,
    code     VARCHAR(50),
    name     VARCHAR(255),
    name_en  VARCHAR(255),
    geometry GEOMETRY(MultiPolygon, 3857)
);

CREATE INDEX IF NOT EXISTS idx_vn_islands_pg_geom ON vn_islands_pg USING GIST (geometry);

-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS vn_islands_pt (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(50),
    name        VARCHAR(255),
    name_en     VARCHAR(255),
    type        VARCHAR(100),
    rank        INTEGER,
    size        VARCHAR(100),
    archipelago VARCHAR(255),
    name_arch   VARCHAR(255),
    geometry    GEOMETRY(MultiPoint, 3857)
);

CREATE INDEX IF NOT EXISTS idx_vn_islands_pt_geom ON vn_islands_pt USING GIST (geometry);
