"""
agrivoltaic.py
Adds agrivoltaic (AGV) modes of operation to existing LNDAGR cluster
technologies so that solar panel co-production competes for the same
land pool as conventional agriculture inside the LP optimizer.

Design follows the livestock.py pattern: receives the base build
outputs from sets_n_ratios.BuildCLEWsModel(), appends AGV mode
labels and IAR/OAR rows, and returns the updated lists for
downstream consumers (livestock, UpdateSETS).

Author:  Yoselyn (YOS), 2025
"""

import os
import decimal
from pathlib import Path

from bcnexus import utils
from bcnexus.clews import model_structure as clews_const

# ---------------------------------------------------------------------------
# AGV configuration  (centralised here; importable by other modules)
# ---------------------------------------------------------------------------

# Crops eligible for agrivoltaic deployment and their yield retention
# factors (fraction of conventional yield kept under partial shading).
AGV_ELIGIBLE_CROPS: dict = {
    'MAI': 0.92,   # Barron-Gafford et al. 2019, Marrou et al. 2013
    'WHE': 0.95,   # Weselek et al. 2019
    'PTW': 0.88,   # Schindele et al. 2020 (flagged uncertain)
}

# Electricity co-product output [PJ / (1000 km^2 / yr)].
# Derived as: solar_input (4470) * panel_efficiency (0.018) * shade_factor (0.70)
AGV_ELECTRICITY_OAR: float = 1

# Fuel code for the electricity output.  Must already exist in the FUEL set.
# Uses ELCB01 (electricity from power plants) so that AGV output enters the
# grid at the same node as utility-scale solar.
AGV_ELECTRICITY_FUEL: str = 'ELCB01'

PRINT_LEVEL: int = 2


# ---------------------------------------------------------------------------
# Cluster data loader  (mirrors the loading logic inside BuildCLEWsModel)
# ---------------------------------------------------------------------------

def _load_cluster_data() -> dict:
    """
    Read the four GeoCLEWs cluster CSV files for every land region
    and return them in a dict keyed by region code.

    Returns a dict of the form::

        {
          'BC1': {
              'Clusters':                     [header_line, data_line, ...],
              'PrecipitationClusters':        [...],
              'EvapotranspirationClusters':   [...],
              'IrrigationWaterDeficitClusters': [...]
          },
          ...
        }
    """
    lcd = clews_const.LandCluster_data
    root = lcd['root']
    result = {}

    for region in clews_const.LandRegions:
        cluster_file = os.path.join(
            root, lcd['ClusterBaseFileName'] + region + '.csv')
        precip_file = os.path.join(
            root, lcd['PrecipitationClusterBaseFileName'] + region + '.csv')
        evt_file = os.path.join(
            root, lcd['EvapotranspirationClusterBaseFileName'] + region + '.csv')
        cwd_file = os.path.join(
            root, lcd['IrrigationWaterDeficitClusterBaseFileName'] + region + '.csv')

        result[region] = {
            'Clusters': open(cluster_file, 'r').readlines(),
            'PrecipitationClusters': open(precip_file, 'r').readlines(),
            'EvapotranspirationClusters': open(evt_file, 'r').readlines(),
            'IrrigationWaterDeficitClusters': open(cwd_file, 'r').readlines(),
        }

    return result


# ---------------------------------------------------------------------------
# Mode mapping builder
# ---------------------------------------------------------------------------

def _build_parent_mode_lookup(ModeList: list) -> dict:
    """
    Scan ModeList for crop combinations that match AGV-eligible crops
    and return a lookup dict.

    Returns::

        {
          'MAI': [('MAIHI', 0), ('MAIII', 1), ('MAIHR', 2), ...],
          'WHE': [...],
          'PTW': [...]
        }

    The integer is the 0-based index in ModeList (mode number = index + 1).
    """
    lookup: dict = {}
    for idx, combo in enumerate(ModeList):
        if len(combo) < 3:
            continue
        crop_prefix = combo[:-2]          # 'MAIHI' -> 'MAI'
        if crop_prefix in AGV_ELIGIBLE_CROPS:
            lookup.setdefault(crop_prefix, []).append((combo, idx))
    return lookup


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def build_agrivoltaic_modes(
    SetNames: list,
    NewSetItems: list,
    IARList: list,
    OARList: list,
    ModeList: list,
) -> tuple:
    """
    Append agrivoltaic modes to the LNDAGR cluster technologies.

    For each eligible crop-intensity-irrigation combination, a new mode
    is added to every LNDAGR cluster technology.  The new mode:

    * Consumes the same land commodity as the parent mode (IAR = 1).
    * Consumes the same precipitation and irrigation water.
    * Produces the same crop fuel but at a reduced OAR (yield factor).
    * Produces ELCB01 electricity as a co-product (the novel output).
    * Produces the same evapotranspiration, groundwater, runoff OARs.

    Parameters
    ----------
    SetNames, NewSetItems, IARList, OARList, ModeList
        The base build outputs from sets_n_ratios.BuildCLEWsModel().

    Returns
    -------
    tuple
        (SetNames, NewSetItems, IARList, OARList, ModeList) with AGV
        modes appended.  The caller can pass these directly to
        livestock.main() or sets_n_ratios.UpdateSETS().
    """
    from bcnexus.clews.sets_n_ratios import AddActivityListItems, Fill_Set
    utils.print_banner("Building Agrivoltaic Modes")

    # Decimal context matching sets_n_ratios (2 significant figures)
    ctx = decimal.Context()
    ctx.prec = 4

    # Reference data from model_structure
    IrrigationTypeList = clews_const.IrrigationTypeList
    IntensityList = clews_const.IntensityList
    CropYieldFactors = clews_const.CropYieldFactors
    GroundwaterPercentofExcess = clews_const.GroundwaterPercentofExcess
    LandRegions = clews_const.LandRegions
    Regions = clews_const.Regions
    snapshot = clews_const.snapshot
    Years = list(range(snapshot['start'], snapshot['end'] + 1))
    Region = next(iter(Regions))          # 'REGION1'

    # Load cluster data independently (avoids modifying sets_n_ratios)
    cluster_data = _load_cluster_data()

    # Build the lookup from crop code to parent mode indices
    parent_lookup = _build_parent_mode_lookup(ModeList)

    if not parent_lookup:
        utils.print_warning("No AGV-eligible crop modes found in ModeList. "
                            "Skipping agrivoltaic module.")
        return SetNames, NewSetItems, IARList, OARList, ModeList

    # ------------------------------------------------------------------
    # Step 1:  Append AGV mode labels to ModeList and record the mapping
    # ------------------------------------------------------------------
    #
    # agv_modes is a list of dicts, one per new mode:
    #   { 'agv_mode':  <1-based mode number>,
    #     'parent_mode': <1-based mode number of conventional counterpart>,
    #     'label':      'AGVMAIHI',
    #     'parent_label': 'MAIHI',
    #     'crop':       'MAI',
    #     'yield_factor': 0.92 }

    agv_modes: list = []

    for crop in AGV_ELIGIBLE_CROPS:
        if crop not in parent_lookup:
            continue
        yield_factor = AGV_ELIGIBLE_CROPS[crop]

        for (parent_combo, parent_idx) in parent_lookup[crop]:
            agv_label = "AGV" + parent_combo      # e.g. 'AGVMAIHI'
            ModeList.append(agv_label)
            new_mode = len(ModeList)               # 1-based

            agv_modes.append({
                'agv_mode': new_mode,
                'parent_mode': parent_idx + 1,
                'label': agv_label,
                'parent_label': parent_combo,
                'crop': crop,
                'yield_factor': yield_factor,
            })

    utils.print_update(level=PRINT_LEVEL,
        message=f"Created {len(agv_modes)} AGV mode labels "
                f"(crops: {list(AGV_ELIGIBLE_CROPS.keys())})")

    # ------------------------------------------------------------------
    # Step 2:  Write IAR / OAR rows for every AGV mode on every cluster
    # ------------------------------------------------------------------

    rows_written = 0

    for region_code in LandRegions:
        rd = cluster_data[region_code]
        Clusters = rd['Clusters']
        PrecipitationClusters = rd['PrecipitationClusters']
        EvapotranspirationClusters = rd['EvapotranspirationClusters']
        IrrigationWaterDeficitClusters = rd['IrrigationWaterDeficitClusters']

        # Header row of the main cluster file gives column labels
        header_cols = Clusters[0].strip().split(',')

        for clustercount in range(1, len(Clusters)):
            cluster_id = Clusters[clustercount].split(',')[0].zfill(2)
            tech = "LNDAGR" + region_code + "C" + cluster_id

            for info in agv_modes:
                mode_str = str(info['agv_mode'])
                parent_combo = info['parent_label']
                crop = info['crop']
                yf = info['yield_factor']
                suffix = parent_combo[-2:]       # e.g. 'HI'
                intensity_code = suffix[0]       # H, I, or L
                irrig_code = suffix[1]           # I or R

                # Build the label used to index into the cluster CSV
                # columns, e.g. "MAI Irrigation High"
                irrig_name = IrrigationTypeList[irrig_code]
                intens_name = IntensityList[intensity_code]
                combo_label = crop + " " + irrig_name + " " + intens_name

                # Check that this crop combination exists in this cluster
                if combo_label not in header_cols:
                    continue
                col_idx = header_cols.index(combo_label)
                conv_yield_raw = float(
                    Clusters[clustercount].split(',')[col_idx])
                if conv_yield_raw == 0.0:
                    continue                     # crop does not grow here

                # ---------- IARs (identical to parent mode) ----------

                # Land commodity
                AddActivityListItems(
                    Years, Region, tech,
                    "L" + parent_combo + region_code,
                    IARList, value="1", g=mode_str)

                # Precipitation
                precip_val = float(
                    PrecipitationClusters[clustercount].split(',')[1])
                precip_str = format(
                    ctx.create_decimal(repr(precip_val)), 'f')
                AddActivityListItems(
                    Years, Region, tech,
                    "WTRPRC" + region_code,
                    IARList, g=mode_str, v=precip_str)

                # Irrigation water
                cwd_header = (IrrigationWaterDeficitClusters[0]
                              .strip().split(','))
                cwd_col = cwd_header.index(combo_label)
                irrig_val = float(
                    IrrigationWaterDeficitClusters[clustercount]
                    .split(',')[cwd_col])
                if irrig_name == 'Rain-fed':
                    irrig_val = 0.0
                irrig_str = format(
                    ctx.create_decimal(repr(irrig_val)), 'f')
                AddActivityListItems(
                    Years, Region, tech,
                    "AGRWAT" + region_code,
                    IARList, g=mode_str, v=irrig_str)

                # ---------- OARs (modified for AGV) ----------

                # Crop commodity (reduced by yield factor)
                agv_yield = (conv_yield_raw
                             * CropYieldFactors.get(crop, 1.0)
                             * yf)
                agv_yield_str = format(
                    ctx.create_decimal(repr(agv_yield)), 'f')
                AddActivityListItems(
                    Years, Region, tech,
                    "CRP" + crop,
                    OARList, g=mode_str, v=agv_yield_str)

                # Electricity co-product (the novel AGV output)
                elec_str = format(
                    ctx.create_decimal(repr(AGV_ELECTRICITY_OAR)), 'f')
                AddActivityListItems(
                    Years, Region, tech,
                    AGV_ELECTRICITY_FUEL,
                    OARList, g=mode_str, v=elec_str)

                # Evapotranspiration
                evt_header = (EvapotranspirationClusters[0]
                              .strip().split(','))
                evt_col = evt_header.index(combo_label)
                evt_val = float(
                    EvapotranspirationClusters[clustercount]
                    .split(',')[evt_col])
                evt_str = format(
                    ctx.create_decimal(repr(evt_val)), 'f')
                AddActivityListItems(
                    Years, Region, tech,
                    "WTREVT" + region_code,
                    OARList, g=mode_str, v=evt_str)

                # Groundwater
                gw_val = ((precip_val + irrig_val - evt_val)
                          * GroundwaterPercentofExcess)
                gw_str = format(
                    ctx.create_decimal(repr(gw_val)), 'f')
                AddActivityListItems(
                    Years, Region, tech,
                    "WTRGRC" + region_code,
                    OARList, g=mode_str, v=gw_str)

                # Surface runoff
                ro_val = ((precip_val + irrig_val - evt_val)
                          * (1 - GroundwaterPercentofExcess))
                ro_str = format(
                    ctx.create_decimal(repr(ro_val)), 'f')
                AddActivityListItems(
                    Years, Region, tech,
                    "WTRSUR" + region_code,
                    OARList, g=mode_str, v=ro_str)

                rows_written += 1

    utils.print_update(level=PRINT_LEVEL,
        message=f"Wrote IAR/OAR rows for {rows_written} "
                f"AGV mode-cluster combinations")

    # ------------------------------------------------------------------
    # Step 3:  Register AGV mode numbers in MODE_OF_OPERATION set
    # ------------------------------------------------------------------
    # The MODE_OF_OPERATION set is created at the end of BuildCLEWsModel
    # by iterating ModeList.  Since we appended to ModeList before that
    # set is finalised (when called from the right point in the pipeline),
    # the modes will be picked up automatically.
    #
    # If this module runs after UpdateSETS has already written MODE_OF_OPERATION,
    # we need to add the entries here:
    if "MODE_OF_OPERATION" in SetNames:
        for info in agv_modes:
            Fill_Set(NewSetItems, SetNames, "MODE_OF_OPERATION",
                     str(info['agv_mode']), "#000000", info['label'])

    return SetNames, NewSetItems, IARList, OARList, ModeList


# ---------------------------------------------------------------------------
# Convenience main() following the livestock.py calling convention
# ---------------------------------------------------------------------------

def main(SetNames: list,
         NewSetItems: list,
         IARList: list,
         OARList: list,
         ModeList: list,
         csv_save_to: str | Path = None,
) -> tuple:
    """
    Entry point matching the livestock.py pattern.

    Parameters
    ----------
    SetNames, NewSetItems, IARList, OARList, ModeList
        Base build outputs.
    csv_save_to
        If provided, writes updated SETs to this directory immediately.
        If None, just returns the updated lists (caller writes later).

    Returns
    -------
    tuple of (SetNames, NewSetItems, IARList, OARList, ModeList)
    """
    result = build_agrivoltaic_modes(
        SetNames, NewSetItems, IARList, OARList, ModeList)

    if csv_save_to is not None:
        from bcnexus.clews.sets_n_ratios import UpdateSETS
        UpdateSETS(result[0], result[1], result[2], result[3],
                   Path(csv_save_to))

    return result


# ---------------------------------------------------------------------------
# Verification utility
# ---------------------------------------------------------------------------

def verify_agv_modes(iar_csv: str | Path, oar_csv: str | Path) -> None:
    """
    Read compiled IAR and OAR CSVs and print a summary of AGV mode
    rows for manual verification.

    Call after a full build to confirm that:
    * Every eligible crop has AGV modes on every cluster where the
      crop appears.
    * Crop OAR = conventional OAR x yield factor.
    * ELCB01 OAR = AGV_ELECTRICITY_OAR for every AGV mode-cluster pair.
    """
    import pandas as pd

    iar = pd.read_csv(iar_csv)
    oar = pd.read_csv(oar_csv)

    # AGV modes are identified by MODE_OF_OPERATION numbers that
    # exceed the conventional + non-agricultural count.
    # We detect them by checking ModeList labels, but here we look
    # for ELCB01 OAR on LNDAGR technologies as the marker.
    agv_elec = oar[
        (oar['TECHNOLOGY'].str.startswith('LNDAGR')) &
        (oar['FUEL'] == AGV_ELECTRICITY_FUEL)
    ]

    if agv_elec.empty:
        utils.print_warning("No AGV electricity OAR rows found in "
                            f"{oar_csv}.  AGV modes may not have been built.")
        return

    # Group by technology and mode
    summary = (agv_elec
               .groupby(['TECHNOLOGY', 'MODE_OF_OPERATION'])
               .agg(elec_oar=('VALUE', 'first'),
                    years=('YEAR', 'count'))
               .reset_index())

    utils.print_banner("AGV mode verification")
    print(f"  AGV electricity rows found: {len(agv_elec)}")
    print(f"  Unique tech-mode combos:    {len(summary)}")
    print(f"  Technologies covered:       "
          f"{summary['TECHNOLOGY'].nunique()}")
    print(f"  Expected ELCB01 OAR:        {AGV_ELECTRICITY_OAR}")

    mismatched = summary[
        summary['elec_oar'].astype(float) != AGV_ELECTRICITY_OAR]
    if not mismatched.empty:
        utils.print_error("Mismatched electricity OAR values:")
        print(mismatched.to_string(index=False))
    else:
        utils.print_update(level=PRINT_LEVEL,
            message="All electricity OAR values match expected value.")

    # Check crop OAR reduction
    for crop, yf in AGV_ELIGIBLE_CROPS.items():
        crop_fuel = "CRP" + crop
        agv_crop = oar[
            (oar['TECHNOLOGY'].str.startswith('LNDAGR')) &
            (oar['FUEL'] == crop_fuel) &
            (oar['MODE_OF_OPERATION'].isin(
                summary['MODE_OF_OPERATION'].unique()))
        ]
        conv_crop = oar[
            (oar['TECHNOLOGY'].str.startswith('LNDAGR')) &
            (oar['FUEL'] == crop_fuel) &
            (~oar['MODE_OF_OPERATION'].isin(
                summary['MODE_OF_OPERATION'].unique()))
        ]
        if not agv_crop.empty and not conv_crop.empty:
            print(f"\n  {crop} AGV yield check (sample, year "
                  f"{agv_crop['YEAR'].iloc[0]}):")
            print(f"    Conventional OAR range: "
                  f"{conv_crop['VALUE'].min():.4f} to "
                  f"{conv_crop['VALUE'].max():.4f}")
            print(f"    AGV OAR range:          "
                  f"{agv_crop['VALUE'].min():.4f} to "
                  f"{agv_crop['VALUE'].max():.4f}")
            print(f"    Expected ratio:         {yf}")


if __name__ == "__main__":
    # Standalone test: build base model then apply AGV modes
    from bcnexus.clews import sets_n_ratios as SnR

    SetNames, NewSetItems, IARList, OARList, ModeList = \
        SnR.BuildCLEWsModel()

    SetNames, NewSetItems, IARList, OARList, ModeList = \
        build_agrivoltaic_modes(
            SetNames, NewSetItems, IARList, OARList, ModeList)

    save_dir = Path('data/clews_data/SETs')
    SnR.UpdateSETS(SetNames, NewSetItems, IARList, OARList, save_dir)

    with open(save_dir / 'ModeList.txt', 'w') as f:
        for idx, mode in enumerate(ModeList, 1):
            f.write(f"{idx}: {mode}\n")

    print(f"\nModeList ({len(ModeList)} modes):")
    for idx, mode in enumerate(ModeList, 1):
        print(f"  {idx:3d}: {mode}")