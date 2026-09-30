"""Enrich Gold without changing existing summary column meanings."""
from pathlib import Path


def add_population_metrics(con, population_path: Path):
    path = Path(population_path).as_posix().replace("'", "''")
    con.execute(f"CREATE OR REPLACE TABLE silver.sa4_population AS SELECT * FROM read_parquet('{path}')")
    bad = con.execute('''SELECT count(*) FROM gold.sa4_ev_summary g
        LEFT JOIN silver.sa4_population p USING(sa4_code)
        WHERE p.resident_population IS NULL OR p.resident_population <= 0''').fetchone()[0]
    duplicate = con.execute('SELECT count(*)-count(DISTINCT sa4_code) FROM silver.sa4_population').fetchone()[0]
    if bad or duplicate:
        raise ValueError('Population join must be complete and unique')
    con.execute('''CREATE OR REPLACE TABLE gold.sa4_ev_summary AS
        WITH status AS (
          SELECT sa4_code,
            count(*) FILTER(WHERE is_upcoming=false) AS existing_charging_location_count,
            count(*) FILTER(WHERE is_upcoming=false AND charger_type='DC') AS existing_dc_location_count
          FROM silver.ev_locations_sa4 GROUP BY sa4_code
        )
        SELECT g.*, p.resident_population, p.population_year,
          p.population_reference_date, p.population_geography,
          s.existing_charging_location_count, s.existing_dc_location_count,
          s.existing_charging_location_count*10000.0/p.resident_population AS locations_per_10000_residents,
          s.existing_dc_location_count*10000.0/p.resident_population AS dc_locations_per_10000_residents
        FROM gold.sa4_ev_summary g
        JOIN silver.sa4_population p USING(sa4_code)
        JOIN status s USING(sa4_code)''')
