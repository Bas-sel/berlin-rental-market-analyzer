-- =============================================================================
-- Berlin Rental Market Analyzer — Phase 3
-- Query 07: Bezirk affordability index — multi-step CTE
-- File: sql/07_affordability_cte.sql
-- Technique: Three-step CTE chain
--
-- Question answered:
--   How affordable is each Bezirk relative to the Berlin city-wide average?
--   Which Bezirke are genuinely cheap, which are average, which are expensive?
--
-- Why a multi-step CTE?
--   The affordability index requires two independent aggregations:
--     (a) city-wide baseline — one number for all of Berlin
--     (b) per-Bezirk stats — twelve numbers, one per Bezirk
--   Combining these in a single SELECT with a subquery would be hard to read.
--   Three named CTEs express the logic as sequential, readable steps.
--
-- How to read affordability_index:
--   1.00 = exactly at the city average
--   1.25 = 25% more expensive than average
--   0.80 = 20% cheaper than average
--
-- Tier classification thresholds:
--   Affordable  → index < 0.90  (more than 10% below city average)
--   Average     → 0.90 ≤ index < 1.15
--   Expensive   → index ≥ 1.15  (more than 15% above city average)
-- =============================================================================

-- Step 1: Single-row city-wide baseline
WITH city_baseline AS (
    SELECT
        ROUND(AVG(base_rent),     2)   AS city_avg_rent,
        ROUND(AVG(price_per_sqm), 2)   AS city_avg_price_per_sqm,
        COUNT(*)                        AS city_total_listings
    FROM fact_listings
    WHERE base_rent IS NOT NULL
),

-- Step 2: Per-Bezirk aggregates
bezirk_stats AS (
    SELECT
        d.bezirk,
        COUNT(*)                        AS listing_count,
        ROUND(AVG(f.base_rent),     2)  AS avg_rent,
        ROUND(AVG(f.price_per_sqm), 2)  AS avg_price_per_sqm,
        ROUND(MIN(f.base_rent),     2)  AS min_rent,
        ROUND(MAX(f.base_rent),     2)  AS max_rent
    FROM fact_listings  f
    JOIN dim_districts  d ON f.district_id = d.district_id
    WHERE f.base_rent IS NOT NULL
    GROUP BY d.bezirk
),

-- Step 3: Join the two above, compute affordability index and tier
affordability AS (
    SELECT
        b.bezirk,
        b.listing_count,
        b.avg_rent,
        b.avg_price_per_sqm,
        b.min_rent,
        b.max_rent,
        c.city_avg_rent,
        c.city_total_listings,

        -- Index: ratio of this Bezirk's avg rent to the city-wide avg
        ROUND(b.avg_rent / NULLIF(c.city_avg_rent, 0), 3)      AS affordability_index,

        -- Human-readable tier classification
        CASE
            WHEN b.avg_rent / NULLIF(c.city_avg_rent, 0) < 0.90  THEN 'Affordable'
            WHEN b.avg_rent / NULLIF(c.city_avg_rent, 0) < 1.15  THEN 'Average'
            ELSE                                                        'Expensive'
        END                                                      AS affordability_tier,

        -- How far above or below the city average in EUR
        ROUND(b.avg_rent - c.city_avg_rent, 2)                  AS deviation_from_city_avg_eur

    FROM bezirk_stats  b
    CROSS JOIN city_baseline c
)

-- Final SELECT — ordered from most expensive to most affordable
SELECT *
FROM affordability
ORDER BY affordability_index DESC;
