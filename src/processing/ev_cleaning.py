import re

from pathlib import Path

import pandas as pd


COLUMN_MAPPING = {
    "OBJECTID": "source_object_id",
    "Station_name": "station_name",
    "Station_address": "station_address",
    "Operator": "operator_raw",
    "Number_of_plugs": "number_of_plugs",
    "Charger_Type": "charger_type_raw",
    "Charger_rating": "charger_rating_raw",
    "Latitude": "latitude",
    "Longitude": "longitude",
    "LGANAME": "lga_name_raw",
    "PCODE": "postcode_raw",
    "Source": "source",
}


OPERATOR_ALIAS_MAP = {
    "Tesla Motors": "Tesla",
    "BP Australia": "BP",
    "NRMA Electric": "NRMA",
}

SILVER_COLUMNS = [
    # Source / lineage
    "source_object_id",
    "operator_raw",
    "charger_type_raw",
    "charger_rating_raw",
    "lga_name_raw",
    "postcode_raw",
    "source",

    # Clean analytical fields
    "station_name",
    "station_address",
    "operator",
    "operator_standardised",
    "number_of_plugs",
    "latitude",
    "longitude",
    "lga_name",
    "postcode",
    "charger_type",
    "is_upcoming",

    # Derived fields
    "address_postcode",
    "charger_power_kw",
    "charger_power_min_kw",
    "charger_power_max_kw",
    "coordinate_record_count",

    # Data-quality flags
    "address_needs_review",
    "postcode_conflict",
    "charger_rating_is_complex",
    "charger_rating_needs_review",
    "number_of_plugs_invalid",
    "number_of_plugs_high_outlier",
    "coordinate_invalid",
    "coordinate_direction_suspicious",
    "repeated_coordinate",
    "potential_duplicate",
]


def clean_text(series: pd.Series) -> pd.Series:
    return (
        series
        .astype("string")
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

def standardise_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    return df.rename(columns=COLUMN_MAPPING)

def clean_text_fields(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["station_name"] = clean_text(df["station_name"])
    df["station_address"] = clean_text(df["station_address"])
    df["source"] = clean_text(df["source"])

    df["operator"] = clean_text(df["operator_raw"])
    df["lga_name"] = clean_text(df["lga_name_raw"])

    df["station_address"] = (
        df["station_address"]
        .str.replace(r"^[,\s]+", "", regex=True)
        .str.replace(r"[,\s]+$", "", regex=True)
    )

    locality_only_pattern = r"^[A-Za-z .'-]+,\s*\d{4}$"

    df["address_needs_review"] = (
        df["station_address"]
        .str.fullmatch(
            locality_only_pattern,
            case=False,
            na=False,
        )
    )

    return df

def clean_postcode_fields(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    postcode_text = (
        df["postcode_raw"]
        .astype("string")
        .str.strip()
    )

    df["postcode"] = postcode_text.str.extract(
        r"(\d{4})",
        expand=False,
    )

    df["address_postcode"] = (
        df["station_address"]
        .str.extract(
            r"\b(\d{4})\b(?:,\s*Australia)?\s*$",
            expand=False,
        )
    )

    df["postcode_conflict"] = (
        df["postcode"].notna()
        & df["address_postcode"].notna()
        & (df["postcode"] != df["address_postcode"])
    )

    return df

def extract_power_range(value) -> pd.Series:
    if pd.isna(value):
        return pd.Series(
            [pd.NA, pd.NA],
            dtype="Float64",
        )

    powers = re.findall(
        r"(\d+(?:\.\d+)?)\s*kW",
        str(value),
        flags=re.IGNORECASE,
    )

    if not powers:
        return pd.Series(
            [pd.NA, pd.NA],
            dtype="Float64",
        )

    powers = [float(power) for power in powers]

    return pd.Series(
        [min(powers), max(powers)],
        dtype="Float64",
    )

def clean_charger_fields(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Charger type / status
    charger_type_text = (
        df["charger_type_raw"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    df["charger_type"] = charger_type_text.where(
        charger_type_text.isin(["AC", "DC"]),
        pd.NA,
    )

    df["is_upcoming"] = charger_type_text.eq("UPCOMING")

    # Charger rating / power
    rating_text = (
        df["charger_rating_raw"]
        .astype("string")
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    simple_power_text = rating_text.str.extract(
        r"(?i)^(\d+(?:\.\d+)?)\s*(?:kW)?$",
        expand=False,
    )

    df["charger_power_kw"] = pd.to_numeric(
        simple_power_text,
        errors="coerce",
    )

    df["charger_rating_is_complex"] = (
        rating_text.str.contains(
            r"\d+\s*x\s*\d+\s*kW",
            case=False,
            regex=True,
            na=False,
        )
    )

    complex_power_range = (
        df["charger_rating_raw"]
        .where(df["charger_rating_is_complex"])
        .apply(extract_power_range)
    )

    complex_power_range.columns = [
        "charger_power_min_kw",
        "charger_power_max_kw",
    ]

    df[
        [
            "charger_power_min_kw",
            "charger_power_max_kw",
        ]
    ] = complex_power_range

    df["charger_rating_needs_review"] = (
        df["charger_rating_raw"].notna()
        & df["charger_power_kw"].isna()
        & ~df["charger_rating_is_complex"]
    )

    return df

def clean_number_of_plugs(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    plug_numeric = pd.to_numeric(
        df["number_of_plugs"],
        errors="coerce",
    )

    df["number_of_plugs_invalid"] = (
        plug_numeric.isna()
        | (plug_numeric <= 0)
        | ((plug_numeric % 1) != 0)
    )

    # Keep only valid positive integer values in the cleaned field.
    df["number_of_plugs"] = (
        plug_numeric
        .where(~df["number_of_plugs_invalid"])
        .astype("Int64")
    )

    valid_plugs = df.loc[
        ~df["number_of_plugs_invalid"],
        "number_of_plugs",
    ].dropna()

    q1 = valid_plugs.quantile(0.25)
    q3 = valid_plugs.quantile(0.75)
    iqr = q3 - q1
    upper_fence = q3 + 1.5 * iqr

    df["number_of_plugs_high_outlier"] = (
        df["number_of_plugs"] > upper_fence
    ).fillna(False)

    return df

def clean_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    latitude_numeric = pd.to_numeric(
        df["latitude"],
        errors="coerce",
    )

    longitude_numeric = pd.to_numeric(
        df["longitude"],
        errors="coerce",
    )

    df["coordinate_invalid"] = (
        latitude_numeric.isna()
        | longitude_numeric.isna()
        | ~latitude_numeric.between(-90, 90)
        | ~longitude_numeric.between(-180, 180)
    )

    df["latitude"] = latitude_numeric
    df["longitude"] = longitude_numeric

    df["coordinate_direction_suspicious"] = (
        (df["latitude"] >= 0)
        | (df["longitude"] <= 0)
    ).fillna(False)

    return df

def flag_duplicate_locations(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    valid_coordinate_mask = (
        ~df["coordinate_invalid"]
        & df["latitude"].notna()
        & df["longitude"].notna()
    )

    df["coordinate_record_count"] = pd.Series(
        0,
        index=df.index,
        dtype="Int64",
    )

    coordinate_counts = (
        df.loc[valid_coordinate_mask]
        .groupby(["latitude", "longitude"])["latitude"]
        .transform("size")
        .astype("Int64")
    )

    df.loc[
        valid_coordinate_mask,
        "coordinate_record_count",
    ] = coordinate_counts

    df["repeated_coordinate"] = (
        df["coordinate_record_count"] > 1
    )

    duplicate_key = [
        "latitude",
        "longitude",
        "operator",
        "number_of_plugs",
        "charger_type",
        "charger_rating_raw",
    ]

    df["potential_duplicate"] = False

    duplicate_mask = (
        df.loc[valid_coordinate_mask]
        .duplicated(
            subset=duplicate_key,
            keep=False,
        )
    )

    df.loc[
        duplicate_mask.index,
        "potential_duplicate",
    ] = duplicate_mask

    return df

def standardise_operators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Normalise known case inconsistency.
    df["operator"] = df["operator"].replace(
        {
            "Non-Networked": "Non-networked",
        }
    )

    # Apply reviewed operator aliases.
    df["operator_standardised"] = (
        df["operator"]
        .replace(OPERATOR_ALIAS_MAP)
        .astype("string")
    )

    return df

def clean_ev_data(df: pd.DataFrame) -> pd.DataFrame:
    original_row_count = len(df)

    cleaned = standardise_columns(df)
    cleaned = clean_text_fields(cleaned)
    cleaned = clean_postcode_fields(cleaned)
    cleaned = clean_charger_fields(cleaned)
    cleaned = clean_number_of_plugs(cleaned)
    cleaned = clean_coordinates(cleaned)
    cleaned = flag_duplicate_locations(cleaned)
    cleaned = standardise_operators(cleaned)

    # Stabilise important output dtypes.
    cleaned["source_object_id"] = (
        pd.to_numeric(
            cleaned["source_object_id"],
            errors="coerce",
        )
        .astype("Int64")
    )

    cleaned["charger_power_min_kw"] = (
        pd.to_numeric(
            cleaned["charger_power_min_kw"],
            errors="coerce",
        )
        .astype("Float64")
    )

    cleaned["charger_power_max_kw"] = (
        pd.to_numeric(
            cleaned["charger_power_max_kw"],
            errors="coerce",
        )
        .astype("Float64")
    )

    # Cleaning should not silently remove records.
    if len(cleaned) != original_row_count:
        raise ValueError(
            "EV cleaning unexpectedly changed the row count."
        )

    return cleaned

def build_silver_dataset(df: pd.DataFrame) -> pd.DataFrame:
    missing_columns = [
        column
        for column in SILVER_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required Silver columns: {missing_columns}"
        )

    return df[SILVER_COLUMNS].copy()

def write_silver_data(
    df: pd.DataFrame,
    output_dir: str | Path,
) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    parquet_path = (
        output_dir
        / "ev_charging_locations_silver.parquet"
    )

    csv_path = (
        output_dir
        / "ev_charging_locations_silver.csv"
    )

    df.to_parquet(
        parquet_path,
        index=False,
    )

    df.to_csv(
        csv_path,
        index=False,
    )

    return parquet_path, csv_path

def run_ev_silver_pipeline(
    input_csv: str | Path,
    output_dir: str | Path,
) -> tuple[Path, Path]:
    input_csv = Path(input_csv)

    if not input_csv.exists():
        raise FileNotFoundError(
            f"EV Bronze file not found: {input_csv}"
        )

    raw = pd.read_csv(input_csv)

    cleaned = clean_ev_data(raw)
    silver = build_silver_dataset(cleaned)

    return write_silver_data(
        silver,
        output_dir,
    )