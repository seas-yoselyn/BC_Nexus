"""
Give every crop's land the same cost ladder, so none of them is free.

CapitalCost carries one row per crop-land technology per year, and the values
are crop-independent - they vary only by input regime, and only by regime:

    HI 120    HR 112    II 67    IR 60    LR 10

Barley had none. All nine other crops had all five regimes; LNDBAR*BC1 had
zero rows in CapitalCost.csv. otoole defaults a missing CapitalCost to 0, so
barley land was free while every other crop's land cost 10-120, and the
optimiser noticed.

What that did, in the 6ts CEF_High run of 2026-09-04:

    barley land   0.367 -> 7.496   (20.4x Base)
    barley crop   0.064 -> 1.685   against a demand of 0.059  (28.6x)

Barley alone was 84% of the 1.925 Mt by which that run exceeded total crop
demand. The giveaway was the shape rather than the size: barley land came out
almost evenly spread across all five regimes (1.44 / 1.49 / 1.46 / 1.54 /
1.56) when the cost ladder should have pushed it hard toward LR at 10. An even
spread across regimes priced 10 to 120 means the model saw no gradient at all,
because every one of them was zero.

This is the same failure mode as tools/fix_alfalfa_agv.py, which exists
because alfalfa agrivoltaics had no CapitalCost rows and "let it take over the
generation mix". Worth assuming it is not the last: any technology absent from
a cost file is silently free.

The tool is deliberately general. It finds every crop-land technology missing
from a cost file and fills it from a crop that has rows, rather than
hardcoding barley - the next gap should be fixed by re-running this, not by
writing another script.

Idempotent: crops that already have rows are left alone.

There is no --revert. The values are crop-independent, so a row this tool
added is byte-identical to one that was always there, and an automatic undo
cannot tell them apart - a first attempt at one deleted all ten crops rather
than the one it had added. Use git to undo.

Usage
-----
    python tools/fix_crop_land_costs.py --dry-run    # report only
    python tools/fix_crop_land_costs.py              # apply
"""
import argparse
import csv
import re
import sys
from pathlib import Path

TEMPLATE = Path("data/clews_data/csv_template")

# Cost files whose values are crop-independent, so a donor crop's rows can be
# copied verbatim with only the technology name changed.
COST_FILES = ["CapitalCost.csv"]

# LND<CROP><REGIME>BC1 - the crop-land technologies. The regime suffix matters:
# without it this also matches LNDBARBC1, which is BARREN land, not barley.
CROP_LAND = re.compile(r"^LND([A-Z]{3})(HI|HR|II|IR|LR)(BC1)$")


CLUSTERS = Path("data/clews_data/LandClusterData/clustering_results_BC1.csv")


def parse(tech):
    m = CROP_LAND.match(tech)
    return (m.group(1), m.group(2), m.group(3)) if m else None


def expected_crops():
    """Crop codes the builder will create, from the cluster file's header.

    Reading the cost file alone is not enough: a crop with ZERO rows does not
    appear there at all, so it looks complete by being invisible. That is
    exactly how barley hid - the check has to start from the crops that should
    exist, not from the ones already priced.
    """
    if not CLUSTERS.exists():
        sys.exit(f"missing cluster data: {CLUSTERS}")
    with CLUSTERS.open() as fh:
        header = next(csv.reader(fh))
    crops = {col.split(" ")[0] for col in header[10:] if " " in col}
    if not crops:
        sys.exit(f"no crop columns found in {CLUSTERS}")
    return crops


def load(path):
    """(header line, [(fields, raw line)], newline), preserving line endings."""
    with path.open(newline="") as fh:
        lines = fh.read().splitlines(keepends=True)
    if not lines:
        sys.exit(f"empty file: {path}")
    crlf = sum(1 for ln in lines if ln.endswith("\r\n"))
    newline = "\r\n" if crlf * 2 >= len(lines) else "\n"
    body = [(next(csv.reader([ln])), ln) for ln in lines[1:] if ln.strip()]
    return lines[0], body, newline


def save(path, header, body, newline, dry_run):
    if dry_run:
        return
    with path.open("w", newline="") as fh:
        fh.write(header if header.endswith(("\n", "\r")) else header + newline)
        for _, raw in body:
            fh.write(raw if raw.endswith(("\n", "\r")) else raw + newline)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", default=str(TEMPLATE))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    template = Path(a.template)
    if not template.is_dir():
        sys.exit(f"not a directory: {template}\nrun from the repository root")

    expected = expected_crops()
    print(f"crops the builder will create: {', '.join(sorted(expected))}\n")
    changed = 0
    for name in COST_FILES:
        path = template / name
        if not path.exists():
            print(f"  {name:<24} not present, skipped")
            continue
        header, body, newline = load(path)

        present = {}          # crop -> {regime -> [(fields, raw)]}
        for fields, raw in body:
            got = parse(fields[1])
            if got:
                crop, regime, _ = got
                present.setdefault(crop, {}).setdefault(regime, []).append(
                    (fields, raw))
        if not present:
            print(f"  {name:<24} no crop-land rows found, skipped")
            continue

        regimes = max((set(v) for v in present.values()), key=len)
        complete = [c for c, v in present.items() if set(v) == regimes]
        # Start from the crops that SHOULD exist, so a crop with no rows at
        # all is caught rather than being invisible.
        missing = sorted(c for c in expected
                         if set(present.get(c, {})) != regimes)

        if not missing:
            print(f"  {name:<24} ok, all {len(expected)} crops complete")
            continue
        if not complete:
            print(f"  {name:<24} no complete crop to copy from, skipped")
            continue

        donor = sorted(complete)[0]
        for crop in missing:
            have = set(present.get(crop, {}))
            need = sorted(regimes - have)
            new = []
            for regime in need:
                for fields, raw in present[donor][regime]:
                    f = list(fields)
                    f[1] = f"LND{crop}{regime}BC1"
                    new.append((f, ",".join(f) + newline))
            sample = f"{new[0][0][1]} = {new[0][0][-1]}" if new else ""
            print(f"  {name:<24} ADDING {len(new):>4} rows for {crop} "
                  f"({', '.join(need)}) from {donor}   {sample}")
            body.extend(new)
            changed += 1
        save(path, header, body, newline, a.dry_run)

    print(f"\n{changed} change(s) {'would be made' if a.dry_run else 'made'}")
    if a.dry_run:
        print("--dry-run: nothing written")


if __name__ == "__main__":
    main()
