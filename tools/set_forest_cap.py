"""
Cap forest area so it cannot expand onto cropland.

Adds TotalTechnologyAnnualActivityUpperLimit rows for LNDFORBC1 to a set of
built OSeMOSYS input CSVs. Leaves the mode-52 forest VariableCost untouched.

WHY: the negative VariableCost on mode 52 pays the model to create forest.
With land a zero-sum allocation, it outbids low-value cropland and converts
it in a single year. Capping forest area stops the expansion while keeping
every hectare of existing forest, and does not alter anyone's cost logic.

SAFE: a run with LNDFORBC1 = 0 solves to optimality, so LNDFORBC1 = 0 is
feasible. Any upper limit >= 0 therefore preserves a feasible solution and
cannot make the model infeasible.

Apply to the BUILT inputs (data/clews_data/clews_build_data/...), which are
gitignored, so no tracked file changes and a rebuild reverts it.

Usage
-----
  # derive a year-varying cap from a previous run (recommended)
  python set_forest_cap.py --inputs <built_csv_dir> --from-results <result_csvs_dir>

  # flat cap at a level you choose
  python set_forest_cap.py --inputs <built_csv_dir> --value 522.2

  # see what would change, write nothing
  python set_forest_cap.py --inputs <dir> --from-results <dir> --dry-run

  # remove the cap again
  python set_forest_cap.py --inputs <built_csv_dir> --revert
"""
import argparse
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    sys.exit("needs pandas")

TECH = "LNDFORBC1"
PARAM = "TotalTechnologyAnnualActivityUpperLimit"
ACT = "TotalAnnualTechnologyActivityByMode.csv"
FOREST_MODE = 52
ALF_MODES = [1, 2, 3, 4, 5]
COL = {"r": "REGION", "t": "TECHNOLOGY", "m": "MODE_OF_OPERATION", "y": "YEAR"}


def norm(df, stem=None):
    ren = {c: COL[c] for c in df.columns if c in COL}
    if stem and stem in df.columns:
        ren[stem] = "VALUE"
    return df.rename(columns=ren)


def forest_and_cliff(results: Path):
    """Return (forest series, cliff year, pre-cliff max) from a finished run."""
    f = results / ACT
    if not f.exists():
        sys.exit(f"no {ACT} in {results}")
    d = norm(pd.read_csv(f), Path(ACT).stem)
    d = d[d.TECHNOLOGY.str.startswith("LNDAGR")].copy()
    d["MODE_OF_OPERATION"] = d.MODE_OF_OPERATION.astype(int)
    forest = d[d.MODE_OF_OPERATION == FOREST_MODE].groupby("YEAR").VALUE.sum()
    alf = d[d.MODE_OF_OPERATION.isin(ALF_MODES)].groupby("YEAR").VALUE.sum()
    if forest.empty:
        sys.exit("no mode-52 (forest) activity in that run")
    cliff = alf.diff().idxmin() if not alf.empty else forest.index.max()
    pre = forest[forest.index < cliff]
    return forest, cliff, (pre.max() if len(pre) else forest.max())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", required=True,
                    help="directory of built OSeMOSYS input CSVs")
    ap.add_argument("--from-results",
                    help="a finished result_csvs_* dir to derive the cap from")
    ap.add_argument("--value", type=float, help="flat cap value instead")
    ap.add_argument("--mode", choices=("track", "flat"), default="track",
                    help="track: cap follows the run's own forest path, never "
                         "exceeding its pre-cliff peak (closes the end-of-"
                         "horizon gap). flat: constant at the pre-cliff peak.")
    ap.add_argument("--revert", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    inp = Path(a.inputs)
    target = inp / f"{PARAM}.csv"
    if not target.exists():
        sys.exit(f"not found: {target}\n(point --inputs at the built CSV folder)")

    # read everything as text so untouched rows survive byte-identical
    df = pd.read_csv(target, dtype=str, keep_default_na=False)
    for c in ("REGION", "TECHNOLOGY", "YEAR", "VALUE"):
        if c not in df.columns:
            sys.exit(f"unexpected columns in {target.name}: {list(df.columns)}")
    existing = df[df.TECHNOLOGY == TECH]
    kept = df[df.TECHNOLOGY != TECH]

    if a.revert:
        if existing.empty:
            print(f"no {TECH} rows present - nothing to revert")
            return
        print(f"removing {len(existing)} {TECH} rows")
        if not a.dry_run:
            kept.to_csv(target, index=False)
            print(f"wrote {target}")
        return

    years = sorted(df.YEAR.unique(), key=int)
    if a.from_results:
        forest, cliff, pre_max = forest_and_cliff(Path(a.from_results))
        print(f"cliff year detected: {cliff}")
        print(f"pre-cliff forest maximum: {pre_max:.2f}")
        if a.mode == "flat":
            cap = {y: round(pre_max, 3) for y in years}
        else:
            cap = {y: round(min(forest.get(int(y), pre_max), pre_max), 3)
                   for y in years}
    elif a.value is not None:
        cap = {y: a.value for y in years}
    else:
        sys.exit("give either --from-results or --value")

    region = df.REGION.iloc[0] if len(df) else "REGION1"
    new = pd.DataFrame({"REGION": region, "TECHNOLOGY": TECH,
                        "YEAR": [str(y) for y in cap],
                        "VALUE": [f"{v:g}" for v in cap.values()]})
    out = pd.concat([kept, new], ignore_index=True)

    print(f"\n{TECH} cap ({a.mode}), {len(new)} rows:")
    for y in list(cap)[:3] + ["..."] + list(cap)[-3:]:
        print("   ..." if y == "..." else f"   {y}: {cap[y]:.2f}")
    if not existing.empty:
        print(f"(replacing {len(existing)} existing {TECH} rows)")

    if a.dry_run:
        print("\n--dry-run: nothing written")
        return
    out.to_csv(target, index=False)
    print(f"\nwrote {target}  ({len(kept)} other rows preserved)")


if __name__ == "__main__":
    main()
