-- =============================================================================
-- Berlin Rental Market Analyzer — Phase 3
-- Query 09: Bezirke with sufficient listing volume
-- File: sql/09_high_volume_districts.sql
-- Technique: GROUP BY + HAVING COUNT(*) threshold
--
-- Question answered:
--   Which Bezirke have enough listings to support statistically meaningful
--   conclusions — and what do their rental markets look like in detail?
--
-- Why HAVING matters here:
--   The Berlin dataset has ~10,406 rows across 12 Bezirke.
--   Most Bezirke will clear a threshold of 300+ listings with ease.
--   Any that do not are flagged by being absent from this result —
--   useful information in itself (sparse data → weaker analytical power).
--
-- Reading the result:
--   Bezirke that appear here are your primary analysis targets.
--   Use listing_count to weight your confidence in the averages.
--   pct_of_total shows the market share of each Bezirk in the dataset.
-- =============================================================================

SELECT
    d.bezirk,

    COUNT(*)                                                                 AS listing_count,

    -- Share of total Berlin listings this Bezirk represents
    ROUND(
        100.0 * COUNT(*)
        / (SELECT COUNT(*) FROM fact_listings WHERE base_rent IS NOT NULL),
        1
    )                                                                        AS pct_of_total,

    ROUND(AVG(f.base_rent),     2)                                           AS avg_rent_eur,
    ROUND(AVG(f.price_per_sqm), 2)                                           AS avg_price_per_sqm,
    ROUND(AVG(f.living_space),  1)                                           AS avg_size_sqm,
    ROUND(AVG(f.no_rooms),      1)                                           AS avg_rooms,
    ROUND(MIN(f.base_rent),     2)                                           AS min_rent_eur,
    ROUND(MAX(f.base_rent),     2)                                           AS max_rent_eur

FROM fact_listings f
JOIN dim_districts d ON f.district_id = d.district_id

WHERE f.base_rent IS NOT NULL

GROUP BY d.bezirk

-- Only include Bezirke with at least 300 listings — adjust this threshold
-- up or down based on your actual data if any Bezirke fall just below it
HAVING COUNT(*) >= 300

ORDER BY listing_count DESC;
