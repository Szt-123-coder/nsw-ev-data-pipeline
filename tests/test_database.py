import duckdb
import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point, box

from src.database.build_database import (
    GOLD_TABLES,
    build_database,
    connect_database,
    create_gold_tables,
    create_schemas,
    create_silver_tables,
    enable_spatial,
    export_gold_tables,
    validate_database,
)


@pytest.fixture
def synthetic_silver_paths(tmp_path):
    """Create small synthetic Silver datasets for database tests."""

    ev_path = tmp_path / "ev_silver.parquet"
    sa4_path = tmp_path / "sa4_silver.parquet"
    ev_sa4_path = tmp_path / "ev_sa4_silver.parquet"

    # Basic EV Silver dataset.
    ev = pd.DataFrame(
        {
            "station_name": [
                "Station A",
                "Station B",
                "Station C",
            ]
        }
    )

    ev.to_parquet(
        ev_path,
        index=False,
    )

    # Two synthetic SA4 regions.
    sa4 = gpd.GeoDataFrame(
        {
            "SA4_CODE26": [
                "101",
                "102",
            ],
            "SA4_NAME26": [
                "Region A",
                "Region B",
            ],
            "GCC_CODE26": [
                "1GSYD",
                "1RNSW",
            ],
            "GCC_NAME26": [
                "Greater Sydney",
                "Rest of NSW",
            ],
            "STE_CODE26": [
                "1",
                "1",
            ],
            "STE_NAME26": [
                "New South Wales",
                "New South Wales",
            ],
            "AREASQKM26": [
                100.0,
                200.0,
            ],
        },
        geometry=[
            box(
                151.00,
                -34.00,
                151.01,
                -33.99,
            ),
            box(
                151.02,
                -34.00,
                151.03,
                -33.99,
            ),
        ],
        crs="EPSG:7844",
    )

    sa4.to_parquet(
        sa4_path,
        index=False,
    )

    # Spatially enriched EV Silver dataset.
    ev_sa4 = gpd.GeoDataFrame(
        {
            "station_name": [
                "Station A",
                "Station B",
                "Station C",
            ],
            "operator_standardised": [
                "Operator A",
                "Operator A",
                "Operator B",
            ],
            "charger_type": [
                "AC",
                "DC",
                None,
            ],
            "number_of_plugs": [
                2,
                4,
                3,
            ],
            "charger_power_kw": [
                22.0,
                150.0,
                50.0,
            ],
            "sa4_code": [
                "101",
                "101",
                "102",
            ],
            "sa4_name": [
                "Region A",
                "Region A",
                "Region B",
            ],
            "gcc_code": [
                "1GSYD",
                "1GSYD",
                "1RNSW",
            ],
            "gcc_name": [
                "Greater Sydney",
                "Greater Sydney",
                "Rest of NSW",
            ],
            "sa4_area_sqkm": [
                100.0,
                100.0,
                200.0,
            ],
            "sa4_match_method": [
                "within",
                "nearest_fallback",
                "within",
            ],
            "sa4_match_distance_m": [
                None,
                1.5,
                None,
            ],
        },
        geometry=[
            Point(151.005, -33.995),
            Point(151.006, -33.996),
            Point(151.025, -33.995),
        ],
        crs="EPSG:4326",
    )

    ev_sa4.to_parquet(
        ev_sa4_path,
        index=False,
    )

    return {
        "ev": ev_path,
        "sa4": sa4_path,
        "ev_sa4": ev_sa4_path,
    }


def prepare_database(tmp_path, synthetic_silver_paths):
    """Create a temporary DuckDB database with Silver and Gold tables."""

    database_path = tmp_path / "test.duckdb"

    con = connect_database(database_path)

    enable_spatial(con)
    create_schemas(con)

    create_silver_tables(
        con,
        synthetic_silver_paths["ev"],
        synthetic_silver_paths["sa4"],
        synthetic_silver_paths["ev_sa4"],
    )

    create_gold_tables(con)

    return con, database_path


def test_connect_database(tmp_path):
    database_path = tmp_path / "test.duckdb"

    con = connect_database(database_path)

    try:
        assert database_path.is_file()

        result = con.execute(
            "SELECT 1;"
        ).fetchone()[0]

        assert result == 1

    finally:
        con.close()


def test_enable_spatial():
    con = duckdb.connect(":memory:")

    try:
        enable_spatial(con)

        result = con.execute(
            """
            SELECT ST_AsText(
                ST_Point(151.2093, -33.8688)
            );
            """
        ).fetchone()[0]

        assert result.startswith("POINT")

    finally:
        con.close()


def test_create_schemas(tmp_path):
    database_path = tmp_path / "test.duckdb"

    con = connect_database(database_path)

    try:
        create_schemas(con)

        schemas = {
            row[0]
            for row in con.execute(
                """
                SELECT schema_name
                FROM information_schema.schemata;
                """
            ).fetchall()
        }

        assert "silver" in schemas
        assert "gold" in schemas

    finally:
        con.close()


def test_create_silver_tables(
    tmp_path,
    synthetic_silver_paths,
):
    database_path = tmp_path / "test.duckdb"

    con = connect_database(database_path)

    try:
        enable_spatial(con)
        create_schemas(con)

        create_silver_tables(
            con,
            synthetic_silver_paths["ev"],
            synthetic_silver_paths["sa4"],
            synthetic_silver_paths["ev_sa4"],
        )

        ev_count = con.execute(
            """
            SELECT COUNT(*)
            FROM silver.ev_locations;
            """
        ).fetchone()[0]

        sa4_count = con.execute(
            """
            SELECT COUNT(*)
            FROM silver.sa4_regions;
            """
        ).fetchone()[0]

        ev_sa4_count = con.execute(
            """
            SELECT COUNT(*)
            FROM silver.ev_locations_sa4;
            """
        ).fetchone()[0]

        assert ev_count == 3
        assert sa4_count == 2
        assert ev_sa4_count == 3

        schema = con.execute(
            """
            DESCRIBE silver.sa4_regions;
            """
        ).df()

        geometry_type = schema.loc[
            schema["column_name"] == "geometry",
            "column_type",
        ].iloc[0]

        assert "GEOMETRY" in geometry_type
        assert "7844" in geometry_type

    finally:
        con.close()


def test_create_gold_tables_and_validation(
    tmp_path,
    synthetic_silver_paths,
):
    con, _ = prepare_database(
        tmp_path,
        synthetic_silver_paths,
    )

    try:
        validation = validate_database(con)

        assert validation["ev_rows"] == 3
        assert validation["sa4_rows"] == 2
        assert validation["ev_sa4_rows"] == 3

        assert validation["gold_sa4_locations"] == 3
        assert validation["gold_gcc_locations"] == 3
        assert validation["gold_charger_type_locations"] == 3

        assert validation["fallback_count"] == 1

        table_counts = {}

        for table_name in GOLD_TABLES:
            table_counts[table_name] = con.execute(
                f"""
                SELECT COUNT(*)
                FROM gold.{table_name};
                """
            ).fetchone()[0]

        assert table_counts["sa4_ev_summary"] == 2
        assert table_counts["gcc_ev_summary"] == 2
        assert table_counts["operator_ev_summary"] == 2
        assert table_counts["charger_type_summary"] == 3

    finally:
        con.close()


def test_export_gold_tables(
    tmp_path,
    synthetic_silver_paths,
):
    con, _ = prepare_database(
        tmp_path,
        synthetic_silver_paths,
    )

    gold_dir = tmp_path / "gold"

    try:
        outputs = export_gold_tables(
            con,
            gold_dir,
        )

        assert set(outputs.keys()) == set(GOLD_TABLES)

        for table_name, output_path in outputs.items():
            assert output_path.is_file()
            assert output_path.stat().st_size > 0

            source_count = con.execute(
                f"""
                SELECT COUNT(*)
                FROM gold.{table_name};
                """
            ).fetchone()[0]

            exported_count = con.execute(
                f"""
                SELECT COUNT(*)
                FROM read_parquet(
                    '{output_path.as_posix()}'
                );
                """
            ).fetchone()[0]

            assert source_count == exported_count

    finally:
        con.close()


def test_build_database_end_to_end(
    tmp_path,
    synthetic_silver_paths,
):
    database_path = tmp_path / "database" / "test.duckdb"
    gold_dir = tmp_path / "gold"

    result = build_database(
        database_path,
        synthetic_silver_paths["ev"],
        synthetic_silver_paths["sa4"],
        synthetic_silver_paths["ev_sa4"],
        gold_dir,
    )

    assert database_path.is_file()

    assert result["validation"]["ev_rows"] == 3
    assert result["validation"]["sa4_rows"] == 2
    assert result["validation"]["ev_sa4_rows"] == 3
    assert result["validation"]["fallback_count"] == 1

    assert len(result["exports"]) == 4

    for output_path in result["exports"].values():
        assert output_path.is_file()


def test_create_silver_tables_rejects_missing_file(
    tmp_path,
    synthetic_silver_paths,
):
    database_path = tmp_path / "test.duckdb"

    con = connect_database(database_path)

    try:
        create_schemas(con)

        missing_path = tmp_path / "missing.parquet"

        with pytest.raises(
            FileNotFoundError,
            match="Silver file not found",
        ):
            create_silver_tables(
                con,
                synthetic_silver_paths["ev"],
                synthetic_silver_paths["sa4"],
                missing_path,
            )

    finally:
        con.close()