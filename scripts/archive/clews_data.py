import pandas as pd
import argparse
import yaml
from bc_combined_modelling import utils
from bc_combined_modelling import clews_builder
from pathlib import Path
from bc_combined_modelling.AttributesParser_cm import AttributesParserExtended

def update_clews_builder_config(
    clews_builder_config_path:Path
)->tuple:
    """
    This function reads the existing CLEWS Builder Config file and updates the technology and other SET and PARAMETERS.
    """
    ##################################################################################################
    # Read the existing YAML file
    clews_builder_config:dict=utils.load_config(clews_builder_config_path)

    data_cfg=clews_builder_config['FILES']['DATA']
    

    wind_csv_file_path = data_cfg['wind_file']
    wind_future_pkl_file_path = data_cfg['wind_future_file']
    solar_csv_file_path = data_cfg['solar_file']
    solar_future_pkl_file_path = data_cfg['solar_future_file']
    tpp_csv_file_path = data_cfg['tpp_file']
    hydro_generation_csv_file_path = data_cfg['hydro_generation_file']
    hydro_resevoir_csv_file_path = data_cfg['hydro_reservoir_file']
    hydro_reservoir_ts_file_path = data_cfg['data_8760']['CF_hydro_reservoir']

    # Define cascade groups from the YAML file
    cascade_group = clews_builder_config['HYDRO_GENERATION']

    # Read the CSV files
    wind_df = pd.read_csv(wind_csv_file_path)
    wind_future_df = pd.read_pickle(wind_future_pkl_file_path)
    solar_df = pd.read_csv(solar_csv_file_path)
    solar_future_df = pd.read_pickle(solar_future_pkl_file_path)
    tpp_df = pd.read_csv(tpp_csv_file_path)
    hydro_generation_df = pd.read_csv(hydro_generation_csv_file_path)
    hydro_resevoir_df = pd.read_csv(hydro_resevoir_csv_file_path)
    hydro_reservoir_ts_df = pd.read_csv(hydro_reservoir_ts_file_path)

    # Create new PWRWND, PWRSOL, INFLOW and PWRHYD structures
    new_pwrwnd_structure = clews_builder.create_structure(wind_df, id_prefix='PWRWNDB')
    
    new_pwrwnd_future_structure = clews_builder.create_structure(wind_df, 
                                                                 id_prefix='PWRWNDB', 
                                                                 start_index=len(wind_df), 
                                                                 future_df=wind_future_df)
    
    new_pwrsol_structure = clews_builder.create_structure(solar_df, id_prefix='PWRSOLB')
    
    new_pwrsol_future_structure = clews_builder.create_structure(solar_df, 
                                                                 id_prefix='PWRSOLB', 
                                                                 start_index=len(solar_df), 
                                                                 future_df=solar_future_df)
    
    new_tpp_bio_structure = clews_builder.create_structure_tpp(tpp_df, id_prefix='PWRBIOB')
    
    new_tpp_ngs_structure = clews_builder.create_structure_tpp(tpp_df, id_prefix='PWRNGSB')
    
    new_inflow_structure = clews_builder.create_structure_inflow(hydro_generation_df, 
                                                                 hydro_resevoir_df, 
                                                                 hydro_reservoir_ts_df, 
                                                                 cascade_group, 
                                                                 'INFLOW')
    new_hydro_structure = clews_builder.create_structure_hydro(hydro_generation_df, 
                                                               cascade_group, 
                                                               'PWRHYDB')

    merged_pwrsol_structure = {**new_pwrsol_structure, 
                               **new_pwrsol_future_structure}
    
    merged_pwrwnd_structure = {**new_pwrwnd_structure, 
                               **new_pwrwnd_future_structure}

    # Update the TECHNOLOGIES section
    if 'TECHNOLOGIES' not in clews_builder_config:
        clews_builder_config['TECHNOLOGIES'] = {}

    clews_builder_config['TECHNOLOGIES']['PWRWND'] = merged_pwrwnd_structure
    clews_builder_config['TECHNOLOGIES']['PWRSOL'] = merged_pwrsol_structure
    clews_builder_config['TECHNOLOGIES']['PWRBIO'] = new_tpp_bio_structure
    clews_builder_config['TECHNOLOGIES']['PWRNGS'] = new_tpp_ngs_structure
    clews_builder_config['TECHNOLOGIES']['INFLOW'] = new_inflow_structure
    clews_builder_config['TECHNOLOGIES']['PWRHYD'] = new_hydro_structure

    # Save the updated YAML back to the same file
    with open(clews_builder_config_path, 'w') as file:
        yaml.dump(clews_builder_config, file, default_flow_style=False)

    print(f"Updated YAML file saved at: {clews_builder_config}")
    
    return (new_pwrwnd_structure,
            new_pwrwnd_future_structure,
            new_pwrsol_structure,
            new_pwrsol_future_structure,
            new_inflow_structure,
            new_hydro_structure)

def prepare_capacity_factor_data(
    clews_builder_config:dict,
    new_pwrwnd_structure,
    new_pwrwnd_future_structure,
    new_pwrsol_structure,
    new_pwrsol_future_structure,
    new_inflow_structure,
    new_hydro_structure):
    """
    Generates the Capacity Factor(CF) data with 1 hour resolution i.e. 8760 timeslices for a year.
    """
    config:dict=clews_builder_config
    ### GENERATE CAPACITY FACTOR CSV WITH 8760 TIMESLICES FOR 1 YEAR
    ##################################################################################################
    # Generate the capacity_factor CSV
    region = config['GENERAL']['region']
    start_year = config['GENERAL']['start_year']
    last_year = config['GENERAL']['last_year']
    wind_ts_file_path = config['FILES']['DATA']['data_8760']['CF_wind']
    wind_future_ts_file_path = config['FILES']['DATA']['data_8760']['CF_wind_future']
    solar_ts_file_path = config['FILES']['DATA']['data_8760']['CF_solar']
    solar_future_ts_file_path = config['FILES']['DATA']['data_8760']['CF_solar_future']
    hydro_reservoir_ts_file_path = config['FILES']['DATA']['data_8760']['CF_hydro_reservoir']
    hydro_ror_ts_file_path = config['FILES']['DATA']['data_8760']['CF_hydro_ror']
    capacity_factor_file_path = config['FILES']['capacity_factor_8760_file']

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
    capacity_factor_df.to_csv(capacity_factor_file_path, index=False)

    print(f"Capacity factor CSV file saved at: {capacity_factor_file_path}")

def update_specified_demand_profile(
    clews_builder_config:dict
):
    """
    Generates specified demand profile CSV files with 1 hour resolution for a year.
    """
    ### GENERATE SPECIFIED DEMAND PROFILE CSV WITH 8760 TIMESLICES FOR 1 YEAR
    ##################################################################################################
    config:dict=clews_builder_config
    region = config['GENERAL']['region']
    start_year = config['GENERAL']['start_year']
    last_year = config['GENERAL']['last_year']
    
    # Load the pickle file
    data_file_path = config['FILES']['DATA']['data_8760']['SDP']
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
    final_df = pd.concat(demand_rows, ignore_index=True)

    # Save the final DataFrame to a CSV file
    specified_demand_profile_file_path = config['FILES']['specified_demand_profile_8760_file']
    final_df.to_csv(specified_demand_profile_file_path, index=False)

    print(f"Specified demand profile CSV file saved at: {specified_demand_profile_file_path}")


def update_residual_capacity(
    clews_builder_config:dict
):
    ### UPDATE RESIDUAL CAPACITY
    ##################################################################################################
    config:dict=clews_builder_config
    residual_capacity_file = config['FILES']['residual_capacity_file']
    techs = config['TECHNOLOGIES']
    region = config['GENERAL']['region']
    start_year = config['GENERAL']['start_year']
    last_year = config['GENERAL']['last_year']

    df_filtered = clews_builder.delete_technologies(residual_capacity_file, techs)

    # Add the new technologies
    for category, tech_details in techs.items():
        for tech_key, tech_info in tech_details.items():
            df_filtered = clews_builder.add_technologies_residual_cap(df_filtered, tech_key, tech_info, start_year, region)

    # Save the file with updated technologies
    df_filtered.to_csv(residual_capacity_file, index=False)

    print(f"Residual capacity CSV file saved at: {residual_capacity_file}")
    
def update_operational_life(
    clews_builder_config:dict
):
    config:dict=clews_builder_config
    ### UPDATE OPERATIONAL LIFE
    ##################################################################################################
    operational_life_file = config['FILES']['operational_life_file']
    techs = config['TECHNOLOGIES']
    storage_techs = config['STORAGE_TECHNOLOGY']
    region = config['GENERAL']['region']
    start_year = config['GENERAL']['start_year']
    last_year = config['GENERAL']['last_year']

    # Delete technologies based on TECHS
    df_filtered = clews_builder.delete_technologies(operational_life_file, techs)

    # Delete storage technologies based on STORAGE_TECHNOLOGY
    df_filtered = clews_builder.delete_technologies(df_filtered, storage_techs)

    #Add the new technologies
    for category, tech_details in techs.items():
        for tech_key, tech_info in tech_details.items():
            df_filtered = clews_builder.add_technologies_operational_life(df_filtered, tech_key, tech_info, region)

    # Add the storage technologies
    for storage_key, storage_info in storage_techs.items():
        df_filtered = clews_builder.add_technologies_operational_life(df_filtered, storage_key, storage_info, region)

    # Save the file with updated technologies
    df_filtered.to_csv(operational_life_file, index=False)

    print(f"Operational life CSV file saved at: {operational_life_file}")

def update_operational_life_storage(
    clews_builder_config:dict
):
    config:dict=clews_builder_config
    ### UPDATE OPERATIONAL LIFE STORAGE
    ##################################################################################################
    operational_life_storage_file = config['FILES']['operational_life_storage_file']
    storage = config['STORAGE']
    region = config['GENERAL']['region']

    df_filtered = clews_builder.delete_technologies(operational_life_storage_file, storage, 'STORAGE')

    #Add the new storage
    for storage_key, storage_info in storage.items():
        df_filtered = clews_builder.add_technologies_operational_life(df_filtered, storage_key, storage_info, region, 'STORAGE', 'operational_life_storage')

    # Save the file with updated technologies
    df_filtered.to_csv(operational_life_storage_file, index=False)

    print(f"Operational life storage CSV file saved at: {operational_life_storage_file}")
    
def update_capex(
clews_builder_config:dict
):
    config:dict=clews_builder_config
    
    ### UPDATE CAPITAL COST
    ##################################################################################################
    capital_cost_file = config['FILES']['capital_cost_file']
    techs = config['TECHNOLOGIES']
    storage_techs = config['STORAGE_TECHNOLOGY']
    region = config['GENERAL']['region']
    start_year = config['GENERAL']['start_year']
    last_year = config['GENERAL']['last_year']

    # Delete technologies based on TECHS
    df_filtered = clews_builder.delete_technologies(capital_cost_file, techs)

    # Delete storage technologies based on STORAGE_TECHNOLOGY
    df_filtered = clews_builder.delete_technologies(df_filtered, storage_techs)

    # Add the new technologies
    for category, tech_details in techs.items():
        for tech_key, tech_info in tech_details.items():
            df_filtered = clews_builder.add_technologies_capital_cost(df_filtered, tech_key, tech_info, start_year, last_year, region)

    # Add the storage technologies
    for storage_key, storage_info in storage_techs.items():
        df_filtered = clews_builder.add_technologies_capital_cost(df_filtered, storage_key, storage_info, start_year, last_year, region)

    # Save the file with updated technologies
    df_filtered.to_csv(capital_cost_file, index=False)

    print(f"Capital cost CSV file saved at: {capital_cost_file}")

def update_availability_factor(
    clews_builder_config:dict
):
    config:dict=clews_builder_config
    ### UPDATE AVAILABILITY FACTOR
    ##################################################################################################
    availability_factor_file = config['FILES']['availability_factor_file']
    techs = config['TECHNOLOGIES']
    region = config['GENERAL']['region']
    start_year = config['GENERAL']['start_year']
    last_year = config['GENERAL']['last_year']
    # Delete technologies based on TECHS
    df_filtered = clews_builder.delete_technologies(availability_factor_file, techs)

    # Add the new technologies
    for category, tech_details in techs.items():
        for tech_key, tech_info in tech_details.items():
            df_filtered = clews_builder.add_technologies_availability_factor(df_filtered, tech_key, tech_info, start_year, last_year, region)

    # Save the file with updated technologies
    df_filtered.to_csv(availability_factor_file, index=False)

    print(f"Availability factor CSV file saved at: {availability_factor_file}")

def update_capex_storage(
    clews_builder_config:dict
):
    config:dict=clews_builder_config
    ### UPDATE CAPITAL COST STORAGE
    ##################################################################################################
    capital_cost_storage_file = config['FILES']['capital_cost_storage_file']
    storage = config['STORAGE']
    region = config['GENERAL']['region']
    start_year = config['GENERAL']['start_year']
    last_year = config['GENERAL']['last_year']

    df_filtered = clews_builder.delete_technologies(capital_cost_storage_file, storage, 'STORAGE')

    #Add the new storage
    for storage_key, storage_info in storage.items():
        df_filtered = clews_builder.add_technologies_capital_cost(df_filtered, storage_key, storage_info, start_year, last_year, region, 'STORAGE', 'capital_cost_storage')


    # Save the file with updated technologies
    df_filtered.to_csv(capital_cost_storage_file, index=False)

    print(f"Capital cost storage CSV file saved at: {capital_cost_storage_file}")

def update_technology_from_to_storage(
clews_builder_config:dict
):
    config:dict=clews_builder_config
    ### UPDATE TECHNOLOGY TO STORAGE
    ##################################################################################################
    technology_to_storage_file = config['FILES']['technology_to_storage_file']
    storage = config['STORAGE']
    region = config['GENERAL']['region']
    start_year = config['GENERAL']['start_year']
    last_year = config['GENERAL']['last_year']

    df_filtered = clews_builder.delete_technologies(technology_to_storage_file, storage, 'STORAGE')

    #Add the new storage
    for storage_key, storage_info in storage.items():
        df_filtered = clews_builder.add_technology_to_and_from_storage(df_filtered, storage_key, storage_info, region, operation_type='TO')

    # Save the file with updated technologies
    df_filtered.to_csv(technology_to_storage_file, index=False)

    print(f"Technology to storage CSV file saved at: {technology_to_storage_file}")

    ### UPDATE TECHNOLOGY FROM STORAGE
    ##################################################################################################
    technology_from_storage_file = config['FILES']['technology_from_storage_file']
    storage = config['STORAGE']

    df_filtered = clews_builder.delete_technologies(technology_from_storage_file, storage, 'STORAGE')

    #Add the new storage
    for storage_key, storage_info in storage.items():
        df_filtered = clews_builder.add_technology_to_and_from_storage(df_filtered, storage_key, storage_info, region, operation_type='FROM')

    # Save the file with updated technologies
    df_filtered.to_csv(technology_from_storage_file, index=False)

    print(f"Technology from storage CSV file saved at: {technology_from_storage_file}")
    
def main(
    config_file_path:str
):
    aparser=AttributesParserExtended(config_file_path)

    
    #step 1: Update the CLEWS builder config
    print(f"\n>> Updating CLEWS Builder configuration file...")
    (new_pwrwnd_structure,new_pwrwnd_future_structure,new_pwrsol_structure,
     new_pwrsol_future_structure,new_inflow_structure,new_hydro_structure) =update_clews_builder_config(config_file_path)
    
    
    #step 2: Load the updated CLEWS BUILDER CONFIG
    print(f"\n>> Loading the updated CLEWS Builder config...")
    # config=utils.load_config(config_file_path)
    config:dict=aparser.config
    
    #step 3: Update CAPACITY FACTOR
    print(f"\n>> Updating CAPACITY FACTOR...")
    prepare_capacity_factor_data(config,new_pwrwnd_structure,new_pwrwnd_future_structure,new_pwrsol_structure,
     new_pwrsol_future_structure,new_inflow_structure,new_hydro_structure)
    
    #step 4: update SPECIFIED DEMAND PROFILE
    print(f"\n>> Updating SPECIFIED DEMAND PROFILE...")
    update_specified_demand_profile(config)
    
    #step 5: update RESIDUAL CAPACITY
    print(f"\n>> Updating RESIDUAL CAPACITY...")
    update_residual_capacity(config)
    
    #step 6: Update OPERATIONAL LIFE
    print(f"\n>> Updating OPERATIONAL LIFE...")
    update_operational_life(config)
    update_operational_life_storage(config)

    #step 7: Update AVAILABILITY FACTOR
    print(f"\n>> Updating AVAILABILITY FACTOR...")
    update_availability_factor(config)
    
    #step 8: Update CAPEX
    print(f"\n>> Updating CAPITAL COST...")
    update_capex(config)
    update_capex_storage(config)

    #step 9: Update TECHNOLOGY from/to STORAGE
    print(f"\n>> Updating TECHNOLOGY FROM STORAGE...")
    update_technology_from_to_storage(config)
    
    return 


# %%

if __name__ == "__main__":
    # """ 
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Run data preparation script')
    parser.add_argument('config', 
                        type=str, 
                        default='config/clews_builder.yaml',
                        help=f"Path to the configuration file , the default is set to 'config/clews_builder.yaml' ", 
                        )
    
    # Parse the arguments
    args = parser.parse_args()
    main(args.config)
    # """
    #----------------------- for notebook run/Debugging------------------------------------
    # config_file_path='config/clews_builder.yaml'
    # main(config_file_path)
