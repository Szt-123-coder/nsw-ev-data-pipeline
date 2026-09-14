import requests
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

BASE_URL = "https://opendata.transport.nsw.gov.au/data"
DATASET_ID = "be1c4de4-4517-4bd0-8a09-2965ddfc7179"

def get_dataset_metadata(base_url=BASE_URL, dataset_id=DATASET_ID):
    endpoint = f"{base_url}/api/3/action/package_show"

    response = requests.get(
        endpoint, 
        params={"id": dataset_id},
        timeout=30,
        )

    response.raise_for_status()

    data = response.json()
    if not data.get("success"):
        raise ValueError("CKAN package_show request was not successful.")

    return data.get("result")

def select_current_csv_resource(resources):
    for resource in resources:
        if (
            resource.get("format", "").lower() == "csv"
        and "not updated" not in resource.get("name", "").lower()
        ):
            return resource
    raise ValueError("No CSV resource found in the dataset resources.")

def get_resource_metadata(resource_id, base_url=BASE_URL):
    endpoint = f"{base_url}/api/3/action/resource_show"

    response = requests.get(
        endpoint, 
        params={"id": resource_id},
        timeout=30,
        )

    response.raise_for_status()

    data = response.json()
    if not data.get("success"):
        raise ValueError("CKAN resource_show request was not successful.")

    return data.get("result")

def download_resource(resource_metadata, output_dir):
    download_url = resource_metadata.get("url", "").strip()
    if not download_url:
        raise ValueError("Resource metadata does not contain a valid download URL.")

    filename = Path(urlparse(download_url).path).name

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = Path(output_dir) / filename

    with requests.get(
        download_url,
        stream=True,
        timeout=60,
        ) as response:
        response.raise_for_status()

        content_type = response.headers.get("Content-Type")
        with output_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    return output_path, content_type

def calculate_sha256(file_path):
    file_path = Path(file_path)

    sha256_hash = hashlib.sha256()

    with file_path.open("rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def build_provenance(
    dataset_metadata,
    resource_metadata,
    file_path,
    file_hash,
    http_content_type=None,
):
    file_path = Path(file_path)

    retrieved_at = datetime.now(timezone.utc).isoformat()

    provenance = {
        "dataset_id": dataset_metadata["id"],
        "dataset_title": dataset_metadata["title"],
        "resource_id": resource_metadata["id"],
        "resource_name": resource_metadata["name"],
        "resource_format": resource_metadata["format"],
        "resource_description": resource_metadata.get("description"),
        "resource_last_modified": resource_metadata.get("last_modified"),
        "source_url": resource_metadata["url"].strip(),
        "retrieved_at_utc": retrieved_at,
        "local_filename": file_path.name,
        "file_size_bytes": file_path.stat().st_size,
        "sha256": file_hash,
        "http_content_type": http_content_type,
    }

    return provenance

def save_provenance(provenance, file_path):
    file_path = Path(file_path)

    metadata_path = file_path.with_suffix(".metadata.json")

    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(
            provenance,
            f,
            indent=2,
            ensure_ascii=False,
        )

    return metadata_path

def acquire_ev_data(output_dir):
    dataset_metadata = get_dataset_metadata()
    resource_metadata = select_current_csv_resource(dataset_metadata["resources"])
    resource_details = get_resource_metadata(resource_metadata["id"])
    downloaded_file_path, content_type = download_resource(resource_details, output_dir)
    file_hash = calculate_sha256(downloaded_file_path)
    provenance = build_provenance(
        dataset_metadata,
        resource_details,
        downloaded_file_path,
        file_hash,
        http_content_type=content_type,
    )
    metadata_file_path = save_provenance(provenance, downloaded_file_path)

    return downloaded_file_path, metadata_file_path
