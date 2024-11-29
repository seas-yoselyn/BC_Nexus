import pandas as pd
import argparse
import yaml
from bc_combined_modelling import utils
from bc_combined_modelling import clews_builder
from pathlib import Path
from bc_combined_modelling.AttributesParser_cm import AttributesParserExtended


def update_residual_capacity(
    combined_model_config_path:Path,
    clews_builder_config_path:Path,
):
    ### UPDATE RESIDUAL CAPACITY
    ##################################################################################################
    cb_config:dict=utils.load_config(clews_builder_config_path)
    cm_config:dict=utils.load_config(combined_model_config_path)
    
    residual_capacity_file = Path ('data/clews_data/inputs_csv/ResidualCapacity.csv') # config['FILES']['residual_capacity_file']
    techs = cb_config['TECHNOLOGIES']
    
    region = cm_config['clews']['GENERAL']['region']
    start_year = cm_config['clews']['GENERAL']['start_year']
    last_year = cm_config['clews']['GENERAL']['last_year']

    df_filtered = clews_builder.delete_technologies(residual_capacity_file, techs)

    # Add the new technologies
    for category, tech_details in techs.items():
        for tech_key, tech_info in tech_details.items():
            df_filtered = clews_builder.add_technologies_residual_cap(df_filtered, tech_key, tech_info, start_year, region)
            
    residual_capacity_out=Path(f'data/clews_data/inputs_csv/ResidualCapacity.csv')
    # Save the file with updated technologies
    df_filtered.to_csv(residual_capacity_out, index=False)

    print(f"Residual capacity CSV file saved at: {residual_capacity_file}")
    
def update_operational_life(
    combined_model_config_path:Path,
    clews_builder_config_path:Path,
):
    cb_config:dict=utils.load_config(clews_builder_config_path)
    cm_config:dict=utils.load_config(combined_model_config_path)
    ### UPDATE OPERATIONAL LIFE
    ##################################################################################################
    operational_life_file =  Path ('data/clews_data/inputs_csv/OperationalLife.csv') # config['FILES']['operational_life_file']
    
    techs = cb_config['TECHNOLOGIES']
    storage_techs = cb_config['STORAGE_TECHNOLOGY']
    
    region = cm_config['clews']['GENERAL']['region']
    start_year = cm_config['clews']['GENERAL']['start_year']
    last_year = cm_config['clews']['GENERAL']['last_year']

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

    operational_life_out=Path(f'data/clews_data/inputs_csv/OperationalLife.csv')
    # Save the file with updated technologies
    df_filtered.to_csv(operational_life_out, index=False)

    print(f"Operational life CSV file saved at: {operational_life_file}")

def update_operational_life_storage(
    combined_model_config_path:Path,
    clews_builder_config_path:Path,
):
    cb_config:dict=utils.load_config(clews_builder_config_path)
    cm_config:dict=utils.load_config(combined_model_config_path)
    ### UPDATE OPERATIONAL LIFE STORAGE
    ##################################################################################################
    operational_life_storage_file = Path ('data/clews_data/inputs_csv/OperationalLifeStorage.csv') #config['FILES']['operational_life_storage_file']
    storage = cb_config['STORAGE']
    
    region = cm_config['clews']['GENERAL']['region']

    df_filtered = clews_builder.delete_technologies(operational_life_storage_file, storage, 'STORAGE')

    #Add the new storage
    for storage_key, storage_info in storage.items():
        df_filtered = clews_builder.add_technologies_operational_life(df_filtered, storage_key, storage_info, region, 'STORAGE', 'operational_life_storage')

    operational_life_storage_out=Path ('data/clews_data/inputs_csv/OperationalLifeStorage.csv')
    # Save the file with updated technologies
    df_filtered.to_csv(operational_life_storage_out, index=False)

    print(f"Operational life storage CSV file saved at: {operational_life_storage_file}")
    
def update_capex(
    combined_model_config_path:Path,
    clews_builder_config_path:Path,
):
    cb_config:dict=utils.load_config(clews_builder_config_path)
    cm_config:dict=utils.load_config(combined_model_config_path)
    
    ### UPDATE CAPITAL COST
    ##################################################################################################
    capital_cost_file = Path ('data/clews_data/inputs_csv/CapitalCost.csv') #config['FILES']['capital_cost_file']
    
    techs = cb_config['TECHNOLOGIES']
    storage_techs = cb_config['STORAGE_TECHNOLOGY']
    
    region = cm_config['clews']['GENERAL']['region']
    start_year = cm_config['clews']['GENERAL']['start_year']
    last_year = cm_config['clews']['GENERAL']['last_year']

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
        
    capital_cost_out = Path ('data/clews_data/inputs_csv/CapitalCost.csv')
    # Save the file with updated technologies
    df_filtered.to_csv(capital_cost_out, index=False)

    print(f"Capital cost CSV file saved at: {capital_cost_file}")

def update_availability_factor(
    combined_model_config_path:Path,
    clews_builder_config_path:Path,
):
    cb_config:dict=utils.load_config(clews_builder_config_path)
    cm_config:dict=utils.load_config(combined_model_config_path)
    
    ### UPDATE AVAILABILITY FACTOR
    ##################################################################################################
    availability_factor_file = Path ('data/clews_data/inputs_csv/AvailabilityFactor.csv') # config['FILES']['availability_factor_file']
    techs = cb_config['TECHNOLOGIES']
    
    region = cm_config['clews']['GENERAL']['region']
    start_year = cm_config['clews']['GENERAL']['start_year']
    last_year = cm_config['clews']['GENERAL']['last_year']
    # Delete technologies based on TECHS
    df_filtered = clews_builder.delete_technologies(availability_factor_file, techs)

    # Add the new technologies
    for category, tech_details in techs.items():
        for tech_key, tech_info in tech_details.items():
            df_filtered = clews_builder.add_technologies_availability_factor(df_filtered, tech_key, tech_info, start_year, last_year, region)
    
    availability_factor_out = Path ('data/clews_data/inputs_csv/AvailabilityFactor.csv')
    # Save the file with updated technologies
    df_filtered.to_csv(availability_factor_out, index=False)

    print(f"Availability factor CSV file saved at: {availability_factor_out}")

def update_capex_storage(
    combined_model_config_path:Path,
    clews_builder_config_path:Path,
):
    cb_config:dict=utils.load_config(clews_builder_config_path)
    cm_config:dict=utils.load_config(combined_model_config_path)
    
    ### UPDATE CAPITAL COST STORAGE
    ##################################################################################################
    
    capital_cost_storage_file = Path ('data/clews_data/inputs_csv/CapitalCostStorage.csv') # config['FILES']['capital_cost_storage_file']
    
    storage = cb_config['STORAGE']
    
    region = cm_config['clews']['GENERAL']['region']
    start_year = cm_config['clews']['GENERAL']['start_year']
    last_year = cm_config['clews']['GENERAL']['last_year']

    df_filtered = clews_builder.delete_technologies(capital_cost_storage_file, storage, 'STORAGE')

    #Add the new storage
    for storage_key, storage_info in storage.items():
        df_filtered = clews_builder.add_technologies_capital_cost(df_filtered, storage_key, storage_info, start_year, last_year, region, 'STORAGE', 'capital_cost_storage')

    capital_cost_storage_out = Path ('data/clews_data/inputs_csv/CapitalCostStorage.csv')
    # Save the file with updated technologies
    df_filtered.to_csv(capital_cost_storage_out, index=False)

    print(f"Capital cost storage CSV file saved at: {capital_cost_storage_out}")

def update_technology_from_to_storage(
    combined_model_config_path:Path,
    clews_builder_config_path:Path,
):
    cb_config:dict=utils.load_config(clews_builder_config_path)
    cm_config:dict=utils.load_config(combined_model_config_path)
    
    ### UPDATE TECHNOLOGY TO STORAGE
    ##################################################################################################
    technology_to_storage_file = Path ('data/clews_data/inputs_csv/TechnologyToStorage.csv') #config['FILES']['technology_to_storage_file']
    
    storage = cb_config['STORAGE']
    
    region = cm_config['clews']['GENERAL']['region']
    start_year = cm_config['clews']['GENERAL']['start_year']
    last_year = cm_config['clews']['GENERAL']['last_year']

    df_filtered = clews_builder.delete_technologies(technology_to_storage_file, storage, 'STORAGE')

    #Add the new storage
    for storage_key, storage_info in storage.items():
        df_filtered = clews_builder.add_technology_to_and_from_storage(df_filtered, storage_key, storage_info, region, operation_type='TO')
    
    technology_to_storage_out = Path ('data/clews_data/inputs_csv/TechnologyToStorage.csv')
    # Save the file with updated technologies
    df_filtered.to_csv(technology_to_storage_out, index=False)

    print(f"Technology to storage CSV file saved at: {technology_to_storage_out}")

    ### UPDATE TECHNOLOGY FROM STORAGE
    ##################################################################################################
    technology_from_storage_file = Path ('data/clews_data/inputs_csv/TechnologyFromStorage.csv') #config['FILES']['technology_from_storage_file']

    df_filtered = clews_builder.delete_technologies(technology_from_storage_file, storage, 'STORAGE')

    #Add the new storage
    for storage_key, storage_info in storage.items():
        df_filtered = clews_builder.add_technology_to_and_from_storage(df_filtered, storage_key, storage_info, region, operation_type='FROM')

    technology_from_storage_out = Path ('data/clews_data/inputs_csv/TechnologyFromStorage.csv')
    # Save the file with updated technologies
    df_filtered.to_csv(technology_from_storage_out, index=False)

    print(f"Technology from storage CSV file saved at: {technology_from_storage_out}")
    
def main(
    combined_model_config_path:Path,
    clews_builder_config_path:Path
):
    
    #step 5: update RESIDUAL CAPACITY
    print(f"\n>> Updating RESIDUAL CAPACITY...")
    update_residual_capacity(combined_model_config_path,
                             clews_builder_config_path)
    
    #step 6: Update OPERATIONAL LIFE
    print(f"\n>> Updating OPERATIONAL LIFE...")
    update_operational_life(combined_model_config_path,
                             clews_builder_config_path)
    update_operational_life_storage(combined_model_config_path,
                             clews_builder_config_path)

    #step 7: Update AVAILABILITY FACTOR
    print(f"\n>> Updating AVAILABILITY FACTOR...")
    update_availability_factor(combined_model_config_path,
                             clews_builder_config_path)
    
    #step 8: Update CAPEX
    print(f"\n>> Updating CAPITAL COST...")
    update_capex(combined_model_config_path,
                             clews_builder_config_path)
    update_capex_storage(combined_model_config_path,
                             clews_builder_config_path)

    #step 9: Update TECHNOLOGY from/to STORAGE
    print(f"\n>> Updating TECHNOLOGY FROM STORAGE...")
    update_technology_from_to_storage(combined_model_config_path,
                             clews_builder_config_path)
    
    print(f"CLEWs yearly Parameters updated.")
    
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