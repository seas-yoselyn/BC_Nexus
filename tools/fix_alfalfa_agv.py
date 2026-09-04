"""
Make sure the alfalfa agrivoltaic technologies exist everywhere the other
AGV crops do, in the BASE-CASE input templates.

Adding 'ALF' to AGV_ELIGIBLE_CROPS creates five LNDAGVALF*BC1 technologies.
Any parameter file that has rows for LNDAGVMAI* but none for LNDAGVALF* will
silently give alfalfa an otoole default - CapitalCost 0 above all, which made
alfalfa agrivoltaics free and let it take over the generation mix.

This copies the maize AGV rows to alfalfa. AGV values are crop-independent
(they vary by input regime, not by crop), so maize is the correct template.

Only the base-case files are touched. Scenario overrides in
config/scenarios_bcnexus.yaml still apply on top at overlay time - e.g. the
subsidy scenarios drop capital cost to the conventional agriculture ladder.

Idempotent: files that already have alfalfa rows are left alone.

Usage
-----
    python tools/fix_alfalfa_agv.py --dry-run     # report only
    python tools/fix_alfalfa_agv.py               # apply
    python tools/fix_alfalfa_agv.py --revert      # remove the ALF rows again
"""
import argparse
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    sys.exit("needs pandas")

TEMPLATE = Path("data/clews_data/csv_template")
SRC, DST = "LNDAGVMAI", "LNDAGVALF"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", default=str(TEMPLATE),
                    help="csv_template directory")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--revert", action="store_true")
    a = ap.parse_args()

    d = Path(a.template)
    if not d.is_dir():
        sys.exit(f"not a directory: {d}\nrun from the repository root")

    changed = ok = 0
    for f in sorted(d.glob("*.csv")):
        try:
            df = pd.read_csv(f, dtype=str, keep_default_na=False)
        except Exception:
            continue
        if "TECHNOLOGY" not in df.columns:
            continue
        src = df[df.TECHNOLOGY.str.startswith(SRC)]
        dst = df[df.TECHNOLOGY.str.startswith(DST)]

        if a.revert:
            if dst.empty:
                continue
            print(f"  {f.name:<44} removing {len(dst)} alfalfa rows")
            changed += 1
            if not a.dry_run:
                df[~df.TECHNOLOGY.str.startswith(DST)].to_csv(f, index=False)
            continue

        if src.empty:
            continue
        if not dst.empty:
            print(f"  {f.name:<44} ok ({len(dst)} alfalfa rows already)")
            ok += 1
            continue

        new = src.copy()
        new["TECHNOLOGY"] = new.TECHNOLOGY.str.replace(SRC, DST, regex=False)
        sample = f"{new.iloc[0].TECHNOLOGY} = {new.iloc[0][new.columns[-1]]}"
        print(f"  {f.name:<44} ADDING {len(new):>4} rows   ({sample})")
        changed += 1
        if not a.dry_run:
            pd.concat([df, new], ignore_index=True).to_csv(f, index=False)

    print(f"\n{changed} file(s) {'would change' if a.dry_run else 'changed'}"
          f", {ok} already correct")
    if a.dry_run:
        print("--dry-run: nothing written")
        return

    if not a.revert:
        print("\nalfalfa AGV base-case values now in place:")
        for name in ("CapitalCost", "FixedCost", "OperationalLife",
                     "CapacityToActivityUnit"):
            p = d / f"{name}.csv"
            if not p.exists():
                continue
            t = pd.read_csv(p, dtype=str, keep_default_na=False)
            r = t[t.TECHNOLOGY.str.startswith(DST)]
            if r.empty:
                print(f"  {name:<24} MISSING")
            else:
                print(f"  {name:<24} {len(r):>4} rows, "
                      f"first = {r.iloc[0][r.columns[-1]]}")


if __name__ == "__main__":
    main()
