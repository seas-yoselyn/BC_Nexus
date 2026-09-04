"""
Why does alfalfa land collapse around 2028?

Run from the repo root with no arguments - it finds the runs itself:

    python check_2028_cliff.py                 # every run it can find
    python check_2028_cliff.py AGV_SUB         # just runs matching a name
    python check_2028_cliff.py path/to/result_csvs_gurobi

Read-only. Changes nothing, needs no solver, no rebuild.
"""
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    sys.exit("needs pandas. Try:  %s check_2028_cliff.py"
             % (Path.home() / "anaconda3" / "python.exe"))

ALF = {1: "ALFHI", 2: "ALFII", 3: "ALFHR", 4: "ALFIR", 5: "ALFLR"}
COVER = {51: "Barren", 52: "Forest", 53: "Grassland",
         54: "Built-up(power)", 55: "Water", 56: "OtherAg"}
NEEDED = "TotalAnnualTechnologyActivityByMode.csv"
SETS = Path("data/clews_data/SETs")


def real_modes():
    """(technology, mode) pairs that actually appear in the IAR or OAR.

    A technology-mode with neither is a phantom: it sits in no constraint and
    carries no cost, so the LP is indifferent to its value and a barrier solve
    without crossover parks it anywhere. Those values are not land and must not
    be summed as if they were.
    """
    keep = set()
    for name in ("InputActivityRatio.csv", "OutputActivityRatio.csv"):
        f = SETS / name
        if not f.exists():
            return None
        d = pd.read_csv(f)
        d = norm(d)
        if not {"TECHNOLOGY", "MODE_OF_OPERATION", "VALUE"} <= set(d.columns):
            return None
        d = d[d.VALUE.astype(float) != 0]
        keep |= set(zip(d.TECHNOLOGY, d.MODE_OF_OPERATION.astype(int)))
    return keep

# otoole has used both long and short column names over the years.
COLMAP = {"r": "REGION", "t": "TECHNOLOGY", "m": "MODE_OF_OPERATION",
          "y": "YEAR", "value": "VALUE", "f": "FUEL"}


def norm(df, stem=None):
    """Rename short otoole columns to the long form, if present.

    Older result files name the value column after the variable itself
    (e.g. 'TotalCapacityAnnual') rather than 'VALUE'.
    """
    ren = {c: COLMAP[c] for c in df.columns if c in COLMAP}
    if stem and stem in df.columns:
        ren[stem] = "VALUE"
    return df.rename(columns=ren)


def find_runs(root: Path, want: str | None):
    """Any directory holding the file we need counts as a run."""
    hits = sorted({p.parent for p in root.rglob(NEEDED)})
    if want:
        hits = [h for h in hits if want.lower() in str(h).lower()]
    else:
        hits = [h for h in hits if "archive" not in str(h).lower()]
    return hits


def label(p: Path) -> str:
    for part in p.parts[::-1]:
        if part.startswith("Model_"):
            return part
    return str(p)


def report(run: Path):
    print("\n" + "=" * 72)
    print(label(run))
    print("=" * 72)

    bym = norm(pd.read_csv(run / NEEDED), Path(NEEDED).stem)
    if not {"TECHNOLOGY", "MODE_OF_OPERATION", "VALUE"} <= set(bym.columns):
        print(f"  older column layout {list(bym.columns)[:4]} - skipping")
        return
    bym = bym[bym.TECHNOLOGY.str.startswith("LNDAGR")].copy()
    if bym.empty:
        print("  no LNDAGR rows - skipping")
        return
    bym["MODE_OF_OPERATION"] = bym.MODE_OF_OPERATION.astype(int)

    keep = real_modes()
    if keep is None:
        print("  [warn] SETs not found - phantom modes NOT filtered")
    else:
        before = len(bym)
        pairs = list(zip(bym.TECHNOLOGY, bym.MODE_OF_OPERATION))
        bym = bym[[p in keep for p in pairs]]
        dropped = before - len(bym)
        if dropped:
            print(f"  [filtered {dropped} phantom technology-mode rows "
                  f"with no IAR/OAR]")

    alf = bym[bym.MODE_OF_OPERATION.isin(ALF)].groupby("YEAR").VALUE.sum()
    if alf.empty or len(alf) < 3:
        print("  no alfalfa activity - skipping")
        return

    cov = (bym[bym.MODE_OF_OPERATION.isin(COVER)]
           .assign(C=lambda x: x.MODE_OF_OPERATION.map(COVER))
           .pivot_table(index="YEAR", columns="C", values="VALUE",
                        aggfunc="sum").fillna(0.0))

    yr = alf.diff().idxmin()
    loss = -alf.diff()[yr]
    print(f"\nQ1. Biggest alfalfa drop: {loss:.2f} kkm2 in {yr}"
          f"   ({alf[yr-1]:.2f} -> {alf[yr]:.2f})")
    for c in cov.columns:
        g = cov[c].diff()[yr]
        if abs(g) > 1e-6:
            print(f"      {c:<17}{g:>+10.2f}   {100*g/loss:>+7.1f}% of the loss")

    print(f"\nQ2. Alfalfa by cluster, {yr-1} -> {yr}")
    cl = (bym[bym.MODE_OF_OPERATION.isin(ALF)]
          .pivot_table(index="YEAR", columns="TECHNOLOGY",
                       values="VALUE", aggfunc="sum").fillna(0.0))
    for t in sorted(cl.columns):
        a, b = cl[t].get(yr-1, 0.0), cl[t].get(yr, 0.0)
        if max(a, b) > 1e-6:
            print(f"      {t[-3:]:<6}{a:>10.2f} ->{b:>10.2f}{b-a:>+10.2f}")

    print("\nQ3. Was the pre-drop level forced by capacity, or chosen?")
    f = run / "TotalCapacityAnnual.csv"
    if not f.exists():
        print("      TotalCapacityAnnual.csv not in this run - can't tell")
        return
    cap = norm(pd.read_csv(f), "TotalCapacityAnnual")
    c = cap[cap.TECHNOLOGY.str.startswith("LNDALF")]
    if c.empty:
        print("      no LNDALF capacity rows")
        return
    s = c.groupby("YEAR").VALUE.sum()
    print(f"      {'YEAR':<7}{'capacity':>11}{'activity':>11}{'slack':>10}")
    for y in [yr-2, yr-1, yr, yr+1]:
        if y in s.index and y in alf.index:
            print(f"      {y:<7}{s[y]:>11.3f}{alf[y]:>11.3f}{s[y]-alf[y]:>10.3f}")
    sl = s.get(yr-1, 0) - alf.get(yr-1, 0)
    print(f"\n      VERDICT: slack before the drop = {sl:.3f}")
    if abs(sl) < 1e-3:
        print("      -> capacity was BINDING. The cliff is LNDALF residual"
              " capacity expiring.")
        print("         Nothing to do with forest - you can fix this freely.")
    else:
        print("      -> capacity was SLACK. The cliff is economic, i.e. the"
              " mode-52")
        print("         forest cost. That's the file you don't want to touch.")


root = Path.cwd()
arg = sys.argv[1] if len(sys.argv) > 1 else None
if arg and (Path(arg) / NEEDED).exists():
    runs = [Path(arg)]
else:
    runs = find_runs(root, arg)

if not runs:
    print(f"No runs found under {root}")
    print(f"(looked for any folder containing {NEEDED})")
    print("\nIf your results are elsewhere, pass the folder:")
    print("    python check_2028_cliff.py D:/path/to/result_csvs_gurobi")
    sys.exit(1)

print(f"Found {len(runs)} run(s) under {root}")
for r in runs:
    try:
        report(r)
    except Exception as e:
        print(f"\n  {label(r)}: failed - {type(e).__name__}: {e}")
