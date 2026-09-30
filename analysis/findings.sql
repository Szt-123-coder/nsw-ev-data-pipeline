-- Existing location records only. Shares describe the current operator labels.
WITH existing AS (
  SELECT * FROM silver.ev_locations_sa4 WHERE is_upcoming=false
), statewide AS (
  SELECT count(*) AS existing_locations,
    count(*) FILTER(WHERE charger_type='DC') AS dc_locations FROM existing
), hunter AS (
  SELECT count(*) AS hunter_locations,
    count(*) FILTER(WHERE charger_type='DC') AS hunter_dc FROM existing WHERE sa4_code='106'
), geography AS (
  SELECT count(*) FILTER(WHERE gcc_name='Greater Sydney') AS sydney_locations,
    count(*) FILTER(WHERE gcc_name='Greater Sydney' AND charger_type='DC') AS sydney_dc,
    count(*) FILTER(WHERE gcc_name='Rest of NSW') AS rest_locations,
    count(*) FILTER(WHERE gcc_name='Rest of NSW' AND charger_type='DC') AS rest_dc FROM existing
), population AS (
  SELECT sum(resident_population) AS nsw_population,
    sum(resident_population) FILTER(WHERE sa4_code='106') AS hunter_population
  FROM gold.sa4_ev_summary
), operators AS (
  SELECT operator_standardised, count(*) AS locations FROM existing
  GROUP BY operator_standardised ORDER BY locations DESC, operator_standardised LIMIT 3
)
SELECT *, hunter_dc*1.0/hunter_locations AS hunter_dc_share,
  dc_locations*1.0/existing_locations AS nsw_dc_share,
  (hunter_dc*1.0/hunter_locations)/(dc_locations*1.0/existing_locations) AS hunter_relative_dc_share,
  sydney_dc*1.0/sydney_locations AS sydney_dc_share,
  rest_dc*1.0/rest_locations AS rest_dc_share,
  (sydney_dc*1.0/sydney_locations-rest_dc*1.0/rest_locations)*100 AS dc_gap_percentage_points,
  hunter_dc*10000.0/hunter_population AS hunter_dc_per_10000_residents,
  dc_locations*10000.0/nsw_population AS nsw_dc_per_10000_residents,
  (hunter_dc*1.0/hunter_population)/(dc_locations*1.0/nsw_population) AS hunter_relative_dc_per_capita,
  (SELECT sum(locations) FROM operators) AS top_three_locations,
  (SELECT sum(locations) FROM operators)*1.0/existing_locations AS top_three_share
FROM statewide CROSS JOIN hunter CROSS JOIN geography CROSS JOIN population;
