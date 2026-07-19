import sys
from pathlib import Path

import pandas as pd

from bcnexus import utils
from bcnexus.clews.datapackage import GetDataPackage
from bcnexus.vis import plot_Climate, plot_Energy, plot_Land, plot_Water


def _safe(plot_fn, *dfs, **kwargs):
    """Call a plot function only if all required DataFrames are present;
    return None (skipped, logged) otherwise so one missing CSV never
    aborts the whole plot run."""
    if any(d is None for d in dfs):
        utils.print_update(level=print_level_base+1,
            message=f"skipped {plot_fn.__name__}: missing input dataframe(s)")
        return None
    try:
        return plot_fn(*dfs, **kwargs)
    except Exception as e:
        utils.print_update(level=print_level_base+1,
            message=f"skipped {plot_fn.__name__}: {e}")
        return None

print_level_base=1
def save_plots(nexus_plots:dict,
               plots_save_to:str|Path):
    
    for plot_genre in nexus_plots:
        for plot_name in nexus_plots[plot_genre]:
            plot = nexus_plots[plot_genre][plot_name]
            if plot is not None:
                if hasattr(plot, 'write_html'):
                    plot_file_path = plots_save_to / f'Nexus_{plot_name}.html'
                    plot.write_html(plot_file_path)
                    utils.print_update(level=print_level_base+1, message=f"Plotly Html file saved @ {plot_file_path}")
                elif hasattr(plot, 'write_image'):
                    plot_file_path = plots_save_to / f'Nexus_{plot_name}.png'
                    plot.write_image(plot_file_path)
                    utils.print_update(level=print_level_base+1, message=f"Plotly Image file saved @ {plot_file_path}")
                elif hasattr(plot, 'savefig'):  # Check if it's a matplotlib plot
                    plot_file_path = plots_save_to / f'Nexus_{plot_name}.png'
                    plot.savefig(plot_file_path, format='png')
                    utils.print_update(level=print_level_base+1, message=f"Matplotlib plot saved @ {plot_file_path}")
                else:
                    print(f"Plot {plot_name} is not a Plotly (HTML, PNG), or Matplotlib figure (PNG).")

def _get_scenario_info(scenario: str,
                       scenario_cfg_path: str | Path = 'config/scenarios_bcnexus.yaml',
                       dashboard_cfg_path: str | Path = 'config/dashboard.yaml') -> str:
    """Brief scenario description: SCENARIOS[<scenario>]['info'] (or 'remarks')
    from the scenario yaml; falls back to dashboard.yaml info_SCENARIOS."""
    import yaml
    try:
        cfg = yaml.safe_load(open(scenario_cfg_path, encoding='utf-8'))
        entry = (cfg.get('SCENARIOS') or {}).get(scenario) or {}
        for key in ('info', 'remarks', 'description'):
            if entry.get(key):
                return str(entry[key])
    except Exception:
        pass
    try:
        dcfg = yaml.safe_load(open(dashboard_cfg_path, encoding='utf-8'))
        for k, v in (dcfg.get('info_SCENARIOS') or {}).items():
            if scenario in k:
                return str(v)
    except Exception:
        pass
    return ""


from bcnexus.vis import report as _report

# re-exported for backward compatibility (definitions live in vis/report.py)
GITHUB_URL = _report.GITHUB_URL
SITE_URL = _report.SITE_URL
DELTAE_URL = _report.DELTAE_URL


def save_combined_html(nexus_plots: dict,
                       scenario: str,
                       save_to: str | Path,
                       scenario_info: str = "",
                       run_meta: str = "",
                       extra_info: str = "",
                       plotly_js: str = "inline",
                       layout: str = "2",
                       runlog=None,
                       constants=None,
                       sets=None,
                       constraints=None,
                       solver_meta=None,
                       gurobi_log=None,
                       **kwargs):
    """Write the combined tabbed CLEW report.

    Thin wrapper: markup/CSS/JS live in bcnexus/vis/templates/report_template.html
    and the rendering logic in bcnexus/vis/report.build_report() — edit the
    template for styling, this signature stays stable. Extra kwargs
    (github_url, site_url, deltae_url, logo_path, template) pass straight
    through to build_report().
    """
    path = _report.build_report(nexus_plots, scenario=scenario, save_to=save_to,
                                scenario_info=scenario_info, run_meta=run_meta,
                                extra_info=extra_info, plotly_js=plotly_js,
                                layout=layout, runlog=runlog,
                                constants=constants, sets=sets,
                                constraints=constraints, solver_meta=solver_meta,
                                gurobi_log=gurobi_log, **kwargs)
    utils.print_update(level=print_level_base+1,
                       message=f"Combined CLEW report saved @ {path}")
    return path


def get_plots(nexus_scenario:str='Base_CNZ',
         timeslices:int=24,
         storage_algorithm:str="Kotzur",
         solver:str="gurobi",
         results_csvs:Path=None,
         input_csvs:str|Path=None,
         plots_save_to:str|Path='vis',
         save_individual:bool=False,
         extra_info:str="",
         layout:str="2",
         runlog=None,
         constraints=None,
         gurobi_log=None,
         date_tag:str=None,
         auto_diagnostics:bool=True):
    """Build all CLEW plots and save the combined tabbed HTML report
    (CLEW_report_<scenario>_<ts>ts_<solver>.html).

    save_individual: False (default) -> combined report only.
                     True -> additionally write each plot as its own
                     Nexus_<name>.html file (the legacy behavior).
    extra_info: optional one-line note/disclaimer shown in the report header
                below the run signature; omitted if empty.
    layout: initial plot grid ("1", "2" or "3" columns); switchable in-report.
    runlog: OPTIONAL path to runtime_memory_log.txt (or dict). When provided,
            a run-diagnostics button appears beside the tabs with runtime,
            memory, start/end times, user and threads. Skipped when None.
    constraints: OPTIONAL path to constraints_summary.txt (or dict with
            'binding'/'non_binding'). When provided, a solver-diagnostics
            button appears beside it. Skipped when None.
    gurobi_log: OPTIONAL path to gurobi.log; solve stats join the solver panel.
    input_csvs: folder holding the model's INPUT csvs (sets + parameters).
            Needed for the Constants tab (set sizes) and the Inputs tab —
            the results folder contains result variables only, no SET files.
            When None, it is auto-discovered near the results path.
    date_tag: optional YYYY_MM_DD suffix for the report filename. When None it
            is inferred from the results path (the dated folder inside <N>ts).
    auto_diagnostics: when True (default) and the above are not given
            explicitly, look for runtime_memory_log.txt, constraints_summary.txt
            and gurobi.log in the results directory's PARENT (the run dir,
            e.g. .../32ts/) and use them if present. Set False to disable.
    """

    nexus_results_root=Path(results_csvs) if results_csvs else Path(f'results/clews/Model_{storage_algorithm}_{nexus_scenario}/{timeslices}ts_csvs_{solver}')
    # infer the dated folder (…/<N>ts/YYYY_MM_DD/result_csvs_x) for the filename
    if date_tag is None:
        import re as _re
        for _part in nexus_results_root.parts[::-1]:
            if _re.fullmatch(r'\d{4}_\d{2}_\d{2}', _part):
                date_tag = _part
                break

    result_pack=GetDataPackage(nexus_results_root)
    if result_pack is None:
        utils.print_update("no results found")
        sys.exit(1)
    
    # ---- diagnostics: search the results dir, its parent (run dir) and the
    #      scenario root, so both the new ({N}ts/result_csvs_x) and legacy
    #      ({N}ts_csvs_x_<runtag>) layouts are covered.
    def _find(*names):
        roots = [nexus_results_root,
                 nexus_results_root.parent,
                 nexus_results_root.parent.parent]
        for root in roots:
            for name in names:
                cand = root / name
                if cand.exists():
                    return cand
        # last resort: shallow recursive search under the scenario root
        for name in names:
            hits = sorted(nexus_results_root.parent.parent.rglob(name),
                          key=lambda f: f.stat().st_mtime, reverse=True)
            if hits:
                return hits[0]
        return None

    if auto_diagnostics:
        if runlog is None:
            runlog = _find('runtime_memory_log.txt')
        if constraints is None:
            constraints = _find('constraints_summary.txt')
        if gurobi_log is None:
            gurobi_log = _find(f'{solver}.log', 'gurobi.log', 'cbc.log')
        utils.print_update(level=print_level_base+1,
            message=(f"diagnostics -> runlog: {runlog or 'not found'} | "
                     f"constraints: {constraints or 'not found'} | "
                     f"solver log: {gurobi_log or 'not found'}"))

    plots_save_to=utils.ensure_path(plots_save_to)

    nexus_ts_plots={}
    plot_categories = ['Inputs', 'Climate', 'Land', 'Energy',
                       'Water', str(timeslices)]
    nexus_plots = {category: {} for category in plot_categories}
    nexus_plots[f'{timeslices}'] = nexus_ts_plots

    # ---- locate the INPUT csvs (sets live here, not in the results folder)
    def _find_input_dir():
        if input_csvs:
            return Path(input_csvs)
        # search upward from the results folder, then the usual build locations
        seeds = [nexus_results_root.parent.parent.parent,
                 Path('data/clews_data/clews_build_data'),
                 Path('data/clews_data')]
        for seed in seeds:
            try:
                hits = sorted(seed.rglob('TECHNOLOGY.csv'),
                              key=lambda f: f.stat().st_mtime, reverse=True)
            except Exception:
                hits = []
            for h in hits:
                # prefer a folder that also carries the demand file
                if (h.parent / 'AccumulatedAnnualDemand.csv').exists():
                    return h.parent
            if hits:
                return hits[0].parent
        return None

    _input_dir = _find_input_dir()
    utils.print_update(level=print_level_base+1,
        message=f"input csvs -> {_input_dir or 'not found (Constants/Inputs limited)'}")

    # ---- Constants: model configuration at a glance ----------------------
    _sets = {}
    if _input_dir is not None:
        for _s in ('TECHNOLOGY', 'FUEL', 'TIMESLICE', 'MODE_OF_OPERATION',
                   'YEAR', 'STORAGE', 'EMISSION', 'SEASON', 'DAYTYPE', 'REGION'):
            _f = Path(_input_dir) / f'{_s}.csv'
            if _f.exists():
                try:
                    _sets[_s.replace('_', ' ').title()] = len(pd.read_csv(_f))
                except Exception:
                    pass
    _years = result_pack.get_df('YEAR')
    if _years is None and _input_dir is not None and (Path(_input_dir)/'YEAR.csv').exists():
        _years = pd.read_csv(Path(_input_dir)/'YEAR.csv')
    _meta = {
        'Scenario': nexus_scenario,
        'Storage algorithm': storage_algorithm,
        'Timeslices': timeslices,
        'Solver': solver,
        'Horizon': (f"{int(_years.VALUE.min())}\u2013{int(_years.VALUE.max())}"
                    if _years is not None else '\u2014'),
        'Run tag': date_tag or '\u2014',
        'Input CSVs': str(_input_dir) if _input_dir else 'not found',
        'Results': str(nexus_results_root),
    }
    # constants travel to the report as a panel (small button), not a tab

    # ---- Inputs tab (all prescribed values) ------------------------------
    if _input_dir is not None:
        try:
            from bcnexus.vis import plot_Inputs as _pI
            nexus_plots['Inputs'] = _pI.build_input_plots(
                _input_dir, scenario=nexus_scenario)
            # reference energy system gets its own full-viewport page
            _map_fig = _safe(_pI.plot_model_structure, _input_dir,
                             scenario=nexus_scenario)
            if _map_fig is not None:
                _map_path = _report.save_model_map(
                    _map_fig,
                    Path(plots_save_to) /
                    (f'CLEW_model_map_{nexus_scenario}'
                     f'{"_" + date_tag if date_tag else ""}.html'),
                    scenario=nexus_scenario)
                utils.print_update(level=print_level_base+1,
                    message=f"Model map saved @ {_map_path}")
        except Exception as e:
            utils.print_update(level=print_level_base+1,
                message=f"Inputs tab skipped: {type(e).__name__}: {e}")

    nexus_climate_plots={}
    nexus_plots['Climate'] = nexus_climate_plots

    nexus_climate_plots['emission_total']=plot_Climate.get_total_annual_emission(result_pack.get_df('AnnualEmissions'), nexus_scenario)
    
    nexus_climate_plots['emission_by_source']=plot_Climate.get_emission_from_fuels(result_pack.get_df('AnnualTechnologyEmission'), nexus_scenario)
    nexus_climate_plots['emission_by_sector']=plot_Climate.get_emission_from_sector(result_pack.get_df('AnnualTechnologyEmission'), nexus_scenario)

    # shared dataframes for the new plot suites (load once, reuse)
    _em   = result_pack.get_df('AnnualEmissions')
    _tem  = result_pack.get_df('AnnualTechnologyEmission')
    _prod = result_pack.get_df('ProductionByTechnologyAnnual')
    _cap  = result_pack.get_df('TotalCapacityAnnual')
    _newc = result_pack.get_df('NewCapacity')
    _sl   = result_pack.get_df('StorageLevelYearStart')
    _use  = result_pack.get_df('UseByTechnology')
    _bymode = result_pack.get_df('TotalAnnualTechnologyActivityByMode')
    _final_year = int(_prod.YEAR.max()) if _prod is not None else None

    nexus_climate_plots['emission_cumulative'] = _safe(plot_Climate.plot_cumulative_emissions, _em, scenario=nexus_scenario)
    nexus_climate_plots['emission_net_vs_ccs'] = _safe(plot_Climate.plot_net_emissions_ccs, _tem, scenario=nexus_scenario)
    nexus_climate_plots['grid_carbon_intensity'] = _safe(plot_Climate.plot_electricity_carbon_intensity, _tem, _prod, scenario=nexus_scenario)
    nexus_climate_plots['sector_emission_intensity'] = _safe(plot_Climate.plot_sector_emission_intensity, _tem, _prod, scenario=nexus_scenario)
    nexus_climate_plots['emissions_penalty_cost'] = _safe(plot_Climate.plot_emissions_penalty_cost, result_pack.get_df('DiscountedTechnologyEmissionsPenalty'), scenario=nexus_scenario)
    nexus_climate_plots['emission_target_gap'] = _safe(plot_Climate.plot_target_gap, _em, scenario=nexus_scenario)

    nexus_land_plots={}
    nexus_plots['Land'] = nexus_land_plots
    nexus_land_plots['Landuse_for_clusters('] = plot_Land.plot_landuse_for_clusters(result_pack.get_df('RateOfProductionByTechnologyByMode'), nexus_scenario)
    nexus_land_plots['land_area_by_crop'] = _safe(plot_Land.plot_land_area_by_crop, _prod, scenario=nexus_scenario)
    nexus_land_plots['irrigated_vs_rainfed'] = _safe(plot_Land.plot_irrigated_vs_rainfed, _prod, scenario=nexus_scenario)
    nexus_land_plots['landcover_change'] = _safe(plot_Land.plot_landcover_change, _cap, scenario=nexus_scenario)
    nexus_land_plots['cropland_change'] = _safe(plot_Land.plot_cropland_change, _cap, scenario=nexus_scenario)
    nexus_land_plots['energy_land_footprint'] = _safe(plot_Land.plot_energy_land_footprint, _prod, _newc, scenario=nexus_scenario)
    if _bymode is not None and _final_year is not None:
        nexus_land_plots['cluster_crop_heatmap'] = _safe(plot_Land.plot_cluster_crop_heatmap, _bymode, year=_final_year, scenario=nexus_scenario)
    nexus_land_plots['effective_yield'] = _safe(plot_Land.plot_effective_yield, _prod, scenario=nexus_scenario)
    nexus_land_plots['forest_trajectory'] = _safe(plot_Land.plot_forest_trajectory, _cap, scenario=nexus_scenario)

    nexus_water_plots={}
    nexus_plots['Water'] = nexus_water_plots
    nexus_water_plots['water_balance'] = _safe(plot_Water.plot_water_balance, _prod, scenario=nexus_scenario)
    nexus_water_plots['water_use_by_purpose'] = _safe(plot_Water.plot_water_use_by_purpose, _prod, scenario=nexus_scenario)
    nexus_water_plots['reservoir_levels'] = _safe(plot_Water.plot_reservoir_levels, _sl, scenario=nexus_scenario)
    nexus_water_plots['hydro_water_energy'] = _safe(plot_Water.plot_hydro_water_energy, _prod, _sl, scenario=nexus_scenario)

    nexus_energy_plots={}
    nexus_plots['Energy'] = nexus_energy_plots

    nexus_energy_plots["sectoral_consumption"] , nexus_energy_plots["Nexus_fuel_consumption"] = plot_Energy.plot_combined_stacked_energy_consumption(result_pack.get_df('UseByTechnology'), 
                                                                                                                                                        'gwh',
                                                                                                                                                        nexus_scenario)
    nexus_energy_plots["generation_from_fuels"]=plot_Energy.get_annual_generation_plot(result_pack.get_df('ProductionByTechnology'), 
                                                                                    nexus_scenario,timeslices)
    nexus_energy_plots["capacity_investments"]=plot_Energy.get_capacity_plot(result_pack.get_df('NewCapacity'),
                                                                                nexus_scenario,
                                                                                investment=True)
    nexus_energy_plots["capacity_total"]=plot_Energy.get_capacity_plot(result_pack.get_df('TotalCapacityAnnual'),nexus_scenario,investment=False)
    nexus_energy_plots["power_generation_timeslices"]=plot_Energy.get_generation_timeseries_plot(result_pack.get_df('RateOfProductionByTechnology'),timeslices,nexus_scenario)
    nexus_energy_plots["power_generation_annual"]=plot_Energy.get_annual_power_generation_plot(result_pack.get_df('ProductionByTechnologyAnnual'),nexus_scenario,timeslices)
    nexus_energy_plots["capital_investment_power"]=plot_Energy.get_capital_investments(result_pack.get_df('CapitalInvestment'),nexus_scenario)
    nexus_energy_plots['system_cost_breakdown'] = _safe(
        plot_Energy.plot_system_cost_breakdown,
        CapitalInvestment=result_pack.get_df('CapitalInvestment'),
        AnnualFixedOperatingCost=result_pack.get_df('AnnualFixedOperatingCost'),
        AnnualVariableOperatingCost=result_pack.get_df('AnnualVariableOperatingCost'),
        DiscountedTechnologyEmissionsPenalty=result_pack.get_df('DiscountedTechnologyEmissionsPenalty'),
        scenario=nexus_scenario)
    nexus_energy_plots['fossil_imports'] = _safe(plot_Energy.plot_fossil_imports, _prod, scenario=nexus_scenario)
    # nexus Sankey with a year slider (all model years; drag to see flows evolve)
    nexus_energy_plots['nexus_sankey'] = _safe(
        plot_Energy.plot_nexus_sankey_slider, _prod, _use,
        scenario=nexus_scenario, step=1)

    # ---- one colour vocabulary across every figure ------------------------
    # Legacy plots colour by CODE keys (custom_colors) while their legends show
    # LABELS, so plotly fell back to default colours; the palette resolves both
    # vocabularies and only recolours labels it actually knows.
    from bcnexus.vis import palette as _palette
    _palette.load_from_yaml()
    for _genre in nexus_plots:
        for _name, _fig in nexus_plots[_genre].items():
            _palette.harmonize(_fig)

    if save_individual:
        save_plots(nexus_plots,
                   plots_save_to)

    # combined tabbed report (single html, all plots + scenario info)
    save_combined_html(
        nexus_plots,
        scenario=nexus_scenario,
        save_to=Path(plots_save_to) /
                (f'CLEW_report_{storage_algorithm}_{nexus_scenario}_{timeslices}ts_{solver}'
                 f'{"_" + date_tag if date_tag else ""}.html'),
        scenario_info=_get_scenario_info(nexus_scenario),
        run_meta=f"{storage_algorithm} · {timeslices} timeslices · {solver}",
        extra_info=extra_info,
        layout=layout,
        constants=_meta,
        sets=_sets,
        runlog=runlog,
        constraints=constraints,
        gurobi_log=gurobi_log,
        solver_meta={'Solver': solver, 'Storage algorithm': storage_algorithm,
                     'Timeslices': timeslices}
                    if (constraints or gurobi_log) else None)

    return nexus_plots

def main(nexus_scenario: str, 
         storage_algorithm: str, 
         timeslices: int,
         results_csvs: str,
         plots_save_to:str,):
    
    print("Running CLEWs plotter:")
    print("  Scenario          : {nexus_scenario}")
    print("  Storage Algorithm : {storage_algorithm}")
    print("  Timeslices        : {timeslices}")
    
    get_plots(nexus_scenario=nexus_scenario,
              storage_algorithm=storage_algorithm,
              timeslices=timeslices,
              results_csvs=results_csvs,
              plots_save_to=plots_save_to)
    

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(
#         description="Plot results from CLEWs model runs with flexible settings.",
#         formatter_class=argparse.ArgumentDefaultsHelpFormatter
#     )

#     parser.add_argument(
#         "nexus_scenario",
#         type=str,
#         help="Name of the Nexus scenario to load"
#     )

#     parser.add_argument(
#         "storage_algorithm",
#         type=str,
#         choices=["Kotzur", "Niet", "Welsch", "Novo"],
#         help="Storage clustering algorithm"
#     )

#     parser.add_argument(
#         "timeslices",
#         type=int,
#         help="Number of timeslices (e.g., 24, 48, 96)"
#     )

#     # Optional helpers
#     parser.add_argument(
#         "-v", "--verbose",
#         action="store_true",
#         help="Enable verbose logging"
#     )

#     args = parser.parse_args()

#     if args.verbose:
#         print("Verbose mode: ON")
#         print("Parsed arguments:", args)

#     # Call main
#     main(
#         nexus_scenario=args.nexus_scenario,
#         storage_algorithm=args.storage_algorithm,
#         timeslices=args.timeslices
#     )
