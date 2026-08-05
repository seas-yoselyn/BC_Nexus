# BC Nexus Model
or **`BC-CLEWS-Model`**

The objective of this project is to develop a model that integrates water, food, energy, and climate factors, calibrated to British Columbia specifications. Using the open-source Climate, Land, Energy, Water Systems (CLEWS) modeling platform, the model will examine the impacts of various decarbonization policies in British Columbia on the security of these interconnected systems. The model uses cost optimization assessments to identify the least expensive pathway and the most reliable energy technology mix to successfully implement the policies while still meeting policy constraints and demand. The model also identifies the points of interaction among the various sectors, such as the land requirements for energy, the water requirements for agriculture and energy systems, and the connection between food and water infrastructure. The term "nexus" is used to describe the model because it captures the interdependence of the various components and how changes in one component can affect the security of other components within the nexus.Related publications related to this model are [[1]](#1),[[2]](#2).

The repository is broken into several main folders. The [__Wiki__](https://github.com/DeltaE/BC-CLEWS-Model/wiki) associated with this repository provides detailed information on the the model structure and the modelling methodology. Check the [__Public Dashboard__](https://deltae.github.io/BC-CLEWS-Model/).

# Project Description
Decarbonizing B.C.’s energy system
- [Brief descristion about the project](https://pics.uvic.ca/projects/decarbonizing-b-c-s-energy-system/)
- [High level overview of the modelling components](https://www.sfu.ca/see/research/delta-e/projects/decarbonization-of-bc-s-energy-system.html)
- [How to run the model](https://github.com/DeltaE/BC-CLEWS-Model/wiki/How-to-Run-the-Model)

# Repository layout

| Path | Contents |
|---|---|
| `codebase/bcnexus/` | the Python package: model builder, runner, stage CLI, plots — see [`codebase/bcnexus/Readme.md`](codebase/bcnexus/Readme.md) |
| `codebase/workflow_v3/` | Snakemake orchestration over the stage CLI |
| `config/` | scenario definitions, builder schema, dashboard colours |
| `data/` | otoole input CSVs, RESource drops, calibration notes |
| `models/` | OSeMOSYS GNU MathProg formulations (Kotzur / Niet storage) |
| `vis/` | generated per-run reports and model maps |
| `report/` | the master index, `BCNexus_report_v1.html` |
| `docs/` | resources, including the temporal-resolution explorer |
| `AGENTS.md` | contract for AI agents and new contributors working in this repo |

# Running the model

Two entry points compose the **same** `stage_*` methods, so results do not
depend on which you choose.

**Notebook / interactive**

```python
from bcnexus.clews.runner import RunModel
m = RunModel(run_scenario='Base_CNZ_noCCS', storage_algorithm='Kotzur',
             clustering_attributes={'hour_grouping': 4, 'n_clusters': 1})
m.run(build=True, threads=16)
```

**Stage CLI** — each stage reads and writes files, so a run can resume after a
crash and scenarios can execute in parallel:

```bash
python -m bcnexus.stages solve -s Base_CNZ_noCCS -a Kotzur -hg 4 -nc 1 --threads 16
```

Results are written to `<scenario_results>/<N>ts/<YYYY_MM_DD>/`; the timeslice
count is read from `TIMESLICE.csv` rather than assumed.

# Make targets

Run from the repository root; `make help` prints this list with current
variable values. On Windows use Git Bash/WSL, install make into the conda
environment (`conda install -c conda-forge make`), or use `make.bat`.

**Environment**

| Target | Action |
|---|---|
| `make setup` | create the conda environment, install the package, init submodules |
| `make update` | update the environment from `env/environment.yml` |
| `make export` | export the environment back to `env/environment.yml` |
| `make submodules` | initialise and update submodules |
| `make clean` | remove the `bc_nexus` conda environment |

**Legacy entry points** (`workflow/scripts`)

| Target | Action |
|---|---|
| `make nexus` | run the model via `BCNexus.py` |
| `make nexus_plots` | plot results for `NEXUS_SCENARIO` / `NEXUS_TIMESLICES` |
| `make plots` | scenario plots (calls `nexus_plots`) |

**Stage pipeline** (`bcnexus.stages` — resumable, Snakemake-facing)

| Target | Action |
|---|---|
| `make build` | stages 1–3: builder → temporal clustering → storage schema |
| `make overlay` | stage 4a: apply scenario overrides |
| `make datafile` | stage 4b: CSVs → otoole datafile |
| `make lp` | stage 5: datafile → `.lp` via glpsol |
| `make solve` | stage 6: `.lp` → `.sol` |
| `make results` | stage 7: `.sol` → result CSVs + report, then reindex |
| `make run` | the whole pipeline for one scenario |
| `make workflow` | the Snakemake scenario matrix, then reindex |

**Reporting**

| Target | Action |
|---|---|
| `make index` | rebuild `report/BCNexus_report_v1.html` |
| `make index-all` | same, also scanning sub-folders (dated run dirs) |
| `make clean-index` | delete the index only; reports untouched |

**Variables** — `NEXUS_SCENARIO`, `NEXUS_TIMESLICES` (legacy targets);
`SCEN`, `ALGO`, `HG`, `NC`, `SOLVER`, `THREADS`, `VIS`, `INDEX` (stage targets).

```bash
make run SCEN=Base_CNZ_noCCS HG=4 NC=1 THREADS=16
make solve SCEN=CNZ_LIMITED_CO2 SOLVER=cbc
make nexus_plots NEXUS_SCENARIO=CNZ_1 NEXUS_TIMESLICES=96
make index VIS=vis INDEX=report/BCNexus_report_v1.html
```

# Reporting

`plots.get_plots()` writes one self-contained HTML report per run plus a
standalone reference-energy-system page:

```
vis/CLEW_report_<algo>_<scenario>_<N>ts_<solver>_<YYYY_MM_DD>.html
vis/CLEW_model_map_<scenario>_<YYYY_MM_DD>.html
```

The report has Inputs and Outputs tabs (Outputs holds sticky Climate / Land /
Energy / Water sub-tabs), a floating bar with a 1–2–3 column switch, run,
solver, constraint and configuration diagnostics panels, reader-side dark mode
and font choice, and inlined plotly.js so it works offline.

`bcnexus.vis.index` builds a master index across every report in a folder,
with cascading dropdowns for scenario, timeslices, storage algorithm, solver
and run date, plus an "All runs" table:

```bash
make index          # -> report/BCNexus_report_v1.html
# equivalently: python -m bcnexus.vis.index vis report/BCNexus_report_v1.html
```

The index lives in `report/` (created if absent) and links back into `vis/`
with relative paths, so the two folders must keep their relative position. The
manifest is baked in at build time — a page opened from `file://` cannot list a
directory — so re-run after new runs; `make results` and `make workflow` do
this automatically.

# Interpreting results

End-use fuel demand is **exogenous** in this model: the `DEM*` technologies are
100 %-efficiency pass-throughs, so the fuel mix in the demand projection is an
assumption of the input data, not an optimisation outcome. Read
`data/calibration/README.md` before reporting any end-use fuel level as a model
finding.

# Contributors 

-  [Nastaran Arianpoo](https://www.linkedin.com/in/nastaran-arianpoo-ph-d-97301025/)
     - pre-Model<sub>v1</sub> Developement on top of OSeMOSYS framework, momani user-interface based data intake,git-wiki
- [Md Eliasinul Islam](https://www.linkedin.com/in/eliasinul/)
     - Model<sub>v1-2</sub> workflow automation, visualization, bug-fixes, otoole user-interface based data intake and result processing, model version control and git management, git-wiki 
     - PICS project data schema, project data sync automation
     - Data automation, timeslice downscaling automation of Model<sub>v2</sub> developemnt
- Bruno Borba
     - Developing storage, timeslice-aggregation, H<sub>2</sub> inclusion in Model<sub>v2</sub>
- [Pierre McWhannelView](https://www.linkedin.com/in/pierre-mcwhannel/)
     - coordination and development of dataschema, conceptualization and implementation of storage and time-slice aggreagtion, datasync of Model<sub>v2</sub>
- [Taco Niet](https://www.sfu.ca/see/research/delta-e/people/taco-niet.html?cq_ck=1647992649531)
      - Principal investigator (PI),supervision, conceptualization and review of the scientific articles, model results validation
- [Andrew S. Wright](https://www.linkedin.com/in/andrew-wright-6197a3125/) 
      - Supervision, conceptualization and review of the scientific articles, model results validation


# References

<a id="1">[1]</a>
*[Electrification Policy Impacts on Land System in British Columbia, Canada](https://doi.org/10.1016/j.rset.2024.100080)*; Nastaran Arianpoo, Md Eliasinul Islam, Andrew S. Wright, and Taco Niet, Aug 2024

<a id="2">[2]</a> 
*[ELECTRIFICATION POLICY IMPACTS ON LAND SYSTEM IN BRITISH COLUMBIA, CANADA](https://emi-ime.ca/wp-content/uploads/2021/04/EMI-2020-Arianpoo_report_BC-CLEWs.pdf)*; Nastaran Arianpoo, Andrew S. Wright, and Taco Niet, March 2021

#
<a rel="license" href="http://creativecommons.org/licenses/by-nc/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc/4.0/88x31.png" /></a><br /><span xmlns:dct="http://purl.org/dc/terms/" href="http://purl.org/dc/dcmitype/Text" property="dct:title" rel="dct:type">BC Nexus Model</span> by <a xmlns:cc="http://creativecommons.org/ns#" href="http://www.sfu.ca/see/research/delta-e.html" property="cc:attributionName" rel="cc:attributionURL">Delta E+ Team</a> is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-nc/4.0/">Creative Commons Attribution-NonCommercial 4.0 International License</a>.<br />Based on a work at <a xmlns:dct="http://purl.org/dc/terms/" href="https://github.com/DeltaE/BC-CLEWS-Model/wiki" rel="dct:source">https://github.com/DeltaE/BC-CLEWS-Model/wiki</a> | 2023
