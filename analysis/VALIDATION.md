# Validation and changed-file inventory

Analysis scope: existing charging-location records (`is_upcoming=false`); population: ABS ERP at 30 June 2025. [findings.json](findings.json) holds numerators, denominators, provenance and checksums; [findings.sql](findings.sql) reproduces the conclusions; [sa4_population_density.csv](sa4_population_density.csv) lists all 28 regions. [powerbi_validation.dax](powerbi_validation.dax) checks the measures in Power BI.

## Verified results

| Check | Result |
| --- | --- |
| Existing / DC locations | 1,860 / 433 |
| NSW population / DC per 10k | 8,592,524 / 0.5039264365 |
| Hunter population / DC locations / DC per 10k | 316,250 / 9 / 0.2845849802 |
| Hunter DC rate relative to NSW | 56.47351669% |
| Sydney / rest DC shares | 27.96892342% / 18.87382690% |
| DC share gap | 9.0950965154 percentage points |
| Top three locations / share | 818 / 43.97849462% |
| Sydney population after GCC filter | 5,638,830 |
| Population with AC filter | 8,592,524; numerator becomes 1,427 existing AC locations |

SQL and live Desktop model DAX agree. Snapshot findings stay constant under charger filters. Population measures use raw counts/populations, with rounding only for display.

46 tests passed; PBIR validator: zero errors/warnings; TMDL: five tables, four relationships, 17 measures. Three pages and 37 containers have valid bindings/interactions, fit their canvas and do not overlap.

Original EV/SA4 Silver hashes, relationships and all Power Query partition/source definitions are unchanged. Gold and DuckDB were rebuilt; original count meanings are unchanged. No notebooks were edited. No changes were committed.

All three pages rendered in a temporary Desktop copy during the population update. Subsequently, both Azure Maps visuals were replaced with a fact-based SA4 ranking and a station details table because tenant map processing is blocked. Both replacements rendered successfully in a separate Desktop preview; after refresh, the local model returned the same analytical results. PBIR bindings, interactions and bounds were revalidated. Check station-table scrolling at your preferred screen size; see [report notes](../powerbi/REPORT_LAYER_NOTES.md).

## Every reviewable file added or modified

- `.gitignore` (modified)
- `README.md` (modified)
- `powerbi/NSW_EV_Dashboard.Report/definition.pbir` (modified)
- `powerbi/NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/page.json` (modified)
- `powerbi/NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/visuals/1c436f33d112c4d3ba70/visual.json` (modified)
- `powerbi/NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/visuals/6d190b64ba9207dc7caa/visual.json` (modified)
- `powerbi/NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/visuals/806945678615e3c85a1b/visual.json` (modified)
- `powerbi/NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/visuals/efc29faa6b65ec6da240/visual.json` (modified)
- `powerbi/NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/visuals/fc696a309c0da8304559/visual.json` (modified)
- `powerbi/NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/6a9a468e35118f6af062/visual.json` (modified)
- `powerbi/NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/8fd5ed192a9d8d3e5223/visual.json` (modified)
- `powerbi/NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/9fa8c15cf0d6d4ca4ba1/visual.json` (modified)
- `powerbi/NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/f165b3a390659f810d7a/visual.json` (modified)
- `powerbi/NSW_EV_Dashboard.SemanticModel/definition/tables/EV_Locations.tmdl` (modified)
- `powerbi/NSW_EV_Dashboard.SemanticModel/definition/tables/SA4_Summary.tmdl` (modified)
- `powerbi/NSW_EV_Dashboard.pbip` (modified)
- `powerbi/REPORT_LAYER_NOTES.md` (modified)
- `requirements.txt` (modified)
- `src/database/build_database.py` (modified)
- `analysis/VALIDATION.md` (added)
- `analysis/findings.json` (added)
- `analysis/findings.sql` (added)
- `analysis/powerbi_validation.dax` (added)
- `analysis/sa4_population_density.csv` (added)
- `powerbi/NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/visuals/b41b40bb9fdf4dfeab77/visual.json` (added)
- `powerbi/NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/801b70a956804655aae0/visual.json` (added)
- `powerbi/NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/963aaedff8af4c129d50/visual.json` (added)
- `powerbi/NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/99feff707712407f89a9/visual.json` (added)
- `src/acquisition/population.py` (added)
- `src/database/findings.py` (added)
- `src/database/population_metrics.py` (added)
- `src/pipeline.py` (added)
- `src/processing/sa4_population.py` (added)
- `tests/test_population.py` (added)

## Generated files (ignored by Git)

- `data/bronze/population/32180DS0003_2001-25.xlsx`
- `data/bronze/population/32180DS0003_2001-25.metadata.json`
- `data/bronze/population/CG_SA4_2021_SA4_2026.csv`
- `data/bronze/population/CG_SA4_2021_SA4_2026.metadata.json`
- `data/silver/population/sa4_population.parquet`
- `data/silver/population/sa4_population.metadata.json`
- `data/gold/sa4_ev_summary.parquet`
- `data/gold/gcc_ev_summary.parquet`
- `data/gold/operator_ev_summary.parquet`
- `data/gold/charger_type_summary.parquet`
- `data/database/nsw_ev.duckdb`

Validation helpers and Desktop previews are under the system temporary directory, outside the repository.
