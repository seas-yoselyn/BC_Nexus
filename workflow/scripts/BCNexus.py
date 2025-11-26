import sys
from pathlib import Path
from typing import Dict, Any
import bcnexus.utils as utils

# ============================================================
# User-defined scenario list
# ============================================================
scenarios = [
    # 'Base_CNZ',
    'Base_CNZ_noCCS',
    # 'CNZ_LIMITED_CO2_PTY'
    # 'CNZ_LIMITED_CO2',
    # 'NUC_standard_2028',
    # 'NUC_standard_2028_2xCost',
    # 'NUC_standard_2030',
    # 'NUC_standard_2030_2xCost',
    # 'NUC_standard_2035',
    # 'NUC_standard_2035_2xCost',
    # 'NUC_standard_2035_4xCost',
    # 'IMP_USA_100'
    # 'HYDROGEN', # contains bugs
]


# ============================================================
# Default model run attributes
# ============================================================
run_attributes: Dict[str, Any] = dict(
    storage_algorithm="Kotzur",
    clustering_attributes=dict(
        hour_grouping=12,   # must divide 24
        n_clusters=4
    )
)


# ============================================================
# Helper: validate run_attributes structure
# ============================================================
def validate_run_attributes(attrs: Dict[str, Any]) -> None:
    if "storage_algorithm" not in attrs:
        raise KeyError("run_attributes must contain 'storage_algorithm'.")

    if "clustering_attributes" not in attrs:
        raise KeyError("run_attributes must contain 'clustering_attributes' dict.")

    cl = attrs["clustering_attributes"]

    if not isinstance(cl, dict):
        raise TypeError("'clustering_attributes' must be a dict.")

    if "hour_grouping" not in cl or "n_clusters" not in cl:
        raise KeyError("clustering_attributes must contain 'hour_grouping' and 'n_clusters'.")

    hg = cl["hour_grouping"]
    if not isinstance(hg, int) or hg <= 0:
        raise ValueError(f"Invalid hour_grouping={hg}. Must be a positive integer.")

    if 24 % hg != 0:
        raise ValueError(f"hour_grouping={hg} must divide 24 evenly (24 % hg == 0).")

    nc = cl["n_clusters"]
    if not isinstance(nc, int) or nc <= 0:
        raise ValueError(f"Invalid n_clusters={nc}. Must be a positive integer.")


# ============================================================
# Model runner
# ============================================================
def run_model(scenario: str, attributes: Dict[str, Any]) -> None:
    """
    Run a CLEWS scenario with robust input validation.
    """
    print(f"\n=== [RUN] Scenario: {scenario} ===")

    # --- Validate attributes once ---
    validate_run_attributes(attributes)

    # Merge attributes and scenario safely
    args = {**attributes, "run_scenario": scenario}

    try:
        from bcnexus.clews.runner import RunModel
    except ImportError as e:
        print(f"[ERROR] Unable to import RunModel: {e}")
        sys.exit(1)

    try:
        model = RunModel(**args)
    except TypeError as e:
        raise RuntimeError(f"Failed to initialize RunModel with args={args}\n{e}")

    try:
        model.run(
            build=False,
            include_livestock=False,
            solver_name="gurobi",
            threads=32,
            machine_id="srye-deltae-07",
        )
        print(f"[OK] Scenario '{scenario}' completed successfully.")
    except Exception as e:
        print(f"[ERROR] Scenario '{scenario}' failed during execution:\n{e}")
        raise


# ============================================================
# Plotting wrapper
# ============================================================
def plot_results(scenario: str, attributes: Dict[str, Any]) -> None:
    """
    Plot results with robust checks.
    """
    print(f"--- [PLOT] Scenario: {scenario} ---")

    try:
        validate_run_attributes(attributes)
    except Exception as e:
        print(f"[ERROR] Plot cannot proceed due to invalid attributes: {e}")
        return

    cl = attributes["clustering_attributes"]

    timeslices = (24 // cl["hour_grouping"]) * cl["n_clusters"]
    
    if timeslices <= 0:
        print(f"[ERROR] Computed invalid timeslices={timeslices}.")
        return

    try:
        import bcnexus.plots as plotter
    except ImportError as e:
        print(f"[ERROR] Failed to import plotting module: {e}")
        return

    try:
        plotter.main(scenario, attributes["storage_algorithm"], timeslices=timeslices)
        print(f"[OK] Plot completed for '{scenario}'.")
    except Exception as e:
        print(f"[ERROR] Plotting failed for '{scenario}':\n{e}")


# ============================================================
# Batch Execution Loop
# ============================================================
if __name__ == "__main__":
    print("==============================")
    print("   BC-NEXUS BATCH EXECUTION   ")
    print("==============================")

    for scen in scenarios:
        try:
            run_model(scen, run_attributes)
        except Exception as e:
            utils.prin(f"[CRITICAL] Model failed for '{scen}'. Continuing to next scenario.\n{e}")
            continue

        # Attempt plotting even if model fails
        try:
            plot_results(scen, run_attributes)
        except Exception as e:
            print(f"[CRITICAL] Plotting failed for '{scen}'.\n{e}")
            continue

    print("\n=== ALL SCENARIOS DONE ===\n")
