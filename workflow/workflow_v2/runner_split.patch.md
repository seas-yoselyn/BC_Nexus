# Patch draft: split `RunModel.run()` into stage methods

**Author:** Md Eliasinul Islam
**Target:** `bcnexus/clews/runner.py` (local codebase version, `run()` at line ~523)
**Principle:** `run()` keeps working identically for the notebook — it becomes a thin composition of the new stage methods. Nothing is deleted; logic moves.

---

## 0. Pre-condition to fix first: deterministic paths

`run()` builds the solution directory as
`{scenario_results_root}/{ts}ts_{self.aparser.runtag}/...` where `runtag` is a
**timestamp**. Under snakemake this breaks caching: every invocation writes a
new directory, so no output path is ever "already built," and resume becomes
impossible. The patch therefore routes all stage outputs through one
deterministic helper (§1). Keep the runtag for *logs only*.

This is the single most consequential change in the patch — review it first.

---

## 1. Add: path helper (place after `get_all_attributes`, ~line 147)

```python
    # ---------------------------------------------------------------- paths
    def run_dir(self) -> Path:
        """Deterministic output directory for this (scenario, algo, temporal) branch.

        Replaces the runtag-suffixed directory so an orchestrator can declare
        real file targets. One branch == one directory, re-entrant.
        """
        self.timeslices = len(pd.read_csv(self.input_csvs / 'TIMESLICE.csv'))
        d = self.scenario_results_root / f'{self.timeslices}ts'
        d.mkdir(parents=True, exist_ok=True)
        return d
```

## 2. Add: stage methods (place directly above `run()`, ~line 522)

```python
    # ---------------------------------------------------------------- stages
    # Each stage: file inputs -> file outputs, no reliance on state set by a
    # previous stage *in the same process*. run() composes them; snakemake
    # calls them one process each via bcnexus/stages.py.

    def stage_build(self, include_livestock: bool = True) -> Path:
        """#1-#3: CLEWs builder -> temporal profiles -> storage-case schema."""
        utils.print_update(level=1,
            message=f'CLEWs Builder: SETs and Params for scenario: {self.run_scenario}')
        self.clewsBuilder.build(include_livestock=include_livestock,
                                update_clews_builder=True)
        self.clewsBuilder.update_temporal_profiles()
        utils.copy_csv_files(src_folder=self.clewsBuilder.clews_build_input_csv_dir,
                             dest_folder=self.clewsBuilder.storage_case_input_csvs,
                             all_files=True)
        self.clewsBuilder.update_storage_case_temporal_schema()
        return Path(self.clewsBuilder.storage_case_input_csvs)

    def stage_scenario(self) -> Path:
        """#4a: apply scenario overrides from scenarios_bcnexus.yaml onto built CSVs."""
        utils.print_update(level=1,
            message=f'Loading scenario config @ {self.scenario_cfg}')
        self.process_scenario_data()
        return Path(self.input_csvs)

    def stage_datafile(self) -> tuple[Path, Path]:
        """#4b: CSVs -> otoole datafile + model file selection."""
        utils.print_update(level=1, message='Preparing model and data files.')
        self.data_file, self.model_file = self.get_model_run_files()
        return Path(self.data_file), Path(self.model_file)

    def stage_lp(self) -> Path:
        """#5a: glpsol -> LP file. Re-derives datafile paths if not in memory."""
        if not hasattr(self, 'data_file'):
            self.stage_datafile()
        self.write_LP_file(self.model_file, self.data_file, self.LP_file)
        return Path(self.LP_file)

    def stage_solve(self, solver_name: str = 'gurobi', threads: int = 32) -> Path | None:
        """#5b: solve LP -> .sol; gurobi path also writes duals, binding-constraint
        summary, and the ELCB02 shadow-price plot. Returns solution path or None."""
        out = self.run_dir()
        self.solution_path = out / f'{self.timeslices}ts_solution_{solver_name}.sol'
        self.solver_log_save_to = out / f'{solver_name}.log'

        utils.print_update(level=1,
            message=f'Solving the LP problem with {solver_name} solver')

        if solver_name == 'gurobi':
            self.solved_model = self.solve_model_gurobi(self.LP_file,
                                                        log_path=self.solver_log_save_to,
                                                        threads=threads)
            if not solver.get_solve_status(self.solved_model):
                utils.print_error(
                    f'X Model not solved, check logs @ {self.solver_log_save_to}')
                return None
            if self.solution_path.exists():
                self.solution_path.unlink()
            self.write_solution(self.solved_model, self.solution_path)

            # post-solve diagnostics (moved verbatim from run() tail)
            self.shadow_price_ELCB02 = self.get_shadow_price_ELCB02(
                self.solved_model,
                plot_save_to=out / f'shadowprice_ELC02_{self.timeslices}ts.png',
                show=False)
            self.duals_df, self.binding_constraints, self.non_binding_constraints = \
                self.get_constraints(self.solved_model)
            self.get_summary_report(self.binding_constraints,
                                    self.non_binding_constraints,
                                    out / 'constraints_summary.txt')
            self.duals_df.to_csv(out / 'EBa11_EnergyBalanceEachTS5_duals.csv')

        elif solver_name == 'cbc':
            self.solve_model_cbc(lp_path=self.LP_file,
                                 solution_path=self.solution_path,
                                 threads=threads)

        return self.solution_path if self.solution_path.exists() else None

    def stage_results(self, solver_name: str = 'gurobi') -> Path | None:
        """#6: .sol -> result CSVs via otoole. Re-derives solution path if needed."""
        if not hasattr(self, 'solution_path'):
            out = self.run_dir()
            self.solution_path = out / f'{self.timeslices}ts_solution_{solver_name}.sol'
        if not self.solution_path.exists():
            utils.print_update(level=1, message='X Solution file not found.')
            return None
        self.results_dir = self.get_result_csvs(solution_file=self.solution_path,
                                                solver_name=solver_name)
        return self.results_dir
```

## 3. Replace: `run()` body becomes a composition (identical behavior)

```python
    def run(self,
            input_csvs: str | Path = None,
            build: bool = False,
            include_livestock: bool = True,
            solver_name: str = 'gurobi',
            threads: int = 32,
            machine_id: str = None):
        """Composed pipeline; see stage_* methods. Notebook behavior unchanged."""
        start_time = time.time()
        process = psutil.Process()

        if build:
            self.stage_build(include_livestock=include_livestock)
        else:
            utils.print_update(level=1,
                message=f'Skipping CLEWs builder; using SETs/Params from {input_csvs or self.input_csvs}')
            # temporal/storage schema still refresh, as before
            self.clewsBuilder.update_temporal_profiles()
            utils.copy_csv_files(src_folder=self.clewsBuilder.clews_build_input_csv_dir,
                                 dest_folder=self.clewsBuilder.storage_case_input_csvs,
                                 all_files=True)
            self.clewsBuilder.update_storage_case_temporal_schema()

        self.stage_scenario()
        self.stage_datafile()
        self.stage_lp()
        sol = self.stage_solve(solver_name=solver_name, threads=threads)
        if sol is not None:
            self.stage_results(solver_name=solver_name)

        memory_usage = process.memory_info().rss
        RunModel.log_runtime_and_memory(self.run_scenario, self.timeslices,
                                        self.clustering_attributes, start_time,
                                        memory_usage, self.run_dir(), machine_id)
```

## 4. Behavior changes to sign off on (everything else is a pure move)

1. **Runtag removed from output paths** (§0/§1): results overwrite per branch
   instead of accumulating timestamped copies. If you want history, that's now
   DVC's job (`dvc add results/` snapshots) — which is the better tool for it.
   *This changes where the dashboard looks for results* — check
   `config/dashboard.yaml` path patterns.
2. **`log_runtime_and_memory` save path**: old code had
   `Path(self.run_scenario/self.scenario_results_root/...)` — `str / Path` is
   a latent TypeError when `run_scenario` is a str; the patch uses `run_dir()`.
   Verify this was not intentionally relying on some path coercion.
3. **Non-build branch of `run()`** previously *always* ran
   `update_temporal_profiles` + copy + schema (steps #2-#3 sat outside the
   if/else). Preserved verbatim in the composed `run()`; `stage_build` includes
   them for the snakemake path. Double-run of these steps when `build=True` is
   avoided now — in the old code they ran regardless; confirm they are idempotent
   (they appear to be: overwrite semantics).
4. **`stage_solve` early-returns `None`** on non-optimal status instead of
   falling through — snakemake then marks the branch failed instead of
   attempting result extraction on a stale .sol.

## 5. After applying

`bcnexus/stages.py` commands map 1:1 (`build`→`stage_build`+`stage_scenario` split as-is, `lp`→`stage_lp`, etc.) — update its bodies to call the stage methods and delete the interim workarounds. Then upgrade the Snakefile sentinels to real targets:

```
rule lp:      output: "results/{run}/model.lp"      # from stage_lp return
rule solve:   output: "results/{run}/{ts}ts_solution_gurobi.sol"
rule results: output: directory("results/{run}/result_csvs")
```

Test sequence: (1) notebook `run()` on Base_CNZ_noCCS, diff results vs a pre-patch run; (2) `python -m bcnexus.stages lp -s Base_CNZ_noCCS ...` alone from a clean state; (3) `snakemake -c2` two-scenario matrix.
