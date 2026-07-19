# Changelog
All notable changes to the BCNexus codebase.
---

## [released] — 2026-07-19

Workflow modularization, a full CLEW plotting suite, and a self-contained
scenario report. Backwards compatible: `RunModel.run()` and the existing
notebook path behave as before.

### Added

**Workflow orchestration**

- `bcnexus/stages.py` — stage-level CLI (`build`, `scenario-overlay`,
  `datafile`, `lp`, `solve`, `results`). Each stage is an independent process
  with file boundaries, enabling crash-resume and parallel scenario runs.
- `workflow/staged` — Snakemake scaffold (`Snakefile`, `config.yaml`,
  `README_WORKFLOW.md`, `runner_split.patch.md`) driving a
  `{scenario} × {storage_algorithm} × {hour_grouping, n_clusters}` matrix,
  with DVC guidance for versioning data drops.
- `BCNexus_wf_modes.ipynb` — notebook demonstrating the Python API, the CLI, and
  the Snakemake matrix for the same pipeline.
- `BCNexus_dev.ipynb` - notebook demonstrates the comprehensive and informative input UI within notebook. Helps to inspect the staged outputs in developer mode.

**Visualization**

- `bcnexus/vis/plot_Water.py` (new module) — water balance, withdrawals by
  purpose, reservoir levels, hydro-generation vs reservoir state.
- `bcnexus/vis/plot_Land.py` — 7 plots added: land area by crop, irrigated vs
  rainfed (with irrigation-intensity axis), land-cover change, crop-land
  change, energy-system land footprint, cluster × crop heatmap, effective
  yield, forest trajectory. Model operation-mode names embedded via
  `get_mode_names()`.
- `bcnexus/vis/plot_Climate.py` — 7 plots added: cumulative emissions,
  gross vs captured vs net, grid carbon intensity (g/kWh), sectoral
  final-energy intensity (g/MJ), emissions-penalty cost, abatement wedges
  across scenarios, emissions vs legislated targets.
- `bcnexus/vis/plot_Energy.py` — system cost breakdown, fossil-fuel imports,
  cross-dimension nexus Sankey, and `plot_nexus_sankey_slider()` (year slider
  with shared node indices).
- `bcnexus/vis/palette.py` (new module) — single colour source seeded from
  `config/dashboard.yaml`, extended for crops, land covers, water flows, cost
  components; `canon()` reconciles the two label vocabularies in the codebase.

**Reporting**

- `bcnexus/vis/report.py` + `bcnexus/vis/templates/report_template.html`
  (new) — combined tabbed C/L/E/W HTML report. Markup/CSS/JS live in the
  template; Python only substitutes tokens.
- Report features: scenario description from `scenarios_bcnexus.yaml`,
  optional one-line notice, layout switcher (1/2/3 columns), font selector
  (Arial / Times New Roman / Cambria), dark-mode toggle, fullscreen, GitHub
  and project-site links, Delta E+ logo. Offline-capable (plotly.js inlined).
- Optional diagnostics panels beside the tabs, each rendered only when its
  source exists: run diagnostics (`runtime_memory_log.txt`), solver log
  (`gurobi.log`), constraints summary (`constraints_summary.txt`).
  `get_plots(auto_diagnostics=True)` discovers these in the run directory.

**Notebook UI (`bcnexus/utils.py`)**

- `build_scenario_ui()` reworked: multi-select scenario checkboxes (drives a
  run loop), Kotzur/Niet toggle, solver group (Gurobi default; others greyed),
  GMPL compiler group (Glpk; Mosox visible but disabled), threads group
  (4–32, warning on physical vs logical cores), dark/light theme switch, and a
  link to the temporal-resolution guide.
- `button_select()` and `get_selected_scenarios()` helpers.
- `docs/resources/temporal_resolution_explorer.html` — interactive guide to
  hour grouping and cluster choices, with solve-cost indication.

### Changed

- `bcnexus/clews/runner.py` — `run()` split into `stage_build`,
  `stage_scenario`, `stage_datafile`, `stage_lp`, `stage_solve`,
  `stage_results`; `run()` now composes them (identical behaviour).
- Output paths made deterministic via `run_dir()`; the timestamp `runtag` no
  longer appears in result directories. **Downstream effect:** results
  overwrite per branch instead of accumulating timestamped folders — update
  any script or dashboard globbing `*ts_csvs_<solver>_<runtag>`.
- `bcnexus/clews/datapackage.py` — `get_dataframe()` renamed to `get_df()`
  (alias retained for backwards compatibility).
- `bcnexus/plots.py` — registers all new plots; `save_combined_html()` reduced
  to a thin wrapper over `vis/report.py`; new arguments `save_individual`
  (default False — combined report only), `extra_info`, `layout`, `runlog`,
  `constraints`, `gurobi_log`, `auto_diagnostics`. Report filename now
  includes timeslices and solver.

### Fixed

- `plots.py`: timeslice count was hardcoded to 24 in the generation-timeseries
  call, mislabelling the annotation and mis-padding x-axis labels on non-24ts
  runs.
- Colour inconsistency between Energy and Climate figures: legacy plots mapped
  colours by technology *code* while legends displayed *labels*, so Plotly fell
  back to default colours. The palette now canonicalizes both vocabularies and
  every figure is harmonized before output.
- `stage_build` resets the CSV template before building, preventing duplicate
  rows on re-runs.
- Land-use change plot mixed land-cover and crop-land technologies in one
  stack (double-counting area); split into `plot_landcover_change()` and
  `plot_cropland_change()`, with the barley/barren code collision resolved via
  the regime suffix.
- Land plots matched only `HI`/`HR` regimes, silently dropping `II`, `IR` and
  `LR` land; all five GAEZ regimes are now included.
- `log_runtime_and_memory()` received `str / Path` (latent `TypeError`); now
  uses `run_dir()`.

### Known issues / follow-ups

- `include_livestock=True` triggered workflow results yet to be validated.
- Modelled irrigation intensity is ~80–100 mm/yr and irrigated area far exceeds
  BC statistics — review water input coefficients on irrigated land technologies.
- Industrial biomass (`DEMINDBIO`) carries full stack CO₂; confirm the intended
  biogenic-carbon accounting convention.
- `bcnexus/vis/plot_results_BC_Nexus.py` is unreferenced and superseded by
  `plots.py` (note: `workflow/scripts/plot_results_BCNexus.py` is still live via
  the makefile).
- Operation-mode names in `plot_Land.get_mode_names()` are hard-coded; have the
  builder emit the mode list when the model structure changes.
----
### Value added

- **Reproducibility** — deterministic output paths, stage-level re-runs, and a
  scenario report that carries its own provenance (run, solver and constraint
  diagnostics) in one shareable file.
- **Scalability** — the stage split and Snakemake matrix make multi-scenario
  campaigns resumable and parallel, a prerequisite for the pan-Canadian model.
- **Analytical coverage** — all four CLEW dimensions now have dedicated plots,
  including the land–water and water–energy coupling views that motivate the
  nexus framing.
- **Consistency** — one colour vocabulary across every figure and scenario.
- **Diagnostic value** — the new plots surfaced two calibration issues and one
  silent unit/labelling bug that annual-total figures had hidden.
