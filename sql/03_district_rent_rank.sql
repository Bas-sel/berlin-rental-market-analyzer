-- =============================================================================
-- Berlin Rental Market Analyzer — Phase 3
-- Query 03: District rent ranking with window functions
-- File: sql/03_district_rent_rank.sql
-- Technique: CTE + RANK() OVER (ORDER BY …) + RANK() OVER (PARTITION BY …)
--
-- Question answered:
--   How does each neighbourhood (regio3) rank city-wide by price per m²?
--   And how does it rank within its own Bezirk?
--
-- Two window function calls are used:
--   city_rank    — overall ranking across all neighbourhoods
--   bezirk_rank  — ranking within each Bezirk (resets at each Bezirk boundary)
--
-- Reading the result:
--   city_rank = 1 is the most expensive neighbourhood in all of Berlin.
--   bezirk_rank = 1 is the priciest neighbourhood inside that particular Bezirk.
--   This lets you spot relative outliers: a neighbourhood that is not #1 city-wide
--   but IS #1 within an otherwise affordable Bezirk.
-- =============================================================================

WITH district_stats AS (
    -- Pre-aggregate to one row per neighbourhood
    SELECT
        d.regio3,
        d.bezirk,
        d.district_tier,
        COUNT(*)                        AS listing_count,
        ROUND(AVG(f.base_rent), 2)      AS avg_rent,
        ROUND(AVG(f.price_per_sqm), 2)  AS avg_price_per_sqm
    FROM fact_listings  f
    JOIN dim_districts  d ON f.district_id = d.district_id
    WHERE f.base_rent     IS NOT NULL
      AND f.price_per_sqm IS NOT NULL
    GROUP BY d.regio3, d.bezirk, d.district_tier
    HAVING COUNT(*) >= 5    -- exclude neighbourhoods with fewer than 5 listings
)

SELECT
    regio3,
    bezirk,
    district_tier,
    listing_count,
    avg_rent,
    avg_price_per_sqm,

    -- City-wide rank: 1 = most expensive neighbourhood in Berlin
    RANK() OVER (
        ORDER BY avg_price_per_sqm DESC
    )                                           AS city_rank,

    -- Bezirk-level rank: resets for each Bezirk, 1 = priciest in that Bezirk
    RANK() OVER (
        PARTITION BY bezirk
        ORDER BY avg_price_per_sqm DESC
    )                                           AS bezirk_rank

FROM district_stats
ORDER BY city_rank;
