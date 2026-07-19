# AGENTS.md — agent contract for the BCNexus repository

Author: Md Eliasinul Islam · Delta E+ Research Group, Simon Fraser University
Scope: everything under this repository root. Read this file before editing code.

---

## 1. What this repository is

BCNexus is a **CLEWs (Climate–Land–Energy–Water) model of British Columbia built on
OSeMOSYS**. The Python package `bcnexus` is not the model — it is the machinery that
*assembles* a model instance from tabular data, hands it to a linear-programming
solver, and turns the solution back into figures.

The distinction matters for every task in this repository:

| Layer | Artefact | Where it lives |
|---|---|---|
| Data | otoole-format CSVs (sets + parameters) | `data/clews_data/`, `data/RESource/` |
| Structure | technology/fuel/emission vocabulary | `bcnexus/clews/model_structure.py`, `config/clews_builder.yaml` |
| Scenario | overrides on a built model | `config/scenarios_bcnexus.yaml` |
| Formulation | OSeMOSYS GNU MathProg | `models/model_Kotzur`, `models/model_Niet` |
| Execution | CSV → datafile → LP → solution → result CSVs | `bcnexus/clews/runner.py` |
| Reporting | figures + combined HTML report | `bcnexus/plots.py`, `bcnexus/vis/` |

An agent asked to "fix the biomass numbers" is almost always being asked to change
the **data** or the **scenario**, not the Python. An agent asked to "add a plot" is
being asked to change only the reporting layer. Establish which layer the request
belongs to before writing anything.

---

## 2. The pipeline, in order

`RunModel` (`bcnexus/clews/runner.py`) is the single execution path. It is exposed
two ways, and they compose the *same* `stage_*` methods — never fork the logic.

```
stage_build          CLEWs builder → temporal clustering → storage-case schema
stage_scenario       apply scenario overrides (techs / demand / emissions)
stage_datafile       CSVs → otoole datafile (+ model file)
stage_lp             datafile → .lp via glpsol
stage_solve          .lp → .sol via gurobi | cbc
stage_results        .sol → result CSVs → runtime log → plots/report
```

Interactive use:

```python
from bcnexus.clews.runner import RunModel
m = RunModel(run_scenario='Base_CNZ_noCCS', storage_algorithm='Kotzur',
             clustering_attributes={'hour_grouping': 4, 'n_clusters': 1})
m.run(build=True, include_livestock=False, threads=16)
```

Orchestrated use (`bcnexus/stages.py`, a Typer CLI; driven by `workflow_v3/Snakefile`):

```bash
python -m bcnexus.stages solve -s Base_CNZ_noCCS -a Kotzur -hg 4 -nc 1 --threads 16
```

Each stage reads files and writes files. That is deliberate: it lets Snakemake
resume after a crash and run scenarios in parallel. **If you add work to the
pipeline, add it inside a `stage_*` method** so both entry points inherit it.

### Output location

`RunModel.run_dir()` is the only authority on where results go:

```
<scenario_results_root>/<N>ts/<YYYY_MM_DD>/
```

`N` is read from `TIMESLICE.csv` at call time, not assumed. The date folder comes
from the `date_tag` argument (`True` → today, a string → literal, `False` → flat).
Never hard-code a results path; call `run_dir()`.

---

## 3. Reporting layer

`plots.get_plots()` builds every figure and writes one self-contained HTML report.

```python
from bcnexus import plots
plots.get_plots(nexus_scenario='Base_CNZ_noCCS', timeslices=24, solver='gurobi',
                results_csvs=RESULTS)
```

It auto-discovers the input CSV folder (the one containing
`AccumulatedAnnualDemand.csv`) and the run diagnostics
(`runtime_memory_log.txt`, `constraints_summary.txt`, `<solver>.log`) near the
results directory. Two files are emitted: the tabbed report, and
`CLEW_model_map_<scenario>_<date>.html` — the reference energy system as a
standalone full-viewport page.

Module map under `bcnexus/vis/`:

- `palette.py` — the **single** colour source. Seeded from `config/dashboard.yaml`;
  `canon()` reconciles the two label vocabularies in this codebase (dashboard
  legend labels vs `model_structure.NamingConvention`). Never set a colour
  literal in a plot module; register it here.
- `plot_Inputs.py` — what the model was *given*.
- `plot_Energy / plot_Land / plot_Water / plot_Climate` — what the optimiser *produced*.
- `report.py` + `templates/report_template.html` — Python substitutes tokens; **all**
  markup, CSS and JS live in the template. Styling changes require no Python edit.

Every plot function returns a plotly figure, or `None` when its source CSV is
absent or empty. `plots.py` wraps calls in `_safe()`, so a missing input degrades
the report rather than killing the run. Preserve that contract.

---

## 4. Rules an agent must follow

1. **Never delete files in bulk without explicit approval.** Single-file deletion
   requires evidence of zero imports across the repo, stated in the reply.
2. **Do not change output paths, folder layout, or the fuel/technology naming
   convention** casually. Downstream plots, the otoole config and the CLEWs merge
   contract all key off those names.
3. **`run()` and the `stage_*` CLI must stay behaviourally identical.** Changing one
   without the other is a defect.
4. **Do not invent data.** No placeholder capacity factors, costs, or emission
   factors. If a number is missing, say so and cite what would be needed.
5. **Prescribed inputs are not results.** End-use fuel demand is exogenous in this
   model (the `DEM*` technologies are 100 %-efficiency pass-throughs), so the fuel
   mix in the demand projection is an assumption, not a model finding. See
   `data/calibration/README.md` §4 before reporting any end-use fuel level.
6. **Style edits go in the template**, colour edits go in `palette.py`, never inline.
7. **Author attribution** on generated documents is *Md Eliasinul Islam*.
8. Prose follows scientific-writing conventions: declarative, no filler, claims
   traceable to a file or a source.

---

## 5. Known open items (do not treat as bugs to silently fix)

- `clews/livestock.py::update_IARlist` — deduplication sets are not seeded from
  existing lists, which produces GLPK "already defined" errors when
  `include_livestock=True`. A revised function exists; confirm before touching.
- `update_yearly_params.py` resets some unintended parameters — work in progress.
- Input CSV horizon can disagree with the solved horizon; check both before
  interpreting a trend.
- `SEASON.csv` may be empty in some builds.

---

## 6. Companion project

`E:\CoWork\PROJECTS\CLEWS2070` extends this codebase to a pan-Canadian model, importing
node and transmission structure from OSeMOSYS Global. The adoption rationale is in
`Pan-Canada_CLEWs_Adoption_Plan.md` there. The BC codebase remains the reference
implementation: changes that break BC to serve Canada are not acceptable.

---

## 7. Where to look first

| Task | Start here |
|---|---|
| add or change a parameter | `clews/builder.py`, `config/clews_builder.yaml` |
| add a technology or fuel | `clews/model_structure.py`, then `clews/schema.py` |
| define a scenario | `config/scenarios_bcnexus.yaml` |
| change run behaviour | `clews/runner.py` (the `stage_*` methods) |
| batch or parallel runs | `workflow_v3/Snakefile`, `workflow_v3/config.yaml` |
| add a figure | the matching `vis/plot_*.py`, then register in `plots.py` |
| change report appearance | `vis/templates/report_template.html` |
| change a colour | `vis/palette.py` |
| paths and defaults | `attributes_parser.py` |
