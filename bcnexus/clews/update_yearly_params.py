import argparse
from pathlib import Path

from bcnexus.clews import schema
from bcnexus.clews import model_structure as clews_const
from bcnexus import utils

region=next(iter(clews_const.Regions)) #gets the first key of the dictionary i.e. 'REGION1'
clews_snapshot=clews_const.snapshot
start_year=clews_snapshot['start']
last_year=clews_snapshot['end']
# Constants for file paths
DATA_DIR = Path('data/clews_data/inputs_csv')

FILES = {
    'total_max_capacity': DATA_DIR / 'TotalAnnualMaxCapacity.csv',
    'residual_capacity': DATA_DIR / 'ResidualCapacity.csv',
    'operational_life': DATA_DIR / 'OperationalLife.csv',
    'operational_life_storage': DATA_DIR / 'OperationalLifeStorage.csv',
    'capital_cost': DATA_DIR / 'CapitalCost.csv',
    'availability_factor': DATA_DIR / 'AvailabilityFactor.csv',
    'capital_cost_storage': DATA_DIR / 'CapitalCostStorage.csv',
    'technology_to_storage': DATA_DIR / 'TechnologyToStorage.csv',
    'technology_from_storage': DATA_DIR / 'TechnologyFromStorage.csv',
}

def get_committed_sites(committed_sites_dict:dict[list])->list:
    # get the committed sites
    committed_sites_list: list = []

    for k_tech in committed_sites_dict.keys():
        sites:list[list]=committed_sites_dict[k_tech]
        for site in sites:
            committed_sites_list.append(site[0])
    return committed_sites_list

def update_TotalAnnualMaxCapacity(
    clews_builder_config:dict,
):
    
    # get the committed sites
    committed_sites = get_committed_sites(committed_sites_dict=clews_const.committed_sites)

    ### UPDATE RESIDUAL CAPACITY
    ##################################################################################################
    utils.print_update(level=3,message="Updating TOTAL ANNUAL MAX CAPACITY...")
    total_max_capacity_file = FILES['total_max_capacity'] # config['FILES']['residual_capacity_file']
    techs = clews_builder_config['TECHNOLOGIES']
    
    df_filtered = schema.delete_technologies(total_max_capacity_file, techs)

    # Add the new technologies
    for category, tech_details in techs.items():
        for tech_key, tech_info in tech_details.items():
            
            if not tech_info:  # Check if the value is an empty dictionary
                utils.print_update(level=4,message=f"Disregarding {tech_key} as it is empty")
                continue
            
            tech_actual_name = tech_info.get('name', {})
            if tech_actual_name in committed_sites:
                pass  # Skip committed sites
            else:
                 df_filtered = schema.add_technologies_max_cap(df_filtered, tech_key, tech_info, start_year, last_year, region)
            
    # Save the file with updated technologies
    df_filtered.to_csv(total_max_capacity_file, index=False)
    utils.print_update(level=4, message=f"File Updated: {total_max_capacity_file}")
    # return df_filtered

def update_residual_capacity(
    clews_builder_config:dict,
):
    ### UPDATE RESIDUAL CAPACITY
    ##################################################################################################
    utils.print_update(level=3,message="Updating RESIDUAL CAPACITY...")
    residual_capacity_file = FILES['residual_capacity'] # config['FILES']['residual_capacity_file']
    techs = clews_builder_config['TECHNOLOGIES']


    df_filtered = schema.delete_technologies(residual_capacity_file, techs)

    # Add the new technologies
    for category, tech_details in techs.items():
        for tech_key, tech_info in tech_details.items():
            if not tech_info:  # Check if the value is an empty dictionary
                utils.print_update(level=4,message=f"Disregarding {tech_key} as it is empty")
                continue
            df_filtered = schema.add_technologies_residual_cap(df_filtered, tech_key, tech_info, start_year, last_year, region)
            
    # Save the file with updated technologies
    df_filtered.to_csv(residual_capacity_file, index=False)

    utils.print_update(level=4, message=f"File updated: {residual_capacity_file}")
    
def update_operational_life(

    clews_builder_config:dict,
):

    ### UPDATE OPERATIONAL LIFE
    #################################################################################################
    utils.print_update(level=3,message="Updating OPERATIONAL LIFE...")
    operational_life_file = FILES['operational_life']
    
    techs = clews_builder_config['TECHNOLOGIES']
    storage_techs = clews_builder_config['STORAGE_TECHNOLOGY']


    # Delete technologies based on TECHS
    df_filtered = schema.delete_technologies(operational_life_file, techs)

    # Delete storage technologies based on STORAGE_TECHNOLOGY
    df_filtered = schema.delete_technologies(df_filtered, storage_techs)

    #Add the new technologies
    for category, tech_details in techs.items():
        for tech_key, tech_info in tech_details.items():
            if not tech_info:  # Check if the value is an empty dictionary
                utils.print_update(level=4,message=f"Disregarding {tech_key} as it is empty")
                continue
            # Process the non-empty tech_info
            df_filtered = schema.add_technologies_operational_life(df_filtered, tech_key, tech_info, region)

    # Add the storage technologies
    for storage_key, storage_info in storage_techs.items():
        df_filtered = schema.add_technologies_operational_life(df_filtered, storage_key, storage_info, region)

    # Save the file with updated technologies
    df_filtered.to_csv(operational_life_file, index=False)

    utils.print_update(level=4, message=f"File updated: {operational_life_file}")

def update_operational_life_storage(
   
    clews_builder_config:dict,
):

    ### UPDATE OPERATIONAL LIFE STORAGE
    ##################################################################################################
    operational_life_storage_file = FILES['operational_life_storage']
    storage = clews_builder_config['STORAGE']


    df_filtered = schema.delete_technologies(operational_life_storage_file, storage, 'STORAGE')

    #Add the new storage
    for storage_key, storage_info in storage.items():
        if not storage_info:  # Check if the value is an empty dictionary
                utils.print_update(level=4,message=f"Disregarding {storage_key} as it is empty")
                continue
        df_filtered = schema.add_technologies_operational_life(df_filtered, storage_key, storage_info, region, 'STORAGE', 'operational_life_storage')

    # Save the file with updated technologies
    df_filtered.to_csv(operational_life_storage_file, index=False)

    utils.print_update(level=4, message=f"File Updated : {operational_life_storage_file}")
    
def update_capex(
   
    clews_builder_config:dict,
):

    
    ### UPDATE CAPITAL COST
    ##################################################################################################
    utils.print_update(level=3,message="Updating CAPITAL COST...")
    capital_cost_file = FILES['capital_cost'] #config['FILES']['capital_cost_file']
    
    techs = clews_builder_config['TECHNOLOGIES']
    storage_techs = clews_builder_config['STORAGE_TECHNOLOGY']
    
    # Delete technologies based on TECHS
    df_filtered = schema.delete_technologies(capital_cost_file, techs)

    # Delete storage technologies based on STORAGE_TECHNOLOGY
    df_filtered = schema.delete_technologies(df_filtered, storage_techs)

    # Add the new technologies
    for category, tech_details in techs.items():
        for tech_key, tech_info in tech_details.items():
            if not tech_info:  # Check if the value is an empty dictionary
                utils.print_update(level=4,message=f"Disregarding {tech_key} as it is empty")
                continue
            df_filtered = schema.add_technologies_capital_cost(df_filtered, tech_key, tech_info, start_year, last_year, region)

    # Add the storage technologies
    for storage_key, storage_info in storage_techs.items():
        df_filtered = schema.add_technologies_capital_cost(df_filtered, storage_key, storage_info, start_year, last_year, region)

    # Save the file with updated technologies
    df_filtered.to_csv(capital_cost_file, index=False)

    utils.print_update(level=4, message=f"updated: {capital_cost_file}")

def update_availability_factor(
   
    clews_builder_config:dict,
):

    ### UPDATE AVAILABILITY FACTOR
    ##################################################################################################
    utils.print_update(level=3,message="Updating AVAILABILITY FACTOR...")
    availability_factor_file = FILES['availability_factor'] # config['FILES']['availability_factor_file']
    techs = clews_builder_config['TECHNOLOGIES']
    
    # Delete technologies based on TECHS
    df_filtered = schema.delete_technologies(availability_factor_file, techs)

    # Add the new technologies
    for category, tech_details in techs.items():
        for tech_key, tech_info in tech_details.items():
            if not tech_info:  # Check if the value is an empty dictionary
                utils.print_update(level=4,message=f"Disregarding {tech_key} as it is empty")
                continue
            df_filtered = schema.add_technologies_availability_factor(df_filtered, tech_key, tech_info, start_year, last_year, region)

    # Save the file with updated technologies
    df_filtered.to_csv(availability_factor_file, index=False)

    utils.print_update(level=4, message=f"updated: {availability_factor_file}")

def update_capex_storage(
   
    clews_builder_config:dict,
):
    
    ### UPDATE CAPITAL COST STORAGE
    ##################################################################################################
    capital_cost_storage_file = FILES['capital_cost_storage']
    storage = clews_builder_config['STORAGE']
    
    df_filtered = schema.delete_technologies(capital_cost_storage_file, storage, 'STORAGE')

    #Add the new storage
    for storage_key, storage_info in storage.items():
        if not storage_info:  # Check if the value is an empty dictionary
                utils.print_update(level=4,message=f"Disregarding {storage_key} as it is empty")
                continue
        df_filtered = schema.add_technologies_capital_cost(df_filtered, storage_key, storage_info, start_year, last_year, region, 'STORAGE', 'capital_cost_storage')
    # Save the file with updated technologies
    df_filtered.to_csv(capital_cost_storage_file, index=False)

    utils.print_update(level=4, message=f"updated: {capital_cost_storage_file}")

def update_technology_from_to_storage(
    clews_builder_config:dict,
):
    
    ### UPDATE TECHNOLOGY TO STORAGE
    ##################################################################################################
    utils.print_update(level=3,message="Updating TECHNOLOGY FROM STORAGE...")
    technology_to_storage_file = FILES['technology_to_storage']#config['FILES']['technology_to_storage_file']
    
    storage = clews_builder_config['STORAGE']

    df_filtered = schema.delete_technologies(technology_to_storage_file, storage, 'STORAGE')

    #Add the new storage
    for storage_key, storage_info in storage.items():
        if not storage_info:  # Check if the value is an empty dictionary
            utils.print_update(level=4,message=f"Disregarding {storage_key} as it is empty")
            continue
        df_filtered = schema.add_technology_to_and_from_storage(df_filtered, storage_key, storage_info, region, operation_type='TO')

    # Save the file with updated technologies
    df_filtered.to_csv(technology_to_storage_file, index=False)

    utils.print_update(level=4, message=f"updated: {technology_to_storage_file}")

    ### UPDATE TECHNOLOGY FROM STORAGE
    ##################################################################################################
    technology_from_storage_file = Path ('data/clews_data/inputs_csv/TechnologyFromStorage.csv') #config['FILES']['technology_from_storage_file']

    df_filtered = schema.delete_technologies(technology_from_storage_file, storage, 'STORAGE')

    #Add the new storage
    for storage_key, storage_info in storage.items():
        if not storage_info:  # Check if the value is an empty dictionary
            utils.print_update(level=4,message=f"Disregarding {storage_key} as it is empty")
            continue
        df_filtered = schema.add_technology_to_and_from_storage(df_filtered, storage_key, storage_info, region, operation_type='FROM')

    technology_from_storage_out = Path ('data/clews_data/inputs_csv/TechnologyFromStorage.csv')
    # Save the file with updated technologies
    df_filtered.to_csv(technology_from_storage_out, index=False)

    utils.print_update(level=4, message=f"updated : {technology_from_storage_out}")

def main(
   
    clews_builder_config:dict
):
    
    #step 5: update RESIDUAL CAPACITY
    # update_residual_capacity(clews_builder_config) # the data is already updated in the template file
    
    #step 6: Update OPERATIONAL LIFE
    update_operational_life(clews_builder_config)
    update_operational_life_storage(clews_builder_config)

    #step 7: Update AVAILABILITY FACTOR
    update_availability_factor(clews_builder_config)
    
    #step 8: Update CAPEX
    update_capex(clews_builder_config)
    update_capex_storage(clews_builder_config)

    #step 9: Update TECHNOLOGY from/to STORAGE
    update_technology_from_to_storage(clews_builder_config)
    
    #step 10: Update TOTAL ANNUAL MAX CAP
    update_TotalAnnualMaxCapacity(clews_builder_config)
    
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