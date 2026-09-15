from pathlib import Path

import duckdb


GOLD_TABLES = [
    "sa4_ev_summary",
    "gcc_ev_summary",
    "operator_ev_summary",
    "charger_type_summary",
]


def _sql_path(path: Path) -> str:
    """Convert a filesystem path into a SQL-safe POSIX path."""
    return Path(path).as_posix().replace("'", "''")


def connect_database(database_path: Path) -> duckdb.DuckDBPyConnection:
    """Create or open the persistent DuckDB database."""
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    return duckdb.connect(str(database_path))


def enable_spatial(con: duckdb.DuckDBPyConnection) -> None:
    """Load DuckDB Spatial, installing it only when required."""
    try:
        con.execute("LOAD spatial;")
    except duckdb.Error:
        con.execute("INSTALL spatial;")
        con.execute("LOAD spatial;")


def create_schemas(con: duckdb.DuckDBPyConnection) -> None:
    """Create Silver and Gold analytical schemas."""
    con.execute("CREATE SCHEMA IF NOT EXISTS silver;")
    con.execute("CREATE SCHEMA IF NOT EXISTS gold;")


def create_silver_tables(
    con: duckdb.DuckDBPyConnection,
    ev_silver_path: Path,
    sa4_silver_path: Path,
    ev_sa4_silver_path: Path,
) -> None:
    """Materialise validated Silver Parquet datasets in DuckDB."""
    paths = [
        ev_silver_path,
        sa4_silver_path,
        ev_sa4_silver_path,
    ]

    for path in paths:
        if not Path(path).is_file():
            raise FileNotFoundError(f"Silver file not found: {path}")

    ev_path = _sql_path(ev_silver_path)
    sa4_path = _sql_path(sa4_silver_path)
    ev_sa4_path = _sql_path(ev_sa4_silver_path)

    con.execute(
        f"""
        CREATE OR REPLACE TABLE silver.ev_locations AS
        SELECT *
        FROM read_parquet('{ev_path}');
        """
    )

    con.execute(
        f"""
        CREATE OR REPLACE TABLE silver.sa4_regions AS
        SELECT *
        FROM read_parquet('{sa4_path}');
        """
    )

    con.execute(
        f"""
        CREATE OR REPLACE TABLE silver.ev_locations_sa4 AS
        SELECT *
        FROM read_parquet('{ev_sa4_path}');
        """
    )


def create_gold_tables(con: duckdb.DuckDBPyConnection) -> None:
    """Build reusable Gold analytical tables."""

    con.execute(
        """
        CREATE OR REPLACE TABLE gold.sa4_ev_summary AS
        SELECT
            sa4_code,
            sa4_name,
            gcc_code,
            gcc_name,
            MAX(sa4_area_sqkm) AS sa4_area_sqkm,
            COUNT(*) AS charging_location_count,
            SUM(number_of_plugs) AS total_plug_count,
            ROUND(AVG(number_of_plugs), 2) AS avg_plugs_per_location,
            COUNT(DISTINCT operator_standardised) AS operator_count,
            ROUND(AVG(charger_power_kw), 2) AS avg_charger_power_kw,
            MAX(charger_power_kw) AS max_charger_power_kw,
            ROUND(
                COUNT(*) * 1000.0 / MAX(sa4_area_sqkm),
                2
            ) AS locations_per_1000_sqkm,
            SUM(
                CASE
                    WHEN sa4_match_method = 'nearest_fallback'
                    THEN 1
                    ELSE 0
                END
            ) AS fallback_location_count
        FROM silver.ev_locations_sa4
        GROUP BY
            sa4_code,
            sa4_name,
            gcc_code,
            gcc_name;
        """
    )

    con.execute(
        """
        CREATE OR REPLACE TABLE gold.gcc_ev_summary AS
        SELECT
            gcc_code,
            gcc_name,
            COUNT(*) AS charging_location_count,
            SUM(number_of_plugs) AS total_plug_count,
            ROUND(AVG(number_of_plugs), 2) AS avg_plugs_per_location,
            COUNT(DISTINCT operator_standardised) AS operator_count,
            ROUND(AVG(charger_power_kw), 2) AS avg_charger_power_kw,
            MAX(charger_power_kw) AS max_charger_power_kw,
            COUNT(DISTINCT sa4_code) AS sa4_count,
            SUM(
                CASE
                    WHEN sa4_match_method = 'nearest_fallback'
                    THEN 1
                    ELSE 0
                END
            ) AS fallback_location_count
        FROM silver.ev_locations_sa4
        GROUP BY
            gcc_code,
            gcc_name;
        """
    )

    con.execute(
        """
        CREATE OR REPLACE TABLE gold.operator_ev_summary AS
        SELECT
            operator_standardised AS operator_name,
            COUNT(*) AS charging_location_count,
            SUM(number_of_plugs) AS total_plug_count,
            ROUND(AVG(number_of_plugs), 2) AS avg_plugs_per_location,
            COUNT(DISTINCT sa4_code) AS sa4_coverage_count,
            COUNT(DISTINCT gcc_code) AS gcc_coverage_count,
            ROUND(AVG(charger_power_kw), 2) AS avg_charger_power_kw,
            MAX(charger_power_kw) AS max_charger_power_kw
        FROM silver.ev_locations_sa4
        WHERE operator_standardised IS NOT NULL
        GROUP BY operator_standardised;
        """
    )

    con.execute(
        """
        CREATE OR REPLACE TABLE gold.charger_type_summary AS
        SELECT
            COALESCE(charger_type, 'Unknown') AS charger_type,
            COUNT(*) AS charging_location_count,
            SUM(number_of_plugs) AS total_plug_count,
            ROUND(AVG(number_of_plugs), 2) AS avg_plugs_per_location,
            ROUND(AVG(charger_power_kw), 2) AS avg_charger_power_kw,
            MAX(charger_power_kw) AS max_charger_power_kw,
            COUNT(DISTINCT sa4_code) AS sa4_coverage_count
        FROM silver.ev_locations_sa4
        GROUP BY COALESCE(charger_type, 'Unknown');
        """
    )


def validate_database(con: duckdb.DuckDBPyConnection) -> dict:
    """Validate Silver-to-Gold database consistency."""
    result = con.execute(
        """
        SELECT
            (SELECT COUNT(*)
             FROM silver.ev_locations) AS ev_rows,

            (SELECT COUNT(*)
             FROM silver.sa4_regions) AS sa4_rows,

            (SELECT COUNT(*)
             FROM silver.ev_locations_sa4) AS ev_sa4_rows,

            (SELECT SUM(charging_location_count)
             FROM gold.sa4_ev_summary) AS gold_sa4_locations,

            (SELECT SUM(charging_location_count)
             FROM gold.gcc_ev_summary) AS gold_gcc_locations,

            (SELECT SUM(charging_location_count)
             FROM gold.charger_type_summary)
             AS gold_charger_type_locations,

            (SELECT SUM(fallback_location_count)
             FROM gold.sa4_ev_summary) AS fallback_count;
        """
    ).fetchone()

    validation = {
        "ev_rows": result[0],
        "sa4_rows": result[1],
        "ev_sa4_rows": result[2],
        "gold_sa4_locations": result[3],
        "gold_gcc_locations": result[4],
        "gold_charger_type_locations": result[5],
        "fallback_count": result[6],
    }

    if validation["ev_rows"] != validation["ev_sa4_rows"]:
        raise ValueError(
            "EV and EV-SA4 Silver row counts do not match."
        )

    expected = validation["ev_sa4_rows"]

    for key in [
        "gold_sa4_locations",
        "gold_gcc_locations",
        "gold_charger_type_locations",
    ]:
        if validation[key] != expected:
            raise ValueError(
                f"Gold reconciliation failed for {key}."
            )

    return validation


def export_gold_tables(
    con: duckdb.DuckDBPyConnection,
    gold_dir: Path,
) -> dict[str, Path]:
    """Export validated Gold tables as Parquet."""
    gold_dir = Path(gold_dir)
    gold_dir.mkdir(parents=True, exist_ok=True)

    outputs = {}

    for table_name in GOLD_TABLES:
        output_path = gold_dir / f"{table_name}.parquet"
        sql_path = _sql_path(output_path)

        con.execute(
            f"""
            COPY gold.{table_name}
            TO '{sql_path}'
            (FORMAT PARQUET);
            """
        )

        source_count = con.execute(
            f"SELECT COUNT(*) FROM gold.{table_name};"
        ).fetchone()[0]

        exported_count = con.execute(
            f"""
            SELECT COUNT(*)
            FROM read_parquet('{sql_path}');
            """
        ).fetchone()[0]

        if source_count != exported_count:
            raise ValueError(
                f"Gold export validation failed: {table_name}"
            )

        outputs[table_name] = output_path

    return outputs


def build_database(
    database_path: Path,
    ev_silver_path: Path,
    sa4_silver_path: Path,
    ev_sa4_silver_path: Path,
    gold_dir: Path,
) -> dict:
    """Run the complete Silver-to-Gold DuckDB pipeline."""
    con = connect_database(database_path)

    try:
        enable_spatial(con)
        create_schemas(con)

        create_silver_tables(
            con,
            ev_silver_path,
            sa4_silver_path,
            ev_sa4_silver_path,
        )

        create_gold_tables(con)

        validation = validate_database(con)

        exports = export_gold_tables(
            con,
            gold_dir,
        )

        return {
            "validation": validation,
            "exports": exports,
        }

    finally:
        con.close()