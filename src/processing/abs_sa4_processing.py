from pathlib import Path

import geopandas as gpd


NSW_STATE_CODE = "1"
EXPECTED_CRS_EPSG = 7844

SILVER_COLUMNS = [
    "SA4_CODE26",
    "SA4_NAME26",
    "GCC_CODE26",
    "GCC_NAME26",
    "STE_CODE26",
    "STE_NAME26",
    "AREASQKM26",
    "geometry",
]


def load_abs_sa4(path: Path) -> gpd.GeoDataFrame:
    """Load the ABS SA4 Bronze shapefile."""
    path = Path(path)

    if not path.is_file():
        raise FileNotFoundError(f"ABS SA4 shapefile not found: {path}")

    gdf = gpd.read_file(path)

    if gdf.empty:
        raise ValueError("ABS SA4 Bronze dataset is empty.")

    if gdf.crs is None:
        raise ValueError("ABS SA4 Bronze dataset has no CRS.")

    return gdf


def validate_bronze_schema(gdf: gpd.GeoDataFrame) -> None:
    """Check that required fields are present."""
    missing = set(SILVER_COLUMNS) - set(gdf.columns)

    if missing:
        raise ValueError(
            f"ABS Bronze dataset is missing required columns: {sorted(missing)}"
        )


def filter_nsw_sa4(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Select all NSW SA4 records."""
    nsw = gdf[gdf["STE_CODE26"] == NSW_STATE_CODE].copy()

    if nsw.empty:
        raise ValueError("No NSW SA4 records were found.")

    return nsw


def filter_spatial_regions(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Remove non-spatial statistical records."""
    spatial = gdf[
        gdf.geometry.notna()
        & ~gdf.geometry.is_empty
    ].copy()

    if spatial.empty:
        raise ValueError("No spatial SA4 regions remain after filtering.")

    return spatial


def validate_abs_silver(gdf: gpd.GeoDataFrame) -> None:
    """Validate schema, CRS, identifiers, attributes and geometries."""
    if gdf.empty:
        raise ValueError("ABS Silver dataset is empty.")

    if list(gdf.columns) != SILVER_COLUMNS:
        raise ValueError(
            "ABS Silver schema does not match the expected column order."
        )

    if gdf.crs is None:
        raise ValueError("ABS Silver dataset has no CRS.")

    if gdf.crs.to_epsg() != EXPECTED_CRS_EPSG:
        raise ValueError(
            f"Unexpected ABS Silver CRS: {gdf.crs}; "
            f"expected EPSG:{EXPECTED_CRS_EPSG}."
        )

    if gdf.isna().sum().sum() != 0:
        raise ValueError("ABS Silver dataset contains missing values.")

    if gdf.geometry.is_empty.any():
        raise ValueError("ABS Silver dataset contains empty geometries.")

    if not gdf.geometry.is_valid.all():
        raise ValueError("ABS Silver dataset contains invalid geometries.")

    if gdf["SA4_CODE26"].duplicated().any():
        raise ValueError("ABS Silver contains duplicate SA4 codes.")

    if gdf["SA4_NAME26"].duplicated().any():
        raise ValueError("ABS Silver contains duplicate SA4 names.")

    if (gdf["AREASQKM26"] <= 0).any():
        raise ValueError("ABS Silver contains non-positive SA4 areas.")


def build_abs_silver(
    nsw_spatial: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Build the selected NSW SA4 Silver schema."""
    missing = set(SILVER_COLUMNS) - set(nsw_spatial.columns)

    if missing:
        raise ValueError(
            f"Cannot build ABS Silver; missing columns: {sorted(missing)}"
        )

    silver = nsw_spatial[SILVER_COLUMNS].copy()

    validate_abs_silver(silver)

    return silver


def validate_round_trip(
    original: gpd.GeoDataFrame,
    loaded: gpd.GeoDataFrame,
) -> None:
    """Confirm that GeoParquet preserves the Silver dataset."""
    if original.shape != loaded.shape:
        raise ValueError("GeoParquet round trip changed dataset shape.")

    if original.columns.tolist() != loaded.columns.tolist():
        raise ValueError("GeoParquet round trip changed the schema.")

    if original.crs != loaded.crs:
        raise ValueError("GeoParquet round trip changed the CRS.")

    if original["SA4_CODE26"].tolist() != loaded["SA4_CODE26"].tolist():
        raise ValueError("GeoParquet round trip changed SA4 codes.")

    if (
        original.geometry.to_wkb().tolist()
        != loaded.geometry.to_wkb().tolist()
    ):
        raise ValueError("GeoParquet round trip changed geometries.")

    validate_abs_silver(loaded)


def write_abs_silver(
    gdf: gpd.GeoDataFrame,
    output_path: Path,
) -> Path:
    """Write ABS Silver as GeoParquet and validate the saved result."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    validate_abs_silver(gdf)

    gdf.to_parquet(
        output_path,
        index=False,
    )

    loaded = gpd.read_parquet(output_path)

    validate_round_trip(gdf, loaded)

    return output_path


def run_abs_silver_pipeline(
    bronze_path: Path,
    output_path: Path,
) -> gpd.GeoDataFrame:
    """Run the complete ABS Bronze-to-Silver processing pipeline."""
    bronze = load_abs_sa4(bronze_path)

    validate_bronze_schema(bronze)

    nsw = filter_nsw_sa4(bronze)

    nsw_spatial = filter_spatial_regions(nsw)

    silver = build_abs_silver(nsw_spatial)

    write_abs_silver(
        silver,
        output_path,
    )

    return silver