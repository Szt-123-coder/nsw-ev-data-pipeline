import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests


ABS_LANDING_PAGE = (
    "https://www.abs.gov.au/statistics/standards/"
    "australian-statistical-geography-standard-asgs/"
    "edition-4-july-2026-june-2031/"
    "access-and-downloads/digital-boundary-files"
)

ABS_RESOURCE_URL = (
    ABS_LANDING_PAGE
    + "/SA4_2026_AUST_SHP_GDA2020.zip"
)

def download_abs_resource(output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = Path(urlparse(ABS_RESOURCE_URL).path).name
    output_path = output_dir / filename

    with requests.get(
        ABS_RESOURCE_URL, 
        stream=True, 
        timeout=30
        ) as response:

        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").lower()

        with output_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    return output_path, content_type

def validate_zip(file_path):
    file_path = Path(file_path)
    return zipfile.is_zipfile(file_path)

def extract_abs_archive(archive_path, output_dir):
    archive_path = Path(archive_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)

    return output_dir

def validate_shapefile_components(extract_dir):
    extract_dir = Path(extract_dir)

    base_name = "SA4_2026_AUST_GDA2020"

    required_files = [
        extract_dir / f"{base_name}.shp",
        extract_dir / f"{base_name}.shx",
        extract_dir / f"{base_name}.dbf",
        extract_dir / f"{base_name}.prj",
    ]

    return all(file_path.is_file() for file_path in required_files)

def calculate_sha256(file_path):
    file_path = Path(file_path)

    sha256_hash = hashlib.sha256()

    with file_path.open("rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()

def build_provenance(
    archive_path,
    file_hash,
    content_type,
    archive_valid,
    shapefile_components_valid,
):
    archive_path = Path(archive_path)

    retrieved_at_utc = datetime.now(timezone.utc).isoformat()

    provenance = {
        "dataset_title": "Statistical Areas Level 4 (SA4) - 2026",
        "publisher": "Australian Bureau of Statistics",
        "edition": "ASGS Edition 4",
        "geography_level": "SA4",
        "reference_year": 2026,
        "coordinate_system": "GDA2020",
        "landing_page": ABS_LANDING_PAGE,
        "source_url": ABS_RESOURCE_URL,
        "retrieved_at_utc": retrieved_at_utc,
        "local_filename": archive_path.name,
        "file_size_bytes": archive_path.stat().st_size,
        "sha256": file_hash,
        "http_content_type": content_type,
        "archive_valid": archive_valid,
        "required_shapefile_components_present": shapefile_components_valid,
    }

    return provenance

def save_provenance(provenance, archive_path):
    archive_path = Path(archive_path)

    metadata_path = archive_path.with_suffix(
        ".metadata.json"
    )

    with metadata_path.open(
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            provenance,
            f,
            indent=2,
            ensure_ascii=False
        )

    return metadata_path

def acquire_abs_data(output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Download the ABS archive
    archive_path, content_type = download_abs_resource(output_dir)

    # 2. Validate the downloaded ZIP archive
    archive_valid = validate_zip(archive_path)

    if not archive_valid:
        raise ValueError(
            f"Downloaded file is not a valid ZIP archive: {archive_path}"
        )

    # 3. Define the extraction directory
    extract_dir = output_dir / "SA4_2026_AUST_GDA2020"

    # 4. Extract the archive
    extract_abs_archive(
        archive_path,
        extract_dir
    )

    # 5. Validate required Shapefile components
    shapefile_components_valid = validate_shapefile_components(
        extract_dir
    )

    if not shapefile_components_valid:
        raise ValueError(
            f"Required Shapefile components are missing from: {extract_dir}"
        )

    # 6. Calculate SHA-256 checksum
    file_hash = calculate_sha256(
        archive_path
    )

    # 7. Build provenance metadata
    provenance = build_provenance(
        archive_path,
        file_hash,
        content_type,
        archive_valid,
        shapefile_components_valid,
    )

    # 8. Save provenance metadata
    metadata_path = save_provenance(
        provenance,
        archive_path
    )

    # 9. Return pipeline outputs
    return {
        "archive_path": archive_path,
        "extract_dir": extract_dir,
        "metadata_path": metadata_path,
        "archive_valid": archive_valid,
        "shapefile_components_valid": shapefile_components_valid,
    }