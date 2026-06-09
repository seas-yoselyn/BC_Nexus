from bcnexus.clews import sets_n_ratios as SnR
from bcnexus.clews import model_structure
from bcnexus import utils
from pathlib import Path
import pandas as pd

print_level_base = 2

# --------------------------------------------------------------------------
# Livestock Modelling
# --------------------------------------------------------------------------


# 1.  Assing modes of operation

def _assign_livestock_modes(agr_mode_count: int,
                             ms: object = model_structure) -> dict:
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


# 2.  Define SETs

def get_Livestock_SETs(ms: object = model_structure) -> dict:
    """
    Build TECHNOLOGY and FUEL identifier dicts for all three techs
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

            # Level 1 — land allocation tech and allocated land fuel
            lnd_tech   = f'LNDLVS{pathway}{land_region}'
            alloc_fuel = f'LVS{pathway}{land_region}'
            livestock_techs[lnd_tech] = (
                f'Land allocation for {label} in {land_region}'
            )
            livestock_fuels[alloc_fuel] = (
                f'Allocated land for {label} in {land_region}'
            )

            # Level 2 — herd tech
            hrd_tech = f'LVSHRD{pathway}{land_region}'
            livestock_techs[hrd_tech] = (
                f'Herd tech for {label} in {land_region}'
            )

            # Level 3 — production tech
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


# 3.  Activity Ratios

def update_IARlist(IARList_existing: list,
                   OARList_existing: list,
                   livestock_sets: dict,
                   livestock_modes: dict,
                   ms: object = model_structure) -> tuple:
   
    lvs_techs = set(livestock_sets.get('TECHNOLOGY', {}).keys())

    # Purge stale livestock rows from existing lists before appending new ones
    IARList_existing = [r for r in IARList_existing if r['c'][1] not in lvs_techs]
    OARList_existing = [r for r in OARList_existing if r['c'][1] not in lvs_techs]

    IARList_new = []
    OARList_new = []
    seen_iar = set()
    seen_oar = set()

    for region in ms.Regions.keys():
        for year in range(ms.snapshot['start'], ms.snapshot['end'] + 1):
            for land_region in ms.LandRegions:

                base_land_fuel = f'L{land_region}'

                for pathway, attrs in ms.LivestockPathways.items():
                    produce        = attrs['produce']
                    mode           = livestock_modes[pathway]
                    alloc_fuel     = f'LVS{pathway}{land_region}'
                    herd_fuel      = f'HRD{pathway}'
                    commodity_fuel = f'LVS{produce}'
                    stocking       = ms.LivestockStockingDensity[pathway]
                    yield_val      = ms.LivestockCommodityYield[produce]

                    lnd_tech = f'LNDLVS{pathway}{land_region}'
                    hrd_tech = f'LVSHRD{pathway}{land_region}'
                    gan_tech = f'LVS{pathway}{land_region}'

                    # Level 1 — land allocation (mode 1)
                    _add_iar(seen_iar, IARList_new,
                             region, lnd_tech, base_land_fuel, 1, year, 1)
                    _add_oar(seen_oar, OARList_new,
                             region, lnd_tech, alloc_fuel, 1, year, 1)

                    # Level 2 — herd tech
                    _add_iar(seen_iar, IARList_new,
                             region, hrd_tech, alloc_fuel, mode, year, 1)
                    _add_oar(seen_oar, OARList_new,
                             region, hrd_tech, herd_fuel, mode, year, stocking)

                    # Level 3 — production tech
                    _add_iar(seen_iar, IARList_new,
                             region, gan_tech, herd_fuel, mode, year, 1)
                    _add_oar(seen_oar, OARList_new,
                             region, gan_tech, commodity_fuel, mode, year, yield_val)

    IARList_existing.extend(IARList_new)
    OARList_existing.extend(OARList_new)


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

# 5.  Mode of operation CSV

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

# 7.  Dedup

def _dedup(lst: list) -> list:
    seen = set()
    out  = []
    for item in lst:
        k = tuple(item['c'])
        if k not in seen:
            seen.add(k)
            out.append(item)
    return out


# 8.  Save SETs and ratios to CSV

def _append_livestock_to_csvs(IARList: list,
                               OARList: list,
                               csv_save_to: Path,
                               livestock_sets: dict) -> None:
    """
    Append only livestock-specific entries to existing SET and ratio CSVs.
    Does not overwrite only adds rows not already present.
    Runs a final dedup pass on both ratio files.
    """
    lvs_techs = set(livestock_sets.get('TECHNOLOGY', {}).keys())

    # Remove all existing livestock rows before rewriting
    for ratio_file in (csv_save_to / 'InputActivityRatio.csv',
                       csv_save_to / 'OutputActivityRatio.csv'):
        df = pd.read_csv(ratio_file)
        before = len(df)
        after = len(df)
        df.to_csv(ratio_file, index=False)
        if before != after:
            utils.print_update(
                level=print_level_base + 1,
                message=f"Removed {before - after} stale livestock rows from {ratio_file.name}"
            )

    # Append TECHNOLOGY and FUEL sets
    for set_name, livestock_set in livestock_sets.items():
        set_file       = csv_save_to / f'{set_name}.csv'
        existing_df    = pd.read_csv(set_file)
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

    lvs_techs = set(livestock_sets.get('TECHNOLOGY', {}).keys())

    # Append IAR rows
    iar_file        = csv_save_to / 'InputActivityRatio.csv'
    existing_iar    = pd.read_csv(iar_file)
    existing_iar_keys = set(zip(
        existing_iar['REGION'],
        existing_iar['TECHNOLOGY'],
        existing_iar['FUEL'],
        existing_iar['MODE_OF_OPERATION'].astype(int),
        existing_iar['YEAR'].astype(int)
    ))
    new_iar_rows = [
        {
            'REGION': i['c'][0], 'TECHNOLOGY': i['c'][1], 'FUEL': i['c'][2],
            'MODE_OF_OPERATION': i['c'][3], 'YEAR': i['c'][4], 'VALUE': i['v']
        }
        for i in IARList
        if i['c'][1] in lvs_techs
        and (i['c'][0], i['c'][1], i['c'][2],
             int(i['c'][3]), int(i['c'][4])) not in existing_iar_keys
    ]
    if new_iar_rows:
        updated_iar = pd.concat(
            [existing_iar, pd.DataFrame(new_iar_rows)], ignore_index=True
        )
        updated_iar.to_csv(iar_file, index=False)
        utils.print_update(
            level=print_level_base + 1,
            message=f"Added {len(new_iar_rows)} livestock IAR rows."
        )

    # Append OAR rows
    oar_file        = csv_save_to / 'OutputActivityRatio.csv'
    existing_oar    = pd.read_csv(oar_file)
    existing_oar_keys = set(zip(
        existing_oar['REGION'],
        existing_oar['TECHNOLOGY'],
        existing_oar['FUEL'],
        existing_oar['MODE_OF_OPERATION'].astype(int),
        existing_oar['YEAR'].astype(int)
    ))
    new_oar_rows = [
        {
            'REGION': o['c'][0], 'TECHNOLOGY': o['c'][1], 'FUEL': o['c'][2],
            'MODE_OF_OPERATION': o['c'][3], 'YEAR': o['c'][4], 'VALUE': o['v']
        }
        for o in OARList
        if o['c'][1] in lvs_techs
        and (o['c'][0], o['c'][1], o['c'][2],
             int(o['c'][3]), int(o['c'][4])) not in existing_oar_keys
    ]
    if new_oar_rows:
        updated_oar = pd.concat(
            [existing_oar, pd.DataFrame(new_oar_rows)], ignore_index=True
        )
        updated_oar.to_csv(oar_file, index=False)
        utils.print_update(
            level=print_level_base + 1,
            message=f"Added {len(new_oar_rows)} livestock OAR rows."
        )

    # Final dedup pass
    dedup_cols = ['REGION', 'TECHNOLOGY', 'FUEL', 'MODE_OF_OPERATION', 'YEAR']
    
    for ratio_file in (csv_save_to / 'InputActivityRatio.csv',
                       csv_save_to / 'OutputActivityRatio.csv'):
        df = pd.read_csv(ratio_file)
        before = len(df)
        df = df[~df['TECHNOLOGY'].isin(lvs_techs)]
        after = len(df)
        df.to_csv(ratio_file, index=False)
        if before != after:
            utils.print_update(
                level=print_level_base + 1,
                message=f"Removed {before - after} stale livestock rows from {ratio_file.name}"
        )

 # 9.  Writing to SETs

def main(csv_save_to: str | Path = 'data/clews_data/SETs',
         SetNames: list = None,
         NewSetItems: list = None,
         IARList: list = None,
         OARList: list = None) -> None:

    csv_save_to = Path(csv_save_to)

    if any(x is None for x in (SetNames, NewSetItems, IARList, OARList)):
        SetNames, NewSetItems, IARList, OARList = SnR.build(csv_save_to)

    agr_mode_count = (
        len(NewSetItems[SetNames.index('MODE_OF_OPERATION')])
        if 'MODE_OF_OPERATION' in SetNames else 0
    )

    _assert_no_mode_collision(agr_mode_count)
    livestock_modes = _assign_livestock_modes(agr_mode_count)
    livestock_sets  = get_Livestock_SETs()

    NewSetItems = update_SetItems_with_Livestock(SetNames, NewSetItems, livestock_sets)

    IARList, OARList = update_IARlist(
        IARList_existing=IARList,
        OARList_existing=OARList,
        livestock_sets=livestock_sets,
        livestock_modes=livestock_modes,
    )

    IARList = _dedup(IARList)
    OARList = _dedup(OARList)

    _append_livestock_to_csvs(
        IARList=IARList,
        OARList=OARList,
        csv_save_to=csv_save_to,
        livestock_sets=livestock_sets,
    )

    update_mode_of_operation_csv(csv_save_to, livestock_modes)

    utils.print_update(level=print_level_base, message="Livestock build complete.")


if __name__ == '__main__':
    main()