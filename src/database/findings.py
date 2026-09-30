"""Export auditable numerators, denominators, rates and input checksums."""
import hashlib
import json
import duckdb


def export_findings(root, database, ev_path, population_path):
    directory = root / 'analysis'
    directory.mkdir(exist_ok=True)
    with duckdb.connect(str(database), read_only=True) as con:
        findings = con.execute((directory / 'findings.sql').read_text(encoding='utf-8')).fetchdf().iloc[0].to_dict()
        operators = con.execute('''SELECT operator_standardised, count(*) AS existing_locations
            FROM silver.ev_locations_sa4 WHERE is_upcoming=false
            GROUP BY operator_standardised ORDER BY existing_locations DESC, operator_standardised LIMIT 3''').fetchdf().to_dict('records')
        density = con.execute('''SELECT sa4_code,sa4_name,gcc_name,resident_population,population_year,
            existing_charging_location_count,existing_dc_location_count,
            locations_per_10000_residents,dc_locations_per_10000_residents
            FROM gold.sa4_ev_summary ORDER BY sa4_code''').fetchdf()
        density.to_csv(directory / 'sa4_population_density.csv', index=False)
    provenance = json.loads(population_path.with_suffix('.metadata.json').read_text(encoding='utf-8'))
    provenance['bronze_inputs'] = [json.loads(p.read_text(encoding='utf-8'))
        for p in sorted((root / 'data/bronze/population').glob('*.metadata.json'))]
    inputs = {str(p.relative_to(root)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (ev_path, population_path, directory / 'findings.sql')}
    ev_downloads = [json.loads(p.read_text(encoding='utf-8'))
        for p in sorted((root / 'data/bronze/ev').glob('*.metadata.json'))]
    evidence = {'scope': 'Current Silver snapshot; is_upcoming=false; charging-location records',
                'findings': findings, 'top_three_operators': operators,
                'population_provenance': provenance, 'ev_bronze_provenance': ev_downloads,
                'input_sha256': inputs}
    (directory / 'findings.json').write_text(json.dumps(evidence, indent=2, allow_nan=False) + '\n', encoding='utf-8')
