import argparse
import plotly.express as px24
from pathlib import Path
from bcnexus import utils
from bcnexus.clews.datapackage import GetDataPackage
from bcnexus.vis import plot_Climate
from bcnexus.vis import plot_Energy
from bcnexus.vis import plot_Land
import sys
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

def get_plots(nexus_scenario:str='Base_CNZ',
         timeslices:int=24,
         storage_algorithm:str="Kotzur",
         solver:str="gurobi"):

    nexus_results_root=Path(f'results/clews/Model_{storage_algorithm}_{nexus_scenario}/{timeslices}ts_csvs_{solver}')
    result_pack=GetDataPackage(nexus_results_root)
    if result_pack is None:
        utils.print_update("no results found")
        sys.exit(1)
    
    vis_save_to_root = Path('vis/bccm')
    plots_save_to=vis_save_to_root/nexus_scenario/'bc_nexus'
    if not plots_save_to.exists():
        plots_save_to.mkdir(parents=True, exist_ok=True)

    nexus_ts_plots={}
    plot_categories = ['Climate', 'Land', 'Energy', 'Water', str(timeslices)]
    nexus_plots = {category: {} for category in plot_categories}
    nexus_plots[f'{timeslices}'] = nexus_ts_plots

    nexus_climate_plots={}
    nexus_plots['Climate'] = nexus_climate_plots

    nexus_climate_plots['emission_total']=plot_Climate.get_total_annual_emission(result_pack.get_dataframe('AnnualEmissions'), nexus_scenario)
    
    nexus_climate_plots['emission_by_source']=plot_Climate.get_emission_from_fuels(result_pack.get_dataframe('AnnualTechnologyEmission'), nexus_scenario)
    nexus_climate_plots['emission_by_sector']=plot_Climate.get_emission_from_sector(result_pack.get_dataframe('AnnualTechnologyEmission'), nexus_scenario)

    nexus_land_plots={}
    nexus_plots['Land'] = nexus_land_plots
    nexus_land_plots['Landuse_for_clusters('] = plot_Land.plot_landuse_for_clusters(result_pack.get_dataframe('RateOfProductionByTechnologyByMode'), nexus_scenario)


 
    nexus_energy_plots={}
    nexus_plots['Energy'] = nexus_energy_plots

    nexus_energy_plots["sectoral_consumption"] , nexus_energy_plots["Nexus_fuel_consumption"] = plot_Energy.plot_combined_stacked_energy_consumption(result_pack.get_dataframe('UseByTechnology'), 
                                                                                                                                                        'gwh',
                                                                                                                                                        nexus_scenario)
    nexus_energy_plots["generation_from_fuels"]=plot_Energy.get_annual_generation_plot(result_pack.get_dataframe('ProductionByTechnology'), 
                                                                                    nexus_scenario)
    nexus_energy_plots["capacity_investments"]=plot_Energy.get_capacity_plot(result_pack.get_dataframe('NewCapacity'),
                                                                                nexus_scenario,
                                                                                investment=True)
    nexus_energy_plots["capacity_total"]=plot_Energy.get_capacity_plot(result_pack.get_dataframe('TotalCapacityAnnual'),nexus_scenario,investment=False)
    nexus_energy_plots["power_generation_timeslices"]=plot_Energy.get_generation_timeseries_plot(result_pack.get_dataframe('RateOfUseByTechnology'),24,nexus_scenario)
    nexus_energy_plots["power_generation_annual"]=plot_Energy.get_annual_power_generation_plot(result_pack.get_dataframe('ProductionByTechnologyAnnual'),nexus_scenario)
    nexus_energy_plots["capital_investment_power"]=plot_Energy.get_capital_investments(result_pack.get_dataframe('CapitalInvestment'),nexus_scenario)
    
    save_plots(nexus_plots,
               plots_save_to)

    

def main(nexus_scenario: str, storage_algorithm: str, timeslices: int):
    
    print("Running CLEWs plotter:")
    print("  Scenario          : {nexus_scenario}")
    print("  Storage Algorithm : {storage_algorithm}")
    print("  Timeslices        : {timeslices}")
    
    get_plots(nexus_scenario=nexus_scenario,
              storage_algorithm=storage_algorithm,
              timeslices=timeslices)
    

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
