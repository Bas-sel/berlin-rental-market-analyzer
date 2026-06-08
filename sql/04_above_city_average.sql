-- =============================================================================
-- Berlin Rental Market Analyzer — Phase 3
-- Query 04: Listings above the city average rent
-- File: sql/04_above_city_average.sql
-- Technique: CROSS JOIN subquery, conditional aggregation with CASE WHEN
--
-- Question answered:
--   Which Bezirke have the highest share of above-average-rent listings?
--   And which are the best bets for finding a below-average deal?
--
-- How the subquery works:
--   A CROSS JOIN subquery (aliased as city_avg) computes a single city-wide
--   average rent and makes it available as a scalar in every row of the main
--   query — without repeating the subquery inside each aggregate call.
--
-- Reading the result:
--   pct_above_city_avg close to 100% → the Bezirk is almost entirely above average.
--   pct_above_city_avg close to 0%  → a relatively affordable Bezirk.
--   city_avg_rent is the same value in every row — it is the Berlin-wide baseline.
-- =============================================================================

SELECT
    d.bezirk,

    COUNT(*)                                                              AS total_listings,

    -- Count of listings with rent above the city-wide average
    SUM(
        CASE WHEN f.base_rent > city_avg.mean_rent THEN 1 ELSE 0 END
    )                                                                     AS above_avg_count,

    -- Percentage of that Bezirk's listings that are above the city average
    ROUND(
        100.0
        * SUM(CASE WHEN f.base_rent > city_avg.mean_rent THEN 1 ELSE 0 END)
        / COUNT(*),
        1
    )                                                                     AS pct_above_city_avg,

    ROUND(city_avg.mean_rent, 2)                                         AS city_avg_rent

FROM fact_listings f

-- The subquery returns exactly one row (the city average).
-- CROSS JOIN broadcasts that value across every row in fact_listings.
CROSS JOIN (
    SELECT AVG(base_rent) AS mean_rent
    FROM   fact_listings
    WHERE  base_rent IS NOT NULL
) AS city_avg

JOIN dim_districts d ON f.district_id = d.district_id

WHERE f.base_rent IS NOT NULL

GROUP BY d.bezirk, city_avg.mean_rent
ORDER BY pct_above_city_avg DESC;
