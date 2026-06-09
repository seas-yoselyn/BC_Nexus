from bcnexus.clews import sets_n_ratios as SnR
from bcnexus.clews import model_structure
from bcnexus import utils
from pathlib import Path
import pandas as pd

print_level_base = 2

# --------------------------------------------------------------------------
# Agrivoltaic Modelling
# --------------------------------------------------------------------------
# Two-level structure mirroring regular crops:
#
# Level 1 — Land allocation techs (one per crop × intensity × irrigation × region):
#   Tech:  LNDAGV{Crop}{Intensity}{IrrType}{Region}
#   IAR:   L{Region}  (base land fuel, mode 1) — competes with regular crop
#   OAR:   LAGV{Crop}{Intensity}{IrrType}{Region}  (AGV allocated land, mode 1)
#
# Level 2 — AGV cluster techs (one per cluster per region, mirrors LNDAGRBC1C01..C07):
#   Tech:  LNDAGVAGR{Region}C01..C07
#   IAR:   LAGV{Crop}{Intensity}{IrrType}{Region}  (agv allocated land, mode = agv crop mode)
#   IAR:   SOL  (solar input, mode = agv crop mode)
#   OAR:   CRP{Crop}  (crop output, placeholder 1.0, mode = agv crop mode)
#   OAR:   ELCB01  (electricity output, placeholder 1.0, mode = agv crop mode)
#
# Constants defined in model_structure.py:
#   AgrivoltaicCrops    — ['MAI', 'WHE', 'PTW']
#   AgrivoltaicModes    — {'MAI': 63, 'WHE': 64, 'PTW': 65}
#   AgrivoltaicSolarIAR — solar input activity ratio (placeholder: 1.0)
#   AgrivoltaicElecOAR  — electricity output activity ratio (placeholder: 1.0)
# --------------------------------------------------------------------------


# 1.  Create SETs

def get_Agrivoltaic_SETs(ms: object = model_structure) -> dict:
    """
    Build TECHNOLOGY and FUEL identifier dicts for all agrivoltaic variants.

    Level 1 techs:  LNDAGV{Crop}{Intensity}{IrrType}{Region}
    Level 1 fuels:  LAGV{Crop}{Intensity}{IrrType}{Region}
    Level 2 techs:  LNDAGVAGR{Region}C01..C07
    """
    agv_techs = {}
    agv_fuels = {}

    utils.print_update(level=print_level_base,
                       message="Creating Agrivoltaic Technologies and Fuels from model structure...")

    for land_region in ms.LandRegions:

        # -- Level 1: land allocation techs and AGV allocated land fuels ------
        for crop_code in ms.AgrivoltaicCrops:
            for irr_type in ms.IrrigationTypeList.keys():
                for intensity in ms.IntensityList.keys():

                    agv_tech = f'LNDAGV{crop_code}{intensity}{irr_type}{land_region}'
                    agv_techs[agv_tech] = (
                        f'Agrivoltaic land allocation for {crop_code} '
                        f'({ms.IrrigationTypeList[irr_type]}, {ms.IntensityList[intensity]}) '
                        f'in Land region {land_region}'
                    )

                    agv_land_fuel = f'LAGV{crop_code}{intensity}{irr_type}{land_region}'
                    agv_fuels[agv_land_fuel] = (
                        f'Agrivoltaic allocated land for {crop_code} '
                        f'({ms.IrrigationTypeList[irr_type]}, {ms.IntensityList[intensity]}) '
                        f'in Land region {land_region}'
                    )

        # -- Level 2: AGV cluster techs (one per cluster per region) ----------
        for c in range(1, 8):
            agv_cluster_tech = f'LNDAGVAGR{land_region}C{str(c).zfill(2)}'
            agv_techs[agv_cluster_tech] = (
                f'Agrivoltaic cluster tech {c} in Land region {land_region}'
            )

    utils.print_update(level=print_level_base + 1,
                       message=f"Agrivoltaic Technologies: {len(agv_techs)}, "
                                f"AGV land fuels: {len(agv_fuels)}")

    return {'TECHNOLOGY': agv_techs, 'FUEL': agv_fuels}


def update_SetItems_with_Agrivoltaic(SetNames: list,
                                     NewSetItems: list,
                                     agv_sets: dict) -> list:
    """
    Append agrivoltaic TECHNOLOGY and FUEL entries to the existing set-item lists.
    """
    utils.print_update(level=print_level_base, message="Updating Agrivoltaic SETs...")

    for set_name, agv_set in agv_sets.items():
        if set_name not in SetNames:
            raise KeyError(
                f"Set '{set_name}' not found in SetNames. "
                f"Available sets: {SetNames}"
            )
        idx = SetNames.index(set_name)
        existing_values = {item['value'] for item in NewSetItems[idx]}

        for key, description in agv_set.items():
            if key not in existing_values:
                NewSetItems[idx].append({
                    'value': key,
                    'name': description,
                    'color': '#000000'
                })

    utils.print_update(level=print_level_base + 1, message="Agrivoltaic SETs updated.")
    return NewSetItems


# 2.  Ratios

def _assert_no_mode_collision(agr_mode_count: int, ms: object = model_structure) -> None:
    min_agv_mode = min(ms.AgrivoltaicModes.values())
    assert min_agv_mode > agr_mode_count, (
        f"Mode collision detected: agricultural pipeline uses up to mode "
        f"{agr_mode_count}, but agrivoltaic modes start at {min_agv_mode}. "
        f"Increase AgrivoltaicModes values in model_structure.py."
    )


def update_IARlist(IARList_existing: list,
                   OARList_existing: list,
                   agv_sets: dict,
                   agr_mode_count: int = 0,
                   ms: object = model_structure) -> tuple:
    """
    Add agrivoltaic IAR and OAR entries for both levels.

    Level 1 (mode 1):
        IAR: LNDAGV{Crop}{I}{R}{Region}  consumes  L{Region}  (base land)
        OAR: LNDAGV{Crop}{I}{R}{Region}  produces  LAGV{Crop}{I}{R}{Region}

    Level 2 (mode = agv crop mode):
        IAR: LNDAGVAGR{Region}C0X  consumes  LAGV{Crop}{I}{R}{Region}
        IAR: LNDAGVAGR{Region}C0X  consumes  SOL
        OAR: LNDAGVAGR{Region}C0X  produces  CRP{Crop}  (placeholder 1.0)
        OAR: LNDAGVAGR{Region}C0X  produces  ELCB01     (placeholder 1.0)
    """
    if agr_mode_count > 0:
        _assert_no_mode_collision(agr_mode_count, ms)

    IARList_new = []
    OARList_new = []
    seen_iar = set()
    seen_oar = set()

    agv_modes = ms.AgrivoltaicModes     # {'MAI': 63, 'WHE': 64, 'PTW': 65}
    solar_iar = ms.AgrivoltaicSolarIAR  # placeholder: 1.0
    elec_oar  = ms.AgrivoltaicElecOAR   # placeholder: 1.0

    for region in ms.Regions.keys():
        for year in range(ms.snapshot['start'], ms.snapshot['end'] + 1):
            for land_region in ms.LandRegions:

                base_land_fuel = f'L{land_region}'  # e.g. LBC1

                # AGV cluster techs for this land region
                agv_cluster_techs = [
                    f'LNDAGVAGR{land_region}C{str(c).zfill(2)}'
                    for c in range(1, 8)
                ]

                for crop_code in ms.AgrivoltaicCrops:
                    agv_mode  = agv_modes[crop_code]
                    crop_fuel = f'CRP{crop_code}'

                    for irr_type in ms.IrrigationTypeList.keys():
                        for intensity in ms.IntensityList.keys():

                            agv_tech      = f'LNDAGV{crop_code}{intensity}{irr_type}{land_region}'
                            agv_land_fuel = f'LAGV{crop_code}{intensity}{irr_type}{land_region}'

                            # ── Level 1 IAR: consumes base land (e.g. LBC1) in mode 1 ─────
                            key = (region, agv_tech, base_land_fuel, 1, year)
                            if key not in seen_iar:
                                IARList_new.append({'c': list(key), 'v': 1})
                                seen_iar.add(key)

                            # ── Level 1 OAR: produces AGV allocated land fuel in mode 1 ───
                            key = (region, agv_tech, agv_land_fuel, 1, year)
                            if key not in seen_oar:
                                OARList_new.append({'c': list(key), 'v': 1})
                                seen_oar.add(key)

                            # ── Level 2: AGV cluster techs ────────────────────────────────
                            for agv_cluster_tech in agv_cluster_techs:

                                # IAR 1: consumes AGV allocated land fuel
                                key = (region, agv_cluster_tech, agv_land_fuel, agv_mode, year)
                                if key not in seen_iar:
                                    IARList_new.append({'c': list(key), 'v': 1})
                                    seen_iar.add(key)

                                # IAR 2: consumes SOL (solar input)
                                key = (region, agv_cluster_tech, 'SOL', agv_mode, year)
                                if key not in seen_iar:
                                    IARList_new.append({'c': list(key), 'v': solar_iar})
                                    seen_iar.add(key)

                                # OAR 1: produces crop fuel (placeholder yield 1.0)
                                key = (region, agv_cluster_tech, crop_fuel, agv_mode, year)
                                if key not in seen_oar:
                                    OARList_new.append({'c': list(key), 'v': 1})
                                    seen_oar.add(key)

                                # OAR 2: produces electricity
                                key = (region, agv_cluster_tech, 'ELCB01', agv_mode, year)
                                if key not in seen_oar:
                                    OARList_new.append({'c': list(key), 'v': elec_oar})
                                    seen_oar.add(key)

    IARList_existing.extend(IARList_new)
    OARList_existing.extend(OARList_new)

    utils.print_update(level=print_level_base,
                       message=f"Agrivoltaic Ratios updated. "
                                f"Added {len(IARList_new)} IAR rows and "
                                f"{len(OARList_new)} OAR rows.")
    return IARList_existing, OARList_existing


# 3.  MODE OF OPERATION CSV

def update_mode_of_operation_csv(csv_save_to: str | Path,
                                 ms: object = model_structure) -> None:
    """
    Ensure all agrivoltaic modes are present in MODE_OF_OPERATION.csv and
    appended (without duplicates) to ModeList.txt in the same directory.
    """
    csv_save_to = Path(csv_save_to)
    mop_file = csv_save_to / 'MODE_OF_OPERATION.csv'
    mode_list_file = csv_save_to / 'ModeList.txt'

    utils.print_update(level=print_level_base + 1,
                       message=f"Checking MODE_OF_OPERATION at {mop_file}")

    existing_df = pd.read_csv(mop_file, usecols=['VALUE'])
    existing_modes = set(existing_df['VALUE'].astype(str))
    new_modes = set(map(str, ms.AgrivoltaicModes.values()))
    missing_modes = new_modes - existing_modes

    if missing_modes:
        utils.print_update(level=print_level_base + 2,
                           message=f"Adding {len(missing_modes)} new agrivoltaic mode(s) to {mop_file}")
        updated_df = pd.concat(
            [existing_df, pd.DataFrame({'VALUE': sorted(missing_modes)})],
            ignore_index=True
        )
        updated_df.to_csv(mop_file, index=False)
    else:
        utils.print_update(level=print_level_base + 2, message="No new agrivoltaic modes to add.")

    existing_lines = mode_list_file.read_text() if mode_list_file.exists() else ''
    with open(mode_list_file, 'a') as f:
        for crop_code, mode in sorted(ms.AgrivoltaicModes.items(), key=lambda x: x[1]):
            mode_prefix = f"{mode}:"
            if mode_prefix in existing_lines:
                continue
            label = ms.NamingConvention.get(crop_code, crop_code)
            f.write(f"{mode}: Agrivoltaic {label}\n")


# 4.  Save results

def _append_agrivoltaic_to_csvs(SetNames, NewSetItems, IARList, OARList,
                                 csv_save_to, agv_sets):
    """
    Appends only agrivoltaic TECHNOLOGY, FUEL and IAR/OAR rows to existing CSVs.
    Does NOT overwrite — only adds rows not already present.
    Runs a final dedup pass on both ratio files.
    """
    csv_save_to = Path(csv_save_to)

    # Append agrivoltaic TECHNOLOGY and FUEL to their SET CSVs
    for set_name, agv_set in agv_sets.items():
        set_file = csv_save_to / f'{set_name}.csv'
        existing_df = pd.read_csv(set_file)
        existing_values = set(existing_df['VALUE'].astype(str))
        new_rows = [{'VALUE': k} for k in agv_set.keys() if k not in existing_values]
        if new_rows:
            updated_df = pd.concat([existing_df, pd.DataFrame(new_rows)], ignore_index=True)
            updated_df.to_csv(set_file, index=False)
            utils.print_update(level=print_level_base + 1,
                               message=f"Added {len(new_rows)} rows to {set_name}.csv")

    # Collect all agrivoltaic tech codes for filtering
    agv_techs = set(agv_sets.get('TECHNOLOGY', {}).keys())

    # Append agrivoltaic IAR rows
    iar_file = csv_save_to / 'InputActivityRatio.csv'
    existing_iar = pd.read_csv(iar_file)
    existing_iar_keys = set(zip(
        existing_iar['REGION'], existing_iar['TECHNOLOGY'], existing_iar['FUEL'],
        existing_iar['MODE_OF_OPERATION'].astype(int), existing_iar['YEAR'].astype(int)
    ))
    new_iar_rows = [
        {'REGION': i['c'][0], 'TECHNOLOGY': i['c'][1], 'FUEL': i['c'][2],
         'MODE_OF_OPERATION': i['c'][3], 'YEAR': i['c'][4], 'VALUE': i['v']}
        for i in IARList
        if i['c'][1] in agv_techs
        and (i['c'][0], i['c'][1], i['c'][2], int(i['c'][3]), int(i['c'][4])) not in existing_iar_keys
    ]
    if new_iar_rows:
        updated_iar = pd.concat([existing_iar, pd.DataFrame(new_iar_rows)], ignore_index=True)
        updated_iar.to_csv(iar_file, index=False)
        utils.print_update(level=print_level_base + 1,
                           message=f"Added {len(new_iar_rows)} agrivoltaic IAR rows.")

    # Append agrivoltaic OAR rows
    oar_file = csv_save_to / 'OutputActivityRatio.csv'
    existing_oar = pd.read_csv(oar_file)
    existing_oar_keys = set(zip(
        existing_oar['REGION'], existing_oar['TECHNOLOGY'], existing_oar['FUEL'],
        existing_oar['MODE_OF_OPERATION'].astype(int), existing_oar['YEAR'].astype(int)
    ))
    new_oar_rows = [
        {'REGION': o['c'][0], 'TECHNOLOGY': o['c'][1], 'FUEL': o['c'][2],
         'MODE_OF_OPERATION': o['c'][3], 'YEAR': o['c'][4], 'VALUE': o['v']}
        for o in OARList
        if o['c'][1] in agv_techs
        and (o['c'][0], o['c'][1], o['c'][2], int(o['c'][3]), int(o['c'][4])) not in existing_oar_keys
    ]
    if new_oar_rows:
        updated_oar = pd.concat([existing_oar, pd.DataFrame(new_oar_rows)], ignore_index=True)
        updated_oar.to_csv(oar_file, index=False)
        utils.print_update(level=print_level_base + 1,
                           message=f"Added {len(new_oar_rows)} agrivoltaic OAR rows.")

    # Final dedup pass
    dedup_cols = ['REGION', 'TECHNOLOGY', 'FUEL', 'MODE_OF_OPERATION', 'YEAR']
    for ratio_file in (iar_file, oar_file):
        df = pd.read_csv(ratio_file)
        before = len(df)
        df = df.drop_duplicates(subset=dedup_cols, keep='first')
        after = len(df)
        if before != after:
            df.to_csv(ratio_file, index=False)
            utils.print_update(level=print_level_base + 1,
                               message=f"Removed {before - after} duplicate rows from {ratio_file.name}")


# 5.  Dedup helper

def _dedup(lst: list) -> list:
    seen = set()
    out = []
    for item in lst:
        k = tuple(item['c'])
        if k not in seen:
            seen.add(k)
            out.append(item)
    return out


# 6.  Main entry point

def main(csv_save_to: str | Path = 'data/clews_data/SETs',
         SetNames: list = None,
         NewSetItems: list = None,
         IARList: list = None,
         OARList: list = None) -> None:
    """
    Build the agrivoltaic SET/Ratio CSV extensions.

    Steps
    -----
    1. Use pre-built sets if provided, otherwise call SnR.build()
    2. Generate agrivoltaic TECHNOLOGY and FUEL identifiers
    3. Append agrivoltaic sets to existing set-item lists
    4. Append agrivoltaic IAR / OAR entries
    5. Dedup both lists
    6. Write to CSVs (agrivoltaic rows only, no overwrite of base rows)
    7. Patch MODE_OF_OPERATION.csv and ModeList.txt
    """
    csv_save_to = Path(csv_save_to)

    # Step 1 — base build
    if SetNames is None or NewSetItems is None or IARList is None or OARList is None:
        SetNames, NewSetItems, IARList, OARList = SnR.build(csv_save_to)

    agr_mode_count = len(
        NewSetItems[SetNames.index('MODE_OF_OPERATION')]
    ) if 'MODE_OF_OPERATION' in SetNames else 0

    # Step 2 — agrivoltaic identifiers
    agv_sets = get_Agrivoltaic_SETs()

    # Step 3 — append to SET lists
    NewSetItems = update_SetItems_with_Agrivoltaic(SetNames, NewSetItems, agv_sets)

    # Step 4 — append IAR / OAR
    IARList, OARList = update_IARlist(
        IARList_existing=IARList,
        OARList_existing=OARList,
        agv_sets=agv_sets,
        agr_mode_count=agr_mode_count,
    )

    # Step 5 — dedup
    IARList = _dedup(IARList)
    OARList = _dedup(OARList)

    # Step 6 — write CSVs
    _append_agrivoltaic_to_csvs(
        SetNames=SetNames,
        NewSetItems=NewSetItems,
        IARList=IARList,
        OARList=OARList,
        csv_save_to=csv_save_to,
        agv_sets=agv_sets,
    )

    # Step 7 — MODE_OF_OPERATION patch
    update_mode_of_operation_csv(csv_save_to)

    utils.print_update(level=print_level_base,
                       message="✅ Agrivoltaic build complete.")


if __name__ == '__main__':
    main()