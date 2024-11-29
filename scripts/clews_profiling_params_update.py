import pandas as pd
import argparse
import yaml
from bc_combined_modelling import utils
from bc_combined_modelling import clews_builder
from pathlib import Path
import clews_tech_schema_update

def prepare_capacity_factor_data(
    combined_model_config_path:Path,
    clews_builder_config_path:Path,
    new_pwrwnd_structure:dict,
    new_pwrwnd_future_structure:dict,
    new_pwrsol_structure:dict,
    new_pwrsol_future_structure:dict,
    new_inflow_structure:dict,
    new_hydro_structure:dict)->pd.DataFrame:
    
    """
    Generates the Capacity Factor(CF) data with 1 hour resolution i.e. 8760 timeslices for a year.
    """
        
    cm_config:dict=utils.load_config(combined_model_config_path)
    clewsb_config:dict=utils.load_config(clews_builder_config_path)
    
    ### GENERATE CAPACITY FACTOR CSV WITH 8760 TIMESLICES FOR 1 YEAR
    ##################################################################################################
    
    # Generate the capacity_factor CSV
    region = cm_config['clews']['GENERAL']['region']
    start_year = cm_config['clews']['GENERAL']['start_year']
    last_year = cm_config['clews']['GENERAL']['last_year']
    wind_ts_file_path =  cm_config['pypsa']['output']['create_ext_wind_ts'] ['fname']  # config['FILES']['DATA']['data_8760']['CF_wind']
    wind_future_ts_file_path = Path (cm_config['results']['linking']['root'])/ cm_config['results']['linking']['clusters_CFts_topSites']['wind'] # config['FILES']['DATA']['data_8760']['CF_wind_future']
    solar_ts_file_path =  cm_config['pypsa']['output']['create_ext_solar_ts'] ['fname'] # config['FILES']['DATA']['data_8760']['CF_solar']
    solar_future_ts_file_path = Path (cm_config['results']['linking']['root'])/ cm_config['results']['linking']['clusters_CFts_topSites']['solar'] #config['FILES']['DATA']['data_8760']['CF_solar_future']
    hydro_reservoir_ts_file_path = cm_config['pypsa']['output']['reservoir_inflows'] ['fname']  #  config['FILES']['DATA']['data_8760']['CF_hydro_reservoir']
    hydro_ror_ts_file_path = cm_config['pypsa']['output']['ror_ps'] ['fname']  # config['FILES']['DATA']['data_8760']['CF_hydro_ror']
    
    capacity_factor_file_out = Path ("data/clews_data/inputs_csv_8760_2020/CapacityFactor.csv")


    # data_cfg=clews_builder_config['FILES']['DATA']


    # Read time series data
    wind_ts_df = pd.read_csv(wind_ts_file_path)
    wind_future_ts_df = pd.read_pickle(wind_future_ts_file_path)
    solar_ts_df = pd.read_csv(solar_ts_file_path)
    solar_future_ts_df = pd.read_pickle(solar_future_ts_file_path)
    hydro_reservoir_ts_df = pd.read_csv(hydro_reservoir_ts_file_path)
    hydro_ror_ts_df = pd.read_csv(hydro_ror_ts_file_path)

    # Generate rows for PWRWND, PWRSOL and INFLOW
    rows = []
    rows.extend(clews_builder.generate_capacity_factor(new_pwrwnd_structure, wind_ts_df, region, start_year))
    rows.extend(clews_builder.generate_capacity_factor(new_pwrwnd_future_structure, wind_future_ts_df, region, start_year))
    rows.extend(clews_builder.generate_capacity_factor(new_pwrsol_structure, solar_ts_df, region, start_year))
    rows.extend(clews_builder.generate_capacity_factor(new_pwrsol_future_structure, solar_future_ts_df, region, start_year))
    rows.extend(clews_builder.generate_capacity_factor(new_inflow_structure, hydro_reservoir_ts_df, region, start_year))
    rows.extend(clews_builder.generate_capacity_factor(new_hydro_structure, hydro_ror_ts_df, region, start_year))

    # Create DataFrame and save to CSV
    capacity_factor_df = pd.DataFrame(rows)
    capacity_factor_file_out=Path ("data/clews_data/inputs_csv_8760_2020/CapacityFactor.csv")
    capacity_factor_df.to_csv(capacity_factor_file_out, index=False)

    print(f"Capacity factor CSV file saved at: {capacity_factor_file_out}")
    return capacity_factor_df

def update_specified_demand_profile(
    combined_model_config_path:Path,
    clews_builder_config_path:Path
)->pd.DataFrame:
    """
    Generates specified demand profile CSV files with 1 hour resolution for a year.
    """
    ### GENERATE SPECIFIED DEMAND PROFILE CSV WITH 8760 TIMESLICES FOR 1 YEAR
    ##################################################################################################
    clews_builder_config:dict=utils.load_config(clews_builder_config_path)
    cm_config:dict=utils.load_config(combined_model_config_path)
    
    region = cm_config['clews']['GENERAL']['region']
    start_year = cm_config['clews']['GENERAL']['start_year']
    last_year = cm_config['clews']['GENERAL']['last_year']
    
    # Load the pickle file
    data_file_path = "data/downloaded_data/CODERS/data-pull/demand/BC_provincial_demand_profile.csv"
    
    df = pd.read_csv(data_file_path)

    # Filter the DataFrame to remove February 29, 2020
    df_filtered = df[~((df['local_time'] >= '2020-02-29') & (df['local_time'] < '2020-03-01'))].copy()

    # Ensure the 'demand_MWh' column is of type float64
    df_filtered['demand_MWh'] = df_filtered['demand_MWh'].astype(float)

    # Normalize the 'demand_MWh' column
    df_filtered.loc[:, 'demand_MWh'] = df_filtered['demand_MWh'] / df_filtered['demand_MWh'].sum()

    # Define demands
    demands = ['AGRELCB02', 'COMELCB02', 'INDELCB02', 'RESELCB02', 'TRAELCB02']

    # Generate demand profile rows
    demand_rows = clews_builder.generate_demand_profile(demands, df_filtered, region, start_year)

    # Concatenate all the new rows into a single DataFrame
    specified_demand_profile_df = pd.concat(demand_rows, ignore_index=True)

    # Save the final DataFrame to a CSV file
    specified_demand_profile_file_out = Path('data/clews_data/inputs_csv_8760_2020/SpecifiedDemandProfile.csv')#clews_builder_config['FILES']['specified_demand_profile_8760_file']
    specified_demand_profile_df.to_csv(specified_demand_profile_file_out, index=False)

    print(f"Specified demand profile CSV file saved at: {specified_demand_profile_file_out}")

    return specified_demand_profile_df

def main(
    combined_model_config_path:Path,
    clews_builder_config_path:Path
):

    #step 1: Update the CLEWS builder config
    print(f"\n>> Updating CLEWS Builder configuration file...")
    (new_pwrwnd_structure,new_pwrwnd_future_structure,new_pwrsol_structure,
     new_pwrsol_future_structure,new_inflow_structure,new_hydro_structure) = clews_tech_schema_update.update_clews_builder_config(combined_model_config_path,
                                                                                                                                  clews_builder_config_path)
    
    
    #step 2: Load the updated CLEWS BUILDER CONFIG
    print(f"\n>> Loading the updated CLEWS Builder config...")
    # config=utils.load_config(config_file_path)
    # clews_builder_config:dict=utils.load_config(clews_builder_config_path)
    # combined_model_config:dict=utils.load_config(clews_builder_config_path)
    
    #step 3: Update CAPACITY FACTOR
    print(f"\n>> Updating CAPACITY FACTOR...")
    prepare_capacity_factor_data(combined_model_config_path,
                                clews_builder_config_path,
                                 new_pwrwnd_structure,
                                 new_pwrwnd_future_structure,
                                 new_pwrsol_structure,
                                 new_pwrsol_future_structure,
                                 new_inflow_structure,
                                 new_hydro_structure)
    
    #step 4: update SPECIFIED DEMAND PROFILE
    print(f"\n>> Updating SPECIFIED DEMAND PROFILE...")
    update_specified_demand_profile(combined_model_config_path,
                                    clews_builder_config_path)
    
    return 

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Run CLEWs paramater update script')
    
    # Positional arguments (without default values)
    parser.add_argument('combined_model_config', 
                        type=str, 
                        help="Path to the combined model configuration file")
    
    parser.add_argument('clews_builder_config', 
                        type=str, 
                        help="Path to the CLEWs builder configuration file")
    
    # Parse the arguments
    args = parser.parse_args()
    
    main(args.combined_model_config, args.clews_builder_config)
    # """
    #----------------------- for notebook run/Debugging------------------------------------
    # config_file_path='config/config.yaml'
    # main(config_file_path)
