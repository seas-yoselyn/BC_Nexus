"""
Do the emission limits leave room for the emissions the demands force?

Emissions used to be almost entirely inert: 87 of 104 EmissionActivityRatio
keys named a mode their technology did not have, so they contributed zero.
AnnualEmissionLimit and ModelPeriodEmissionLimit therefore never bound, and
nobody had reason to check whether their values were realistic. Now that the
rows are generated onto live (technology, mode) pairs, those limits bind for
the first time - and a limit that was never exercised is exactly the kind of
placeholder that turns a working model infeasible.

This computes a LOWER BOUND on annual emissions from the demand side alone:

  livestock  AccumulatedAnnualDemand / LivestockCommodityYield -> thousand
             head -> LivestockEmissionFactors. Demand is a floor the optimiser
             must meet, so this herd, and these emissions, cannot be avoided.

  crop soil  CropSoilN2O x crop land area. Land area is a decision variable,
             so this one is scenario-dependent; --crop-land sets the assumed
             area (default: the CROP_RESERVE that pin_historical_land leaves
             free, which is roughly what past runs drew).

A lower bound is what matters here: if the floor already exceeds the cap, the
solve is infeasible before the optimiser makes a single choice, and no solver
setting will change that.

Reads only model_structure and the parameter CSVs. Writes nothing.

    python tools/check_emission_headroom.py
    python tools/check_emission_headroom.py --crop-land 44
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bcnexus.clews import model_structure as ms

TEMPLATE = Path("data/clews_data/csv_template")
CROP_RESERVE_DEFAULT = 50.0


def load(name):
    p = TEMPLATE / name
    if not p.exists():
        sys.exit(f"missing {p}; run from the repository root")
    return pd.read_csv(p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crop-land", type=float, default=CROP_RESERVE_DEFAULT,
                    help="assumed crop land area, thousand sq km "
                         f"(default {CROP_RESERVE_DEFAULT}, the crop reserve)")
    ap.add_argument("--year", type=int, default=ms.snapshot["start"])
    a = ap.parse_args()

    demand = load("AccumulatedAnnualDemand.csv")
    annual = load("AnnualEmissionLimit.csv")
    period = load("ModelPeriodEmissionLimit.csv")
    penalty = load("EmissionsPenalty.csv")

    years = ms.snapshot["end"] - ms.snapshot["start"] + 1
    d = demand[demand.YEAR == a.year].set_index("FUEL")["VALUE"].to_dict()

    print(f"Emission headroom, year {a.year}, {years}-year horizon\n")

    # ---- herd forced by livestock commodity demand ----------------------
    print("Herd forced by demand (thousand head):")
    heads = {}
    for pw, attrs in ms.LivestockPathways.items():
        produce = attrs["produce"]
        fuel = f"LVS{produce}"
        if fuel not in d:
            continue
        heads.setdefault(produce, d[fuel] / ms.LivestockCommodityYield[produce])
    # One pathway per produce carries the demand; BEF has two (BEFN/BEFC) with
    # identical factors, so the split does not change the emission total.
    pathway_for = {}
    for pw, attrs in ms.LivestockPathways.items():
        pathway_for.setdefault(attrs["produce"], pw)
    for produce, h in sorted(heads.items()):
        print(f"  {produce}  demand {d['LVS' + produce]:9.2f} / yield "
              f"{ms.LivestockCommodityYield[produce]:<7} = {h:9.2f}")

    # ---- emissions ------------------------------------------------------
    forced = {}
    for produce, h in heads.items():
        pw = pathway_for[produce]
        for emission, factor in ms.LivestockEmissionFactors[pw].items():
            forced[emission] = forced.get(emission, 0.0) + h * factor
    for emission, factor in ms.CropSoilN2O.items():
        forced[emission] = forced.get(emission, 0.0) + a.crop_land * factor

    lim_a = annual[annual.YEAR == a.year].set_index("EMISSION")["VALUE"].to_dict()
    lim_p = period.set_index("EMISSION")["VALUE"].to_dict()
    pen = penalty[penalty.YEAR == a.year].set_index("EMISSION")["VALUE"].to_dict()

    print(f"\nForced annual emissions vs limits "
          f"(crop land assumed {a.crop_land} thousand sq km):\n")
    hdr = (f"  {'EMISSION':<10}{'forced/yr':>12}{'annual cap':>12}{'use':>8}"
           f"{'  ':2}{'forced total':>14}{'period cap':>12}{'use':>8}"
           f"{'':>4}{'priced':>7}")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))

    breaches = []
    for emission in sorted(set(forced) | set(lim_a) | set(lim_p)):
        f = forced.get(emission, 0.0)
        total = f * years
        la, lp = lim_a.get(emission), lim_p.get(emission)
        ua = f / la if la else None
        up = total / lp if lp else None
        row = (f"  {emission:<10}{f:>12.1f}"
               f"{(f'{la:.0f}' if la is not None else '-'):>12}"
               f"{(f'{ua:.2f}x' if ua is not None else '-'):>8}  "
               f"{total:>14.1f}"
               f"{(f'{lp:.0f}' if lp is not None else '-'):>12}"
               f"{(f'{up:.2f}x' if up is not None else '-'):>8}"
               f"{'':>4}{('yes' if emission in pen else 'no'):>7}")
        over = (ua is not None and ua > 1) or (up is not None and up > 1)
        print(row + ("   <== OVER" if over else ""))
        if over:
            breaches.append((emission, ua, up))

    print("\nCO2 is excluded from the forced total above: it comes from the")
    print("energy system, which this script does not solve. Its own cap is")
    print("listed for reference only.")

    if not breaches:
        print("\nNo forced breach. The emission limits leave room for the")
        print("emissions the demands require; anything that binds after this")
        print("is a genuine optimiser trade-off.")
        return 0

    print(f"\n{len(breaches)} FORCED BREACH(ES) - infeasible before the")
    print("optimiser chooses anything:")
    for emission, ua, up in breaches:
        parts = []
        if ua is not None and ua > 1:
            parts.append(f"{ua:.2f}x the annual cap")
        if up is not None and up > 1:
            parts.append(f"{up:.2f}x the model-period cap")
        print(f"  {emission}: {' and '.join(parts)}")
    print("\nThe demands are floors and the caps are hard, so no solver")
    print("setting reaches this. Either the caps are placeholders that need")
    print("real values, or the emission factors need the unit fix the")
    print("Emissions dict in model_structure still flags as pending.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
