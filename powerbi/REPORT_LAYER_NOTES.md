# NSW EV report and population analysis

## Result

Three PBIR pages remain on a 1920 × 1080 canvas. There are 37 containers: five KPI cards, three DAX finding cards, eleven bar charts, three tables, nine slicers and six title/subtitle textboxes. No Azure Maps visuals remain.

- Overview: three findings recalculate from existing location records after refresh. These snapshot cards ignore page selections to stay consistent with the published conclusions. Hunter's finding measures DC locations per resident; the others describe the Sydney/rest DC mix and top-three operator concentration. A fact-based SA4 ranking replaces the map and responds to the region, charger-type and upcoming-status slicers.
- Geographic Distribution: the original area-density chart remains alongside a population-density ranking. The baseline table adds population and existing location/DC rates per 10,000 residents. A station details table replaces the map, responds to slicers, and exposes station, operator, charger type, SA4, power, plugs, upcoming status, latitude and longitude. Scroll right for additional fields.
- Operator & Charging Infrastructure: original visuals and bindings remain.

## Population and filtering

ABS ERP is dated 30 June 2025, originally on ASGS 2021 geography. Official correspondence validates 28 unique, weight-one spatial NSW SA4 mappings to SA4 2026. Population reconciles to 8,592,524.

`Resident Population` sums population once per SA4. Existing relationships remain unchanged; `TREATAS` propagates GCC selections to the population denominator. SA4/GCC selections affect both sides. Charger/operator selections affect the numerator without shrinking the population to regions containing those operators. State totals use a ratio of sums, never an average of regional rates.

Gold's original counts include upcoming records; new population rates use existing records. Labels explain this distinction. Gold area-density, coverage and baseline tables retain their static scope. Fact rankings, station details and population measures respond to applicable filters.

## Validation

- `python -m src.pipeline --from-silver` completed and exported Gold plus SQL/JSON/CSV evidence.
- `python -m pytest -q`: 46 passed, including unsafe population correspondence and density denominator cases.
- Microsoft report-authoring CLI: zero PBIR errors/warnings.
- Microsoft Analysis Services TMDL parser: five tables, four relationships, 17 measures.
- All three page registrations, 37 visual bindings, interaction targets, canvas bounds and non-overlapping rectangles checked.
- A temporary Power BI Desktop model refreshed and evaluated `analysis/powerbi_validation.dax`. SQL and DAX agree, including geography and charger filters. All three pages rendered in a non-map preview, including the final four-panel geographic layout and population table.
- Original Silver Parquet hashes and relationship definition are unchanged. All five original Power Query partitions and source paths are unchanged.
- After replacing maps, the new SA4 chart and station details table rendered successfully in a separate Desktop preview. The refreshed local model returned the same population and finding results. PBIR validation again returned zero errors/warnings, and all 37 bindings and visual rectangles passed inspection.

## Desktop checks remaining

Reopen the source PBIP to load the new report definitions; a data refresh alone does not reload externally edited visuals. Avoid saving a stale session over external edits. Check the geographic layout and station-table scrolling at your preferred screen size. Azure Maps was replaced because the signed-in tenant blocks out-of-region map processing; the report no longer requires that permission.

The live EV/boundary re-download branch was not run, to preserve this snapshot. The documented `--from-silver` route was run. Raw downloads, Parquet, DuckDB and Desktop caches are intentionally ignored by Git. No changes were staged or committed.

See [the complete changed-file inventory and evidence](../analysis/VALIDATION.md).
