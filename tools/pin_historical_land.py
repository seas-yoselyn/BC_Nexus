"""
Anchor the land-water system to observed data, and freeze land cover in the
historical years.

Three defects let land and water float free of the input data:

1. MINPRCBC1 (precipitation) has no TotalTechnologyAnnualActivityUpperLimit,
   while MINLNDBC1 (land) has one. Rainfall therefore became a free decision
   variable: runs reached 12550 against a physically correct 739, so every
   extra hectare the optimiser allocated paid for itself in extra water.

2. The land-cluster data covers 763.757 thousand sq km, but MINLNDBC1 is
   capped at 925 - BC's real land area. The clustering holds 19649 cells of
   38.87 sq km; BC needs about 23800, so roughly 4100 cells inside BC are
   missing, almost certainly no-data in the 2010 land-cover raster. The
   difference was land the optimiser could allocate but had no description
   of, and it parked it in forest (+145) and cropland (+31).

3. No land-cover technology has any anchor at all. LNDFORBC1 has zero rows in
   TotalAnnualMaxCapacity, TotalAnnualMinCapacity, both activity limit files
   and ResidualCapacity, so forest area is decided fresh each year. Base-year
   forest came out 38.9% above observed, and it moved between scenarios that
   override nothing but energy demand.

Scaling
-------
The model must represent all of BC, so the clustered sample is treated as
representative and scaled up to TOTAL_AREA (925). Every derived quantity is
scaled by the same factor, which keeps the system internally consistent:
land covers, the crop headroom, and the precipitation ceiling all move
together. Set --total-area 763.757 to model only the clustered extent
instead, with no scaling.

The scaling assumption is that the unmapped ~17% of BC has the same cover mix
as the mapped part. That is doing real work and should be stated in any
write-up: it raises forest from the measured 372.730 to 451.44. Note the
measured figure implies BC is only 40% forested, against a real value nearer
55-60%, which is consistent with the dropped cells being forest-heavy - so
scaling moves toward reality rather than away from it, but does not reach it.

Capacity is not area
--------------------
Land AREA is technology ACTIVITY, not capacity: in the Sep 2026 runs forest
carried 611.57 capacity against 517.71 area, because CapitalCost is 0.01 and
overbuilding is nearly free. Pinning capacity alone would cap forest from
above while still letting it shrink. This pins both - activity so the physics
is right, capacity so the land-cover plots agree, since plot_landcover_change
reads TotalCapacityAnnual.

Both default to 1 for these technologies (no CapacityFactor or
AvailabilityFactor rows exist), so capacity == activity is feasible.

How the land budget closes
--------------------------
Crops need no per-crop constraint; they take what the covers leave:

    covers  +  CROP_RESERVE  +  NON_CLUSTER_LAND_RESERVE  =  TOTAL_AREA

The first attempt sized the covers to leave only the observed cultivated area
(14.5) for crops, and the model went infeasible on the remote: 2021 crop
demand is 2.666 Mt and the pre-fix runs needed about 38 thousand sq km to
produce it. CROP_RESERVE now carries that gap explicitly - see its comment for
why the gap exists and why it is a symptom of diluted yields rather than of
missing farmland.

Every number is derived from data/clews_data/LandClusterData at run time.
Nothing is hardcoded, so re-running after the cluster data changes gives
values consistent with the new data.

A caveat worth carrying: the land-cover raster is faocmb_2010.tif, a 2010
snapshot, eleven years before the 2021 base year, and the only land-cover
observation available. All frozen years therefore take the same values. Read
FREEZE_THROUGH as "years the optimiser may not rewrite", not as years for
which measurements are held.

The cluster ceilings are a stopgap
---------------------------------
They bound each cluster's activity to its own area, which stops the optimiser
processing more land in a cluster than that cluster contains. But the real
defect is upstream: land commodities carry no spatial identity. LALFHIBC1 is
produced by one region-wide technology and consumed by six clusters, so a
hectare of alfalfa land can be farmed wherever the yield is best. Crop yields
are cluster-specific, correctly, from GAEZ; the land is not.

The consequence, CEF_High 2021: cluster 3 held 17.764 thousand sq km (2.3% of
BC) but processed 118 and grew 41.9% of all crops, while cluster 1 held 61.7%
of the land and grew almost none. Cluster 3's alfalfa yield is 126,500x cluster
1's.

The structural fix is cluster-specific land commodities - LALFHIBC1C03 rather
than LALFHIBC1 - after which the area constraint falls out on its own and
these ceilings can be deleted. Deferred 2026-09-04: it multiplies the land
commodity set by 7 and touches fuel and IAR/OAR generation in sets_n_ratios,
so it needs its own validation run.

Note also that these ceilings inherit any error in the cluster areas, and the
clustering is missing roughly 4100 cells inside BC.

Idempotent: rows this tool wrote are replaced, not duplicated.

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

# Last year the optimiser is forbidden from changing land cover. The model
# starts in 2021; today is 2026, so every elapsed year is frozen.
FREEZE_THROUGH = 2025

# Land area the model must represent, thousand sq km. BC's real land area.
TOTAL_AREA = 925.0

# Land that draws on the LBC1 supply but is NOT described by the land-cluster
# file, so scaling the cover classes up to TOTAL_AREA would leave it nothing.
# Two consumers: livestock pasture (model_structure.LivestockLandArea sums to
# 8.989 at base year, and the Sep 2026 runs grow it to 12.544, about 1.4x) and
# agrivoltaic arrays (0.141 in the CEF_High run, up to ~0.9 in AGV_SUB_HIGH by
# 2050). 15.0 covers both with margin.
#
# Omitting this reserve is what made the first version of this tool infeasible:
# covers plus crops consumed the whole 925 and livestock had nowhere to go.
# check_budget() below now fails loudly rather than shipping that to a solve.
NON_CLUSTER_LAND_RESERVE = 15.0

# Cropland to leave free, thousand sq km.
#
# The observed cultivated area is 12.156 (14.5 scaled), but the model cannot
# meet crop demand on it: 2021 demand is 2.666 Mt and the pre-fix runs needed
# ~38 to produce it. Pinning cropland to the observed area makes the model
# INFEASIBLE - that is what happened on the first remote solve, 2026-09-04.
#
# The gap is not a land-data error alone. sets_n_ratios notes that cluster-mean
# yields are "a dilution artifact of averaging yields over clusters dominated
# by non-crop cells": diluted yields need more land per tonne, and the model
# was compensating with area. So this reserve is a workaround for the yield
# problem, not a statement about how much of BC is farmed. BC's real farm area
# is roughly 26 (2.6 Mha), between the raster's 12.2 and the model's 38.
#
# Sized from the pre-fix Base_Current_Measure runs (37.954 at 6ts, 43.566 at
# 24ts) with margin, because the cluster ceilings push crops off the highest
# yielding cluster and raise the land needed further. Lower it once the yields
# are de-diluted; the land pins get tighter and more honest as it falls.
CROP_RESERVE = 50.0

YEAR_START, YEAR_END = 2021, 2050
REGION = "REGION1"
REGION_CODE = "BC1"      # land region; cluster techs are LNDAGR<REGION_CODE>C<nn>
CLUSTER_PREFIX = "LNDAGR" + REGION_CODE + "C"

LAND_SUPPLY = "MINLNDBC1"
PRECIP_SUPPLY = "MINPRCBC1"

# Land-cover column in clustering_results_BC1.csv -> technology it feeds.
COVER_COLUMNS = {
    "Barren and sparsely vegetated land": "LNDBARBC1",
    "Built-up land": "LNDBLTBC1",
    "Forest land": "LNDFORBC1",
    "Grassland & woodland": "LNDGRSBC1",
    "Water bodies": "LNDWATBC1",
}

# Cultivated columns are not pinned. They are reported so the closing of the
# land budget can be checked, and they bound crops implicitly.
CULTIVATED_COLUMNS = ["Irrigated cultivated land", "Rain-fed cultivated land"]

# Clustered area not attributed to any named cover class. It is a residual -
# what the raster could not label - not an observation, so it is deliberately
# NOT pinned. It carries the slack instead: crops, livestock and AGV all draw
# on the same budget, and something has to absorb the difference.
#
# Pinning it was the second cause of infeasibility on the remote (2026-09-04):
# the residual scaled to 31.445 and was written as min == max, while the model
# had never used more than 0.061 of it. An equality on a bucket the model does
# not want is exactly the constraint that cannot be satisfied.
RESIDUAL_TECH = "LNDOTHBC1"

# Only the classes the raster actually measured are frozen.
PINNED_TECHS = sorted(set(COVER_COLUMNS.values()))

# Rows any version of this tool may have written, for cleanup on revert
# and before re-applying. Includes RESIDUAL_TECH, which earlier versions
# pinned and this one deliberately does not.
OURS = set(PINNED_TECHS) | {RESIDUAL_TECH}

# Files this tool writes. Activity limits bind land area; capacity limits keep
# the land-cover plots consistent with it.
ACTIVITY_LO = "TotalTechnologyAnnualActivityLowerLimit.csv"
ACTIVITY_HI = "TotalTechnologyAnnualActivityUpperLimit.csv"
CAPACITY_LO = "TotalAnnualMinCapacity.csv"
CAPACITY_HI = "TotalAnnualMaxCapacity.csv"


def read_observed(total_area, crop_reserve):
    """Return observed areas scaled to total_area, plus the precipitation cap.

    Also returns each cluster's own area, scaled the same way. A cluster
    technology's activity is the land it processes, so it cannot exceed the
    land the cluster physically holds - but nothing enforced that, and the
    model exploited it: activity ran at 6.64x area in cluster 3 and 4.00x in
    cluster 6, the two wettest, while the driest cluster sat at 0.74x. Routing
    land through a wet cluster harvests that cluster's rainfall, and imports
    its crop yields onto land physically somewhere else.
    """
    main = CLUSTERS / "clustering_results_BC1.csv"
    prc = CLUSTERS / "clustering_results_prc_BC1.csv"
    for path in (main, prc):
        if not path.exists():
            sys.exit(f"missing cluster data: {path}")

    with main.open() as fh:
        rows = list(csv.DictReader(fh))
    with prc.open() as fh:
        precip = {r["cluster"]: float(r["precipitation"])
                  for r in csv.DictReader(fh)}

    areas = {tech: 0.0 for tech in COVER_COLUMNS.values()}
    cluster_areas = {}
    clustered = cultivated = precip_cap = 0.0

    for row in rows:
        cluster_area = float(row["land_area_total"])
        clustered += cluster_area
        cluster_areas["LNDAGR" + REGION_CODE + "C"
                      + row["cluster"].zfill(2)] = cluster_area
        for column, tech in COVER_COLUMNS.items():
            areas[tech] += float(row[column])
        cultivated += sum(float(row[c]) for c in CULTIVATED_COLUMNS)
        # Precipitation is a depth; the volume a cluster supplies is
        # depth x area. Summed, that is the rain the region receives.
        precip_cap += cluster_area * precip[row["cluster"]]

    # Clustered area not accounted for by any named class.
    areas[RESIDUAL_TECH] = clustered - sum(areas.values()) - cultivated

    # Two different scales, and the difference matters.
    #
    # Cluster ceilings bound ALL land the cluster processes - covers, crops,
    # livestock, AGV - so they scale to the full modelled area.
    #
    # Cover pins describe only what the cluster file measured, so they scale to
    # the area left after reserving space for livestock and AGV. Scaling both
    # the same way is what made the first version infeasible: the covers
    # expanded to fill land livestock needed.
    cluster_scale = total_area / clustered
    cover_room = total_area - NON_CLUSTER_LAND_RESERVE - crop_reserve
    cover_unscaled = sum(areas.values())
    if cover_room <= 0:
        sys.exit("reserves exceed the modelled area; nothing left for cover")
    scale = cover_room / cover_unscaled
    areas = {tech: value * scale for tech, value in areas.items()}
    cluster_areas = {t: v * cluster_scale for t, v in cluster_areas.items()}
    # Rain falls on every hectare the clusters process, not just the part
    # the cover classes occupy, so the ceiling scales with cluster_scale.
    return (areas, cluster_areas, clustered, scale,
            cultivated * scale, precip_cap * cluster_scale)


def load(path):
    """Return (header_line, [(fields, raw_line), ...], newline).

    Lines are kept verbatim. These files carry mixed endings - most rows are
    CRLF but some blocks are LF - and rewriting them through csv.writer
    normalises every line, burying the real change in hundreds of lines of
    whitespace diff. Untouched rows are written back byte for byte.
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


def drop(body, techs, years=None):
    """Remove rows for these technologies, optionally limited to a year range."""
    keep = []
    for fields, raw in body:
        if fields[1] in techs and (years is None or int(fields[2]) in years):
            continue
        keep.append((fields, raw))
    return keep


def check_budget(template, areas, cluster_areas, crop_reserve,
                 capped=True):
    """Refuse to write a parameter set the solver cannot satisfy.

    Cluster technologies process land, so their ceilings bound everything that
    consumes LBC1: the pinned covers, crops, livestock and AGV. Lower limits
    written by anyone - this tool, or the pre-existing LNDLVSBEFNBC1 floor -
    are demands that must fit underneath. Comparing the two here catches an
    infeasible template in a second instead of after a multi-hour solve.
    """
    lo_path = template / ACTIVITY_LO
    existing = 0.0
    for fields, _ in load(lo_path)[1]:
        tech, year, value = fields[1], fields[2], fields[3]
        # Rows this tool is about to replace do not count as pre-existing.
        if tech in OURS or not tech.startswith("LND"):
            continue
        if year == str(YEAR_START):
            existing += float(value)

    # Without ceilings the clusters are unbounded, so the only real limit is
    # the land supply itself; say so rather than implying a false constraint.
    capacity = sum(cluster_areas.values())
    label = "cluster processing capacity" if capped else "land supply (no caps)"
    pinned = sum(areas[t] for t in PINNED_TECHS)
    demand = pinned + crop_reserve + existing
    margin = capacity - demand

    print(f"\nLand budget check (year {YEAR_START}):")
    print(f"  {label:<29} {capacity:10.3f}")
    print(f"  pinned covers                 {pinned:10.3f}")
    print(f"  cropland reserved             {crop_reserve:10.3f}")
    print(f"  other LND floors already set  {existing:10.3f}")
    print(f"  free for residual cover       "
          f"{margin:10.3f}")
    print(f"  {'margin':<29} {margin:+10.3f}")
    if margin < 0:
        sys.exit(f"\nland budget infeasible by {-margin:.3f}: the cluster "
                 f"ceilings cannot process everything that must be allocated. "
                 f"Raise --total-area, or NON_CLUSTER_LAND_RESERVE if "
                 f"livestock needs more room.")
    return margin


def pin(template, filename, areas, frozen, dry_run):
    """Write min == max rows for every pinned cover over the frozen years."""
    path = template / filename
    header, body, newline = load(path)
    body = drop(body, OURS, set(frozen))
    body.extend(make_rows(
        [[REGION, tech, str(y), f"{areas[tech]:.3f}"]
         for tech in PINNED_TECHS for y in frozen], newline))
    save(path, header, body, newline, dry_run)
    return len(PINNED_TECHS) * len(list(frozen))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", default=str(TEMPLATE),
                    help="csv_template directory")
    ap.add_argument("--freeze-through", type=int, default=FREEZE_THROUGH,
                    help=f"last frozen year (default {FREEZE_THROUGH})")
    ap.add_argument("--total-area", type=float, default=TOTAL_AREA,
                    help=f"land area the model represents, thousand sq km "
                         f"(default {TOTAL_AREA}; pass 763.757 to model only "
                         f"the clustered extent unscaled)")
    ap.add_argument("--crop-reserve", type=float, default=CROP_RESERVE,
                    help=f"cropland left free, thousand sq km "
                         f"(default {CROP_RESERVE})")
    ap.add_argument("--no-cluster-caps", action="store_true",
                    help="skip the per-cluster activity ceilings, to isolate "
                         "whether they cause an infeasibility")
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
        path = template / ACTIVITY_HI
        header, body, newline = load(path)
        body = drop(body, {PRECIP_SUPPLY} | OURS)
        body = [(f, r) for f, r in body if not f[1].startswith(CLUSTER_PREFIX)]
        save(path, header, body, newline, a.dry_run)

        for name in (ACTIVITY_LO, CAPACITY_LO, CAPACITY_HI):
            path = template / name
            header, body, newline = load(path)
            body = drop(body, OURS, set(frozen))
            save(path, header, body, newline, a.dry_run)

        verb = "would remove" if a.dry_run else "removed"
        print(f"{verb} the precipitation cap and all land-cover pins for {span}")
        return

    # ---- apply --------------------------------------------------------
    (areas, cluster_areas, clustered, scale,
     cultivated, precip_cap) = read_observed(a.total_area, a.crop_reserve)

    pinned_total = sum(areas[t] for t in PINNED_TECHS)
    headroom = a.total_area - NON_CLUSTER_LAND_RESERVE - pinned_total

    print(f"Clustered extent {clustered:.3f}  ->  modelled area "
          f"{a.total_area:.3f}   (scale {scale:.5f})\n")
    print("Land cover pinned for " + span + " (thousand sq km):")
    for tech in PINNED_TECHS:
        print(f"  {tech:<12} {areas[tech]:10.3f}")
    print(f"  {'pinned total':<12} {pinned_total:10.3f}")
    print(f"  {'crop headroom':<12} {headroom:10.3f}   "
          f"vs observed cultivated {cultivated:.3f}")
    print(f"  {'precip cap':<12} {precip_cap:10.3f}")
    print("\nCluster activity ceilings, all years (thousand sq km):")
    for tech, area in sorted(cluster_areas.items()):
        print(f"  {tech:<15} {area:10.3f}")
    print(f"  {'sum':<15} {sum(cluster_areas.values()):10.3f}")

    if headroom < 0:
        sys.exit("land budget infeasible: pinned covers exceed the land area")

    check_budget(template, areas, cluster_areas, a.crop_reserve,
                 capped=not a.no_cluster_caps)

    # Activity upper limits: precipitation cap, the land-cover ceiling, and
    # each cluster's own area. The cluster caps apply in every year, not just
    # the frozen ones - a cluster never grows, whatever the scenario.
    path = template / ACTIVITY_HI
    header, body, newline = load(path)
    body = drop(body, {PRECIP_SUPPLY} | OURS)
    body = [(f, r) for f, r in body if not f[1].startswith(CLUSTER_PREFIX)]
    body.extend(make_rows(
        [[REGION, PRECIP_SUPPLY, str(y), f"{precip_cap:.3f}"]
         for y in all_years]
        + [[REGION, tech, str(y), f"{areas[tech]:.3f}"]
           for tech in PINNED_TECHS for y in frozen]
        + ([] if a.no_cluster_caps else
           [[REGION, tech, str(y), f"{area:.3f}"]
            for tech, area in sorted(cluster_areas.items())
            for y in all_years]), newline))
    save(path, header, body, newline, a.dry_run)

    # Activity floor pins the area; capacity min/max keeps the plots honest.
    n = pin(template, ACTIVITY_LO, areas, frozen, a.dry_run)
    for name in (CAPACITY_LO, CAPACITY_HI):
        pin(template, name, areas, frozen, a.dry_run)

    verb = "would write" if a.dry_run else "wrote"
    print(f"\n{verb} into {ACTIVITY_HI}:")
    print(f"  {len(list(all_years)):>4} precipitation cap rows")
    n_clus = 0 if a.no_cluster_caps else len(cluster_areas) * len(list(all_years))
    print(f"  {n_clus:>4} cluster ceiling rows"
          f"{'  (--no-cluster-caps)' if a.no_cluster_caps else ''}")
    print(f"  {n:>4} land-cover pin rows")
    print(f"and {n} land-cover pin rows into each of "
          f"{ACTIVITY_LO}, {CAPACITY_LO}, {CAPACITY_HI}")
    print(f"\nMINLNDBC1 left at its existing cap; modelled land totals "
          f"{a.total_area:.3f}")


if __name__ == "__main__":
    main()
