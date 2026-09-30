"""Reproducible acquisition, Silver, Gold and evidence entry point."""
import argparse
from pathlib import Path

from src.acquisition.population import acquire_population
from src.processing.sa4_population import build_population_silver
from src.database.build_database import build_database
from src.database.findings import export_findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--from-silver', action='store_true', help='Preserve the existing EV and boundary snapshot')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    data = root / 'data'
    ev = data / 'silver/ev/ev_charging_locations_silver.parquet'
    sa4 = data / 'silver/abs/nsw_sa4_silver.parquet'
    joined = data / 'silver/ev_sa4/ev_charging_locations_sa4_silver.parquet'
    if not args.from_silver:
        from src.acquisition.ev import acquire_ev_data
        from src.acquisition.abs import acquire_abs_data
        from src.processing.ev_cleaning import run_ev_silver_pipeline
        from src.processing.abs_sa4_processing import run_abs_silver_pipeline
        from src.processing.spatial_join import run_ev_sa4_pipeline
        csv, _ = acquire_ev_data(data / 'bronze/ev')
        boundaries = acquire_abs_data(data / 'bronze/abs')
        run_ev_silver_pipeline(csv, ev.parent)
        shapefiles = list(Path(boundaries['extract_dir']).rglob('*.shp'))
        if len(shapefiles) != 1:
            raise ValueError('Expected one ABS SA4 shapefile')
        run_abs_silver_pipeline(shapefiles[0], sa4)
        run_ev_sa4_pipeline(ev, sa4, joined)
    for path in (ev, sa4, joined):
        if not path.is_file():
            raise FileNotFoundError(path)
    workbook, correspondence = acquire_population(data / 'bronze/population')
    population = data / 'silver/population/sa4_population.parquet'
    build_population_silver(workbook, correspondence, sa4, population)
    database = data / 'database/nsw_ev.duckdb'
    result = build_database(database, ev, sa4, joined, data / 'gold', population)
    export_findings(root, database, joined, population)
    print(result)
    print('Analysis evidence exported to analysis/')


if __name__ == '__main__':
    main()
