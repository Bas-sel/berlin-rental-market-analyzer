-- =============================================================================
-- Berlin Rental Market Analyzer — Phase 3
-- File: sql/schema.sql
-- Purpose: Creates the three-table normalised star schema in SQLite.
--
-- Tables
--   dim_districts      — one row per unique neighbourhood (regio3 / Bezirk pair)
--   dim_property_types — one row per unique apartment type
--   fact_listings      — all cleaned listing rows, with FK references to both dims
--
-- Run order: this file is executed automatically by src/load_to_sqlite.py.
--            Do NOT run it manually against an already-populated database —
--            the loader drops and recreates the DB file first.
-- =============================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- Dimension: Districts
-- Granularity: one row per unique regio3 (neighbourhood / Kiez) value.
-- The bezirk column holds the mapped official Bezirk name (12 Bezirke).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_districts (
    district_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    regio3        TEXT    NOT NULL,           -- Kiez-level name from raw data
    bezirk        TEXT    NOT NULL,           -- Official Berlin Bezirk (12 values)
    district_tier TEXT                        -- Premium / Mid / Affordable (Phase 2)
);

-- Unique index: regio3 must map to exactly one row (prevents duplicate inserts)
CREATE UNIQUE INDEX IF NOT EXISTS uix_districts_regio3
    ON dim_districts (regio3);

-- ---------------------------------------------------------------------------
-- Dimension: Property Types
-- Granularity: one row per unique typeOfFlat value from the raw dataset.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_property_types (
    property_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name        TEXT NOT NULL UNIQUE,    -- raw value, e.g. "roof_storey"
    type_label       TEXT                     -- clean display label, e.g. "Roof Storey"
);

-- ---------------------------------------------------------------------------
-- Fact: Listings
-- Granularity: one row per deduplicated listing (scoutId, most-recent date).
-- Foreign keys link to both dimension tables.
-- Boolean amenity columns (has_kitchen, balcony, …) are stored as INTEGER 0/1.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_listings (
    listing_id       INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Identifiers
    scout_id         INTEGER NOT NULL,        -- original scoutId from ImmobilienScout24
    scrape_date      TEXT,                    -- Sep18 | May19 | Oct19 | Feb20

    -- Foreign keys
    district_id      INTEGER  REFERENCES dim_districts(district_id),
    property_type_id INTEGER  REFERENCES dim_property_types(property_type_id),

    -- Core financials
    base_rent        REAL,                    -- Kaltmiete in EUR (primary target variable)
    living_space     REAL,                    -- floor area in m²
    no_rooms         REAL,                    -- number of rooms (excl. kitchen/bath)
    service_charge   REAL,                    -- Nebenkosten in EUR
    total_rent       REAL,                    -- Warmmiete = base_rent + service_charge

    -- Physical attributes
    floor_number     INTEGER,
    year_constructed INTEGER,
    condition_state  TEXT,                    -- well_kept | refurbished | … (9 values)
    interior_qual    TEXT,                    -- simple | normal | sophisticated | luxury
    heating_type     TEXT,

    -- Rental policy
    pets_allowed     TEXT,                    -- yes | no | negotiable

    -- Amenity flags (0 = No, 1 = Yes)
    has_kitchen      INTEGER,
    cellar           INTEGER,
    balcony          INTEGER,
    garden           INTEGER,
    lift             INTEGER,
    newly_const      INTEGER,

    -- Geography
    geo_plz          INTEGER,                 -- postal code

    -- Derived columns (engineered in Phase 2)
    price_per_sqm    REAL,                    -- base_rent / living_space
    size_category    TEXT,                    -- Micro | Small | Medium | Large
    era              TEXT,                    -- construction era band
    price_trend      REAL                     -- platform price-trend score
);

-- Indexes on the most frequently joined / filtered columns
CREATE INDEX IF NOT EXISTS idx_listings_district
    ON fact_listings (district_id);

CREATE INDEX IF NOT EXISTS idx_listings_property_type
    ON fact_listings (property_type_id);

CREATE INDEX IF NOT EXISTS idx_listings_base_rent
    ON fact_listings (base_rent);

CREATE INDEX IF NOT EXISTS idx_listings_price_per_sqm
    ON fact_listings (price_per_sqm);
