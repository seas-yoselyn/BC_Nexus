"""
======================================================
Agrivoltaic Modelling
======================================================

"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

import pandas as pd

from bcnexus.clews import sets_n_ratios as SnR
from bcnexus.clews import model_structure
from bcnexus import utils

print_level_base = 2


# ==========================================================================
# GeoCLEWs Baseline
# ==========================================================================

_BASELINE_CACHE: dict[tuple[str, str], dict] = {}

DEFAULT_WS_INTENSITY: str = 'Rain-fed High'
DEFAULT_LANDCLUSTER_ROOT: Path = Path('data/clews_data/LandClusterData')


def get_geoclews_baselines(land_region: str,
                           landcluster_root: str | Path | None = None,
                           ws_intensity: str = DEFAULT_WS_INTENSITY,
                           refresh: bool = False) -> dict:

    cache_key = (land_region, ws_intensity)
    if not refresh and cache_key in _BASELINE_CACHE:
        return _BASELINE_CACHE[cache_key]

    root = Path(landcluster_root) if landcluster_root else DEFAULT_LANDCLUSTER_ROOT

    utils.print_update(
        level=print_level_base,
        message=f"Loading GeoCLEWs baselines for '{land_region}' "
                f"(ws_intensity='{ws_intensity}') from {root}"
    )

    baselines = _compute_geoclews_baselines(land_region, root, ws_intensity)
    _BASELINE_CACHE[cache_key] = baselines

    utils.print_update(
        level=print_level_base + 1,
        message=f"  PRC (BC-wide) = {baselines['precipitation']:.4f} m/yr "
                f"over {baselines['total_area']:.2f} k.sqkm, "
                f"{len(baselines['cluster_ids'])} clusters"
    )
    return baselines


def _compute_geoclews_baselines(land_region: str,
                                root: Path,
                                ws_intensity: str) -> dict:
    yld_df = pd.read_csv(root / f'clustering_results_{land_region}.csv')
    prc_df = pd.read_csv(root / f'clustering_results_prc_{land_region}.csv')
    evt_df = pd.read_csv(root / f'clustering_results_evt_{land_region}.csv')
    cwd_df = pd.read_csv(root / f'clustering_results_cwd_{land_region}.csv')

    yld_df = yld_df.merge(prc_df, on='cluster', how='left')

    cluster_ids = yld_df['cluster'].astype(int).tolist()
    cluster_areas = dict(zip(
        yld_df['cluster'].astype(int),
        yld_df['land_area_total'].astype(float)
    ))
    cluster_precipitation = dict(zip(
        yld_df['cluster'].astype(int),
        yld_df['precipitation'].astype(float)
    ))

    total_area = float(yld_df['land_area_total'].sum())
    precipitation_aw = float(
        (yld_df['land_area_total'] * yld_df['precipitation']).sum() / total_area
    )


    crops = sorted({
        col.split(' ')[0]
        for col in yld_df.columns
        if ' ' in col and any(tag in col for tag in ('Rain-fed', 'Irrigation'))
    })

    cluster_yield_per_crop: dict[str, dict[int, float]] = {}
    cluster_evt_per_crop:   dict[str, dict[int, float]] = {}
    cluster_cwd_per_crop:   dict[str, dict[int, float]] = {}
    suitable_clusters:      dict[str, list[int]]        = {}

    yield_aw: dict[str, float]     = {}
    evt_aw:   dict[str, float]     = {}
    cwd_aw:   dict[str, float]     = {}
    evt_ratio: dict[str, float]    = {}

    evt_idx = evt_df.set_index('cluster')
    cwd_idx = cwd_df.set_index('cluster')

    for crop in crops:
        col = f'{crop} {ws_intensity}'
        if col not in yld_df.columns:
            continue

        cluster_yield_per_crop[crop] = {}
        cluster_evt_per_crop[crop]   = {}
        cluster_cwd_per_crop[crop]   = {}

        for cid in cluster_ids:
            y = float(yld_df.loc[yld_df['cluster'] == cid, col].iloc[0])
            cluster_yield_per_crop[crop][cid] = y
            cluster_evt_per_crop[crop][cid]   = float(evt_idx.loc[cid, col]) \
                                                if col in evt_idx.columns else 0.0
            cluster_cwd_per_crop[crop][cid]   = float(cwd_idx.loc[cid, col]) \
                                                if col in cwd_idx.columns else 0.0

        eligible = [cid for cid in cluster_ids
                    if cluster_yield_per_crop[crop][cid] > 0]
        suitable_clusters[crop] = eligible

        if eligible:
            areas = pd.Series({cid: cluster_areas[cid] for cid in eligible})
            yvals = pd.Series({cid: cluster_yield_per_crop[crop][cid]
                                for cid in eligible})
            evals = pd.Series({cid: cluster_evt_per_crop[crop][cid]
                                for cid in eligible})
            cvals = pd.Series({cid: cluster_cwd_per_crop[crop][cid]
                                for cid in eligible})
            wsum = areas.sum()
            yield_aw[crop] = float((areas * yvals).sum() / wsum)
            evt_aw[crop]   = float((areas * evals).sum() / wsum)
            cwd_aw[crop]   = float((areas * cvals).sum() / wsum)
            evt_ratio[crop] = (
                evt_aw[crop] / precipitation_aw if precipitation_aw > 0 else float('nan')
            )
        else:
            yield_aw[crop]   = float('nan')
            evt_aw[crop]     = float('nan')
            cwd_aw[crop]     = float('nan')
            evt_ratio[crop]  = float('nan')

    return {
        'land_region':            land_region,
        'ws_intensity_used':      ws_intensity,
        'cluster_ids':            cluster_ids,
        'cluster_areas':          cluster_areas,
        'cluster_precipitation':  cluster_precipitation,
        'cluster_yield_per_crop': cluster_yield_per_crop,
        'cluster_evt_per_crop':   cluster_evt_per_crop,
        'cluster_cwd_per_crop':   cluster_cwd_per_crop,
        'suitable_clusters':      suitable_clusters,
        'precipitation':          precipitation_aw,
        'total_area':             total_area,
        'yield_per_crop':         yield_aw,
        'evt_per_crop':           evt_aw,
        'cwd_per_crop':           cwd_aw,
        'evt_ratio_per_crop':     evt_ratio,
    }


def clear_geoclews_cache() -> None:
    _BASELINE_CACHE.clear()


def baseline_summary(land_region: str,
                     crops: Iterable[str] | None = None,
                     **kwargs) -> str:
    """Diagnostic summary of derived baselines (BC-wide aggregates)."""
    b = get_geoclews_baselines(land_region, **kwargs)
    lines = [
        f"GeoCLEWs baselines for '{land_region}'",
        f"  ws_intensity:  {b['ws_intensity_used']}",
        f"  precipitation: {b['precipitation']:.4f}  m/yr   (BC-wide AW)",
        f"  total_area:    {b['total_area']:.2f}  k.sqkm",
        f"  clusters:      {b['cluster_ids']}",
        '',
        f"  {'Crop':<6}{'Yield':>10}{'ET':>10}{'CWD':>10}{'EvtRatio':>12}   Suitable clusters",
        f"  {'-'*60}",
    ]
    crop_iter = list(crops) if crops else sorted(b['yield_per_crop'].keys())
    for crop in crop_iter:
        y = b['yield_per_crop'].get(crop, float('nan'))
        e = b['evt_per_crop'].get(crop, float('nan'))
        c = b['cwd_per_crop'].get(crop, float('nan'))
        r = b['evt_ratio_per_crop'].get(crop, float('nan'))
        sc = b['suitable_clusters'].get(crop, [])
        lines.append(f"  {crop:<6}{y:>10.4f}{e:>10.4f}{c:>10.6f}{r:>12.4f}   {sc}")
    return '\n'.join(lines)


def cluster_summary(land_region: str,
                    crops: Iterable[str] | None = None,
                    **kwargs) -> str:
    """Per-cluster breakdown used for AGV mode generation."""
    b = get_geoclews_baselines(land_region, **kwargs)
    crop_iter = list(crops) if crops else sorted(b['cluster_yield_per_crop'].keys())

    lines = [
        f"GeoCLEWs per-cluster values for '{land_region}' ({b['ws_intensity_used']})",
        '',
        f"  {'Cluster':<8}{'Area':>8}{'PRC':>8}   crops & yields",
        f"  {'-'*55}",
    ]
    for cid in b['cluster_ids']:
        area = b['cluster_areas'][cid]
        prc  = b['cluster_precipitation'][cid]
        crops_here = []
        for crop in crop_iter:
            y = b['cluster_yield_per_crop'].get(crop, {}).get(cid, 0)
            if y > 0:
                crops_here.append(f"{crop}={y:.3f}")
        lines.append(f"  {cid:<8}{area:>8.2f}{prc:>8.3f}   {', '.join(crops_here)}")
    return '\n'.join(lines)



# ==========================================================================
# 2.  SETs
# ==========================================================================

def get_Agrivoltaic_SETs(ms=model_structure) -> dict:
    """One new LNDAGV{pathway}{land_region}C{cid:02d} technology per
    suitable (pathway, cluster). No new fuels — AGV reuses existing
    land, water, electricity, and commodity fuels."""
    techs = {}
    for land_region in ms.LandRegions:
        baselines = get_geoclews_baselines(land_region)
        for pathway, attrs in ms.AgrivoltaicPathways.items():
            crop = attrs['crop']
            for cid in baselines['suitable_clusters'].get(crop, []):
                name = f'LNDAGV{pathway}{land_region}C{cid:02d}'
                techs[name] = {
                    'description': (
                        f"Agrivoltaic {attrs['label']} in {land_region}, "
                        f"cluster {cid:02d}"
                    ),
                    'color': '#FFB300',
                }
    utils.print_update(
        level=print_level_base,
        message=f"Agrivoltaic SETs: {len(techs)} new technologies."
    )
    return {'TECHNOLOGY': techs, 'FUEL': {}}


def update_SetItems_with_Agrivoltaic(SetNames: list,
                                     NewSetItems: list,
                                     agv_sets: dict) -> list:
    idx = SetNames.index('TECHNOLOGY')
    existing = {item['value'] for item in NewSetItems[idx]}
    added = 0
    for name, attrs in agv_sets['TECHNOLOGY'].items():
        if name not in existing:
            NewSetItems[idx].append({
                'value': name,
                'name':  attrs['description'],
                'color': attrs.get('color', '#000000'),
            })
            added += 1
    utils.print_update(
        level=print_level_base + 1,
        message=f"Added {added} agrivoltaic technologies to TECHNOLOGY set."
    )
    return NewSetItems


# ==========================================================================
# 3.  Activity Ratios
# ==========================================================================

def update_IARlist(IARList_existing: list,
                   OARList_existing: list,
                   agv_sets: dict,
                   ms: object = model_structure) -> tuple:
    """Emit IAR/OAR rows for the new LNDAGV* technologies (single mode
    of operation = 1). Land is drawn directly from the raw land fuel
    L{land_region}, putting AGV in direct competition with the regular
    cluster ag techs (LNDAGR{land_region}C{cid:02d})."""

    new_techs = set(agv_sets['TECHNOLOGY'].keys())

    # Purge prior rows on the new tech names (idempotency for re-runs)
    IARList_existing = [r for r in IARList_existing if r['c'][1] not in new_techs]
    OARList_existing = [r for r in OARList_existing if r['c'][1] not in new_techs]

    IARList_new, OARList_new = [], []
    seen_iar, seen_oar = set(), set()

    shade_factor  = ms.AgrivoltaicShadeFactor
    gw_pct        = ms.GroundwaterPercentofExcess
    yield_factors = ms.AgrivoltaicCropYieldFactor
    solar_inputs  = ms.AgrivoltaicSolarInput
    elec_yields   = ms.AgrivoltaicElectricityYield

    for region in ms.Regions.keys():
        for land_region in ms.LandRegions:
            baselines = get_geoclews_baselines(land_region)
            grid_letter = ms.LandToGridMap[land_region]
            elec_fuel = f'ELC{grid_letter}01'

            raw_land_fuel = f'L{land_region}'
            prc_fuel = f'WTRPRC{land_region}'
            irr_fuel = f'AGRWAT{land_region}'
            evt_fuel = f'WTREVT{land_region}'
            grc_fuel = f'WTRGRC{land_region}'
            sur_fuel = f'WTRSUR{land_region}'

            for year in range(ms.snapshot['start'], ms.snapshot['end'] + 1):
                for pathway, attrs in ms.AgrivoltaicPathways.items():
                    crop = attrs['crop']
                    commodity_fuel = f'CRP{crop}'
                    yld_factor = yield_factors[crop]
                    solar_in   = solar_inputs[crop]
                    elec_yld   = elec_yields[crop]

                    suitable = baselines['suitable_clusters'].get(crop, [])
                    if not suitable:
                        continue

                    for cid in suitable:
                        tech = f'LNDAGV{pathway}{land_region}C{cid:02d}'

                        prc_v  = baselines['cluster_precipitation'][cid]
                        base_y = baselines['cluster_yield_per_crop'][crop][cid]
                        base_e = baselines['cluster_evt_per_crop'][crop][cid]
                        base_c = baselines['cluster_cwd_per_crop'][crop][cid]
                        if base_y <= 0:
                            continue

                        crop_y = base_y * yld_factor
                        evt_v  = base_e * shade_factor
                        irr_v  = base_c * shade_factor
                        excess = prc_v + irr_v - evt_v
                        grc_v  = excess * gw_pct
                        sur_v  = excess * (1 - gw_pct)

                        # IAR
                        _add(seen_iar, IARList_new, region, tech, raw_land_fuel, 1, year, 1)
                        _add(seen_iar, IARList_new, region, tech, prc_fuel,      1, year, prc_v)
                        _add(seen_iar, IARList_new, region, tech, irr_fuel,      1, year, irr_v)
                        _add(seen_iar, IARList_new, region, tech, 'SOL',         1, year, solar_in)

                        # OAR
                        _add(seen_oar, OARList_new, region, tech, commodity_fuel, 1, year, crop_y)
                        _add(seen_oar, OARList_new, region, tech, evt_fuel,       1, year, evt_v)
                        _add(seen_oar, OARList_new, region, tech, grc_fuel,       1, year, grc_v)
                        _add(seen_oar, OARList_new, region, tech, sur_fuel,       1, year, sur_v)
                        _add(seen_oar, OARList_new, region, tech, elec_fuel,      1, year, elec_yld)

    IARList_existing.extend(IARList_new)
    OARList_existing.extend(OARList_new)

    utils.print_update(
        level=print_level_base,
        message=f"Agrivoltaic Ratios updated: "
                f"{len(IARList_new)} IAR rows, {len(OARList_new)} OAR rows."
    )
    return IARList_existing, OARList_existing


def _add(seen, lst, region, tech, fuel, mode, year, value):
    key = (region, tech, fuel, mode, year)
    if key not in seen:
        lst.append({'c': list(key), 'v': value})
        seen.add(key)


def _purge_beta1_residue(csv_save_to: Path,
                        ms: object = model_structure) -> None:
    cluster_tech_pat = r'^LNDAGR[A-Z0-9]+C\d{2}$'

    for ratio_file in ('InputActivityRatio.csv', 'OutputActivityRatio.csv'):
        path = csv_save_to / ratio_file
        if not path.exists():
            continue
        df = pd.read_csv(path)
        tech = df['TECHNOLOGY'].astype(str)
        mode = df['MODE_OF_OPERATION'].astype(int)

        live_modes = set(mode[~tech.str.match(cluster_tech_pat)].tolist())
        cluster_mode_counts = (
            mode[tech.str.match(cluster_tech_pat)]
            .value_counts()
        )
        cluster_only_modes = set(cluster_mode_counts.index) - live_modes
        if not cluster_only_modes:
            continue

        mop_path = csv_save_to / 'MODE_OF_OPERATION.csv'
        if mop_path.exists():
            current_modes = set(pd.read_csv(mop_path)['VALUE'].astype(int))
            cluster_only_modes &= current_modes  # only purge ones that exist

        before = len(df)
        df = df[~((tech.str.match(cluster_tech_pat)) &
                  (mode.isin(cluster_only_modes)))]
        after = len(df)
        if before != after:
            df.to_csv(path, index=False)
            utils.print_update(
                level=print_level_base + 1,
                message=f"Purged {before - after} β-1 residue rows "
                        f"from {ratio_file} (modes {sorted(cluster_only_modes)})"
            )


# ==========================================================================
# 5.  Dedup
# ==========================================================================

def _dedup(lst: list) -> list:
    seen = set()
    out  = []
    for item in lst:
        k = tuple(item['c'])
        if k not in seen:
            seen.add(k)
            out.append(item)
    return out


# ==========================================================================
# 6.  Save IAR/OAR rows and parameters to CSV
# ==========================================================================

def _append_agrivoltaic_to_csvs(IARList: list,
                                OARList: list,
                                csv_save_to: Path,
                                agv_sets: dict) -> None:
    csv_save_to = Path(csv_save_to)
    new_techs = set(agv_sets['TECHNOLOGY'].keys())

    # Update TECHNOLOGY.csv
    tech_file = csv_save_to / 'TECHNOLOGY.csv'
    if tech_file.exists():
        df = pd.read_csv(tech_file)
        existing = set(df['VALUE'].astype(str))
        missing = sorted(new_techs - existing)
        if missing:
            df = pd.concat(
                [df, pd.DataFrame({'VALUE': missing})], ignore_index=True
            )
            df.to_csv(tech_file, index=False)
            utils.print_update(
                level=print_level_base + 1,
                message=f"Added {len(missing)} AGV techs to TECHNOLOGY.csv"
            )

    # Append IAR rows
    iar_file = csv_save_to / 'InputActivityRatio.csv'
    _append_ratio_rows(iar_file, IARList, new_techs, 'IAR')

    # Append OAR rows
    oar_file = csv_save_to / 'OutputActivityRatio.csv'
    _append_ratio_rows(oar_file, OARList, new_techs, 'OAR')


def _append_ratio_rows(path: Path, rows_list: list, new_techs: set, label: str) -> None:
    df = pd.read_csv(path)
    df = df[~df['TECHNOLOGY'].astype(str).isin(new_techs)]   # idempotent
    new_rows = [
        {'REGION': r['c'][0], 'TECHNOLOGY': r['c'][1], 'FUEL': r['c'][2],
         'MODE_OF_OPERATION': r['c'][3], 'YEAR': r['c'][4], 'VALUE': r['v']}
        for r in rows_list if r['c'][1] in new_techs
    ]
    if new_rows:
        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
        df = df.drop_duplicates(
            subset=['REGION', 'TECHNOLOGY', 'FUEL', 'MODE_OF_OPERATION', 'YEAR'],
            keep='last'
        )
        df.to_csv(path, index=False)
        utils.print_update(
            level=print_level_base + 1,
            message=f"Appended {len(new_rows)} agrivoltaic {label} rows."
        )


def update_parameters_csv(csv_save_to: Path,
                          agv_sets: dict,
                          ms=model_structure) -> None:
    """Write TotalAnnualMaxCapacity for AGV (cluster physical area).
    OperationalLife, CapitalCost, ResidualCapacity, and
    CapacityToActivityUnit are all managed by hand in csv_template/."""
    region = list(ms.Regions.keys())[0]
    years  = list(range(ms.snapshot['start'], ms.snapshot['end'] + 1))

    # TotalAnnualMaxCapacity = cluster physical area (1000 km^2)
    rows = []
    for land_region in ms.LandRegions:
        baselines = get_geoclews_baselines(land_region)
        for pathway, attrs in ms.AgrivoltaicPathways.items():
            crop = attrs['crop']
            for cid in baselines['suitable_clusters'].get(crop, []):
                tech = f'LNDAGV{pathway}{land_region}C{cid:02d}'
                area = baselines['cluster_areas'][cid]
                rows.extend({'REGION': region, 'TECHNOLOGY': tech,
                             'YEAR': y, 'VALUE': area} for y in years)
    _append_param_rows(
        csv_save_to / 'TotalAnnualMaxCapacity.csv',
        cols=['REGION', 'TECHNOLOGY', 'YEAR', 'VALUE'],
        rows=rows,
        key_cols=['REGION', 'TECHNOLOGY', 'YEAR'],
    )


def _append_param_rows(path: Path, cols: list, rows: list, key_cols: list) -> None:
    df = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=cols)
    new = pd.DataFrame(rows, columns=cols)
    df = pd.concat([df, new], ignore_index=True)
    df = df.drop_duplicates(subset=key_cols, keep='last')
    df.to_csv(path, index=False)
    utils.print_update(
        level=print_level_base + 1,
        message=f"Updated {path.name} with {len(new)} AGV rows."
    )

# ==========================================================================
# 7.  Writing entry point
# ==========================================================================

def main(csv_save_to: str | Path = 'data/clews_data/SETs',
         SetNames: list = None,
         NewSetItems: list = None,
         IARList: list = None,
         OARList: list = None) -> None:
    """Build agrivoltaics under Option α (standalone technology per
    pathway × cluster, single mode of operation, OperationalLife and
    CapitalCost managed manually in csv_template/)."""
    csv_save_to = Path(csv_save_to)

    if any(x is None for x in (SetNames, NewSetItems, IARList, OARList)):
        SetNames, NewSetItems, IARList, OARList = SnR.build(csv_save_to)

    agv_sets = get_Agrivoltaic_SETs()
    NewSetItems = update_SetItems_with_Agrivoltaic(SetNames, NewSetItems, agv_sets)
    IARList, OARList = update_IARlist(IARList, OARList, agv_sets)
    IARList = _dedup(IARList)
    OARList = _dedup(OARList)

    _append_agrivoltaic_to_csvs(IARList, OARList, csv_save_to, agv_sets)
    update_parameters_csv(csv_save_to, agv_sets)

    utils.print_update(
        level=print_level_base,
        message="Agrivoltaic (Option α, standalone tech with manual "
                "OperationalLife) build complete."
    )


if __name__ == '__main__':
    main()