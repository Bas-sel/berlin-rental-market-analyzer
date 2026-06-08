-- =============================================================================
-- Berlin Rental Market Analyzer — Phase 3
-- Query 05: Fitted-kitchen rent premium
-- File: sql/05_kitchen_premium.sql
-- Technique: GROUP BY on a boolean column, CASE WHEN for display labels
--
-- Question answered:
--   How much more do Berlin renters pay for an apartment that includes a
--   fitted kitchen (Einbauküche)?
--
-- Context for German market:
--   In Germany it is very common to rent an apartment without a kitchen —
--   tenants bring their own. An Einbauküche is therefore a meaningful amenity
--   that can justify a rent premium. This query measures that premium directly.
--
-- Reading the result:
--   Two rows: "With fitted kitchen" and "Without fitted kitchen".
--   The rent_premium_eur column (only visible in run_all_queries output) is the
--   difference between the two avg_rent_eur values — the cost of the kitchen.
-- =============================================================================

SELECT
    CASE has_kitchen
        WHEN 1 THEN 'With fitted kitchen (Einbauküche)'
        WHEN 0 THEN 'Without fitted kitchen'
        ELSE        'Unknown'
    END                                 AS kitchen_status,

    COUNT(*)                            AS listing_count,
    ROUND(AVG(base_rent),      2)       AS avg_rent_eur,
    ROUND(AVG(price_per_sqm),  2)       AS avg_price_per_sqm,
    ROUND(AVG(living_space),   1)       AS avg_size_sqm,
    ROUND(AVG(no_rooms),       1)       AS avg_rooms

FROM fact_listings

WHERE base_rent    IS NOT NULL
  AND has_kitchen  IS NOT NULL

GROUP BY has_kitchen
ORDER BY avg_rent_eur DESC;
