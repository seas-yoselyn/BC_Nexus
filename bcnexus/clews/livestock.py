''' 
# Goal
 - Create New sets, ratios using clewsy (ideally) or use the equivalent script in BCNexus i.e. (sets_n_ratios.py)
'''

from bcnexus.clews import sets_n_ratios as SnR
from bcnexus.clews import model_structure
from bcnexus import utils
from pathlib import Path
import pandas as pd

print_level_base=2
'''
# Step 1

# - Load the Sets,Ratios Builder module (functionality of _clewsy_)
# - Create the Standard CLEWs Sets,Ratios 
'''
SetNames, NewSetItems, IARList, OARList=SnR.BuildCLEWsModel()

'''
# Step 2
    - Prepare the Livestock Sets (already defined in Model Structure)
'''

def get_Livestock_SETs(model_structure:dict=model_structure)->dict:
    """
    Generates and returns dictionaries of livestock-related technologies and fuels for each land region and livestock produce item.
    This function iterates over all land regions and livestock produce items defined in the `model_structure` module. It creates:
      - Technology identifiers and names for land used in livestock production, distinguishing between meat and non-meat produce.
      - Fuel identifiers and names for both produce and land supply associated with livestock.
    Returns:
        dict: A dictionary with two keys:
            - 'TECHNOLOGY': A dictionary mapping technology codes to descriptive names for livestock land use.
            - 'FUEL': A dictionary mapping fuel codes to descriptive names for livestock produce and land supply.
    Side Effects:
        Prints status updates using the `utils.print_update` function at different verbosity levels.
    """
    
    livestock_code=model_structure.Livestock_code
    livestock_techs = {}
    livestock_fuels={}
    
    utils.print_update(level=print_level_base,message="Creating Livestock Technologies and Fuels from model structure....")
    
    for land_region in  model_structure.LandRegions:
        
        for produce_item in model_structure.LivestockProduce.keys():
            
                livestock_produce_fuel=livestock_code+produce_item
                livestock_produce_fuel_name=f'Fuel (Produce) from Livestock {model_structure.LivestockProduce.get(produce_item,"")} in Land region {land_region}'
                livestock_fuels[livestock_produce_fuel]=livestock_produce_fuel_name
                
                if produce_item in model_structure.LivestockProduceMeats:
                    meat_type = produce_item
                    
                    for pasture_type in model_structure.MeatPastureTypeList:
                        livestock_land_tech = 'LND' + livestock_code + meat_type + pasture_type+land_region
                        livestock_techs_name= f'Land for Livestock {model_structure.LivestockProduce.get(produce_item,"")} meat ({model_structure.MeatPastureTypeList[pasture_type]}) in Land region {land_region}'
                        livestock_land_fuel='L' + meat_type + pasture_type+land_region
                        livestock_land_fuel_name=f' Fuel (Land supply) to produce Livestock {model_structure.LivestockProduce.get(produce_item,"")} meat ({model_structure.MeatPastureTypeList[pasture_type]}) in Land region {land_region}'
                        
                        livestock_techs[livestock_land_tech] = livestock_techs_name
                        livestock_fuels[livestock_land_fuel]=livestock_land_fuel_name

                else:
                    livestock_land_tech = 'LND' + livestock_code + produce_item+land_region
                    livestock_land_tech_name=f'Land for Livestock {model_structure.LivestockProduce.get(produce_item,"")} in Land region {land_region}'
                    livestock_techs[livestock_land_tech] = livestock_land_tech_name
                    
                    livestock_land_fuel='L' + produce_item+land_region
                    livestock_land_fuel_name=f' Fuel (Land supply) to produce Livestock {model_structure.LivestockProduce.get(produce_item,"")} in Land region {land_region}'
                    livestock_fuels[livestock_land_fuel]=livestock_land_fuel_name

    utils.print_update(level=print_level_base+1,message="Livestock Technologies and Fuels Created.")
    
    livestock_sets:dict={
        'TECHNOLOGY':livestock_techs,
        'FUEL':livestock_fuels
    }
    return livestock_sets

def update_SetItems_with_Livestock(SetNames:list,
                                    NewSetItems:list,
                                    livestock_sets:dict):
    """
    Updates the provided list of set items with new livestock set items.
    Args:
        SetNames (list): A list of set names corresponding to livestock sets.
        NewSetItems (list): A list of lists, where each sublist contains items for a set in SetNames.
        livestock_sets (dict): A dictionary where keys are set names and values are dictionaries mapping livestock item keys to their names. Expected keys 'TECHNOLOGY','FUEL'
    Returns:
        list: The updated NewSetItems list with new livestock items added to the appropriate sets.
    Notes:
        - Each new livestock item is represented as a dictionary with 'value', 'name', and a default 'color' key.
        - The function assumes that each set name in livestock_sets exists in SetNames.
    """

    utils.print_update(level=print_level_base,message="Creating Livestock SETs....")
    
    # Create new list items from livestock_sets
    new_livestock_dicts = []
    for set in livestock_sets.keys():
        utils.print_update(level=print_level_base+1,message=f"updating Livestock SET : '{set}'")
        livestock_set=livestock_sets[set]
        for key,value in livestock_set.items():
            new_livestock_dicts.append({
                'value': key,
                'name': value,
                'color': '#000000'
            })

        NewSetItems[SetNames.index(set)].extend(new_livestock_dicts)
        
    utils.print_update(level=print_level_base+1,message="Livestock SETs updated.")
    
    return NewSetItems

def update_IARlist(
                   IARList_existing:list,
                   OARList_existing:list,
                   livestock_sets:dict,
                   source_land_tech:str,
                   ):
    """
    Updates and extends the IAR (Input Activity Ratio) and OAR (Output Activity Ratio) lists for livestock-related technologies.
    This function iterates over regions, technologies, and fuels defined in the provided livestock sets and model structure.
    It generates new entries for IAR and OAR lists based on livestock yield factors and land regions, and appends them to the existing lists.
    Args:
        IARList_existing (list): Existing list of IAR entries to be updated.
        OARList_existing (list): Existing list of OAR entries to be updated.
        livestock_sets (dict): Dictionary containing sets of 'TECHNOLOGY' and 'FUEL' relevant to livestock.
        source_land_tech (str, optional): Technology identifier to use for land supply entries.
    Returns:
        tuple: A tuple containing:
            - IARlist_updated (list): The updated IAR list including new entries.
            - OARlist_updated (list): The updated OAR list including new entries.
    Note:
        - This function relies on the global `model_structure` object for region, technology, fuel, and mode definitions.
        - The function modifies the input lists in place and also returns them for convenience.
    """
    
    IARList_new = []
    OARList_new=[]

    for region in model_structure.Regions.keys():
        for tech in livestock_sets.get('TECHNOLOGY'):
            for fuel in livestock_sets.get('FUEL'):
                if fuel[-3:] in model_structure.LivestockYieldFactors.keys(): # produce supply
                    for mode in model_structure.LivestockProduce_Modes.keys(): # produce supply
                        for year_iter in range(model_structure.snapshot['start'], model_structure.snapshot['start']+1 ): # +1
                            entry = {
                                'c': [region, tech, fuel, model_structure.LivestockProduce_Modes.get(fuel[-3:]), year_iter],
                                'v': model_structure.LivestockYieldFactors.get(fuel[-3:], 1)
                            }
                            OARList_new.append(entry)
                            
                if fuel[-3:] in model_structure.LandRegions:  # Land Supply
                    for year_iter in range(model_structure.snapshot['start'], model_structure.snapshot['start']+1): # +1
                        tech = source_land_tech
                        mode = 1
                        entry = {
                            'c': [region, tech, fuel, mode, year_iter],
                            'v': 1
                        }
                        OARList_new.append(entry)
                        IARList_new.append(entry)
                            
                            
    # IARList_updated=IARList_existing.extend(IARList_new)
    OARList_existing.extend(OARList_new)
    OARlist_updated=OARList_existing
    
    IARList_existing.extend(IARList_new)
    IARlist_updated=IARList_existing
    IARlist_updated=IARList_existing
    utils.print_update(level=print_level_base,message="Livestock Ratios updated.")
    return IARlist_updated,OARlist_updated

def update_mode_of_operation_csv(source_csv_files_path:str|Path, 
                                 new_modes_dict):
    """
    Ensures all modes from `new_modes_dict` are present in the CSV at `csv_path`.
    Adds any missing modes and saves the updated CSV.
    """
    utils.print_update(level=print_level_base+1,message= f"Checking MODE_OF_OPERATIONS at {source_csv_files_path}")
    source_csv_files_path=Path(source_csv_files_path)
    mop_existing_file=source_csv_files_path/'MODE_OF_OPERATION.csv'
    
    # Load existing modes from CSV
    existing_df = pd.read_csv(mop_existing_file, usecols=['VALUE'])
    existing_modes = set(existing_df['VALUE'].astype(str))

    # Get new modes from the model structure
    new_modes = set(map(str, new_modes_dict.values()))
    # Find and append missing modes
    missing_modes = new_modes - existing_modes
    if missing_modes:        
        utils.print_update(level=print_level_base+2,message="Updating MODE_OF_OPERATIONS ...")
        updated_df = pd.concat([existing_df, pd.DataFrame({'VALUE': list(missing_modes)})], ignore_index=True)
        updated_df.to_csv(mop_existing_file, index=False)
        utils.print_update(level=print_level_base+2,message= f"Added {len(missing_modes)} new modes to {mop_existing_file}")
    else:
        utils.print_update(level=print_level_base+2,message="No new modes to add.")

def main(source_land_tech:str=None,
         csv_save_to:str|Path='data/clews_data/SETs_and_Ratios'):
    
    #1: Create Sets (FUEL, TECHNOLOGY) from Model structure 
    livestock_sets=get_Livestock_SETs()
    
    #2.1: Update (append) the Livestock Sets to the existing ones
    NewSetItems_updated=update_SetItems_with_Livestock(SetNames,NewSetItems,livestock_sets)

    ratios_update_args={
        'IARList_existing': IARList,
        'OARList_existing': OARList,
        'livestock_sets': livestock_sets,
        'source_land_tech': 'LNDALFHIBC1' if source_land_tech is None else source_land_tech
    }
    
    #2.2: Update (append) the Livestock related Ratios to the existing ones
    IARlist_updated,OARlist_updated=update_IARlist(**ratios_update_args)

    write_to_csvs_args={
        'SetNames': SetNames,
    'NewSetItems': NewSetItems_updated,
    'IARList': IARlist_updated,
    'OARList': OARlist_updated,
    'csv_save_to': Path(csv_save_to)
    }

    #3 - Write the Sets, Ratios to CSV files in Defined Directory
    SnR.UpdateSETS(**write_to_csvs_args) # This will create a MODE_OF_OPERATION, excluding livestock associated ones, as we handled it separately
    
    #4 - Check the MODE_OF_OPERATION in the created CSV files and update
    update_mode_of_operation_csv(write_to_csvs_args['csv_save_to'], 
                                 model_structure.LivestockProduce_Modes)

if __name__ == "__main__":
    main()