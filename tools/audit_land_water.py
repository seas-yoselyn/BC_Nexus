"""
Did the land-water fixes actually take?

Run after a build and solve, from the repo root, with no arguments - it finds
the runs itself:

    python tools/audit_land_water.py                  # every run it can find
    python tools/audit_land_water.py CEF_High         # runs matching a name
    python tools/audit_land_water.py path/to/result_csvs_gurobi

Read-only. Changes nothing, needs no solver, no rebuild. Exits non-zero if any
check fails, so it can gate a pipeline.

What it checks, and what each one caught before the fixes (CEF_High, 24ts,
2026_09_03):

  precipitation   MINPRCBC1 was uncapped and reached 12550 against a
                  physically correct 739 - every extra hectare the optimiser
                  allocated paid for itself in extra water.
  land total      total land drawn from LBC1 should be the modelled area.
  forest frozen   forest moved between scenarios that override nothing but
                  energy demand, and sat 38.9% above the observed value.
  cluster area    cluster 3 processed 118 against the 17.764 it contains
                  (6.64x); cluster 6 ran at 4.00x. Both are the wettest.
  land for power  LND4PWR was produced 2980 and consumed 8.9 - a 330x
                  oversupply, because cluster 1 emitted it from nothing. It
                  also shared mode 1 with alfalfa, welding the power build-out
                  to a crop.
  groundwater     KNOWN OPEN. Recharge 23.40 produced, 0.00 consumed;
                  extraction 154.77 from nothing. Reported, not failed.
  agv parity      AGV modes existed where the conventional parent did not -
                  all five alfalfa regimes in cluster 1, 62% of the land.

A note on reading these files: the column ORDER is not consistent between
them. ProductionByTechnologyAnnual is REGION,TECHNOLOGY,FUEL,YEAR,VALUE but
UseByTechnology is REGION,TIMESLICE,TECHNOLOGY,FUEL,YEAR,VALUE and
RateOfUseByTechnologyByMode puts TIMESLICE second-to-last. Everything here
goes through csv.DictReader and names its columns; never index by position.
"""
import csv
import sys
from pathlib import Path

CLUSTERS = Path("data/clews_data/LandClusterData/clustering_results_BC1.csv")
TEMPLATE = Path("data/clews_data/csv_template")

RESULT_DIR_NAME = "result_csvs_gurobi"
HISTORICAL = range(2021, 2026)      # years the optimiser must not rewrite
BASE_YEAR = 2021

COVERS = {"LNDBARBC1", "LNDBLTBC1", "LNDFORBC1",
          "LNDGRSBC1", "LNDWATBC1", "LNDOTHBC1"}
CLUSTER_PREFIX = "LNDAGRBC1C"
PRECIP_SUPPLY = "MINPRCBC1"
LAND_FUEL = "LBC1"
POWER_LAND = "LND4PWR"

TOL = 0.02          # 2% slack on equalities, for solver tolerance and rounding

PASS, FAIL, WARN, INFO = "PASS", "FAIL", "WARN", "INFO"


# ---------------------------------------------------------------------------
# loading
# ---------------------------------------------------------------------------

_CACHE = {}


def rows(run, name):
    """Every row of one result file as dicts, or [] if the file is absent.

    Cached: several checks read the same file, and the cross-run comparison
    reads one file once per cover per run. RateOfProductionByTechnologyByMode
    runs to hundreds of MB, so re-parsing it turned a fast audit into a
    two-minute one.
    """
    key = (str(run), name)
    if key in _CACHE:
        return _CACHE[key]
    path = run / name
    if not path.exists():
        _CACHE[key] = []
        return _CACHE[key]
    with path.open(newline="") as fh:
        _CACHE[key] = list(csv.DictReader(fh))
    return _CACHE[key]


# Kept across runs for the cross-scenario comparison; small enough to hold.
KEEP_CACHED = {"ProductionByTechnologyAnnual.csv"}


def release(run):
    """Drop a finished run's bulky files so memory does not grow."""
    for key in [k for k in _CACHE
                if k[0] == str(run) and k[1] not in KEEP_CACHED]:
        del _CACHE[key]


def total(records, value_key="VALUE", **match):
    """Sum VALUE over rows matching every key=value pair given.

    Values are matched as strings so callers can pass year=2021 without
    worrying whether the file wrote '2021' or '2021.0'.
    """
    out = 0.0
    for r in records:
        for key, want in match.items():
            got = r.get(key.upper())
            if got is None or str(got).split(".")[0] != str(want):
                break
        else:
            out += float(r[value_key])
    return out


def by(records, key, value_key="VALUE", **match):
    """Sum VALUE grouped by one column, over rows matching the filters."""
    out = {}
    for r in records:
        for k, want in match.items():
            got = r.get(k.upper())
            if got is None or str(got).split(".")[0] != str(want):
                break
        else:
            out[r[key]] = out.get(r[key], 0.0) + float(r[value_key])
    return out


def cluster_areas():
    """Physical area of each cluster, keyed by technology name."""
    if not CLUSTERS.exists():
        return {}
    with CLUSTERS.open() as fh:
        return {CLUSTER_PREFIX + r["cluster"].zfill(2): float(r["land_area_total"])
                for r in csv.DictReader(fh)}


def configured(param, tech):
    """A technology's configured limit for the base year, or None."""
    path = TEMPLATE / param
    if not path.exists():
        return None
    with path.open(newline="") as fh:
        for r in csv.DictReader(fh):
            if r["TECHNOLOGY"] == tech and str(r["YEAR"]) == str(BASE_YEAR):
                return float(r["VALUE"])
    return None


# ---------------------------------------------------------------------------
# checks - each returns (status, headline, [detail lines])
# ---------------------------------------------------------------------------

def check_precipitation(run):
    prod = rows(run, "ProductionByTechnologyAnnual.csv")
    made = {y: total(prod, technology=PRECIP_SUPPLY, year=y)
            for y in (BASE_YEAR, 2050)}
    cap = configured("TotalTechnologyAnnualActivityUpperLimit.csv", PRECIP_SUPPLY)
    if cap is None:
        return (FAIL, "precipitation is UNCAPPED",
                [f"no {PRECIP_SUPPLY} row in TotalTechnologyAnnualActivityUpperLimit",
                 f"produced {made[BASE_YEAR]:.1f} in {BASE_YEAR}, "
                 f"{made[2050]:.1f} in 2050"])
    worst = max(made.values())
    if worst > cap * (1 + TOL):
        return (FAIL, f"precipitation exceeds its cap ({worst:.1f} > {cap:.1f})",
                [f"{y}: {v:.1f}" for y, v in made.items()])
    return (PASS, f"precipitation within cap ({worst:.1f} <= {cap:.1f})",
            [f"{y}: {v:.1f}" for y, v in made.items()])


def check_land_total(run):
    use = rows(run, "UseByTechnology.csv")
    drawn = total(use, fuel=LAND_FUEL, year=BASE_YEAR)
    cap = configured("TotalTechnologyAnnualActivityUpperLimit.csv", "MINLNDBC1")
    detail = [f"land drawn from {LAND_FUEL} in {BASE_YEAR}: {drawn:.3f}"]
    if cap is None:
        return (WARN, "land supply has no configured cap", detail)
    detail.append(f"configured cap: {cap:.3f}")
    if drawn > cap * (1 + TOL):
        return (FAIL, f"land use {drawn:.3f} exceeds cap {cap:.3f}", detail)
    return (PASS, f"land total {drawn:.3f} within {cap:.3f}", detail)


def check_forest_frozen(run):
    prod = rows(run, "ProductionByTechnologyAnnual.csv")
    series = {y: total(prod, technology="LNDFORBC1", year=y) for y in HISTORICAL}
    values = sorted(series.values())
    if not values or values[-1] == 0:
        return (WARN, "no forest activity found", [])
    spread = values[-1] - values[0]
    detail = [f"{y}: {v:.3f}" for y, v in sorted(series.items())]
    if spread > values[-1] * TOL:
        return (FAIL,
                f"forest MOVES across historical years (spread {spread:.3f})",
                detail)
    return (PASS, f"forest frozen at {values[-1]:.3f} through {max(HISTORICAL)}",
            detail)


def check_cluster_area(run):
    act = rows(run, "TotalAnnualTechnologyActivityByMode.csv")
    if not act:
        return (WARN, "no activity-by-mode file", [])
    # Mode 1 historically carried a degenerate LND4PWR variable that the
    # barrier solve parks at an arbitrary value; exclude it so a real
    # over-allocation is not hidden behind that noise.
    used = {}
    for r in act:
        t = r["TECHNOLOGY"]
        if not t.startswith(CLUSTER_PREFIX):
            continue
        if str(r["YEAR"]).split(".")[0] != str(BASE_YEAR):
            continue
        if str(r["MODE_OF_OPERATION"]).split(".")[0] == "1":
            continue
        used[t] = used.get(t, 0.0) + float(r["VALUE"])

    areas = cluster_areas()
    if not areas:
        return (WARN, "cluster data not found; cannot check areas", [])
    # The model may be scaled up from the clustered extent; compare on shares
    # so the check works whichever --total-area the pins were built with.
    scale = sum(used.values()) / sum(areas.values()) if sum(areas.values()) else 1
    bad, detail = [], []
    for t in sorted(areas):
        expect = areas[t] * scale
        got = used.get(t, 0.0)
        ratio = got / expect if expect else 0
        detail.append(f"{t}: {got:8.3f} vs {expect:8.3f} area  ({ratio:.2f}x)")
        if ratio > 1 + TOL:
            bad.append(f"{t} at {ratio:.2f}x")
    if bad:
        return (FAIL, "clusters process more land than they contain: "
                      + ", ".join(bad), detail)
    return (PASS, "every cluster within its own area", detail)


def check_power_land(run):
    prod = rows(run, "ProductionByTechnologyAnnual.csv")
    use = rows(run, "UseByTechnology.csv")
    made = total(prod, fuel=POWER_LAND, year=BASE_YEAR)
    used = total(use, fuel=POWER_LAND, year=BASE_YEAR)
    detail = [f"produced {made:.3f}", f"consumed {used:.3f}"]

    # Which modes emit it? Sharing a mode with a crop welds the power
    # build-out to that crop, because a mode's outputs move together.
    modes = set()
    for r in rows(run, "RateOfProductionByTechnologyByMode.csv"):
        if r.get("FUEL") == POWER_LAND:
            modes.add(str(r["MODE_OF_OPERATION"]).split(".")[0])
    crop_modes = {str(r["MODE_OF_OPERATION"]).split(".")[0]
                  for r in rows(run, "RateOfProductionByTechnologyByMode.csv")
                  if str(r.get("FUEL", "")).startswith("CRP")}
    shared = sorted(modes & crop_modes, key=lambda m: int(m))
    if modes:
        detail.append(f"emitted from mode(s): {', '.join(sorted(modes, key=int))}")

    if shared:
        return (FAIL, f"{POWER_LAND} shares mode(s) {', '.join(shared)} with a "
                      f"crop - power land and crop output are welded together",
                detail)
    if used and made > used * 10:
        return (FAIL, f"{POWER_LAND} oversupplied {made / used:.0f}x - "
                      f"the power land constraint is not binding", detail)
    if not used:
        return (WARN, f"{POWER_LAND} is consumed by nothing", detail)
    return (PASS, f"{POWER_LAND} supply tracks demand "
                  f"({made:.2f} vs {used:.2f})", detail)


def check_groundwater(run):
    """Known open issue. Reported so it stays visible, never failed."""
    prod = rows(run, "ProductionByTechnologyAnnual.csv")
    use = rows(run, "UseByTechnology.csv")
    recharge = total(prod, fuel="WTRGRCBC1", year=BASE_YEAR)
    consumed = total(use, fuel="WTRGRCBC1", year=BASE_YEAR)
    extraction = sum(total(prod, technology=t, year=BASE_YEAR)
                     for t in ("DEMAGRGWTBC1", "DEMPUBGWTBC1"))
    detail = [f"recharge produced   {recharge:.2f}",
              f"recharge consumed   {consumed:.2f}",
              f"extraction          {extraction:.2f}"]
    if consumed == 0 and extraction > 0:
        return (INFO, f"groundwater balance still open: {extraction:.1f} "
                      f"extracted from nothing, {recharge:.1f} recharge "
                      f"discarded", detail)
    return (PASS, "groundwater recharge is connected to extraction", detail)


def check_agv_parity(run):
    """Every AGV crop mode should have a conventional counterpart."""
    prod = rows(run, "RateOfProductionByTechnologyByMode.csv")
    if not prod:
        return (WARN, "no mode-resolved production file", [])
    agv, conv = {}, {}
    for r in prod:
        fuel = str(r.get("FUEL", ""))
        if not fuel.startswith("CRP"):
            continue
        tech, mode = r["TECHNOLOGY"], str(r["MODE_OF_OPERATION"]).split(".")[0]
        # AGV modes are appended after the land-cover modes (>56).
        (agv if int(mode) > 56 else conv).setdefault((tech, fuel), set()).add(mode)
    orphans = sorted(f"{t} {f}" for (t, f) in agv if (t, f) not in conv)
    detail = [f"{len(agv)} AGV tech/crop pairs, {len(conv)} conventional"]
    if orphans:
        return (FAIL, f"{len(orphans)} AGV crop(s) with no conventional "
                      f"counterpart in the same cluster",
                detail + ["  " + o for o in orphans[:10]])
    return (PASS, "every AGV crop has a conventional counterpart", detail)


CHECKS = [
    ("precipitation", check_precipitation),
    ("land total", check_land_total),
    ("forest frozen", check_forest_frozen),
    ("cluster area", check_cluster_area),
    ("land for power", check_power_land),
    ("agv parity", check_agv_parity),
    ("groundwater", check_groundwater),
]


# ---------------------------------------------------------------------------

def check_across_runs(runs):
    """Historical land cover must be identical in every scenario.

    The per-run check only sees whether a cover is flat within one run. Both
    matter, and they fail differently: before the fixes, Base_Current_Measure
    held forest at 521.780 across all five historical years - flat, so the
    per-run check passed - while CEF_High held 461.262. A scenario that
    overrides nothing but energy demand had moved 60 thousand sq km of forest
    in a year that has already happened.
    """
    print("=" * 78)
    print(f"across scenarios: land cover in {BASE_YEAR}")
    print("=" * 78)
    failed = 0
    for cover in sorted(COVERS):
        seen = {}
        for run in runs:
            v = total(rows(run, "ProductionByTechnologyAnnual.csv"),
                      technology=cover, year=BASE_YEAR)
            if v:
                seen[str(run.parent)] = v
        if len(seen) < 2:
            continue
        lo, hi = min(seen.values()), max(seen.values())
        if hi - lo > hi * TOL:
            failed += 1
            print(f"[ FAIL ] {cover:<12} varies {lo:.3f} .. {hi:.3f} "
                  f"(spread {hi - lo:.3f})")
            for label, v in sorted(seen.items(), key=lambda kv: -kv[1]):
                print(f"                          {v:10.3f}  "
                      f"{Path(label).parent.parent.name}")
        else:
            print(f"[   ok ] {cover:<12} identical across "
                  f"{len(seen)} runs ({hi:.3f})")
    print()
    return failed


# Directories never worth descending into. Without this, a plain rglob over
# the repo takes minutes: it walks .git, the archive, and any nested clone.
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "env",
             "archive", "docs", "data", "models", "notebooks", "report"}
MAX_DEPTH = 6


def find_runs(pattern=None):
    """Locate result directories under the repo and the download folder."""
    import os
    roots = [Path("."), Path.home() / "Downloads"]
    seen, out = set(), []
    for root in roots:
        if not root.exists():
            continue
        base = len(root.resolve().parts)
        for dirpath, dirnames, _ in os.walk(root):
            here = Path(dirpath)
            if len(here.resolve().parts) - base >= MAX_DEPTH:
                dirnames[:] = []
                continue
            # Prune in place so os.walk never descends into them.
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            if RESULT_DIR_NAME in dirnames:
                p = here / RESULT_DIR_NAME
                key = p.resolve()
                if key in seen:
                    continue
                seen.add(key)
                if pattern and pattern.lower() not in str(p).lower():
                    continue
                out.append(p)
    return sorted(out, key=lambda p: str(p))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    target = args[0] if args else None

    if target and Path(target).is_dir():
        runs = [Path(target)]
    else:
        runs = find_runs(target)
    if not runs:
        sys.exit(f"no {RESULT_DIR_NAME} directories found"
                 + (f" matching {target!r}" if target else ""))

    failed = 0
    for run in runs:
        label = str(run.parent).replace("\\", "/")
        print("=" * 78)
        print(label)
        print("=" * 78)
        for name, fn in CHECKS:
            try:
                status, headline, detail = fn(run)
            except Exception as exc:                       # noqa: BLE001
                status, headline, detail = WARN, f"check errored: {exc}", []
            mark = {PASS: "  ok  ", FAIL: " FAIL ",
                    WARN: " warn ", INFO: " open "}[status]
            print(f"[{mark}] {name:<16} {headline}")
            for line in detail:
                print(f"                          {line}")
            if status == FAIL:
                failed += 1
        release(run)
        print()

    if len(runs) > 1:
        failed += check_across_runs(runs)

    if failed:
        print(f"{failed} check(s) FAILED")
        sys.exit(1)
    print("all checks passed")


if __name__ == "__main__":
    main()
