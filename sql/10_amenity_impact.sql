-- =============================================================================
-- Berlin Rental Market Analyzer — Phase 3
-- Query 10: Amenity rent premium
-- File: sql/10_amenity_impact.sql
-- Technique: Conditional aggregation with CASE WHEN + UNION ALL
--
-- Question answered:
--   Which individual apartment amenities are associated with the highest rent
--   premium in Berlin — balcony, lift, garden, or cellar?
--
-- How this query works:
--   Each UNION ALL block handles one amenity.
--   Within each block, conditional aggregation (AVG … CASE WHEN … END) computes
--   separate averages for listings that have and do not have that amenity.
--   This avoids running four separate queries and produces a clean summary table.
--
-- Interpretation note:
--   rent_premium_eur is associative, not causal — apartments with a balcony
--   may also tend to be larger or in pricier areas. Treat this as a first-pass
--   signal, not proof that the balcony alone drives the premium.
--
-- Reading the result:
--   Sorted by rent_premium_eur DESC — the amenity with the largest associated
--   rent difference appears at the top.
-- =============================================================================

SELECT
    'Balcony'   AS amenity,
    COUNT(CASE WHEN balcony = 1 THEN 1 END)                              AS count_with,
    COUNT(CASE WHEN balcony = 0 THEN 1 END)                              AS count_without,
    ROUND(AVG(CASE WHEN balcony = 1 THEN base_rent END), 2)             AS avg_rent_with_eur,
    ROUND(AVG(CASE WHEN balcony = 0 THEN base_rent END), 2)             AS avg_rent_without_eur,
    ROUND(
        AVG(CASE WHEN balcony = 1 THEN base_rent END)
      - AVG(CASE WHEN balcony = 0 THEN base_rent END),
    2)                                                                    AS rent_premium_eur
FROM fact_listings
WHERE base_rent IS NOT NULL AND balcony IS NOT NULL

UNION ALL

SELECT
    'Lift'      AS amenity,
    COUNT(CASE WHEN lift = 1 THEN 1 END),
    COUNT(CASE WHEN lift = 0 THEN 1 END),
    ROUND(AVG(CASE WHEN lift = 1 THEN base_rent END), 2),
    ROUND(AVG(CASE WHEN lift = 0 THEN base_rent END), 2),
    ROUND(
        AVG(CASE WHEN lift = 1 THEN base_rent END)
      - AVG(CASE WHEN lift = 0 THEN base_rent END),
    2)
FROM fact_listings
WHERE base_rent IS NOT NULL AND lift IS NOT NULL

UNION ALL

SELECT
    'Garden'    AS amenity,
    COUNT(CASE WHEN garden = 1 THEN 1 END),
    COUNT(CASE WHEN garden = 0 THEN 1 END),
    ROUND(AVG(CASE WHEN garden = 1 THEN base_rent END), 2),
    ROUND(AVG(CASE WHEN garden = 0 THEN base_rent END), 2),
    ROUND(
        AVG(CASE WHEN garden = 1 THEN base_rent END)
      - AVG(CASE WHEN garden = 0 THEN base_rent END),
    2)
FROM fact_listings
WHERE base_rent IS NOT NULL AND garden IS NOT NULL

UNION ALL

SELECT
    'Cellar'    AS amenity,
    COUNT(CASE WHEN cellar = 1 THEN 1 END),
    COUNT(CASE WHEN cellar = 0 THEN 1 END),
    ROUND(AVG(CASE WHEN cellar = 1 THEN base_rent END), 2),
    ROUND(AVG(CASE WHEN cellar = 0 THEN base_rent END), 2),
    ROUND(
        AVG(CASE WHEN cellar = 1 THEN base_rent END)
      - AVG(CASE WHEN cellar = 0 THEN base_rent END),
    2)
FROM fact_listings
WHERE base_rent IS NOT NULL AND cellar IS NOT NULL

ORDER BY rent_premium_eur DESC;
