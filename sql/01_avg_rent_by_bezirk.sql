-- =============================================================================
-- Berlin Rental Market Analyzer — Phase 3
-- Query 01: Average rent by Bezirk
-- File: sql/01_avg_rent_by_bezirk.sql
-- Technique: GROUP BY, aggregate functions
--
-- Question answered:
--   Which Berlin Bezirke are the most and least expensive to rent in?
--
-- Reading the result:
--   Sort is descending by avg_rent_eur — the most expensive Bezirk is at the top.
--   listing_count tells you how many data points back up each average.
--   Bezirke with fewer listings should be interpreted with more caution.
-- =============================================================================

SELECT
    d.bezirk,

    COUNT(*)                        AS listing_count,
    ROUND(AVG(f.base_rent), 2)      AS avg_rent_eur,
    ROUND(MIN(f.base_rent), 2)      AS min_rent_eur,
    ROUND(MAX(f.base_rent), 2)      AS max_rent_eur,

    -- Spread: how wide is the price range within each Bezirk?
    ROUND(MAX(f.base_rent) - MIN(f.base_rent), 2) AS rent_range_eur

FROM fact_listings  f
JOIN dim_districts  d ON f.district_id = d.district_id

WHERE f.base_rent IS NOT NULL

GROUP BY d.bezirk
ORDER BY avg_rent_eur DESC;
