# modules of _bcnexus_ package 
A brief description is given below:

## Attributes Parser
If you need to redefine the directories and include any new attributes via config. It is recommended to update the [Attributes Parser](https://github.com/DeltaE/BC_Nexus/blob/main/bcnexus/attributes_parser.py), to keep the attributes setup centralized, harmonized and flexible.

## clews
Contains all the modules to update,build and run bcnexus model.
- __builder__: updates parameters' data
- __datapackage__: simplified validation and reading sets/params.
- __model_structure__: replaced the legacy 'BCNexus_config.yaml' with a python script. It contains dictionary of the structural components of BCNexus. Required modification if new SETs and connections to be build.
- preprocess_data_<storage_algorithm_name>__: preprocessing script of data to handle sparse matrix parsing. 
   > [why this script is required](https://github.com/OSeMOSYS/osemosys-cloud/blob/bfa7f68a758a5558d384559805e6724c949b2c12/scripts/preprocess_data.py#L3C1-L29C90)
   > 
   > __why do we have different scripts for storage alrogithms?__
   > > storage algorithm requires some customized temporal paramters which are exclusive to these model codes. To keep them simple, we kept them as separate scripts. To be integrated in future to handle alrogithm params via single script.
- __runner__: The model run module to run any model from csvs/datafile. It's a standalone module. Has dependency on other modules only if the methods of _builder_ module (e.g. temporal clustering, parameter, sets upgrades) is used.
- __schema__: The module to handle technology aggregation and dynamically updating the SETs and Parameters associated to TECHNOLOGIES. It handles and dynamically updates the  [clews_builder.yaml](https://github.com/DeltaE/BC_Nexus/blob/main/config/clews_builder.yaml) file. Has dependency on _builder_ module.
   > Currently supports power, carbon capture, storage and hydro inflow technologies. 
- __sets_n_ratios__: replaced the legacy `clewsy` tool with this tailored version. The core methods are adopted from clewsy's scripts.
-__update_global_params__: Handles updating the global params for Technologies.
  > work in progress.

- __update_yearly_params__: Handles the yearly parameter updates to harmonize _schema_ changes.
  > contains bugs that deletes and resets some unintended paramters. work in progress.

## stages

Stage-level CLI exposing each phase of `RunModel.run()` as an independent
command (`build`, `scenario-overlay`, `datafile`, `lp`, `solve`, `results`).
Each stage reads and writes files, so an orchestrator (Snakemake, see
`workflow_v3/`) can resume after a crash and run scenarios in parallel.
`run()` composes the same stages, so the notebook path is unchanged.

```bash
python -m bcnexus.stages solve -s Base_CNZ_noCCS -a Kotzur -hg 4 -nc 1 --threads 16
```

## plots

Builds the full plot set and writes the combined HTML report.
`get_plots()` discovers the input CSVs and the run diagnostics
(`runtime_memory_log.txt`, `constraints_summary.txt`, `<solver>.log`) near the
results folder, so a plain call produces a complete report.

```python
from bcnexus import plots
plots.get_plots(nexus_scenario='Base_CNZ_noCCS', timeslices=24, solver='gurobi',
                results_csvs=RESULTS)     # -> vis/CLEW_report_<scen>_<ts>ts_<solver>_<date>.html
```

Key arguments: `input_csvs` (sets/params folder; auto-discovered),
`save_individual` (also write one HTML per plot), `layout` ("1"/"2"/"3"
columns), `extra_info` (one-line notice in the header), `date_tag`.

## vis

Plot modules and the report builder. All figures share one colour vocabulary.

- __palette__: single colour source, seeded from `config/dashboard.yaml` and
  extended for crops, land covers, water flows and costs. `canon()` reconciles
  the two label vocabularies in the codebase (`dashboard.yaml` legend labels vs
  `model_structure.NamingConvention`) so one commodity keeps one colour
  everywhere.
- __plot_Inputs__: what goes INTO the model — demand by sector / end-use fuel /
  per sector, activity and capacity bounds, OAR-IAR efficiency (pass-through
  technologies flagged), emission factors, costs, temporal profiles, policy
  limits, model sets, and the reference energy system.
- __plot_Energy / plot_Land / plot_Water / plot_Climate__: result plots for the
  four CLEW dimensions, including the year-slider nexus Sankey, land–water
  coupling, reservoir behaviour and emission attribution.
- __report__ + __templates/report_template.html__: the combined report.
  Markup, CSS and JS live in the template; Python only substitutes tokens, so
  styling changes need no code edits. Tabs: __Model Map__ (reference energy
  system), __Inputs__, __Outputs__ (Climate/Land/Energy/Water as sticky
  sub-tabs). A floating bar carries the column switch (1/2/3), diagnostics
  panels (run, solver, constraints, model configuration) and the About button.
  Font, dark mode and fullscreen are reader-side; plotly.js is inlined so the
  file works offline.
- __index__: master index over a results/vis folder. Parses the report and
  model-map filenames into a manifest and writes `CLEW_index.html` with
  cascading dropdowns (scenario / timeslices / storage algorithm / solver /
  run date), an iframe viewer, a model-map view and an "All runs" table.
  Writes `report/BCNexus_report_v1.html` by default (parent created if absent);
  links are rewritten relative to the output location, so the index can sit
  outside the reports folder. Re-run after new runs — a file:// page cannot
  list a directory.

  ```python
  from bcnexus.vis import index
  index.build_index('vis')            # -> report/BCNexus_report_v1.html
  index.build_index('vis', save_to='report/BCNexus_report_v2.html')
  # shell: python -m bcnexus.vis.index vis report/BCNexus_report_v1.html
  ```

- __plot_demand__: deprecated — superseded by `plot_Inputs`; kept as a shim.

## cli

< work in progress >

---

🧢 __For more info and controbution, please connect with the developer : [Elias Islam](https://github.com/eliasinul)__
