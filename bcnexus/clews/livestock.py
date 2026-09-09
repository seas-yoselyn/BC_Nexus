"""
livestock.py
Adds livestock modes of operation to the existing LNDAGR cluster
technologies so that pasture and confined operations compete for the
same land pool as conventional crops inside the LP optimizer.

Structure (mirrors the crop chain in sets_n_ratios.BuildCLEWsModel and
the agrivoltaic chain in agrivoltaic.py):

    MINLND{LR}            -> L{LR}                      region land supply
    LNDLVS{pw}{LR}        L{LR} -> LLVS{pw}{LR}         mode 1, land tier
    LNDAGR{LR}C{cc}       LLVS{pw}{LR} -> LVS{pw}{LR}   livestock mode,
                          + WTRPRC in, WTREVT/WTRGRC/WTRSUR out
    LVSHRD{pw}{LR}        LVS{pw}{LR} -> HRD{pw}        stocking density
    LVS{pw}{LR}           HRD{pw} -> LVS{produce}       commodity yield

The middle row is the change. Livestock land used to run straight from
LNDLVS{pw}{LR} into the herd technology, bypassing the cluster
technologies entirely: it drew on L{LR} but never appeared in any
cluster's activity, so per-cluster area ceilings did not see it, and it
could neither crowd out a crop nor be crowded out by one. Land now
passes through LNDAGR{LR}C{cc} exactly as crop land and agrivoltaic land
do, in a mode of its own, so the cluster's water balance and area
ceiling apply to it.

Note the two land commodities either side of the cluster technology.
LLVS{pw}{LR} is the pre-cluster land tier, the analogue of L{combo}{LR}
for crops; LVS{pw}{LR} is the allocated land the herd technology
consumes, the analogue of CRP{crop}. Keeping them distinct is what lets
the cluster technology sit in between without renaming anything
downstream, so the CapitalCost / FixedCost / VariableCost /
ResidualCapacity / OperationalLife rows keyed on LNDLVS* and LVSHRD* are
unaffected.

Stocking density is not cluster-differentiated - there is no GAEZ-style
per-cluster carrying capacity in the input data - so every cluster gets
every livestock mode at the same yield. Only the water balance varies by
cluster. If per-cluster carrying capacity ever arrives it belongs on the
LNDAGR OAR for LVS{pw}{LR}, the same slot the crop yield occupies, and
it should carry the same MinCropYieldOAR-style floor the crops use.

Author:  Yoselyn (YOS), 2025
"""

import os
import decimal
from pathlib import Path

import pandas as pd

from bcnexus.clews import sets_n_ratios as SnR
from bcnexus.clews import model_structure
from bcnexus import utils

print_level_base = 2

# Prefix of the cluster technologies livestock modes are attached to.
CLUSTER_TECH_PREFIX = 'LNDAGR'

# Significant figures for the water-balance coefficients. Must match the
# decimal context in sets_n_ratios.BuildCLEWsModel and in agrivoltaic, so
# livestock water is not written to finer precision than the crop water it
# now competes against.
_CTX = decimal.Context()
_CTX.prec = 2


def _fmt(value: float) -> str:
    return format(_CTX.create_decimal(repr(float(value))), 'f')


# --------------------------------------------------------------------------
# Cluster data
# --------------------------------------------------------------------------

def _load_cluster_data(ms: object = model_structure) -> dict:
    """
    Read the GeoCLEWs cluster files for every land region.

    Only the main cluster file (for the cluster ids) and the precipitation
    file (for the water balance) are needed: livestock has no crop-combination
    columns to look up, and no irrigation.

    Returns ``{region: {'Clusters': [...], 'PrecipitationClusters': [...]}}``.
    """
    lcd = ms.LandCluster_data
    root = lcd['root']
    out = {}

    for region in ms.LandRegions:
        cluster_file = os.path.join(
            root, lcd['ClusterBaseFileName'] + region + '.csv')
        precip_file = os.path.join(
            root, lcd['PrecipitationClusterBaseFileName'] + region + '.csv')
        out[region] = {
            'Clusters': open(cluster_file, 'r').readlines(),
            'PrecipitationClusters': open(precip_file, 'r').readlines(),
        }

    return out


def _cluster_precipitation(rows: list) -> dict:
    """Map cluster id (zero-padded to two digits) -> precipitation depth."""
    depth = {}
    for line in rows[1:]:
        if not line.strip():
            continue
        parts = line.split(',')
        depth[parts[0].strip().zfill(2)] = float(parts[1])
    return depth


def _cluster_ids(rows: list) -> list:
    """Cluster ids from the main cluster file, zero-padded to two digits."""
    return [line.split(',')[0].strip().zfill(2)
            for line in rows[1:] if line.strip()]


# --------------------------------------------------------------------------
# 1.  Assign modes of operation
# --------------------------------------------------------------------------

def _assign_livestock_modes(ModeList: list = None,
                            agr_mode_count: int = None,
                            ms: object = model_structure) -> dict:
    """
    Allocate one mode of operation per livestock pathway.

    Pass ``ModeList`` (the list returned by sets_n_ratios.BuildCLEWsModel)
    whenever it is available: the labels are appended to it, so the mode
    numbers, MODE_OF_OPERATION.csv and ModeList.txt all stay in step with the
    crop and agrivoltaic modes appended ahead of them. Falling back to
    ``agr_mode_count`` yields the same numbers but leaves ModeList without the
    labels, which is why it is only for callers that genuinely lack the list.
    """
    if ModeList is None and agr_mode_count is None:
        raise TypeError("pass ModeList, or agr_mode_count if it is unavailable")

    if ModeList is not None:
        modes = {}
        for pathway in ms.LivestockPathways:
            label = 'LVS' + pathway
            if label in ModeList:
                modes[pathway] = ModeList.index(label) + 1
                continue
            ModeList.append(label)
            modes[pathway] = len(ModeList)
    else:
        _assert_no_mode_collision(agr_mode_count)
        modes = {
            pw: agr_mode_count + 1 + i
            for i, pw in enumerate(ms.LivestockPathways.keys())
        }

    utils.print_update(
        level=print_level_base + 1,
        message=f"Livestock modes assigned: {modes}"
    )
    return modes


def _assert_no_mode_collision(agr_mode_count: int) -> None:
    assert isinstance(agr_mode_count, int) and agr_mode_count >= 0, (
        f"agr_mode_count must be a non-negative integer, got {agr_mode_count!r}."
    )


# --------------------------------------------------------------------------
# 2.  Define SETs
# --------------------------------------------------------------------------

def get_Livestock_SETs(ms: object = model_structure) -> dict:
    """
    Build TECHNOLOGY and FUEL identifier dicts for the livestock chain.
    """
    livestock_techs = {}
    livestock_fuels = {}

    utils.print_update(
        level=print_level_base,
        message="Creating Livestock Technologies and Fuels"
    )

    for pathway, attrs in ms.LivestockPathways.items():
        produce  = attrs['produce']
        label    = attrs['label']
        produce_label = ms.LivestockProduce.get(produce, produce)

        # Commodity fuel (LVSBEF, LVSMIL)
        commodity_fuel = f'LVS{produce}'
        livestock_fuels.setdefault(
            commodity_fuel,
            f'Commodity fuel for {produce_label}'
        )

        # Herd fuel (HRDBEFN, HRDBEFC, HRDMIL) in thousand of heads
        herd_fuel = f'HRD{pathway}'
        livestock_fuels.setdefault(
            herd_fuel,
            f'Herd fuel (1000 heads) for {label}'
        )

        for land_region in ms.LandRegions:

            # Level 1 - land allocation tech and the pre-cluster land tier.
            # LLVS is the livestock analogue of the L{combo} crop land tier:
            # it is what the cluster technologies compete over.
            lnd_tech  = f'LNDLVS{pathway}{land_region}'
            tier_fuel = f'LLVS{pathway}{land_region}'
            livestock_techs[lnd_tech] = (
                f'Land allocation for {label} in {land_region}'
            )
            livestock_fuels[tier_fuel] = (
                f'Land tier for {label} in {land_region}'
            )

            # Level 2 - land placed in a cluster, then consumed by the herd.
            alloc_fuel = f'LVS{pathway}{land_region}'
            livestock_fuels[alloc_fuel] = (
                f'Cluster-allocated land for {label} in {land_region}'
            )

            hrd_tech = f'LVSHRD{pathway}{land_region}'
            livestock_techs[hrd_tech] = (
                f'Herd tech for {label} in {land_region}'
            )

            # Level 3 - production tech
            gan_tech = f'LVS{pathway}{land_region}'
            livestock_techs[gan_tech] = (
                f'Production tech for {label} in {land_region}'
            )

    return {'TECHNOLOGY': livestock_techs, 'FUEL': livestock_fuels}


def update_SetItems_with_Livestock(SetNames: list,
                                   NewSetItems: list,
                                   livestock_sets: dict) -> list:
    """
    Append livestock TECHNOLOGY and FUEL entries to existing lists.
    """
    utils.print_update(level=print_level_base, message="Updating Livestock SETs...")

    for set_name, livestock_set in livestock_sets.items():
        utils.print_update(
            level=print_level_base + 1,
            message=f"Updating SET: '{set_name}'"
        )

        if set_name not in SetNames:
            raise KeyError(
                f"Set '{set_name}' not found in SetNames. "
                f"Available sets: {SetNames}"
            )

        idx = SetNames.index(set_name)
        existing_values = {item['value'] for item in NewSetItems[idx]}

        for key, description in livestock_set.items():
            if key not in existing_values:
                NewSetItems[idx].append({
                    'value': key,
                    'name': description,
                    'color': '#000000'
                })

    utils.print_update(level=print_level_base + 1, message="Livestock SETs updated.")
    return NewSetItems


# --------------------------------------------------------------------------
# 3.  Activity ratios
# --------------------------------------------------------------------------

def update_IARlist(IARList_existing: list,
                   OARList_existing: list,
                   livestock_sets: dict,
                   livestock_modes: dict,
                   ms: object = model_structure,
                   EARList_existing: list = None) -> tuple:
    """
    Rebuild every livestock IAR/OAR row, including the livestock modes on
    the LNDAGR cluster technologies.

    Pass ``EARList_existing`` to also generate the enteric-fermentation and
    manure emission rows onto the production technologies. Without it the
    ratios are built but no emissions are, which is only right for a caller
    that has no emission handling at all.
    """
    lvs_techs = set(livestock_sets.get('TECHNOLOGY', {}).keys())
    lvs_modes = {str(m) for m in livestock_modes.values()}

    # Purge stale livestock rows before appending new ones. There are two
    # families now: the livestock technologies themselves, and the livestock
    # modes on the shared cluster technologies. Missing the second family
    # would leave rows from a previous build sitting at mode numbers that
    # have since moved - drift that stays invisible until the LP is solved.
    def _stale(row):
        tech, mode = row['c'][1], str(row['c'][3])
        return tech in lvs_techs or (
            str(tech).startswith(CLUSTER_TECH_PREFIX) and mode in lvs_modes)

    IARList_existing = [r for r in IARList_existing if not _stale(r)]
    OARList_existing = [r for r in OARList_existing if not _stale(r)]

    IARList_new = []
    OARList_new = []
    seen_iar = set()
    seen_oar = set()

    # Emissions are keyed the same way but sit only on the production
    # technologies, so the cluster clause in _stale does not apply to them.
    if EARList_existing is None:
        EARList_new = None
        seen_ear = None
    else:
        EARList_existing[:] = [r for r in EARList_existing
                               if r['c'][1] not in lvs_techs]
        EARList_new = []
        seen_ear = set()

    cluster_data = _load_cluster_data(ms)

    for region in ms.Regions.keys():
        for year in range(ms.snapshot['start'], ms.snapshot['end'] + 1):
            for land_region in ms.LandRegions:

                base_land_fuel = f'L{land_region}'
                rd = cluster_data[land_region]
                cluster_ids = _cluster_ids(rd['Clusters'])
                precip = _cluster_precipitation(rd['PrecipitationClusters'])

                for pathway, attrs in ms.LivestockPathways.items():
                    produce        = attrs['produce']
                    mode           = livestock_modes[pathway]
                    tier_fuel      = f'LLVS{pathway}{land_region}'
                    alloc_fuel     = f'LVS{pathway}{land_region}'
                    herd_fuel      = f'HRD{pathway}'
                    commodity_fuel = f'LVS{produce}'
                    stocking       = ms.LivestockStockingDensity[pathway]
                    yield_val      = ms.LivestockCommodityYield[produce]
                    et_frac        = ms.LivestockEvapotranspirationPercent[pathway]
                    gw_frac        = ms.LivestockGroundwaterPercentofExcess[pathway]

                    lnd_tech = f'LNDLVS{pathway}{land_region}'
                    hrd_tech = f'LVSHRD{pathway}{land_region}'
                    gan_tech = f'LVS{pathway}{land_region}'

                    # Level 1 - land tier (mode 1).
                    # No water balance here: the land has not been placed in
                    # a cluster yet, so there is no precipitation depth to
                    # apply. It is applied on the cluster technology below,
                    # exactly as it is for every crop and land cover.
                    _add_iar(seen_iar, IARList_new,
                             region, lnd_tech, base_land_fuel, 1, year, 1)
                    _add_oar(seen_oar, OARList_new,
                             region, lnd_tech, tier_fuel, 1, year, 1)

                    # Level 1b - the cluster technologies. This is where
                    # livestock competes with crops, agrivoltaics and the
                    # non-crop covers for the cluster's area.
                    for cluster_id in cluster_ids:
                        cluster_tech = (f'{CLUSTER_TECH_PREFIX}'
                                        f'{land_region}C{cluster_id}')

                        _add_iar(seen_iar, IARList_new,
                                 region, cluster_tech, tier_fuel,
                                 mode, year, 1)
                        _add_oar(seen_oar, OARList_new,
                                 region, cluster_tech, alloc_fuel,
                                 mode, year, 1)

                        prc = precip.get(cluster_id, 0.0)
                        if prc <= 0:
                            continue
                        prc_str = _fmt(prc)
                        prc_val = float(prc_str)
                        et_val  = prc_val * et_frac
                        excess  = prc_val - et_val
                        grc_val = excess * gw_frac
                        sur_val = excess * (1 - gw_frac)

                        _add_iar(seen_iar, IARList_new,
                                 region, cluster_tech, f'WTRPRC{land_region}',
                                 mode, year, prc_str)
                        _add_oar(seen_oar, OARList_new,
                                 region, cluster_tech, f'WTREVT{land_region}',
                                 mode, year, _fmt(et_val))
                        _add_oar(seen_oar, OARList_new,
                                 region, cluster_tech, f'WTRGRC{land_region}',
                                 mode, year, _fmt(grc_val))
                        _add_oar(seen_oar, OARList_new,
                                 region, cluster_tech, f'WTRSUR{land_region}',
                                 mode, year, _fmt(sur_val))

                    # Level 2 - herd tech
                    _add_iar(seen_iar, IARList_new,
                             region, hrd_tech, alloc_fuel, mode, year, 1)
                    _add_oar(seen_oar, OARList_new,
                             region, hrd_tech, herd_fuel, mode, year, stocking)

                    # Level 3 - production tech
                    _add_iar(seen_iar, IARList_new,
                             region, gan_tech, herd_fuel, mode, year, 1)
                    _add_oar(seen_oar, OARList_new,
                             region, gan_tech, commodity_fuel, mode, year, yield_val)

                    # Enteric fermentation and manure emissions. The
                    # production technology takes HRD{pw} at an input
                    # activity ratio of 1, so its activity is thousand head
                    # and these factors are per thousand head. Generated
                    # here so the mode number can never drift away from the
                    # technology it belongs to - the hand-maintained rows
                    # this replaces were still pinned to modes 58-62 after
                    # agrivoltaics pushed livestock to 78-82, which meant
                    # every livestock emission in the model was zero.
                    if EARList_new is not None:
                        for emission, factor in \
                                ms.LivestockEmissionFactors[pathway].items():
                            _add_ear(seen_ear, EARList_new, region, gan_tech,
                                     emission, mode, year, factor)

    IARList_existing.extend(IARList_new)
    OARList_existing.extend(OARList_new)
    if EARList_new is not None:
        EARList_existing.extend(EARList_new)

    utils.print_update(
        level=print_level_base + 1,
        message=(f"Livestock: {len(IARList_new)} IAR, {len(OARList_new)} OAR "
                 f"and {len(EARList_new) if EARList_new is not None else 0} "
                 f"EAR rows written across {len(livestock_modes)} mode(s) on "
                 f"the {CLUSTER_TECH_PREFIX} cluster technologies")
    )

    return IARList_existing, OARList_existing


def _add_iar(seen, lst, region, tech, fuel, mode, year, value):
    key = (region, tech, fuel, mode, year)
    if key not in seen:
        lst.append({'c': list(key), 'v': value})
        seen.add(key)


def _add_oar(seen, lst, region, tech, fuel, mode, year, value):
    key = (region, tech, fuel, mode, year)
    if key not in seen:
        lst.append({'c': list(key), 'v': value})
        seen.add(key)


def _add_ear(seen, lst, region, tech, emission, mode, year, value):
    key = (region, tech, emission, mode, year)
    if key not in seen:
        lst.append({'c': list(key), 'v': value})
        seen.add(key)


# --------------------------------------------------------------------------
# 4.  Mode of operation CSV
# --------------------------------------------------------------------------

def update_mode_of_operation_csv(csv_save_to: Path,
                                 livestock_modes: dict,
                                 ms: object = model_structure) -> None:

    mop_file       = csv_save_to / 'MODE_OF_OPERATION.csv'
    mode_list_file = csv_save_to / 'ModeList.txt'

    utils.print_update(
        level=print_level_base + 1,
        message=f"Checking MODE_OF_OPERATION at {mop_file}"
    )

    existing_df    = pd.read_csv(mop_file, usecols=['VALUE'])
    existing_modes = set(existing_df['VALUE'].astype(str))
    new_modes      = set(str(m) for m in livestock_modes.values())
    missing_modes  = new_modes - existing_modes

    if missing_modes:
        utils.print_update(
            level=print_level_base + 2,
            message=f"Adding {len(missing_modes)} new mode(s) to {mop_file}"
        )
        updated_df = pd.concat(
            [existing_df, pd.DataFrame({'VALUE': sorted(missing_modes)})],
            ignore_index=True
        )
        updated_df.to_csv(mop_file, index=False)
    else:
        utils.print_update(
            level=print_level_base + 2,
            message="No new modes to add."
        )

    existing_lines = mode_list_file.read_text() if mode_list_file.exists() else ''
    with open(mode_list_file, 'a') as f:
        for pw, mode in sorted(livestock_modes.items(), key=lambda x: x[1]):
            if f"{mode}:" in existing_lines:
                continue
            label = ms.LivestockPathways[pw]['label']
            f.write(f"{mode}: Livestock pathway {label}\n")


# --------------------------------------------------------------------------
# 5.  Keep mode-keyed parameter files in step with the assigned modes
# --------------------------------------------------------------------------

# Parameter files keyed on (TECHNOLOGY, MODE_OF_OPERATION). Livestock mode
# numbers move whenever a crop or agrivoltaic mode is added ahead of them, so
# a hand-maintained row naming a livestock mode silently detaches: the cost
# lands on a mode the technology does not have and the herd becomes free.
# This already happened once - VariableCost.csv carried modes 58-62 while the
# build had moved livestock to 78-82.
#
# EmissionActivityRatio is deliberately NOT in this list. Its livestock rows
# are generated by update_IARlist and written by
# sets_n_ratios.write_emission_activity_ratio, which drops and rewrites them
# wholesale. Remapping them here as well would be a second mechanism editing
# the same rows, and the two would disagree the moment the generated set of
# emissions changes.
MODE_KEYED_PARAM_FILES = (
    'VariableCost.csv',
    'TechnologyActivityByModeLowerLimit.csv',
    'TechnologyActivityByModeUpperLimit.csv',
)


def sync_livestock_param_modes(csv_dir: str | Path,
                               livestock_modes: dict,
                               ms: object = model_structure,
                               dry_run: bool = False) -> dict:
    """
    Rewrite MODE_OF_OPERATION on livestock rows of the mode-keyed parameter
    files so they match the modes just assigned.

    A livestock technology has exactly one mode, so every row naming that
    technology belongs to it whatever number the file happens to carry. That
    makes the remap unambiguous and idempotent. Rows for any other technology
    are left alone - in particular the LNDAGR cluster rows, where the mode
    number does distinguish one land use from another.

    Returns ``{filename: rows_changed}`` for the files that exist.
    """
    csv_dir = Path(csv_dir)

    # tech -> its single mode number
    tech_mode = {}
    for pathway, mode in livestock_modes.items():
        for land_region in ms.LandRegions:
            tech_mode[f'LVSHRD{pathway}{land_region}'] = int(mode)
            tech_mode[f'LVS{pathway}{land_region}'] = int(mode)

    changed = {}
    for name in MODE_KEYED_PARAM_FILES:
        path = csv_dir / name
        if not path.exists():
            continue
        df = pd.read_csv(path)
        if 'TECHNOLOGY' not in df.columns or 'MODE_OF_OPERATION' not in df.columns:
            continue

        target = df['TECHNOLOGY'].map(tech_mode)
        hit = target.notna()
        if not hit.any():
            continue

        current = pd.to_numeric(df['MODE_OF_OPERATION'], errors='coerce')
        differs = hit & (current != target)
        n = int(differs.sum())
        changed[name] = n
        if n:
            if not dry_run:
                df.loc[differs, 'MODE_OF_OPERATION'] = \
                    target[differs].astype(int).values
                df.to_csv(path, index=False)
            utils.print_update(
                level=print_level_base + 1,
                message=(f"{'Would remap' if dry_run else 'Remapped'} {n} "
                         f"livestock row(s) in {name} onto the assigned modes")
            )

    return changed


# --------------------------------------------------------------------------
# 6.  Dedup
# --------------------------------------------------------------------------

def _dedup(lst: list) -> list:
    seen = set()
    out  = []
    for item in lst:
        k = tuple(item['c'])
        if k not in seen:
            seen.add(k)
            out.append(item)
    return out


# --------------------------------------------------------------------------
# 7.  Save SETs and ratios to CSV
# --------------------------------------------------------------------------

def _append_livestock_to_csvs(IARList: list,
                              OARList: list,
                              csv_save_to: Path,
                              livestock_sets: dict,
                              livestock_modes: dict) -> None:
    """
    Merge the livestock rows into the SET and ratio CSVs already on disk.

    Only the standalone path (``main()``) needs this; the builder writes the
    whole of IARList/OARList through sets_n_ratios.UpdateSETS instead.

    Livestock owns two families of rows: its own technologies, and the
    livestock modes on the shared LNDAGR cluster technologies. Both are
    dropped from the file before the new rows go in, so re-running never
    leaves rows behind at mode numbers that have moved.
    """
    lvs_techs = set(livestock_sets.get('TECHNOLOGY', {}).keys())
    lvs_modes = {str(m) for m in livestock_modes.values()}

    def _owned_rows(df):
        tech = df['TECHNOLOGY'].astype(str)
        mode = df['MODE_OF_OPERATION'].astype(str)
        return tech.isin(lvs_techs) | (
            tech.str.startswith(CLUSTER_TECH_PREFIX) & mode.isin(lvs_modes))

    def _is_livestock(row):
        tech, mode = str(row['c'][1]), str(row['c'][3])
        return tech in lvs_techs or (
            tech.startswith(CLUSTER_TECH_PREFIX) and mode in lvs_modes)

    # SET files
    for set_name, livestock_set in livestock_sets.items():
        set_file        = csv_save_to / f'{set_name}.csv'
        existing_df     = pd.read_csv(set_file)
        existing_values = set(existing_df['VALUE'].astype(str))
        new_rows = [
            {'VALUE': k}
            for k in livestock_set.keys()
            if k not in existing_values
        ]
        if new_rows:
            updated_df = pd.concat(
                [existing_df, pd.DataFrame(new_rows)], ignore_index=True
            )
            updated_df.to_csv(set_file, index=False)
            utils.print_update(
                level=print_level_base + 1,
                message=f"Added {len(new_rows)} rows to {set_name}.csv"
            )

    # Ratio files
    for ratio_file, rows in ((csv_save_to / 'InputActivityRatio.csv', IARList),
                             (csv_save_to / 'OutputActivityRatio.csv', OARList)):
        df = pd.read_csv(ratio_file)
        before = len(df)
        df = df[~_owned_rows(df)]
        removed = before - len(df)
        if removed:
            utils.print_update(
                level=print_level_base + 1,
                message=(f"Removed {removed} stale livestock rows from "
                         f"{ratio_file.name}")
            )

        new_rows = [
            {
                'REGION': r['c'][0], 'TECHNOLOGY': r['c'][1], 'FUEL': r['c'][2],
                'MODE_OF_OPERATION': r['c'][3], 'YEAR': r['c'][4], 'VALUE': r['v']
            }
            for r in rows if _is_livestock(r)
        ]
        if new_rows:
            df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
            utils.print_update(
                level=print_level_base + 1,
                message=(f"Added {len(new_rows)} livestock rows to "
                         f"{ratio_file.name}")
            )

        df = df.drop_duplicates(
            subset=['REGION', 'TECHNOLOGY', 'FUEL',
                    'MODE_OF_OPERATION', 'YEAR'],
            keep='last')
        df.to_csv(ratio_file, index=False)


# --------------------------------------------------------------------------
# 8.  Entry point
# --------------------------------------------------------------------------

def main(csv_save_to: str | Path = 'data/clews_data/SETs',
         SetNames: list = None,
         NewSetItems: list = None,
         IARList: list = None,
         OARList: list = None,
         ModeList: list = None,
         EARList: list = None,
         param_csv_dir: str | Path = None) -> None:

    csv_save_to = Path(csv_save_to)

    if any(x is None for x in (SetNames, NewSetItems, IARList, OARList)):
        SetNames, NewSetItems, IARList, OARList, EARList, ModeList = \
            SnR.build(csv_save_to)

    if ModeList is not None:
        livestock_modes = _assign_livestock_modes(ModeList=ModeList)
    else:
        agr_mode_count = (
            len(NewSetItems[SetNames.index('MODE_OF_OPERATION')])
            if 'MODE_OF_OPERATION' in SetNames else 0
        )
        livestock_modes = _assign_livestock_modes(agr_mode_count=agr_mode_count)

    livestock_sets = get_Livestock_SETs()

    NewSetItems = update_SetItems_with_Livestock(SetNames, NewSetItems, livestock_sets)

    IARList, OARList = update_IARlist(
        IARList_existing=IARList,
        OARList_existing=OARList,
        livestock_sets=livestock_sets,
        livestock_modes=livestock_modes,
        EARList_existing=EARList,
    )

    IARList = _dedup(IARList)
    OARList = _dedup(OARList)

    _append_livestock_to_csvs(
        IARList=IARList,
        OARList=OARList,
        csv_save_to=csv_save_to,
        livestock_sets=livestock_sets,
        livestock_modes=livestock_modes,
    )

    update_mode_of_operation_csv(csv_save_to, livestock_modes)

    # Emission rows go where the hand-maintained CO2 rows live, which is the
    # build input directory rather than the SETs directory. Defaults to
    # csv_save_to so the standalone path still produces a complete file.
    if EARList is not None:
        SnR.write_emission_activity_ratio(
            EARList, param_csv_dir if param_csv_dir is not None else csv_save_to)

    sync_livestock_param_modes(
        param_csv_dir if param_csv_dir is not None else csv_save_to,
        livestock_modes)

    utils.print_update(level=print_level_base, message="Livestock build complete.")


if __name__ == '__main__':
    main()
