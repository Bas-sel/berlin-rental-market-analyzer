-- =============================================================================
-- Berlin Rental Market Analyzer — Phase 3
-- Query 06: Rent gap between Bezirke using LAG
-- File: sql/06_bezirk_rent_gap.sql
-- Technique: CTE + LAG() window function
--
-- Question answered:
--   Where in the Bezirk price ranking are the biggest jumps?
--   Is the gap between the most and second-most expensive Bezirk large or small?
--
-- How LAG works here:
--   The result rows are ordered by avg_rent DESC (most expensive first).
--   LAG(avg_rent) OVER (ORDER BY avg_rent DESC) looks back at the row above —
--   i.e. the next-more-expensive Bezirk.
--   Subtracting gives the rent gap between consecutive Bezirke in the ranking.
--
-- Reading the result:
--   next_pricier_bezirk_rent  — the average rent of the Bezirk one step more expensive.
--                               NULL for the most expensive Bezirk (no row above it).
--   rent_gap_to_next_eur      — how much cheaper this Bezirk is vs the one above.
--                               A large gap signals a meaningful market boundary.
-- =============================================================================

WITH bezirk_avg AS (
    -- Step 1: one aggregated row per Bezirk
    SELECT
        d.bezirk,
        COUNT(*)                        AS listing_count,
        ROUND(AVG(f.base_rent), 2)      AS avg_rent,
        ROUND(AVG(f.price_per_sqm), 2)  AS avg_price_per_sqm
    FROM fact_listings  f
    JOIN dim_districts  d ON f.district_id = d.district_id
    WHERE f.base_rent IS NOT NULL
    GROUP BY d.bezirk
)

-- Step 2: apply LAG over the sorted result
SELECT
    bezirk,
    listing_count,
    avg_rent,
    avg_price_per_sqm,

    -- The average rent of the Bezirk ranked one place above this one
    LAG(avg_rent) OVER (ORDER BY avg_rent DESC)   AS next_pricier_bezirk_rent,

    -- Positive value = how much cheaper this Bezirk is vs the one above it
    ROUND(
        LAG(avg_rent) OVER (ORDER BY avg_rent DESC) - avg_rent,
        2
    )                                              AS rent_gap_to_next_eur

FROM bezirk_avg
ORDER BY avg_rent DESC;
