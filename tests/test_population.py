import duckdb
import pandas as pd
import pytest

from src.processing.sa4_population import validate_population_mapping
from src.database.population_metrics import add_population_metrics


@pytest.fixture
def population_inputs():
    population = pd.DataFrame({'sa4_code_2021': ['101','102'], 'resident_population': [10000,20000]})
    mapping = pd.DataFrame({'SA4_CODE_2021': ['101','102'], 'SA4_CODE_2026': ['101','102'],
        'RATIO_FROM_TO': [1.0,1.0], 'INDIV_TO_REGION_QLTY_INDICATOR': ['Good','Good'],
        'OVERALL_QUALITY_INDICATOR': ['Good','Good'], 'BMOS_NULL_FLAG': [0,0]})
    return population, mapping


def test_mapping_complete_population_reconciles(population_inputs):
    population, mapping = population_inputs
    result = validate_population_mapping(population, mapping, ['101','102'])
    assert result.resident_population.sum() == 30000


@pytest.mark.parametrize('problem', ['missing_region','duplicate','partial_weight','poor_quality','null_population','zero_population'])
def test_mapping_rejects_unsafe_correspondence(population_inputs, problem):
    population, mapping = population_inputs
    if problem == 'missing_region': mapping = mapping.iloc[:1]
    elif problem == 'duplicate': mapping.loc[1, 'SA4_CODE_2021'] = '101'
    elif problem == 'partial_weight': mapping.loc[0, 'RATIO_FROM_TO'] = 0.9
    elif problem == 'poor_quality': mapping.loc[0, 'OVERALL_QUALITY_INDICATOR'] = 'Poor'
    elif problem == 'null_population': population.loc[0, 'resident_population'] = None
    elif problem == 'zero_population': population.loc[0, 'resident_population'] = 0
    with pytest.raises(ValueError):
        validate_population_mapping(population, mapping, ['101','102'])


def test_gold_density_excludes_planned_and_uses_each_population_once(tmp_path):
    population = pd.DataFrame({'sa4_code':['101','102'], 'resident_population':[10000,20000],
        'population_year':[2025,2025], 'population_reference_date':['2025-06-30']*2,
        'population_geography':['Test']*2})
    path = tmp_path / 'population.parquet'
    population.to_parquet(path,index=False)
    with duckdb.connect() as con:
        con.execute('CREATE SCHEMA silver; CREATE SCHEMA gold')
        con.execute("CREATE TABLE silver.ev_locations_sa4 AS SELECT * FROM (VALUES ('101',false,'DC'),('101',false,'AC'),('101',true,'DC'),('102',false,'DC')) t(sa4_code,is_upcoming,charger_type)")
        con.execute('CREATE TABLE gold.sa4_ev_summary AS SELECT sa4_code,count(*) AS charging_location_count FROM silver.ev_locations_sa4 GROUP BY sa4_code')
        add_population_metrics(con,path)
        rows = con.execute('SELECT sa4_code,charging_location_count,resident_population,locations_per_10000_residents,dc_locations_per_10000_residents FROM gold.sa4_ev_summary ORDER BY sa4_code').fetchall()
        assert rows == [('101',3,10000,2.0,1.0),('102',1,20000,0.5,0.5)]
        # Statewide rate is a ratio of sums, not the average of region rates.
        assert con.execute('SELECT sum(existing_charging_location_count)*10000.0/sum(resident_population) FROM gold.sa4_ev_summary').fetchone()[0] == 1.0
