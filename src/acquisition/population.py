"""Pinned ABS population and geography correspondence acquisition."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

POPULATION_URL = 'https://www.abs.gov.au/statistics/people/population/regional-population/2024-25/32180DS0003_2001-25.xlsx'
CORRESPONDENCE_URL = 'https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-4-july-2026-june-2031/access-and-downloads/correspondences/CG_SA4_2021_SA4_2026.csv'


def acquire_population(output_dir: Path) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for url in (POPULATION_URL, CORRESPONDENCE_URL):
        path = output_dir / url.rsplit('/', 1)[-1]
        metadata = path.with_suffix('.metadata.json')
        # Preserve a local snapshot only when its recorded checksum verifies.
        if path.exists() and metadata.exists():
            saved = json.loads(metadata.read_text(encoding='utf-8'))
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if saved.get('sha256') != digest or saved.get('source_url') != url:
                raise ValueError(f'Population download checksum/source mismatch: {path}')
        else:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            path.write_bytes(response.content)
            metadata.write_text(json.dumps({
                'publisher': 'Australian Bureau of Statistics',
                'source_url': url,
                'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
                'sha256': hashlib.sha256(response.content).hexdigest(),
                'reference_date': '2025-06-30' if path.suffix == '.xlsx' else None,
            }, indent=2) + '\n', encoding='utf-8')
        paths.append(path)
    return tuple(paths)
