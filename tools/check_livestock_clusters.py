"""
Verify that livestock land competes for the same cluster land as crops.

Builds the SETs into a temporary directory (base -> agrivoltaic -> livestock,
the same order builder.build_SETs_and_ratios uses) and asserts the wiring that
makes livestock share the LNDAGR cluster technologies:

    MINLND{LR}        -> L{LR}
    LNDLVS{pw}{LR}    L{LR} -> LLVS{pw}{LR}          mode 1
    LNDAGR{LR}C{cc}   LLVS{pw}{LR} -> LVS{pw}{LR}    livestock mode
    LVSHRD{pw}{LR}    LVS{pw}{LR} -> HRD{pw}
    LVS{pw}{LR}       HRD{pw} -> LVS{produce}

Nothing here is written to the repository: the build goes to a temp directory
and the parameter-sync check works on copies. Safe to run at any time.

Usage
-----
    python tools/check_livestock_clusters.py
    python tools/check_livestock_clusters.py --no-agrivoltaic
    python tools/check_livestock_clusters.py --keep     # keep the temp build

Exits non-zero on the first family of checks that fails.
"""
import argparse
import shutil
import sys
import tempfile
from pathlib import Path

import pandas as pd

# Run as a script from the repository root: Python puts tools/ on sys.path,
# not the root, so the package would not be importable without this.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bcnexus.clews import agrivoltaic as AGV
from bcnexus.clews import livestock as LVS
from bcnexus.clews import model_structure as ms
from bcnexus.clews import sets_n_ratios as SnR

TEMPLATE = Path("data/clews_data/csv_template")

# The 2-significant-figure decimal context in sets_n_ratios rounds each of
# evapotranspiration, groundwater and runoff independently, so no mode's water
# balance closes exactly. The existing land-cover modes miss by up to ~0.8%.
# Livestock is held to the same bar, not a tighter one: a real error would be
# orders of magnitude bigger, and demanding exactness here would only mean
# re-rounding every crop coefficient in the model.
WATER_TOLERANCE = 0.02

_fails = []


def check(label, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  {detail}" if detail else ""))
    if not ok:
        _fails.append(label)


def build(with_agv, out):
    SetNames, NewSetItems, IARList, OARList, EARList, ModeList = SnR.build(out)
    if with_agv:
        SetNames, NewSetItems, IARList, OARList, EARList, ModeList = \
            AGV.build_agrivoltaic_modes(
                SetNames, NewSetItems, IARList, OARList, EARList, ModeList)

    livestock_sets = LVS.get_Livestock_SETs()
    NewSetItems = LVS.update_SetItems_with_Livestock(
        SetNames, NewSetItems, livestock_sets)
    modes = LVS._assign_livestock_modes(ModeList=ModeList)
    IARList, OARList = LVS.update_IARlist(
        IARList, OARList, livestock_sets, modes, EARList_existing=EARList)

    SnR.UpdateSETS(SetNames, NewSetItems, IARList, OARList, out)
    LVS.update_mode_of_operation_csv(out, modes)

    # Emissions merge into a copy of the template, exactly as the builder does
    # it, so the hand-maintained CO2 rows are part of what gets checked.
    params = out / "params"
    params.mkdir(exist_ok=True)
    for name in ("EmissionActivityRatio.csv",) + LVS.MODE_KEYED_PARAM_FILES:
        if (TEMPLATE / name).exists():
            shutil.copy(TEMPLATE / name, params / name)
    SnR.write_emission_activity_ratio(EARList, params)
    return modes, ModeList, params


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-agrivoltaic", action="store_true",
                    help="build without the AGV modes (livestock lands earlier)")
    ap.add_argument("--keep", action="store_true",
                    help="leave the temporary build directory in place")
    a = ap.parse_args()

    if not TEMPLATE.is_dir():
        sys.exit(f"run from the repository root: {TEMPLATE} not found")

    out = Path(tempfile.mkdtemp(prefix="lvs_cluster_check_"))
    modes, ModeList, params = build(not a.no_agrivoltaic, out)

    iar = pd.read_csv(out / "InputActivityRatio.csv")
    oar = pd.read_csv(out / "OutputActivityRatio.csv")
    techs = set(pd.read_csv(out / "TECHNOLOGY.csv")["VALUE"].astype(str))
    fuels = set(pd.read_csv(out / "FUEL.csv")["VALUE"].astype(str))
    mops = set(pd.read_csv(out / "MODE_OF_OPERATION.csv")["VALUE"].astype(str))

    LR = ms.LandRegions[0]
    clusters = sorted(t for t in techs if t.startswith(f"LNDAGR{LR}C"))
    water_out = [f"WTREVT{LR}", f"WTRGRC{LR}", f"WTRSUR{LR}"]
    y0 = ms.snapshot["start"]

    print(f"\nbuild        {out}")
    print(f"modes        {modes}")
    print(f"clusters     {len(clusters)}")

    print("\n1. sets declared")
    for pw in ms.LivestockPathways:
        check(f"FUEL LLVS{pw}{LR}", f"LLVS{pw}{LR}" in fuels)
        check(f"FUEL LVS{pw}{LR}", f"LVS{pw}{LR}" in fuels)
        check(f"MODE_OF_OPERATION {modes[pw]}", str(modes[pw]) in mops)
        check(f"ModeList label LVS{pw}", ModeList[modes[pw] - 1] == f"LVS{pw}")

    print("\n2. land tier draws region land, nothing else, on mode 1")
    for pw in ms.LivestockPathways:
        t = f"LNDLVS{pw}{LR}"
        i, o = iar[iar.TECHNOLOGY == t], oar[oar.TECHNOLOGY == t]
        check(f"{t} consumes only L{LR}", set(i.FUEL) == {f"L{LR}"}, str(set(i.FUEL)))
        check(f"{t} produces only LLVS{pw}{LR}", set(o.FUEL) == {f"LLVS{pw}{LR}"},
              str(set(o.FUEL)))
        check(f"{t} is single-mode",
              set(i.MODE_OF_OPERATION) | set(o.MODE_OF_OPERATION) == {1})

    print("\n3. every cluster can host every livestock pathway")
    for pw, m in modes.items():
        got_i = set(iar[(iar.MODE_OF_OPERATION == m)
                        & (iar.FUEL == f"LLVS{pw}{LR}")].TECHNOLOGY)
        got_o = set(oar[(oar.MODE_OF_OPERATION == m)
                        & (oar.FUEL == f"LVS{pw}{LR}")
                        & oar.TECHNOLOGY.str.startswith("LNDAGR")].TECHNOLOGY)
        check(f"{pw}: tier consumed on all clusters", got_i == set(clusters),
              f"{len(got_i)}/{len(clusters)}")
        check(f"{pw}: allocated land emitted on all clusters", got_o == set(clusters),
              f"{len(got_o)}/{len(clusters)}")

    print("\n4. water balance lives on the cluster, and is cluster-specific")
    wat = set(water_out) | {f"WTRPRC{LR}"}
    for pw, m in modes.items():
        t = f"LNDLVS{pw}{LR}"
        on_tier = (set(iar[iar.TECHNOLOGY == t].FUEL)
                   | set(oar[oar.TECHNOLOGY == t].FUEL)) & wat
        check(f"{pw}: no water on {t}", not on_tier, str(on_tier))
        prc = iar[(iar.MODE_OF_OPERATION == m) & (iar.FUEL == f"WTRPRC{LR}")
                  & (iar.YEAR == y0)]
        check(f"{pw}: precipitation on all clusters",
              set(prc.TECHNOLOGY) == set(clusters),
              f"{prc.TECHNOLOGY.nunique()}/{len(clusters)}")
        check(f"{pw}: precipitation varies by cluster", prc.VALUE.nunique() > 1,
              f"{sorted(prc.VALUE.unique())}")

    print("\n5. livestock sees the same rainfall as the crops on that cluster")
    crop_prc = (iar[(iar.MODE_OF_OPERATION == 1) & (iar.FUEL == f"WTRPRC{LR}")
                    & (iar.YEAR == y0)].set_index("TECHNOLOGY")["VALUE"].to_dict())
    for pw, m in modes.items():
        lvs_prc = (iar[(iar.MODE_OF_OPERATION == m) & (iar.FUEL == f"WTRPRC{LR}")
                       & (iar.YEAR == y0)].set_index("TECHNOLOGY")["VALUE"].to_dict())
        bad = {t: (lvs_prc.get(t), crop_prc[t]) for t in clusters
               if t in crop_prc and abs(lvs_prc.get(t, -1) - crop_prc[t]) > 1e-9}
        check(f"{pw}: matches crop-mode precipitation", not bad, str(bad))

    print(f"\n6. water balance closes to within {WATER_TOLERANCE:.0%} "
          f"(2-sig-fig rounding), benchmarked against the land covers")

    def worst_residual(mode):
        w = 0.0
        for c in clusters:
            pin = iar[(iar.TECHNOLOGY == c) & (iar.MODE_OF_OPERATION == mode)
                      & (iar.FUEL == f"WTRPRC{LR}") & (iar.YEAR == y0)].VALUE.sum()
            pout = oar[(oar.TECHNOLOGY == c) & (oar.MODE_OF_OPERATION == mode)
                       & (oar.FUEL.isin(water_out))
                       & (oar.YEAR == y0)].VALUE.sum()
            if pin:
                w = max(w, abs(pin - pout) / pin)
        return w

    cover_modes = {ModeList.index(v) + 1: k
                   for k, v in ms.LandUseCodes.items() if v in ModeList}
    cover_worst = max((worst_residual(m) for m in cover_modes), default=0.0)
    print(f"     land covers worst: {cover_worst:.3%}")
    for pw, m in modes.items():
        r = worst_residual(m)
        check(f"{pw}: residual within tolerance", r <= WATER_TOLERANCE, f"{r:.3%}")

    print("\n7. herd and production chain intact on the livestock mode")
    for pw, m in modes.items():
        produce = ms.LivestockPathways[pw]["produce"]
        h_i = iar[(iar.TECHNOLOGY == f"LVSHRD{pw}{LR}") & (iar.MODE_OF_OPERATION == m)]
        h_o = oar[(oar.TECHNOLOGY == f"LVSHRD{pw}{LR}") & (oar.MODE_OF_OPERATION == m)]
        g_i = iar[(iar.TECHNOLOGY == f"LVS{pw}{LR}") & (iar.MODE_OF_OPERATION == m)]
        g_o = oar[(oar.TECHNOLOGY == f"LVS{pw}{LR}") & (oar.MODE_OF_OPERATION == m)]
        check(f"{pw}: herd consumes cluster-allocated land",
              set(h_i.FUEL) == {f"LVS{pw}{LR}"}, str(set(h_i.FUEL)))
        check(f"{pw}: herd emits HRD{pw} at stocking density",
              set(h_o.FUEL) == {f"HRD{pw}"} and not h_o.empty
              and abs(h_o.VALUE.iloc[0] - ms.LivestockStockingDensity[pw]) < 1e-9)
        check(f"{pw}: production consumes HRD{pw}", set(g_i.FUEL) == {f"HRD{pw}"})
        check(f"{pw}: production emits LVS{produce} at commodity yield",
              set(g_o.FUEL) == {f"LVS{produce}"} and not g_o.empty
              and abs(g_o.VALUE.iloc[0]
                      - ms.LivestockCommodityYield[produce]) < 1e-9)

    print("\n8. no dangling references, no duplicate ratio keys")
    for name, df in (("IAR", iar), ("OAR", oar)):
        dup = df[df.duplicated(["REGION", "TECHNOLOGY", "FUEL",
                                "MODE_OF_OPERATION", "YEAR"], keep=False)]
        check(f"{name}: no duplicate keys", dup.empty, f"{len(dup)} rows")
        for col, valid in (("TECHNOLOGY", techs), ("FUEL", fuels),
                           ("MODE_OF_OPERATION", mops)):
            missing = sorted(set(df[col].astype(str)) - valid)
            check(f"{name}: every {col} declared", not missing, str(missing[:5]))

    print("\n9. every livestock commodity is both produced and consumed")
    prod, cons = set(oar.FUEL.astype(str)), set(iar.FUEL.astype(str))
    for pw in ms.LivestockPathways:
        for f in (f"LLVS{pw}{LR}", f"LVS{pw}{LR}", f"HRD{pw}"):
            check(f"{f}", f in prod and f in cons,
                  f"produced={f in prod} consumed={f in cons}")

    print("\n10. mode-keyed parameter files follow the assigned modes")
    LVS.sync_livestock_param_modes(params, modes)
    for n in LVS.MODE_KEYED_PARAM_FILES:
        if not (params / n).exists():
            continue
        df = pd.read_csv(params / n)
        rows = df[df.TECHNOLOGY.astype(str).str.startswith(("LVSHRD", "LVS"))
                  & ~df.TECHNOLOGY.astype(str).str.startswith("LND")]
        if rows.empty:
            continue
        got = set(rows.MODE_OF_OPERATION.astype(int))
        check(f"{n}: livestock rows on assigned modes",
              got <= set(modes.values()), f"{sorted(got)}")
    check("sync is idempotent",
          not any(LVS.sync_livestock_param_modes(params, modes).values()))

    print("\n11. every EmissionActivityRatio row is on a mode its "
          "technology has")
    ear = pd.read_csv(params / "EmissionActivityRatio.csv")
    tech_modes = {}
    for df in (iar, oar):
        for t, m in df[["TECHNOLOGY", "MODE_OF_OPERATION"]].drop_duplicates().values:
            tech_modes.setdefault(str(t), set()).add(int(m))
    keys = ear[["TECHNOLOGY", "EMISSION", "MODE_OF_OPERATION"]].drop_duplicates()
    dead = [(t, e, int(m)) for t, e, m in keys.values
            if int(m) not in tech_modes.get(str(t), set())]
    check("no dead (technology, mode) emission rows", not dead,
          f"{len(dead)} dead: {dead[:5]}")

    # The hand-maintained CO2 rows must survive the merge untouched.
    src = pd.read_csv(TEMPLATE / "EmissionActivityRatio.csv")
    co2_before = src[src.EMISSION == "CO2"]
    co2_after = ear[ear.EMISSION == "CO2"]
    check("hand-maintained CO2 rows preserved",
          len(co2_before) == len(co2_after)
          and set(co2_before.TECHNOLOGY) == set(co2_after.TECHNOLOGY),
          f"{len(co2_before)} -> {len(co2_after)}")

    # Legacy crop-tier rows must be gone, not merely shadowed.
    legacy = ear[ear.TECHNOLOGY.astype(str).str.startswith("LND")
                 & ~ear.TECHNOLOGY.astype(str).str.startswith("LNDAGR")
                 & ear.EMISSION.isin(["N2O_DIR", "N2O_IND"])]
    check("legacy LND{combo} crop-tier N2O rows removed", legacy.empty,
          f"{len(legacy)} rows on {sorted(set(legacy.TECHNOLOGY))[:3]}")

    print("\n12. emission coverage matches the modes that exist")
    for pw, m in modes.items():
        got = set(ear[(ear.TECHNOLOGY == f"LVS{pw}{LR}")
                      & (ear.MODE_OF_OPERATION == m)].EMISSION)
        want = set(ms.LivestockEmissionFactors[pw])
        check(f"{pw}: emits {sorted(want)}", got == want, str(sorted(got)))

    # A soil-N2O-bearing mode is a conventional crop regime (e.g. MAIHI), plus
    # its agrivoltaic counterpart (AGVMAIHI) when panels are set to carry the
    # same soil emission - same crop, same soil, same nitrogen.
    crop_modes = {i + 1 for i, lbl in enumerate(ModeList)
                  if len(lbl) == 5 and lbl[:3] in ms.CropYieldFactors}
    if ms.AgrivoltaicEmitsSoilN2O:
        crop_modes |= {i + 1 for i, lbl in enumerate(ModeList)
                       if len(lbl) == 8 and lbl.startswith("AGV")
                       and lbl[3:6] in ms.CropYieldFactors}
    for emission in ms.CropSoilN2O:
        rows = ear[(ear.EMISSION == emission)
                   & ear.TECHNOLOGY.str.startswith("LNDAGR")]
        pairs = set(map(tuple, rows[["TECHNOLOGY", "MODE_OF_OPERATION"]]
                        .drop_duplicates().values))
        # Exactly the cluster/mode pairs that carry a crop output.
        want = {(t, m) for t in clusters for m in tech_modes.get(t, set())
                if m in crop_modes}
        check(f"{emission}: on every built crop mode, and only those",
              pairs == want,
              f"missing {len(want - pairs)}, extra {len(pairs - want)}")

    if a.keep:
        print(f"\ntemporary build kept at {out}")
    else:
        shutil.rmtree(out, ignore_errors=True)

    if _fails:
        print(f"\n{len(_fails)} FAILURE(S): {_fails}")
        return 1
    print("\nALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
