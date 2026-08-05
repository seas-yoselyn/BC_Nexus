# BCNexus Workflow v3 — Snakemake + DVC scaffold

**Author:** Md Eliasinul Islam
**Status:** scaffold — stage CLI (`bcnexus/stages.py`) + Snakefile + DVC layout. Not yet wired to a live run.

## Design in one paragraph

The `bcnexus` package stays a pure library (notebook use unchanged). `bcnexus/stages.py` exposes RunModel's numbered phases (#1–#5 in `runner.py`) as independent CLI commands with file boundaries. `workflow_v3/Snakefile` orchestrates them over a declared matrix of `{scenario} × {storage_algo} × {hour_grouping, n_clusters}` — parallel branches, crash-resume, rebuild-only-what-changed. DVC versions the data, snakemake versions the computation. Scenario *definitions* remain in `config/scenarios_bcnexus.yaml` exactly as today; `workflow_v3/config.yaml` only selects which scenarios to run.

## Division of labour

| Concern | Tool | Mechanism |
|---|---|---|
| Which runs exist, in what order, resume, parallelism | Snakemake | rule DAG over `{run}` wildcard |
| Which *data* produced a result, sharing large CSVs, rollback | DVC | `dvc add` on data drops; git tracks the tiny `.dvc` pointer files |
| Scenario definitions (techs/demand/emissions overrides) | unchanged | `config/scenarios_bcnexus.yaml`, read by the `scenario-overlay` stage |
| Model math, storage algorithms | unchanged | `bcnexus.clews.*` |

## Setup

```bash
conda activate bc_nexus
pip install snakemake dvc          # snakemake>=8 needs python>=3.11
dvc init                            # once, at repo root

# version the data drops (large, non-git):
dvc add data/clews_data data/RESource data/downloaded_data data/processed_data
git add *.dvc .gitignore .dvc/config && git commit -m "track data drops with DVC"

# optional but recommended: a shared remote so the team pulls identical data
dvc remote add -d store /path/to/shared/drive/bcnexus-dvc   # or s3://... , gdrive://...
dvc push
```

## Running

```bash
dvc pull                            # ensure the exact data version
snakemake -s workflow_v3/Snakefile -n        # dry run: audit the matrix
snakemake -s workflow_v3/Snakefile -c4       # run declared matrix, 4 parallel branches
snakemake -s workflow_v3/Snakefile -c1 results/Base_CNZ_Kotzur_hg4_nc1/.results.done  # one branch
```

Editing `workflow_v3/config.yaml` (uncomment scenarios / temporal configs) changes the matrix; snakemake reruns only affected branches.

## Scenarios still work — the guarantee

The `scenario-overlay` rule depends on `config/scenarios_bcnexus.yaml`. Adding a scenario = add its block there + one line in `workflow_v3/config.yaml`. Changing a scenario's overrides invalidates only that scenario's branches (snakemake sees the yaml mtime change); base builds for other scenarios are untouched. Nothing about the momani/otoole scenario mechanics changes — the overlay stage calls the same `process_scenario_data()`.

## Known gaps (deliberate, in priority order)

1. **Sentinel files instead of real targets.** Rules currently `touch results/{run}/.stage.done` because RunModel writes to its own directory convention internally. The upgrade with the highest payoff: make each stage's real artifact (datafile.txt, model.lp, model.sol, result CSVs) the declared `output:`. Then snakemake becomes content-aware and `--rerun-triggers mtime` gets precise.
2. **Stage isolation is partial.** `solve` re-derives paths via `get_model_run_files()`; duals/shadow-price extraction still lives in `run()`'s tail — needs a small split in `runner.py` (markers are already numbered #1–#5, so the cut points are known).
3. **Per-run directory collision.** Two branches of the same scenario with different temporal configs write into `scenario_results_root/{ts}ts/` — verify RunModel's convention keeps them disjoint before running the matrix in parallel; if not, add the run id to the path.
4. **Canada scaling.** Region set stays *config*, not a wildcard (one coupled multi-region model, not 13 independent ones). When the pan-Canada builder lands, only `build_sets` grows; the DAG shape is unchanged.

## Why DVC and not git-lfs

DVC records data versions *per pipeline state* (`dvc.lock`-style hashes in `.dvc` files), works with any remote (network drive, S3, GDrive), and makes "which data produced Figure 3" answerable by `git log` + `dvc checkout`. git-lfs versions files but ties you to the git host's quota and has no cache-sharing story for a team. For a model whose credibility argument is reproducibility, the audit trail is the feature.
