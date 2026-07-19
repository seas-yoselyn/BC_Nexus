#!/usr/bin/env python3
"""
Stage-level CLI for the BCNexus workflow (Snakemake-facing).

Author: Md Eliasinul Islam

Each command maps 1:1 onto a RunModel.stage_* method (see clews/runner.py).
File inputs -> file outputs per stage, so an orchestrator (Snakemake) can
resume, parallelize, and cache. RunModel.run() composes the same stages for
interactive/notebook use — one code path, two entry styles.
"""
import typer

app = typer.Typer(help="BCNexus stage-level workflow commands (Snakemake-facing).")


def _make_runner(scenario: str, storage: str, hour_grouping: int, n_clusters: int):
    from bcnexus.clews.runner import RunModel
    return RunModel(
        run_scenario=scenario,
        storage_algorithm=storage,
        clustering_attributes={
            "hour_grouping": hour_grouping,
            "n_clusters": n_clusters,
        },
    )


# common options
S = typer.Option(..., "--scenario", "-s")
A = typer.Option("Kotzur", "--storage", "-a")
HG = typer.Option(4, "--hour-grouping", "-hg")
NC = typer.Option(1, "--n-clusters", "-nc")


@app.command()
def build(scenario: str = S, storage: str = A,
          hour_grouping: int = HG, n_clusters: int = NC,
          include_livestock: bool = True):
    """Stage #1-#3: CLEWs builder -> temporal profiles -> storage-case schema."""
    m = _make_runner(scenario, storage, hour_grouping, n_clusters)
    out = m.stage_build(include_livestock=include_livestock)
    typer.echo(f"[build] done -> {out}")


@app.command()
def scenario_overlay(scenario: str = S, storage: str = A,
                     hour_grouping: int = HG, n_clusters: int = NC):
    """Stage #4a: apply scenario overrides (techs/demand/emissions)."""
    m = _make_runner(scenario, storage, hour_grouping, n_clusters)
    out = m.stage_scenario()
    typer.echo(f"[scenario] overrides applied -> {out}")


@app.command()
def datafile(scenario: str = S, storage: str = A,
             hour_grouping: int = HG, n_clusters: int = NC):
    """Stage #4b: CSVs -> otoole datafile + model file."""
    m = _make_runner(scenario, storage, hour_grouping, n_clusters)
    data_file, model_file = m.stage_datafile()
    typer.echo(f"[datafile] {data_file}\n[model]    {model_file}")


@app.command()
def lp(scenario: str = S, storage: str = A,
       hour_grouping: int = HG, n_clusters: int = NC):
    """Stage #5a: glpsol datafile+model -> model.lp."""
    m = _make_runner(scenario, storage, hour_grouping, n_clusters)
    out = m.stage_lp()
    typer.echo(f"[lp] {out}")


@app.command()
def solve(scenario: str = S, storage: str = A,
          hour_grouping: int = HG, n_clusters: int = NC,
          solver: str = typer.Option("gurobi", "--solver"),
          threads: int = typer.Option(32, "--threads")):
    """Stage #5b: solve LP -> .sol (+ duals, constraints report, shadow prices)."""
    m = _make_runner(scenario, storage, hour_grouping, n_clusters)
    sol = m.stage_solve(solver_name=solver, threads=threads)
    if sol is None:
        typer.echo("[solve] FAILED — no optimal solution", err=True)
        raise typer.Exit(code=1)   # snakemake marks the branch failed
    typer.echo(f"[solve] {sol}")


@app.command()
def results(scenario: str = S, storage: str = A,
            hour_grouping: int = HG, n_clusters: int = NC,
            solver: str = typer.Option("gurobi", "--solver")):
    """Stage #6: .sol -> result CSVs via otoole."""
    m = _make_runner(scenario, storage, hour_grouping, n_clusters)
    out = m.stage_results(solver_name=solver)
    if out is None:
        typer.echo("[results] FAILED — solution file missing", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"[results] {out}")


if __name__ == "__main__":
    app()
