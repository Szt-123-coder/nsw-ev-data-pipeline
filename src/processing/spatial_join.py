from pathlib import Path

import geopandas as gpd
import pandas as pd


EV_SOURCE_CRS = "EPSG:4326"
DISTANCE_CRS = "EPSG:9473"
DEFAULT_FALLBACK_MAX_DISTANCE_M = 10.0

SA4_JOIN_COLUMNS = [
    "SA4_CODE26",
    "SA4_NAME26",
    "GCC_CODE26",
    "GCC_NAME26",
    "AREASQKM26",
    "geometry",
]

FINAL_RENAME_MAP = {
    "SA4_CODE26": "sa4_code",
    "SA4_NAME26": "sa4_name",
    "GCC_CODE26": "gcc_code",
    "GCC_NAME26": "gcc_name",
    "AREASQKM26": "sa4_area_sqkm",
}


def load_ev_silver(path: Path) -> pd.DataFrame:
    """Load the cleaned EV Silver dataset."""
    path = Path(path)

    if not path.is_file():
        raise FileNotFoundError(f"EV Silver file not found: {path}")

    df = pd.read_parquet(path)

    if df.empty:
        raise ValueError("EV Silver dataset is empty.")

    return df


def load_sa4_silver(path: Path) -> gpd.GeoDataFrame:
    """Load the NSW SA4 Silver GeoParquet dataset."""
    path = Path(path)

    if not path.is_file():
        raise FileNotFoundError(f"ABS SA4 Silver file not found: {path}")

    gdf = gpd.read_parquet(path)

    if gdf.empty:
        raise ValueError("ABS SA4 Silver dataset is empty.")

    if gdf.crs is None:
        raise ValueError("ABS SA4 Silver dataset has no CRS.")

    return gdf


def create_ev_points(
    ev_df: pd.DataFrame,
) -> gpd.GeoDataFrame:
    """Convert EV longitude/latitude columns into point geometries."""
    required = {"latitude", "longitude"}
    missing = required - set(ev_df.columns)

    if missing:
        raise ValueError(
            f"EV Silver dataset is missing coordinate columns: {sorted(missing)}"
        )

    if ev_df[["latitude", "longitude"]].isna().any().any():
        raise ValueError("EV Silver dataset contains missing coordinates.")

    if not ev_df["latitude"].between(-90, 90).all():
        raise ValueError("EV Silver dataset contains invalid latitude values.")

    if not ev_df["longitude"].between(-180, 180).all():
        raise ValueError("EV Silver dataset contains invalid longitude values.")

    ev = ev_df.copy().reset_index(drop=True)

    points = gpd.GeoDataFrame(
        ev,
        geometry=gpd.points_from_xy(
            ev["longitude"],
            ev["latitude"],
        ),
        crs=EV_SOURCE_CRS,
    )

    if points.geometry.is_empty.any():
        raise ValueError("EV point dataset contains empty geometries.")

    return points


def align_ev_to_sa4_crs(
    ev_points: gpd.GeoDataFrame,
    sa4: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Transform EV points to the CRS used by the SA4 polygons."""
    if ev_points.crs is None:
        raise ValueError("EV point dataset has no CRS.")

    if sa4.crs is None:
        raise ValueError("SA4 dataset has no CRS.")

    return ev_points.to_crs(sa4.crs)


def spatial_join_within(
    ev_points: gpd.GeoDataFrame,
    sa4: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Assign EV locations to SA4 polygons using point-in-polygon matching."""
    missing = set(SA4_JOIN_COLUMNS) - set(sa4.columns)

    if missing:
        raise ValueError(
            f"SA4 dataset is missing join columns: {sorted(missing)}"
        )

    if ev_points.crs != sa4.crs:
        raise ValueError("EV and SA4 CRS values are not aligned.")

    joined = gpd.sjoin(
        ev_points,
        sa4[SA4_JOIN_COLUMNS],
        how="left",
        predicate="within",
    )

    if len(joined) != len(ev_points):
        raise ValueError(
            "Spatial join changed the number of EV records. "
            "Possible overlapping SA4 polygons detected."
        )

    joined["sa4_match_method"] = pd.Series(
        pd.NA,
        index=joined.index,
        dtype="string",
    )

    matched = joined["SA4_CODE26"].notna()

    joined.loc[
        matched,
        "sa4_match_method",
    ] = "within"

    joined["sa4_match_distance_m"] = pd.Series(
        pd.NA,
        index=joined.index,
        dtype="Float64",
    )

    return joined


def apply_nearest_fallback(
    joined: gpd.GeoDataFrame,
    sa4: gpd.GeoDataFrame,
    max_distance_m: float = DEFAULT_FALLBACK_MAX_DISTANCE_M,
) -> gpd.GeoDataFrame:
    """Assign unmatched EV points to a nearby SA4 within a controlled tolerance."""
    result = joined.copy()

    unmatched_mask = result["SA4_CODE26"].isna()

    if not unmatched_mask.any():
        return result

    unmatched = result.loc[
        unmatched_mask,
        ["geometry"],
    ].copy()

    unmatched = gpd.GeoDataFrame(
        unmatched,
        geometry="geometry",
        crs=result.crs,
    )

    unmatched_projected = unmatched.to_crs(DISTANCE_CRS)
    sa4_projected = sa4.to_crs(DISTANCE_CRS)

    nearest = gpd.sjoin_nearest(
        unmatched_projected,
        sa4_projected[SA4_JOIN_COLUMNS],
        how="left",
        max_distance=max_distance_m,
        distance_col="distance_to_sa4_m",
    )

    if nearest.index.duplicated().any():
        raise ValueError(
            "Nearest-SA4 fallback produced multiple equally near matches."
        )

    fallback = nearest[
        nearest["SA4_CODE26"].notna()
    ].copy()

    if fallback.empty:
        return result

    fallback_columns = [
        "SA4_CODE26",
        "SA4_NAME26",
        "GCC_CODE26",
        "GCC_NAME26",
        "AREASQKM26",
    ]

    for column in fallback_columns:
        result.loc[
            fallback.index,
            column,
        ] = fallback[column]

    result.loc[
        fallback.index,
        "sa4_match_method",
    ] = "nearest_fallback"

    result.loc[
        fallback.index,
        "sa4_match_distance_m",
    ] = fallback["distance_to_sa4_m"]

    return result


def finalise_ev_sa4_silver(
    joined: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Prepare the enriched EV-SA4 dataset for Silver-layer persistence."""
    result = joined.copy()

    if "index_right" in result.columns:
        result = result.drop(columns=["index_right"])

    result = result.rename(
        columns=FINAL_RENAME_MAP,
    )

    result = result.to_crs(EV_SOURCE_CRS)

    validate_ev_sa4_silver(result)

    return result


def validate_ev_sa4_silver(
    gdf: gpd.GeoDataFrame,
) -> None:
    """Validate the final enriched EV-SA4 Silver dataset."""
    if gdf.empty:
        raise ValueError("EV-SA4 Silver dataset is empty.")

    required = {
        "sa4_code",
        "sa4_name",
        "gcc_code",
        "gcc_name",
        "sa4_area_sqkm",
        "sa4_match_method",
        "sa4_match_distance_m",
        "geometry",
    }

    missing = required - set(gdf.columns)

    if missing:
        raise ValueError(
            f"EV-SA4 Silver dataset is missing columns: {sorted(missing)}"
        )

    for column in [
        "sa4_code",
        "sa4_name",
        "gcc_code",
        "gcc_name",
        "sa4_area_sqkm",
        "sa4_match_method",
    ]:
        if gdf[column].isna().any():
            raise ValueError(
                f"EV-SA4 Silver contains missing values in {column}."
            )

    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        raise ValueError(
            "EV-SA4 Silver must use EPSG:4326."
        )

    if gdf.geometry.isna().any():
        raise ValueError("EV-SA4 Silver contains missing geometries.")

    if gdf.geometry.is_empty.any():
        raise ValueError("EV-SA4 Silver contains empty geometries.")

    if not gdf.geometry.is_valid.all():
        raise ValueError("EV-SA4 Silver contains invalid geometries.")

    if not (gdf.geom_type == "Point").all():
        raise ValueError("EV-SA4 Silver must contain Point geometries.")

    valid_methods = {
        "within",
        "nearest_fallback",
    }

    actual_methods = set(
        gdf["sa4_match_method"].dropna().unique()
    )

    if not actual_methods.issubset(valid_methods):
        raise ValueError(
            f"Unexpected SA4 match methods: {actual_methods}"
        )

    fallback_mask = (
        gdf["sa4_match_method"] == "nearest_fallback"
    )

    if fallback_mask.any():
        if (
            gdf.loc[
                fallback_mask,
                "sa4_match_distance_m",
            ]
            .isna()
            .any()
        ):
            raise ValueError(
                "Nearest fallback records must contain a match distance."
            )


def write_ev_sa4_silver(
    gdf: gpd.GeoDataFrame,
    output_path: Path,
) -> Path:
    """Write enriched EV-SA4 Silver GeoParquet and validate round trip."""
    output_path = Path(output_path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    validate_ev_sa4_silver(gdf)

    gdf.to_parquet(
        output_path,
        index=False,
    )

    loaded = gpd.read_parquet(output_path)

    if loaded.shape != gdf.shape:
        raise ValueError(
            "GeoParquet round trip changed dataset shape."
        )

    if loaded.columns.tolist() != gdf.columns.tolist():
        raise ValueError(
            "GeoParquet round trip changed dataset schema."
        )

    if loaded.crs != gdf.crs:
        raise ValueError(
            "GeoParquet round trip changed dataset CRS."
        )

    if (
        loaded.geometry.to_wkb().tolist()
        != gdf.geometry.to_wkb().tolist()
    ):
        raise ValueError(
            "GeoParquet round trip changed point geometries."
        )

    validate_ev_sa4_silver(loaded)

    return output_path


def run_ev_sa4_pipeline(
    ev_silver_path: Path,
    sa4_silver_path: Path,
    output_path: Path,
    fallback_max_distance_m: float = DEFAULT_FALLBACK_MAX_DISTANCE_M,
) -> gpd.GeoDataFrame:
    """Run the complete EV-SA4 spatial enrichment pipeline."""
    ev = load_ev_silver(ev_silver_path)
    sa4 = load_sa4_silver(sa4_silver_path)

    ev_points = create_ev_points(ev)

    ev_aligned = align_ev_to_sa4_crs(
        ev_points,
        sa4,
    )

    joined = spatial_join_within(
        ev_aligned,
        sa4,
    )

    joined = apply_nearest_fallback(
        joined,
        sa4,
        max_distance_m=fallback_max_distance_m,
    )

    final = finalise_ev_sa4_silver(joined)

    write_ev_sa4_silver(
        final,
        output_path,
    )

    return final