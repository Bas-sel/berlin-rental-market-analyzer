-- =============================================================================
-- Berlin Rental Market Analyzer — Phase 3
-- Query 08: Property type price and size breakdown
-- File: sql/08_property_type_breakdown.sql
-- Technique: GROUP BY with JOIN to dimension table, HAVING to filter low-sample types
--
-- Question answered:
--   How do average rents, price per m², and apartment size differ across
--   property types (penthouse, roof storey, apartment, etc.)?
--
-- HAVING COUNT(*) >= 10 filters out property types with very few listings —
-- a small sample makes the averages unreliable and misleading.
--
-- Reading the result:
--   Sorted by avg_price_per_sqm DESC — the most premium property type is at the top.
--   listing_count shows how much statistical weight each type carries.
-- =============================================================================

SELECT
    p.type_label,

    COUNT(*)                               AS listing_count,
    ROUND(AVG(f.base_rent),      2)        AS avg_rent_eur,
    ROUND(AVG(f.price_per_sqm),  2)        AS avg_price_per_sqm,
    ROUND(AVG(f.living_space),   1)        AS avg_size_sqm,
    ROUND(AVG(f.no_rooms),       1)        AS avg_rooms,
    ROUND(MIN(f.base_rent),      2)        AS min_rent_eur,
    ROUND(MAX(f.base_rent),      2)        AS max_rent_eur

FROM fact_listings      f
JOIN dim_property_types p ON f.property_type_id = p.property_type_id

WHERE f.base_rent    IS NOT NULL
  AND f.living_space IS NOT NULL

GROUP BY p.type_label

-- Only show types with at least 10 listings — below this the averages are noisy
HAVING COUNT(*) >= 10

ORDER BY avg_price_per_sqm DESC;
