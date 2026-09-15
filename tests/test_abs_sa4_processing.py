from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import box

from src.processing.abs_sa4_processing import (
    SILVER_COLUMNS,
    build_abs_silver,
    filter_nsw_sa4,
    filter_spatial_regions,
    run_abs_silver_pipeline,
    validate_abs_silver,
    write_abs_silver,
)


@pytest.fixture
def sample_bronze_gdf():
    """Small synthetic ABS-like dataset for portable tests."""
    return gpd.GeoDataFrame(
        {
            "SA4_CODE26": ["101", "102", "199", "201"],
            "SA4_NAME26": [
                "Region A",
                "Region B",
                "No usual address (NSW)",
                "Region VIC",
            ],
            "GCC_CODE26": ["1RNSW", "1GSYD", "1RNSW", "2RVIC"],
            "GCC_NAME26": [
                "Rest of NSW",
                "Greater Sydney",
                "Rest of NSW",
                "Rest of Vic.",
            ],
            "STE_CODE26": ["1", "1", "1", "2"],
            "STE_NAME26": [
                "New South Wales",
                "New South Wales",
                "New South Wales",
                "Victoria",
            ],
            "AREASQKM26": [100.0, 200.0, 0.0, 300.0],
        },
        geometry=[
            box(149.0, -35.0, 150.0, -34.0),
            box(150.0, -34.0, 151.0, -33.0),
            None,
            box(144.0, -38.0, 145.0, -37.0),
        ],
        crs="EPSG:7844",
    )


def test_filter_nsw_sa4(sample_bronze_gdf):
    result = filter_nsw_sa4(sample_bronze_gdf)

    assert len(result) == 3
    assert (result["STE_CODE26"] == "1").all()


def test_filter_spatial_regions(sample_bronze_gdf):
    nsw = filter_nsw_sa4(sample_bronze_gdf)

    result = filter_spatial_regions(nsw)

    assert len(result) == 2
    assert result.geometry.notna().all()
    assert not result.geometry.is_empty.any()


def test_build_abs_silver(sample_bronze_gdf):
    nsw = filter_nsw_sa4(sample_bronze_gdf)
    spatial = filter_spatial_regions(nsw)

    result = build_abs_silver(spatial)

    assert result.shape == (2, 8)
    assert result.columns.tolist() == SILVER_COLUMNS
    assert result.crs.to_epsg() == 7844
    assert result.geometry.is_valid.all()


def test_build_abs_silver_rejects_missing_column(sample_bronze_gdf):
    nsw = filter_nsw_sa4(sample_bronze_gdf)
    spatial = filter_spatial_regions(nsw)

    broken = spatial.drop(columns=["GCC_NAME26"])

    with pytest.raises(ValueError, match="missing columns"):
        build_abs_silver(broken)


def test_validate_abs_silver_rejects_wrong_crs(sample_bronze_gdf):
    nsw = filter_nsw_sa4(sample_bronze_gdf)
    spatial = filter_spatial_regions(nsw)
    silver = spatial[SILVER_COLUMNS].copy()

    silver = silver.to_crs("EPSG:4326")

    with pytest.raises(ValueError, match="Unexpected ABS Silver CRS"):
        validate_abs_silver(silver)


def test_validate_abs_silver_rejects_duplicate_code(sample_bronze_gdf):
    nsw = filter_nsw_sa4(sample_bronze_gdf)
    spatial = filter_spatial_regions(nsw)
    silver = spatial[SILVER_COLUMNS].copy()

    silver.loc[silver.index[1], "SA4_CODE26"] = silver.iloc[0]["SA4_CODE26"]

    with pytest.raises(ValueError, match="duplicate SA4 codes"):
        validate_abs_silver(silver)


def test_write_abs_silver(sample_bronze_gdf, tmp_path):
    nsw = filter_nsw_sa4(sample_bronze_gdf)
    spatial = filter_spatial_regions(nsw)
    silver = build_abs_silver(spatial)

    output_path = tmp_path / "nsw_sa4_silver.parquet"

    result_path = write_abs_silver(
        silver,
        output_path,
    )

    assert result_path == output_path
    assert output_path.is_file()
    assert output_path.stat().st_size > 0

    loaded = gpd.read_parquet(output_path)

    assert loaded.shape == silver.shape
    assert loaded.columns.tolist() == SILVER_COLUMNS
    assert loaded.crs == silver.crs
    assert loaded.geometry.is_valid.all()


def test_run_abs_silver_pipeline(sample_bronze_gdf, tmp_path):
    bronze_dir = tmp_path / "bronze"
    bronze_dir.mkdir()

    bronze_path = bronze_dir / "SA4_2026_AUST_GDA2020.shp"
    output_path = tmp_path / "silver" / "nsw_sa4_silver.parquet"

    sample_bronze_gdf.to_file(
        bronze_path,
        driver="ESRI Shapefile",
    )

    result = run_abs_silver_pipeline(
        bronze_path,
        output_path,
    )

    assert result.shape == (2, 8)
    assert result.columns.tolist() == SILVER_COLUMNS
    assert result.crs.to_epsg() == 7844
    assert result.geometry.is_valid.all()

    assert output_path.is_file()

    loaded = gpd.read_parquet(output_path)

    assert loaded.shape == (2, 8)