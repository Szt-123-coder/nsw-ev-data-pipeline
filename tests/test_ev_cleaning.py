import pandas as pd
import pytest

from src.processing.ev_cleaning import (
    SILVER_COLUMNS,
    standardise_columns,
    clean_text_fields,
    clean_postcode_fields,
    clean_charger_fields,
    clean_number_of_plugs,
    clean_coordinates,
    flag_duplicate_locations,
    standardise_operators,
    clean_ev_data,
    build_silver_dataset,
    write_silver_data,
    run_ev_silver_pipeline,
)


def test_standardise_columns():
    df = pd.DataFrame(
        {
            "OBJECTID": [1],
            "Station_name": ["Test Station"],
        }
    )

    result = standardise_columns(df)

    assert "source_object_id" in result.columns
    assert "station_name" in result.columns
    assert "OBJECTID" not in result.columns
    assert "Station_name" not in result.columns


def test_clean_text_fields():
    df = pd.DataFrame(
        {
            "station_name": ["  Test  Station "],
            "station_address": [", Muswellbrook, 2333 "],
            "source": [" Test  Source "],
            "operator_raw": [" Tesla  "],
            "lga_name_raw": [" Sydney "],
        }
    )

    result = clean_text_fields(df)

    assert result.loc[0, "station_name"] == "Test Station"
    assert result.loc[0, "station_address"] == "Muswellbrook, 2333"
    assert result.loc[0, "source"] == "Test Source"
    assert result.loc[0, "operator"] == "Tesla"
    assert result.loc[0, "lga_name"] == "Sydney"
    assert bool(result.loc[0, "address_needs_review"]) is True


def test_clean_postcode_fields():
    df = pd.DataFrame(
        {
            "postcode_raw": [
                "NSW 2500",
                "2000",
            ],
            "station_address": [
                "Wollongong NSW 2500",
                "Sydney NSW 2001",
            ],
        }
    )

    result = clean_postcode_fields(df)

    assert result.loc[0, "postcode"] == "2500"
    assert result.loc[0, "address_postcode"] == "2500"
    assert bool(result.loc[0, "postcode_conflict"]) is False

    assert result.loc[1, "postcode"] == "2000"
    assert result.loc[1, "address_postcode"] == "2001"
    assert bool(result.loc[1, "postcode_conflict"]) is True

def test_clean_charger_fields():
    df = pd.DataFrame(
        {
            "charger_type_raw": [
                "AC",
                "DC",
                "Upcoming",
            ],
            "charger_rating_raw": [
                "22 kW",
                "2x350kW & 2x175kW",
                "AC",
            ],
        }
    )

    result = clean_charger_fields(df)

    assert result.loc[0, "charger_type"] == "AC"
    assert result.loc[0, "charger_power_kw"] == 22
    assert bool(result.loc[0, "charger_rating_is_complex"]) is False

    assert result.loc[1, "charger_type"] == "DC"
    assert bool(result.loc[1, "charger_rating_is_complex"]) is True
    assert result.loc[1, "charger_power_min_kw"] == 175.0
    assert result.loc[1, "charger_power_max_kw"] == 350.0

    assert pd.isna(result.loc[2, "charger_type"])
    assert bool(result.loc[2, "is_upcoming"]) is True
    assert bool(result.loc[2, "charger_rating_needs_review"]) is True


def test_clean_number_of_plugs():
    df = pd.DataFrame(
        {
            "number_of_plugs": [
                1,
                2,
                4,
                20,
                0,
                -1,
                2.5,
                "unknown",
            ]
        }
    )

    result = clean_number_of_plugs(df)

    assert bool(result.loc[0, "number_of_plugs_invalid"]) is False
    assert result.loc[0, "number_of_plugs"] == 1

    assert bool(result.loc[3, "number_of_plugs_high_outlier"]) is True

    for index in [4, 5, 6, 7]:
        assert bool(result.loc[index, "number_of_plugs_invalid"]) is True
        assert pd.isna(result.loc[index, "number_of_plugs"])


def test_clean_coordinates():
    df = pd.DataFrame(
        {
            "latitude": [
                -33.86,
                120,
                -34.0,
                33.0,
                None,
            ],
            "longitude": [
                151.21,
                151.0,
                -151.0,
                151.0,
                150.0,
            ],
        }
    )

    result = clean_coordinates(df)

    assert bool(result.loc[0, "coordinate_invalid"]) is False
    assert bool(result.loc[0, "coordinate_direction_suspicious"]) is False

    assert bool(result.loc[1, "coordinate_invalid"]) is True

    assert bool(result.loc[2, "coordinate_direction_suspicious"]) is True
    assert bool(result.loc[3, "coordinate_direction_suspicious"]) is True

    assert bool(result.loc[4, "coordinate_invalid"]) is True


def test_flag_duplicate_locations():
    df = pd.DataFrame(
        {
            "latitude": [-33.0, -33.0, -33.0, -34.0],
            "longitude": [151.0, 151.0, 151.0, 150.0],
            "coordinate_invalid": [False, False, False, False],
            "operator": [
                "Tesla",
                "Tesla",
                "Chargefox",
                "NRMA",
            ],
            "number_of_plugs": [4, 4, 2, 6],
            "charger_type": ["DC", "DC", "AC", "DC"],
            "charger_rating_raw": [
                "250 kW",
                "250 kW",
                "22 kW",
                "150 kW",
            ],
        }
    )

    result = flag_duplicate_locations(df)

    assert result.loc[0, "coordinate_record_count"] == 3
    assert bool(result.loc[0, "repeated_coordinate"]) is True
    assert bool(result.loc[0, "potential_duplicate"]) is True

    assert result.loc[2, "coordinate_record_count"] == 3
    assert bool(result.loc[2, "repeated_coordinate"]) is True
    assert bool(result.loc[2, "potential_duplicate"]) is False

    assert result.loc[3, "coordinate_record_count"] == 1
    assert bool(result.loc[3, "repeated_coordinate"]) is False
    assert bool(result.loc[3, "potential_duplicate"]) is False


def test_standardise_operators():
    df = pd.DataFrame(
        {
            "operator": [
                "Non-Networked",
                "Tesla Motors",
                "BP Australia",
                "NRMA Electric",
                "Evie Networks",
            ]
        }
    )

    result = standardise_operators(df)

    assert result.loc[0, "operator"] == "Non-networked"
    assert result.loc[0, "operator_standardised"] == "Non-networked"

    assert result.loc[1, "operator_standardised"] == "Tesla"
    assert result.loc[2, "operator_standardised"] == "BP"
    assert result.loc[3, "operator_standardised"] == "NRMA"

    assert result.loc[4, "operator_standardised"] == "Evie Networks"

def test_clean_ev_data_integration():
    raw = pd.DataFrame(
        {
            "OBJECTID": [1, 2, 3],
            "Station_name": [
                " Station A ",
                "Station B",
                None,
            ],
            "Station_address": [
                "Sydney NSW 2000",
                "Wollongong NSW 2500",
                "Somewhere NSW 2001",
            ],
            "Operator": [
                " Tesla Motors ",
                "Chargefox",
                "Non-Networked",
            ],
            "Number_of_plugs": [4, 2, 6],
            "Charger_Type": [
                "DC",
                "AC",
                "Upcoming",
            ],
            "Charger_rating": [
                "250 kW",
                "22 kW",
                "AC",
            ],
            "Latitude": [
                -33.86,
                -34.42,
                -33.90,
            ],
            "Longitude": [
                151.21,
                150.89,
                151.15,
            ],
            "LGANAME": [
                "Sydney",
                "Wollongong",
                "Sydney",
            ],
            "PCODE": [
                "2000",
                "NSW 2500",
                "2001",
            ],
            "Source": [
                "Test",
                "Test",
                "Test",
            ],
        }
    )

    result = clean_ev_data(raw)

    assert len(result) == len(raw)
    assert result.shape[1] == 33

    assert result.loc[0, "station_name"] == "Station A"
    assert result.loc[0, "operator_standardised"] == "Tesla"

    assert result.loc[1, "postcode"] == "2500"
    assert result.loc[1, "charger_power_kw"] == 22

    assert bool(result.loc[2, "is_upcoming"]) is True
    assert pd.isna(result.loc[2, "charger_type"])

    assert result["coordinate_invalid"].sum() == 0


def test_build_silver_dataset():
    raw = pd.DataFrame(
        {
            "OBJECTID": [1],
            "Station_name": ["Station A"],
            "Station_address": ["Sydney NSW 2000"],
            "Operator": ["Tesla"],
            "Number_of_plugs": [4],
            "Charger_Type": ["DC"],
            "Charger_rating": ["250 kW"],
            "Latitude": [-33.86],
            "Longitude": [151.21],
            "LGANAME": ["Sydney"],
            "PCODE": ["2000"],
            "Source": ["Test"],
        }
    )

    cleaned = clean_ev_data(raw)
    silver = build_silver_dataset(cleaned)

    assert silver.columns.tolist() == SILVER_COLUMNS
    assert silver.shape == (1, 33)

def test_build_silver_dataset_rejects_missing_column():
    incomplete = pd.DataFrame(
        {
            "source_object_id": [1],
        }
    )

    with pytest.raises(
        ValueError,
        match="Missing required Silver columns",
    ):
        build_silver_dataset(incomplete)

def test_write_silver_data(tmp_path):
    raw = pd.DataFrame(
        {
            "OBJECTID": [1],
            "Station_name": ["Station A"],
            "Station_address": ["Sydney NSW 2000"],
            "Operator": ["Tesla"],
            "Number_of_plugs": [4],
            "Charger_Type": ["DC"],
            "Charger_rating": ["250 kW"],
            "Latitude": [-33.86],
            "Longitude": [151.21],
            "LGANAME": ["Sydney"],
            "PCODE": ["2000"],
            "Source": ["Test"],
        }
    )

    cleaned = clean_ev_data(raw)
    silver = build_silver_dataset(cleaned)

    parquet_path, csv_path = write_silver_data(
        silver,
        tmp_path,
    )

    assert parquet_path.exists()
    assert csv_path.exists()

    parquet_result = pd.read_parquet(parquet_path)
    csv_result = pd.read_csv(csv_path)

    assert parquet_result.shape == (1, 33)
    assert csv_result.shape == (1, 33)

def test_run_ev_silver_pipeline(tmp_path):
    raw = pd.DataFrame(
        {
            "OBJECTID": [1],
            "Station_name": [" Station A "],
            "Station_address": ["Sydney NSW 2000"],
            "Operator": ["Tesla Motors"],
            "Number_of_plugs": [4],
            "Charger_Type": ["DC"],
            "Charger_rating": ["250 kW"],
            "Latitude": [-33.86],
            "Longitude": [151.21],
            "LGANAME": ["Sydney"],
            "PCODE": ["2000"],
            "Source": ["Test"],
        }
    )

    input_csv = tmp_path / "bronze.csv"
    output_dir = tmp_path / "silver"

    raw.to_csv(
        input_csv,
        index=False,
    )

    parquet_path, csv_path = run_ev_silver_pipeline(
        input_csv,
        output_dir,
    )

    assert parquet_path.exists()
    assert csv_path.exists()

    result = pd.read_parquet(parquet_path)

    assert result.shape == (1, 33)
    assert result.loc[0, "station_name"] == "Station A"
    assert result.loc[0, "operator_standardised"] == "Tesla"