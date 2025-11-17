#!/usr/bin/env python3
import os
from pathlib import Path
import typer
from rich import print
from bcnexus.clews.runner import RunModel

app = typer.Typer(help="BC-NEXUS unified command line tool.")


# ------------------------------------------------------
# Utility: auto-locate project root
# ------------------------------------------------------
from pathlib import Path

def find_project_root(marker: str = "BC_NEXUS") -> Path:
    """
    Traverse upward to find a directory containing a folder or file 
    matching the marker name (case-insensitive).
    """
    marker_lower = marker.lower()
    d = Path.cwd()

    while d != d.parent:  # stop at filesystem root
        # Check all entries in this directory case-insensitively
        for item in d.iterdir():
            if item.name.lower() == marker_lower:
                return d

        d = d.parent

    raise RuntimeError(
        f"Cannot find project root; no directory or file named '{marker}' "
        f"(case-insensitive) found in any parent folders."
    )

# ------------------------------------------------------
# COMMAND: bcnexus run
# ------------------------------------------------------
@app.command()
def run(
    scenario: str = typer.Option("Base", "--scenario", "-s"),
    storage: str = typer.Option("Kotzur", "--storage", "-a"),
    hour_grouping: int = typer.Option(4, "--hour-grouping", "-hg",
                                      help="Grouping of hours before clustering"),
    n_clusters: int = typer.Option(4, "--n-clusters", "-nc",
                                   help="Number of clusters for Kotzur/Welsch/Niet"),
    config: Path = typer.Option(Path("config/config.yaml"), "--config", "-c"),
):
    """Run the CLEWS–BC Nexus integrated model."""

    print(f"[green]▶ Running BC-NEXUS CLEWS model[/green]")
    print(f"Scenario       : {scenario}")
    print(f"Storage        : {storage}")
    print(f"Hour grouping  : {hour_grouping}")
    print(f"Clusters       : {n_clusters}")
    print(f"Config         : {config}")

    # 1. Find project root
    root = find_project_root("BC_NEXUS")
    os.chdir(root)

    # 2. Prepare arguments for RunModel
    args = {
        'scenario': scenario,
        'storage_algorithm': storage,
        'clustering_attributes': {
            'hour_grouping': hour_grouping,
            'n_clusters': n_clusters
        },
        'combined_model_config_path': str(config),
    }

    # 3. Run model
    m = RunModel(**args)
    m.run(build=True)

    print("[bold green]✔ CLEWS run completed successfully.[/bold green]")

# ------------------------------------------------------
# COMMAND: bcnexus plot
# ------------------------------------------------------
@app.command()
def plot(
    scenario: str = typer.Option(..., "--scenario", "-s"),
    storage: str = typer.Option(..., "--storage", "-a"),
    timeslices: int = typer.Option(..., "--timeslices", "-t"),
):
    """Plot results for a scenario."""
    
    print(f"[cyan]▶ Plotting results[/cyan]")
    print(f"Scenario:   {scenario}")
    print(f"Storage:    {storage}")
    print(f"Timeslices: {timeslices}")

    # Here call your real plotting function
    from bcnexus import plots
    plots.main(scenario, storage, timeslices)


def main():
    app()


if __name__ == "__main__":
    main()
