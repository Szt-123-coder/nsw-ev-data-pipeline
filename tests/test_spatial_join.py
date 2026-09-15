import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

from src.processing.spatial_join import (
    DEFAULT_FALLBACK_MAX_DISTANCE_M,
    FINAL_RENAME_MAP,
    align_ev_to_sa4_crs,
    apply_nearest_fallback,
    create_ev_points,
    finalise_ev_sa4_silver,
    run_ev_sa4_pipeline,
    spatial_join_within,
    write_ev_sa4_silver,
)


@pytest.fixture
def sample_ev_df():
    """
    Three synthetic EV locations:
    - EV A: inside SA4 A
    - EV B: inside SA4 B
    - EV C: approximately 2 metres outside SA4 A
    """
    return pd.DataFrame(
        {
            "station_name": [
                "EV A",
                "EV B",
                "EV C",
            ],
            "latitude": [
                -33.995,
                -33.995,
                -33.995,
            ],
            "longitude": [
                151.005,
                151.025,
                151.01002,
            ],
        }
    )


@pytest.fixture
def sample_sa4_gdf():
    """Small synthetic SA4 polygon dataset around Sydney."""
    return gpd.GeoDataFrame(
        {
            "SA4_CODE26": [
                "101",
                "102",
            ],
            "SA4_NAME26": [
                "Synthetic SA4 A",
                "Synthetic SA4 B",
            ],
            "GCC_CODE26": [
                "1GSYD",
                "1GSYD",
            ],
            "GCC_NAME26": [
                "Greater Sydney",
                "Greater Sydney",
            ],
            "AREASQKM26": [
                100.0,
                200.0,
            ],
        },
        geometry=[
            box(
                151.0000,
                -34.0000,
                151.0100,
                -33.9900,
            ),
            box(
                151.0200,
                -34.0000,
                151.0300,
                -33.9900,
            ),
        ],
        crs="EPSG:7844",
    )


def test_create_ev_points(sample_ev_df):
    result = create_ev_points(sample_ev_df)

    assert isinstance(result, gpd.GeoDataFrame)
    assert len(result) == 3
    assert result.crs.to_epsg() == 4326
    assert result.geometry.notna().all()
    assert (result.geom_type == "Point").all()


def test_create_ev_points_rejects_missing_coordinate(sample_ev_df):
    broken = sample_ev_df.copy()
    broken.loc[0, "latitude"] = None

    with pytest.raises(
        ValueError,
        match="missing coordinates",
    ):
        create_ev_points(broken)


def test_align_ev_to_sa4_crs(
    sample_ev_df,
    sample_sa4_gdf,
):
    ev_points = create_ev_points(sample_ev_df)

    result = align_ev_to_sa4_crs(
        ev_points,
        sample_sa4_gdf,
    )

    assert result.crs == sample_sa4_gdf.crs
    assert result.crs.to_epsg() == 7844


def test_spatial_join_within(
    sample_ev_df,
    sample_sa4_gdf,
):
    ev_points = create_ev_points(sample_ev_df)

    ev_aligned = align_ev_to_sa4_crs(
        ev_points,
        sample_sa4_gdf,
    )

    result = spatial_join_within(
        ev_aligned,
        sample_sa4_gdf,
    )

    assert len(result) == 3

    assert result["SA4_CODE26"].notna().sum() == 2
    assert result["SA4_CODE26"].isna().sum() == 1

    assert (
        result["sa4_match_method"]
        .value_counts()
        .to_dict()
        == {
            "within": 2,
        }
    )


def test_apply_nearest_fallback(
    sample_ev_df,
    sample_sa4_gdf,
):
    ev_points = create_ev_points(sample_ev_df)

    ev_aligned = align_ev_to_sa4_crs(
        ev_points,
        sample_sa4_gdf,
    )

    joined = spatial_join_within(
        ev_aligned,
        sample_sa4_gdf,
    )

    result = apply_nearest_fallback(
        joined,
        sample_sa4_gdf,
        max_distance_m=DEFAULT_FALLBACK_MAX_DISTANCE_M,
    )

    assert result["SA4_CODE26"].notna().all()

    counts = (
        result["sa4_match_method"]
        .value_counts()
        .to_dict()
    )

    assert counts == {
        "within": 2,
        "nearest_fallback": 1,
    }

    fallback = result[
        result["sa4_match_method"]
        == "nearest_fallback"
    ]

    assert len(fallback) == 1

    assert (
        fallback["sa4_match_distance_m"].iloc[0]
        <= DEFAULT_FALLBACK_MAX_DISTANCE_M
    )

    assert (
        fallback["SA4_CODE26"].iloc[0]
        == "101"
    )


def test_nearest_fallback_respects_distance_limit(
    sample_ev_df,
    sample_sa4_gdf,
):
    ev_points = create_ev_points(sample_ev_df)

    ev_aligned = align_ev_to_sa4_crs(
        ev_points,
        sample_sa4_gdf,
    )

    joined = spatial_join_within(
        ev_aligned,
        sample_sa4_gdf,
    )

    result = apply_nearest_fallback(
        joined,
        sample_sa4_gdf,
        max_distance_m=0.1,
    )

    assert result["SA4_CODE26"].isna().sum() == 1


def test_finalise_ev_sa4_silver(
    sample_ev_df,
    sample_sa4_gdf,
):
    ev_points = create_ev_points(sample_ev_df)

    ev_aligned = align_ev_to_sa4_crs(
        ev_points,
        sample_sa4_gdf,
    )

    joined = spatial_join_within(
        ev_aligned,
        sample_sa4_gdf,
    )

    joined = apply_nearest_fallback(
        joined,
        sample_sa4_gdf,
    )

    result = finalise_ev_sa4_silver(joined)

    assert len(result) == 3
    assert result.crs.to_epsg() == 4326

    assert "index_right" not in result.columns

    for final_name in FINAL_RENAME_MAP.values():
        assert final_name in result.columns

    assert result["sa4_code"].notna().all()
    assert result["sa4_name"].notna().all()

    assert (
        result["sa4_match_method"]
        .value_counts()
        .to_dict()
        == {
            "within": 2,
            "nearest_fallback": 1,
        }
    )


def test_write_ev_sa4_silver(
    sample_ev_df,
    sample_sa4_gdf,
    tmp_path,
):
    ev_points = create_ev_points(sample_ev_df)

    ev_aligned = align_ev_to_sa4_crs(
        ev_points,
        sample_sa4_gdf,
    )

    joined = spatial_join_within(
        ev_aligned,
        sample_sa4_gdf,
    )

    joined = apply_nearest_fallback(
        joined,
        sample_sa4_gdf,
    )

    final = finalise_ev_sa4_silver(joined)

    output_path = (
        tmp_path
        / "ev_sa4_silver.parquet"
    )

    result_path = write_ev_sa4_silver(
        final,
        output_path,
    )

    assert result_path == output_path
    assert output_path.is_file()
    assert output_path.stat().st_size > 0

    loaded = gpd.read_parquet(output_path)

    assert loaded.shape == final.shape
    assert loaded.crs == final.crs

    assert (
        loaded["sa4_code"].tolist()
        == final["sa4_code"].tolist()
    )


def test_run_ev_sa4_pipeline(
    sample_ev_df,
    sample_sa4_gdf,
    tmp_path,
):
    ev_path = tmp_path / "ev_silver.parquet"
    sa4_path = tmp_path / "sa4_silver.parquet"

    output_path = (
        tmp_path
        / "output"
        / "ev_sa4_silver.parquet"
    )

    sample_ev_df.to_parquet(
        ev_path,
        index=False,
    )

    sample_sa4_gdf.to_parquet(
        sa4_path,
        index=False,
    )

    result = run_ev_sa4_pipeline(
        ev_path,
        sa4_path,
        output_path,
    )

    assert len(result) == 3
    assert result.crs.to_epsg() == 4326

    assert result["sa4_code"].notna().all()

    assert (
        result["sa4_match_method"]
        .value_counts()
        .to_dict()
        == {
            "within": 2,
            "nearest_fallback": 1,
        }
    )

    assert output_path.is_file()

    loaded = gpd.read_parquet(output_path)

    assert len(loaded) == 3
    assert loaded["sa4_code"].notna().all()