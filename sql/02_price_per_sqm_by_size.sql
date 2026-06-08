-- =============================================================================
-- Berlin Rental Market Analyzer — Phase 3
-- Query 02: Price per sqm by size category
-- File: sql/02_price_per_sqm_by_size.sql
-- Technique: GROUP BY, CASE for custom sort order
--
-- Question answered:
--   Do smaller apartments demand a higher price per m² than larger ones?
--   (A well-known pattern in European rental markets.)
--
-- Reading the result:
--   Compare avg_price_per_sqm across the four size tiers.
--   The Micro category typically commands the highest per-m² price.
-- =============================================================================

SELECT
    f.size_category,

    COUNT(*)                            AS listing_count,
    ROUND(AVG(f.price_per_sqm), 2)      AS avg_price_per_sqm,
    ROUND(MIN(f.price_per_sqm), 2)      AS min_price_per_sqm,
    ROUND(MAX(f.price_per_sqm), 2)      AS max_price_per_sqm,
    ROUND(AVG(f.living_space),  1)      AS avg_size_sqm

FROM fact_listings f

WHERE f.price_per_sqm  IS NOT NULL
  AND f.size_category  IS NOT NULL

GROUP BY f.size_category

-- Sort small → large using a CASE to avoid alphabetical ordering
ORDER BY
    CASE f.size_category
        WHEN 'Micro'   THEN 1
        WHEN 'Small'   THEN 2
        WHEN 'Medium'  THEN 3
        WHEN 'Large'   THEN 4
        ELSE                5
    END;
