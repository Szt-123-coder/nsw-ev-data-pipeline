# NSW EV report layer

## Result

Three PBIR pages on a consistent 1920 × 1080 canvas: NSW EV Overview, Geographic Distribution, and Operator & Charging Infrastructure.
33 visual containers: 5 KPI cards, 9 bar charts, 2 Azure Maps, 2 tables, 9 dropdown slicers, and 6 title/subtitle textboxes. All analytical values come from model bindings.

## Filtering and aggregation

- KPI cards, charging-location rankings and breakdowns, charger-power analysis, and maps use EV_Locations fields or existing DAX measures. Top 10 operator filters rank by [Total Charging Locations] and recalculate with slicers.
- The requested SA4 density chart and SA4 comparison table retain Gold summary columns. They show the full-dataset baseline for the selected SA4. GCC and charger-type selections do not recalculate these summaries; their interactions are explicitly disabled.
- Operator SA4 coverage and the operator summary table retain Gold summary columns. Operator selection filters these visuals; GCC and charger-type interactions are disabled. Their subtitles state this scope.
- Density and coverage charts use MAX of their numeric field within the unique SA4/operator group. Comparison tables display raw Gold columns and disable totals to avoid adding averages or density values.
- AC vs DC on page 3 excludes Unknown explicitly. The overview breakdown includes AC, DC, and Unknown.
- Maps group by Station Display and unsummarized latitude/longitude. Tooltips include all six requested fields. Text tooltip fields use MIN (first text value) and numeric tooltip fields use MAX within each station/coordinate group, as required by the Azure Maps tooltip measure roles.
- Each page has independent slicer selections. No cross-page slicer synchronization is configured.

## Validation

- Microsoft powerbi-report-authoring-cli: zero errors and zero warnings.
- All 40 PBIR definition/property JSON files validated against Microsoft JSON schemas with external references resolved.
- Confirmed three page registrations, unique visual IDs, valid interactions, all model field/measure references, descending sorts and both Top 10 filters.
- All visual rectangles are inside the canvas and do not overlap. Tables reserve space for the vertical scrollbar.
- Desktop opened a separate temporary copy successfully. Non-map charts, KPI cards, slicers and tables rendered across all three pages.
- Interactive Desktop smoke check: selecting DC changed locations to 433, plugs to 1,658, and average charger power to 99.0 kW; the Top 10 operator ranking recalculated.
- Azure Maps requested Power BI sign-in. Subsequent non-map rendering checks used placeholders only in the temporary copy; both Azure Maps remain intact in the source report.
- SHA-256 comparisons confirm the entire semantic model, relationships, source definitions, upstream data, src, notebooks, tests, config and pre-existing .gitignore are unchanged from the start of this report-layer task.
- No changes were staged or committed. The report source files were already untracked at task start.

## After reopening the source PBIP

1. Reopen NSW_EV_Dashboard.pbip so Desktop loads external PBIR edits. Avoid saving a stale already-open session over the source files.
2. Sign in to Power BI as needed for Azure Maps, then verify map rendering, station grouping, all tooltips, zoom, and map filtering. Tenant settings may also control Azure Maps availability.
3. Check the report at your preferred zoom/display resolution. SA4/operator lists and tables scroll vertically to retain readable labels.
4. Confirm the full-dataset scope of the four Gold summary visuals suits the intended analysis; dynamic recalculation of those values would require additional fact-based measures, which this report-only task intentionally preserves the model without adding.

## Exact file inventory for this task

4 existing files modified; 37 files added (including this note). No existing files deleted.
Paths below identify every changed or added file; paths are relative to the powerbi directory, with absolute clickable targets.

| Status | File | Purpose |
| --- | --- | --- |
| Added | [NSW_EV_Dashboard.Report/StaticResources/RegisteredResources/NSW-EV-Portfolio-236fc1bb88160c2846c5.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/StaticResources/RegisteredResources/NSW-EV-Portfolio-236fc1bb88160c2846c5.json) | Portfolio colour and typography theme |
| Modified | [NSW_EV_Dashboard.Report/definition.pbir](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition.pbir) | Schema declaration added; existing model reference unchanged |
| Added | [NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/page.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/page.json) | Page title, canvas and interactions |
| Added | [NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/visuals/120b8076d388a4318863/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/visuals/120b8076d388a4318863/visual.json) | Geographic Distribution / slicer-gcc |
| Added | [NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/visuals/1c436f33d112c4d3ba70/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/visuals/1c436f33d112c4d3ba70/visual.json) | Geographic Distribution / page-subtitle |
| Added | [NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/visuals/4482a3925fc1ef0b6d05/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/visuals/4482a3925fc1ef0b6d05/visual.json) | Geographic Distribution / slicer-charger |
| Added | [NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/visuals/6d190b64ba9207dc7caa/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/visuals/6d190b64ba9207dc7caa/visual.json) | Geographic Distribution / sa4-density |
| Added | [NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/visuals/806945678615e3c85a1b/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/visuals/806945678615e3c85a1b/visual.json) | Geographic Distribution / sa4-comparison |
| Added | [NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/visuals/dde728cc6366bc56b603/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/visuals/dde728cc6366bc56b603/visual.json) | Geographic Distribution / slicer-sa4 |
| Added | [NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/visuals/efc29faa6b65ec6da240/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/visuals/efc29faa6b65ec6da240/visual.json) | Geographic Distribution / sa4-map |
| Added | [NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/visuals/f4d143af9fd0ed7c35a5/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/visuals/f4d143af9fd0ed7c35a5/visual.json) | Geographic Distribution / page-title |
| Added | [NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/visuals/fc696a309c0da8304559/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/404d5efbd9b43c7a5eb5/visuals/fc696a309c0da8304559/visual.json) | Geographic Distribution / sa4-ranking |
| Modified | [NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/page.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/page.json) | Page title, canvas and interactions |
| Added | [NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/099ed70145200b8126bb/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/099ed70145200b8126bb/visual.json) | NSW EV Overview / page-subtitle |
| Added | [NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/323336613145e90e0349/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/323336613145e90e0349/visual.json) | NSW EV Overview / slicer-upcoming |
| Added | [NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/55d0f9295b9c36856835/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/55d0f9295b9c36856835/visual.json) | NSW EV Overview / kpi-9c9b607f9f2385fa2625 |
| Added | [NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/5ddb184682845d9d4a77/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/5ddb184682845d9d4a77/visual.json) | NSW EV Overview / slicer-gcc |
| Added | [NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/6a9a468e35118f6af062/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/6a9a468e35118f6af062/visual.json) | NSW EV Overview / location-map |
| Added | [NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/7e27da57630c1830af83/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/7e27da57630c1830af83/visual.json) | NSW EV Overview / kpi-e7bd56250788fd2e8da2 |
| Added | [NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/8fd5ed192a9d8d3e5223/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/8fd5ed192a9d8d3e5223/visual.json) | NSW EV Overview / top-operators |
| Added | [NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/9fa8c15cf0d6d4ca4ba1/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/9fa8c15cf0d6d4ca4ba1/visual.json) | NSW EV Overview / charger-breakdown |
| Added | [NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/a1fb3f14cfc65ffeb5cc/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/a1fb3f14cfc65ffeb5cc/visual.json) | NSW EV Overview / kpi-34ecad9456403c228c6e |
| Added | [NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/e05a29412838410b5d09/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/e05a29412838410b5d09/visual.json) | NSW EV Overview / page-title |
| Added | [NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/e52689765aa15e46fa7c/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/e52689765aa15e46fa7c/visual.json) | NSW EV Overview / kpi-a2e70db069df0df5a467 |
| Added | [NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/f165b3a390659f810d7a/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/f165b3a390659f810d7a/visual.json) | NSW EV Overview / gcc-comparison |
| Added | [NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/f8a5e2b3e9d2ba4da99d/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/f8a5e2b3e9d2ba4da99d/visual.json) | NSW EV Overview / slicer-charger |
| Added | [NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/ff15053fc06d483151a5/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/71e23dd07a6e4d705843/visuals/ff15053fc06d483151a5/visual.json) | NSW EV Overview / kpi-bf31099a500d3ed69b79 |
| Added | [NSW_EV_Dashboard.Report/definition/pages/a62e31680cc81db636b4/page.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/a62e31680cc81db636b4/page.json) | Page title, canvas and interactions |
| Added | [NSW_EV_Dashboard.Report/definition/pages/a62e31680cc81db636b4/visuals/3d863dd46d9107c34e6b/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/a62e31680cc81db636b4/visuals/3d863dd46d9107c34e6b/visual.json) | Operator & Charging Infrastructure / operator-locations |
| Added | [NSW_EV_Dashboard.Report/definition/pages/a62e31680cc81db636b4/visuals/67f4f8f961eb6eaece67/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/a62e31680cc81db636b4/visuals/67f4f8f961eb6eaece67/visual.json) | Operator & Charging Infrastructure / slicer-gcc |
| Added | [NSW_EV_Dashboard.Report/definition/pages/a62e31680cc81db636b4/visuals/7d4839af5c05b73be351/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/a62e31680cc81db636b4/visuals/7d4839af5c05b73be351/visual.json) | Operator & Charging Infrastructure / operator-coverage |
| Added | [NSW_EV_Dashboard.Report/definition/pages/a62e31680cc81db636b4/visuals/837c3978e8300a7ace00/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/a62e31680cc81db636b4/visuals/837c3978e8300a7ace00/visual.json) | Operator & Charging Infrastructure / ac-dc |
| Added | [NSW_EV_Dashboard.Report/definition/pages/a62e31680cc81db636b4/visuals/861e118d7d155e30f355/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/a62e31680cc81db636b4/visuals/861e118d7d155e30f355/visual.json) | Operator & Charging Infrastructure / page-subtitle |
| Added | [NSW_EV_Dashboard.Report/definition/pages/a62e31680cc81db636b4/visuals/8f7c578aa390df83c652/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/a62e31680cc81db636b4/visuals/8f7c578aa390df83c652/visual.json) | Operator & Charging Infrastructure / slicer-operator |
| Added | [NSW_EV_Dashboard.Report/definition/pages/a62e31680cc81db636b4/visuals/ad9ec0beead90db3c2d8/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/a62e31680cc81db636b4/visuals/ad9ec0beead90db3c2d8/visual.json) | Operator & Charging Infrastructure / page-title |
| Added | [NSW_EV_Dashboard.Report/definition/pages/a62e31680cc81db636b4/visuals/b65685230a2f33d419fe/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/a62e31680cc81db636b4/visuals/b65685230a2f33d419fe/visual.json) | Operator & Charging Infrastructure / charger-power |
| Added | [NSW_EV_Dashboard.Report/definition/pages/a62e31680cc81db636b4/visuals/d6780287233eed90213d/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/a62e31680cc81db636b4/visuals/d6780287233eed90213d/visual.json) | Operator & Charging Infrastructure / operator-summary |
| Added | [NSW_EV_Dashboard.Report/definition/pages/a62e31680cc81db636b4/visuals/e880c9cd1533bf513fa5/visual.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/a62e31680cc81db636b4/visuals/e880c9cd1533bf513fa5/visual.json) | Operator & Charging Infrastructure / slicer-charger |
| Modified | [NSW_EV_Dashboard.Report/definition/pages/pages.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/pages/pages.json) | Three-page order and initial page |
| Modified | [NSW_EV_Dashboard.Report/definition/report.json](D:/mycode/nsw-ev-data-pipeline/powerbi/NSW_EV_Dashboard.Report/definition/report.json) | Report setup / documentation |
| Added | [REPORT_LAYER_NOTES.md](D:/mycode/nsw-ev-data-pipeline/powerbi/REPORT_LAYER_NOTES.md) | Report setup / documentation |
