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
    Updates and extends the IAR/OAR lists for livestock-related technologies.

    Args:
        IARList_existing (list): Existing IAR entries; extended in place.
        OARList_existing (list): Existing OAR entries; extended in place.
        livestock_sets (dict): {'TECHNOLOGY': [...], 'FUEL': [...]} for livestock.
        source_land_tech (str): Technology supplying land to livestock.

    Returns:
        tuple: (IARlist_updated, OARlist_updated)

    Note:
        The de-duplication sets are SEEDED FROM THE EXISTING LISTS. Without
        this, the land-supply block re-emits keys the main builder already
        wrote (e.g. (REGION1, PWRBCWB01, ELCB01, 1, 2021)) and GLPK aborts
        with "OutputActivityRatio[...] already defined". Relies on the global
        `model_structure` for regions, land regions, modes and yield factors.
    """

    IARList_new = []
    OARList_new = []

    # seed with what already exists so livestock never re-defines a key
    seen_oar = {tuple(e['c']) for e in OARList_existing}
    seen_iar = {tuple(e['c']) for e in IARList_existing}

    skipped_oar = skipped_iar = 0

    for region in model_structure.Regions.keys():
        for tech in livestock_sets.get('TECHNOLOGY'):
            for fuel in livestock_sets.get('FUEL'):

                # OAR: livestock produce
                if fuel[-3:] in model_structure.LivestockYieldFactors.keys():
                    for mode in model_structure.LivestockProduce_Modes.keys():
                        for year_iter in range(model_structure.snapshot['start'],
                                               model_structure.snapshot['start'] + 1):
                            key = (region, tech, fuel,
                                   model_structure.LivestockProduce_Modes.get(fuel[-3:]),
                                   year_iter)
                            if key in seen_oar:
                                skipped_oar += 1
                                continue
                            OARList_new.append({
                                'c': list(key),
                                'v': model_structure.LivestockYieldFactors.get(fuel[-3:], 1)
                            })
                            seen_oar.add(key)

                # OAR & IAR: land supply to livestock
                if fuel[-3:] in model_structure.LandRegions:
                    for year_iter in range(model_structure.snapshot['start'],
                                           model_structure.snapshot['start'] + 1):
                        tech_land = source_land_tech
                        mode = 1
                        key = (region, tech_land, fuel, mode, year_iter)

                        if key in seen_oar:
                            skipped_oar += 1
                        else:
                            OARList_new.append({'c': list(key), 'v': 1})
                            seen_oar.add(key)

                        if key in seen_iar:
                            skipped_iar += 1
                        else:
                            IARList_new.append({'c': list(key), 'v': 1})
                            seen_iar.add(key)

    OARList_existing.extend(OARList_new)
    IARList_existing.extend(IARList_new)

    utils.print_update(
        level=print_level_base,
        message=(f"Livestock Ratios updated: +{len(OARList_new)} OAR, "
                 f"+{len(IARList_new)} IAR "
                 f"(skipped {skipped_oar} OAR / {skipped_iar} IAR already defined)."))

    return IARList_existing, OARList_existing

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
    
    for mode in missing_modes:
        key = next(k for k, v in new_modes_dict.items() if str(v) == str(mode))
        
        mode_dir = Path('data/clews_data/SETs')
        mode_dir.mkdir(parents=True, exist_ok=True)
        
        with open(mode_dir / 'ModeList.txt', 'a') as ModeFile:
                ModeFile.write(f"{mode}: Livestock produce {model_structure.LivestockProduce[key]}\n")

def main(source_land_tech:str=None,
         csv_save_to:str|Path='data/clews_data/SETs'):
    
    '''
    # 1.1

    # - Load the Sets,Ratios Builder module (functionality of _clewsy_)
    # - Create the Standard CLEWs Sets,Ratios 
    '''
    SetNames, NewSetItems, IARList, OARList,ModeList=SnR.BuildCLEWsModel()

    
    #1.2: Create Sets (FUEL, TECHNOLOGY) from Model structure 
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