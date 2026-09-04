"""
Stop forest moving in years that have already happened, and cap precipitation.

Two defects, and only two:

1. MINPRCBC1 (precipitation) has no TotalTechnologyAnnualActivityUpperLimit,
   while MINLNDBC1 (land) has one. Rainfall was a free decision variable and
   reached 12550 against a physically correct 739, so every extra hectare the
   optimiser allocated paid for itself in extra water.

2. Forest has no anchor of any kind. Every other land cover is already pinned
   by TechnologyActivityByModeLowerLimit floors, which match the solved runs
   to within 0.03:

       mode 51 barren     floor 148.342   run 148.367
       mode 53 grassland  floor 158.904   run 158.928
       mode 54 built-up   floor   3.730   run   3.757
       mode 55 water      floor  43.042   run  43.067
       mode 52 FOREST     floor    NONE   run 524.176   <- floats
       mode 56 otherAg    floor    NONE   run   0.061

   Forest is the one cover nobody constrained, so it absorbed every slack in
   the model. Across the Sep 2026 runs it ranged 461.262 to 524.176 in 2021 -
   63 thousand sq km moving in a year that has already happened, driven by
   scenarios that override nothing but energy demand.

An earlier version of this tool pinned all six covers to values scaled from
the 2010 land-cover raster. That was wrong twice over: it duplicated a
calibration that already existed, and it contradicted it. Built-up land is the
clearest case - the raster says 1.100, the maintained floor says 3.730,
because the modellers already knew the raster undercounts it. Pinning built-up
at the raster value made the model infeasible, and Gurobi's IIS named exactly
that conflict:

    AAC2_TotalAnnualTechnologyActivityUpperLimit(REGION1,LNDBLTBC1,2023)
    LU2_TechnologyActivityByModeLL(REGION1,LNDAGRBC1C0x,54,2023)

The lesson is worth keeping: pin what nothing else pins, and check for an
existing calibration before adding one.

Choosing the forest value
-------------------------
Forest is pinned to what closes the land budget:

    forest = TOTAL_AREA - (existing cover floors) - CROP_RESERVE
             - NON_CLUSTER_LAND_RESERVE

which lands near 506. That is ~55% of BC, consistent with the province's real
forest cover and with the 518-524 the well-behaved runs produce on their own.
It is deliberately NOT the raster's 372.730: that implies BC is 40% forested
and is a known undercount - roughly 4100 cells inside BC are missing from the
clustering, almost certainly no-data in faocmb_2010.tif, and they are
forest-heavy. Override with --forest if you have an inventory figure.

Read FREEZE_THROUGH as "years the optimiser may not rewrite", not as years for
which measurements are held: the raster is a single 2010 snapshot, eleven
years before the base year, so every frozen year takes the same value.

Idempotent. --revert removes everything this tool wrote.

Usage
-----
    python tools/pin_historical_land.py --dry-run    # report only
    python tools/pin_historical_land.py              # apply
    python tools/pin_historical_land.py --revert     # undo
"""
import argparse
import csv
import sys
from pathlib import Path

TEMPLATE = Path("data/clews_data/csv_template")
CLUSTERS = Path("data/clews_data/LandClusterData")

# Last year the optimiser may not rewrite. The model starts in 2021; today is
# 2026, so every elapsed year is frozen.
FREEZE_THROUGH = 2025

# Land area the model represents, thousand sq km. BC's real land area.
TOTAL_AREA = 925.0

# Cropland to leave free. The observed cultivated area is 12.156, but the model
# cannot meet crop demand on it: 2021 demand is 2.666 Mt and the pre-fix runs
# needed ~38 to produce it. That gap is a yield problem, not a land problem -
# sets_n_ratios notes cluster-mean yields are "a dilution artifact of averaging
# yields over clusters dominated by non-crop cells", and diluted yields need
# more land per tonne. Sized from those runs (37.954 at 6ts, 43.566 at 24ts)
# with margin. Lower it once the yields are de-diluted.
CROP_RESERVE = 50.0

# Livestock pasture (LivestockLandArea sums to 8.989 at base year, runs grow it
# to 12.544) plus agrivoltaic arrays (up to ~0.9). Neither is in the cluster
# file, so both need room reserved off the top.
NON_CLUSTER_LAND_RESERVE = 15.0

YEAR_START, YEAR_END = 2021, 2050
REGION = "REGION1"
REGION_CODE = "BC1"
CLUSTER_PREFIX = "LNDAGR" + REGION_CODE + "C"

FOREST = "LNDFORBC1"
PRECIP_SUPPLY = "MINPRCBC1"

# Land-cover technologies already pinned by TechnologyActivityByModeLowerLimit,
# and the mode that pins each. Read at run time so the budget follows the
# calibration rather than a copy of it.
CALIBRATED_MODES = {51: "LNDBARBC1", 53: "LNDGRSBC1",
                    54: "LNDBLTBC1", 55: "LNDWATBC1"}

ACTIVITY_LO = "TotalTechnologyAnnualActivityLowerLimit.csv"
ACTIVITY_HI = "TotalTechnologyAnnualActivityUpperLimit.csv"
CAPACITY_LO = "TotalAnnualMinCapacity.csv"
CAPACITY_HI = "TotalAnnualMaxCapacity.csv"
MODE_LO = "TechnologyActivityByModeLowerLimit.csv"

# Everything this tool has ever written, so --revert and re-apply clean up
# rows left by older versions that pinned all six covers.
LEGACY_TECHS = {"LNDBARBC1", "LNDBLTBC1", "LNDGRSBC1",
                "LNDWATBC1", "LNDOTHBC1", FOREST}


def load(path):
    """Return (header_line, [(fields, raw_line), ...], newline).

    Lines are kept verbatim: these files carry mixed CRLF/LF endings, and
    rewriting them through csv.writer normalises every line, burying the real
    change in hundreds of lines of whitespace diff.
    """
    with path.open(newline="") as fh:
        lines = fh.read().splitlines(keepends=True)
    if not lines:
        sys.exit(f"empty parameter file: {path}")
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


def make_rows(records, newline):
    return [(r, ",".join(r) + newline) for r in records]


def drop(body, techs=(), prefix=None):
    """Remove rows for these technologies, or any tech with this prefix."""
    keep = []
    for fields, raw in body:
        tech = fields[1]
        if tech in techs or (prefix and tech.startswith(prefix)):
            continue
        keep.append((fields, raw))
    return keep


def existing_cover_floors(template):
    """Sum of the already-calibrated cover floors, per year."""
    path = template / MODE_LO
    if not path.exists():
        sys.exit(f"missing {path}; cannot read the existing calibration")
    out = {}
    with path.open(newline="") as fh:
        for r in csv.DictReader(fh):
            mode = int(float(r["MODE_OF_OPERATION"]))
            if mode in CALIBRATED_MODES:
                y = int(float(r["YEAR"]))
                out[y] = out.get(y, 0.0) + float(r["VALUE"])
    if not out:
        sys.exit("no calibrated cover floors found; check "
                 f"{MODE_LO} and CALIBRATED_MODES")
    return out


def precipitation_cap(total_area):
    """Rain the region receives: sum of cluster area x depth, scaled to area."""
    main, prc = (CLUSTERS / "clustering_results_BC1.csv",
                 CLUSTERS / "clustering_results_prc_BC1.csv")
    for p in (main, prc):
        if not p.exists():
            sys.exit(f"missing cluster data: {p}")
    with prc.open() as fh:
        depth = {r["cluster"]: float(r["precipitation"])
                 for r in csv.DictReader(fh)}
    with main.open() as fh:
        rows = list(csv.DictReader(fh))
    clustered = sum(float(r["land_area_total"]) for r in rows)
    volume = sum(float(r["land_area_total"]) * depth[r["cluster"]] for r in rows)
    areas = {CLUSTER_PREFIX + r["cluster"].zfill(2): float(r["land_area_total"])
             for r in rows}
    scale = total_area / clustered
    return volume * scale, {t: v * scale for t, v in areas.items()}, clustered


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", default=str(TEMPLATE))
    ap.add_argument("--freeze-through", type=int, default=FREEZE_THROUGH)
    ap.add_argument("--total-area", type=float, default=TOTAL_AREA)
    ap.add_argument("--crop-reserve", type=float, default=CROP_RESERVE)
    ap.add_argument("--forest", type=float, default=None,
                    help="pin forest at this area instead of the derived value")
    ap.add_argument("--cluster-caps", action="store_true",
                    help="also bound each cluster's activity to its own area. "
                         "A stopgap for land commodities having no spatial "
                         "identity; off by default because it is the most "
                         "aggressive constraint here")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--revert", action="store_true")
    a = ap.parse_args()

    template = Path(a.template)
    if not template.is_dir():
        sys.exit(f"not a directory: {template}")
    for name in (ACTIVITY_LO, ACTIVITY_HI, CAPACITY_LO, CAPACITY_HI):
        if not (template / name).exists():
            sys.exit(f"missing parameter file: {template / name}")

    all_years = range(YEAR_START, YEAR_END + 1)
    frozen = range(YEAR_START, a.freeze_through + 1)
    span = f"{frozen.start}-{frozen.stop - 1}"

    # ---- revert -------------------------------------------------------
    if a.revert:
        for name in (ACTIVITY_LO, ACTIVITY_HI, CAPACITY_LO, CAPACITY_HI):
            path = template / name
            header, body, newline = load(path)
            body = drop(body, LEGACY_TECHS | {PRECIP_SUPPLY}, CLUSTER_PREFIX)
            save(path, header, body, newline, a.dry_run)
        verb = "would remove" if a.dry_run else "removed"
        print(f"{verb} the precipitation cap, the forest pin, and any cover "
              f"or cluster rows left by earlier versions")
        return

    # ---- apply --------------------------------------------------------
    floors = existing_cover_floors(template)
    cap, cluster_areas, clustered = precipitation_cap(a.total_area)

    # The calibrated floors are not flat - built-up land grows about 1.1% a
    # year - so forest has to fit under the WORST year in the frozen span, not
    # the first one. Sizing it from 2021 alone leaves it 0.2 too big by 2025.
    base_floor = floors.get(YEAR_START, 0.0)
    worst = max(floors.get(y, base_floor) for y in frozen)
    forest = (a.forest if a.forest is not None else
              a.total_area - worst - a.crop_reserve
              - NON_CLUSTER_LAND_RESERVE)

    print(f"Land budget for {YEAR_START} (thousand sq km):")
    print(f"  modelled area                 {a.total_area:10.3f}")
    print(f"  already-calibrated covers     {worst:10.3f}   "
          f"(modes {', '.join(str(m) for m in sorted(CALIBRATED_MODES))})")
    print(f"  cropland reserved             {a.crop_reserve:10.3f}")
    print(f"  livestock + AGV reserved      {NON_CLUSTER_LAND_RESERVE:10.3f}")
    print(f"  FOREST pinned for {span}     {forest:10.3f}   "
          f"({100 * forest / a.total_area:.1f}% of BC)")
    print(f"\n  precipitation cap             {cap:10.3f}")

    if forest <= 0:
        sys.exit("nothing left for forest; lower --crop-reserve or raise "
                 "--total-area")
    # Forest must fit under the cover floors' own headroom in every frozen
    # year, not just the first: the built-up floor grows about 1.1% a year.
    if forest + worst + a.crop_reserve + NON_CLUSTER_LAND_RESERVE > \
            a.total_area + 1e-6:
        sys.exit(f"forest {forest:.3f} does not fit in {max(frozen)}: the "
                 f"calibrated floors rise to {worst:.3f} by then. Lower "
                 f"--forest or --crop-reserve.")

    # Activity upper limits: precipitation cap, forest ceiling, cluster caps.
    path = template / ACTIVITY_HI
    header, body, newline = load(path)
    body = drop(body, LEGACY_TECHS | {PRECIP_SUPPLY}, CLUSTER_PREFIX)
    body.extend(make_rows(
        [[REGION, PRECIP_SUPPLY, str(y), f"{cap:.3f}"] for y in all_years]
        + [[REGION, FOREST, str(y), f"{forest:.3f}"] for y in frozen]
        + ([[REGION, t, str(y), f"{v:.3f}"]
            for t, v in sorted(cluster_areas.items()) for y in all_years]
           if a.cluster_caps else []), newline))
    save(path, header, body, newline, a.dry_run)

    # Activity floor pins the area; capacity min/max keeps the land-cover
    # plots consistent, since plot_landcover_change reads TotalCapacityAnnual.
    for name in (ACTIVITY_LO, CAPACITY_LO, CAPACITY_HI):
        path = template / name
        header, body, newline = load(path)
        body = drop(body, LEGACY_TECHS, CLUSTER_PREFIX)
        body.extend(make_rows(
            [[REGION, FOREST, str(y), f"{forest:.3f}"] for y in frozen],
            newline))
        save(path, header, body, newline, a.dry_run)

    verb = "would write" if a.dry_run else "wrote"
    n_clus = len(cluster_areas) * len(list(all_years)) if a.cluster_caps else 0
    print(f"\n{verb} {len(list(all_years))} precipitation rows and "
          f"{n_clus} cluster rows into {ACTIVITY_HI},")
    print(f"and {len(list(frozen))} forest rows into each of "
          f"{ACTIVITY_LO}, {ACTIVITY_HI}, {CAPACITY_LO}, {CAPACITY_HI}")
    print("\nEvery other land cover is left to its existing "
          "TechnologyActivityByModeLowerLimit calibration.")


if __name__ == "__main__":
    main()
