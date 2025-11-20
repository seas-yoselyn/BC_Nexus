import os
import decimal
import colorama

#Local packages
from bcnexus import utils
from bcnexus.clews import builder, model_structure as clews_const
from pathlib import Path
import pandas as pd

PRINT_LEVEL_BASE:int=2    # Handle print levels

# Tailored for BC Combined Model
# Refactoring (C) M Elias Islam (EL), 2024

""" 
Creates the SETS, FUELS and COMMODITIES in MoManI for the energy sector and the land use (from clustered AEZ data).
Original concept and script (C) Taco Niet 2019

"""

def UpdateSETS(SetNames:list, 
                 NewSetItems:list, 
                 IARList:list, 
                 OARList:list, 
                 csv_save_to:str):
    
    csv_save_to = Path(csv_save_to)
    csv_save_to.mkdir(parents=True, exist_ok=True)
    
    utils.print_update(level=PRINT_LEVEL_BASE,message=f"Writing SETs to {csv_save_to}")
    
    # Output the sets for otoole:
    for SetName in SetNames:
        set_file = csv_save_to / f"{SetName}.csv"
        utils.print_update(level=PRINT_LEVEL_BASE+1,message=f"Writing {SetName} to {set_file}")
        with set_file.open('w') as f:
            f.write('VALUE\n')
            for items in NewSetItems[SetNames.index(SetName)]:
                f.write(str(items['value']) + '\n')

    # And output the IAR for otoole:
    iar_file = csv_save_to / 'InputActivityRatio.csv'
    utils.print_update(level=PRINT_LEVEL_BASE+1,message=f"Writing Input Activity Ratios to {iar_file}")
    with iar_file.open('w') as f:
        f.write('REGION,TECHNOLOGY,FUEL,MODE_OF_OPERATION,YEAR,VALUE\n')
        for item in IARList:
            f.write(','.join(map(str, item['c'])) + ',' + str(item['v']) + '\n')

    # And output the OAR for otoole:
    oar_file = csv_save_to / 'OutputActivityRatio.csv'
    utils.print_update(level=PRINT_LEVEL_BASE+1,message=f"Writing Output Activity Ratios to {oar_file}")
    
    with oar_file.open('w') as f:
        f.write('REGION,TECHNOLOGY,FUEL,MODE_OF_OPERATION,YEAR,VALUE\n')
        for item in OARList:
            f.write(','.join(map(str, item['c'])) + ',' + str(item['v']) + '\n')
            
    # mop_file = csv_save_to / 'MODE_OF_OPERATION.csv'


# create_set in BuildCLEWsModel.py
def create_set(set_names, new_SetItems, new_setGroups, sets):
    set_names.append(sets)
    new_SetItems.append([])
    new_setGroups.append([])    
        
# func1 in BuildCLEWsModel.py
def AddActivityListItems(year1, 
                         region, 
                         input1, 
                         input2, 
                         List, 
                         value = None, 
                         g = "1", 
                         v = "1"): 
    """
    ## Args:
        - Year1, 
        - region, 
        - input1 : power plant name and discription
        - input2 : input fuel
        - List : input/output activity ratio; 
        - value = None, 
        - g = "1", 
        - v = "1" 
 
    """   
    for year in year1:
        Sets = [region, input1, input2, g, year]
        Value = value if value is not None else v
        Item = {"c": Sets, "v": Value}
        List.append(Item)
        
def Fill_Set(new_set_items, set_names, sets, value1, color1, name1 = '', t = "name"):
    new_set_items[set_names.index(sets)].append(\
    {"value": value1, t: name1, "color": color1})
    
def get_powerplants():
    updated_resources=utils.load_config(clews_const.clews_builder_cfg_path)
    updated_TECHNOLOGIES=updated_resources['TECHNOLOGIES']
    _PowerPlants_=clews_const.PowerPlants
    PowerPlants = {}

    for resource_type,tech_info in updated_TECHNOLOGIES.items():
        if resource_type=='INFLOW' or resource_type=='CCS' or resource_type=='HDG':    # Handled differently
            pass
        else:
            for tech_id,schema in tech_info.items():
                PowerPlants[tech_id] = _PowerPlants_[f'{resource_type}B']

    return PowerPlants

def get_storage()->dict:
    updated_resources=utils.load_config(clews_const.clews_builder_cfg_path)
    updated_STORAGE:dict=updated_resources['STORAGE']
    storage_techs = {}

    for storage_type,tech_info in updated_STORAGE.items():
        storage_techs[storage_type] = updated_STORAGE[storage_type]

    return storage_techs

def get_transformation_techs_power():
    _TransformationTechnologies_=clews_const.TransformationTechnologies
    updated_resources=utils.load_config(clews_const.clews_builder_cfg_path)
    updated_TECHNOLOGIES=updated_resources['TECHNOLOGIES']

    # Create a separate list for items starting with 'PWR'
    pwr_list = [item for item in _TransformationTechnologies_ if item[0][:3] == 'PWR' and not item[0][:6] == 'PWRTRN']
    # lnd_list = [item for item in _TransformationTechnologies_ if item[0][:3] == 'LND']
    trn_list=[item for item in _TransformationTechnologies_ if item[0][:6] == 'PWRTRN']
    
    updated_pwr_list=[]
    for resource_type,tech_info in updated_TECHNOLOGIES.items():
            if resource_type=='INFLOW':
                pass
            else:
                for tech_id,schema in tech_info.items():
                    # Extract the base ID from the updated item (e.g., 'PWRNGSB' from 'PWRNGSB01')
                    base_id = tech_id[:-2]
                    # Find the matching entry in the original list
                    matching_tech= next((item for item in pwr_list if item[0] == base_id), None)
                    if matching_tech:
                        # Replace the base ID with the updated item
                        updated_entry = [tech_id] + matching_tech[1:]
                        updated_pwr_list.append(updated_entry)

    complete_list= updated_pwr_list + trn_list
                
    return complete_list
                
def BuildCLEWsModel():

    colorama.init()
    # create a decimal context
    ctx = decimal.Context()
    # Set to 4 Sig Figs for MoManI speed
    ctx.prec = 2
    
    # Unpacking variables

    Model = clews_const.Model # Arbitary Model Name
    
    LandToGridMap = clews_const.LandToGridMap
    LandCluster_data=clews_const.LandCluster_data
    TransformationTechnologies:dict = get_transformation_techs_power()
    LandUseIntensity=clews_const.LandUseIntensity_FUEL
    CarbonCaptureFuels=clews_const.CarbonCaptureFuels
  
    ImportFuels:dict = clews_const.ImportFuels
    DomesticMining :dict= clews_const.DomesticMining
    DomesticRenewables :dict= clews_const.DomesticRenewables
    ExportFuels :dict= clews_const.ExportFuels
    LandRegions:dict = clews_const.LandRegions
    
    LandCluster_data :dict= clews_const.LandCluster_data
    ClusterBaseFileName:dict = LandCluster_data['ClusterBaseFileName']
    PrecipitationClusterBaseFileName:dict = LandCluster_data['PrecipitationClusterBaseFileName']
    EvapotranspirationClusterBaseFileName :dict= LandCluster_data['EvapotranspirationClusterBaseFileName']
    IrrigationWaterDeficitClusterBaseFileName :dict= LandCluster_data['IrrigationWaterDeficitClusterBaseFileName']
    
    
    IrrigationTypeList : dict= clews_const.IrrigationTypeList
    IntensityList= clews_const.IntensityList
    CropYieldFactors:dict = clews_const.CropYieldFactors
    GroundwaterPercentofExcess:dict =clews_const.GroundwaterPercentofExcess
    LandUseCodes :dict= clews_const.LandUseCodes
    EvapotranspirationPercentPRCOtherLandUse :dict= clews_const.EvapotranspirationPercentPRCOtherLandUse
    GroundwaterPercentofExcessOtherLandUse :dict= clews_const.GroundwaterPercentofExcessOtherLandUse
        
    EndUseFuels=clews_const.EndUseFuels
    snapshot=clews_const.snapshot
    Years = list(range(snapshot['start'], snapshot['end'] + 1)) # EL
    Regions=clews_const.Regions
    Emissions=clews_const.Emissions
    PowerPlants=get_powerplants()
    Storages=get_storage()
    
    utils.print_update(level=PRINT_LEVEL_BASE+1,message="Checking Land Cluster Data files...")
    check_landcluster_data(LandCluster_data, clews_const.LandToGridMap)

    # ***************************** #
    # CREATE ENERGY SET INFORMATION #
    # ***************************** #

    # Create empty list for new sets
    SetNames = []
    NewSetItems = []
    NewSetGroups = []
    IARList = []
    OARList = []

    # Create set YEARS
    # First create the new set name for year and add space for groups and items for this set
    create_set(SetNames, NewSetItems, NewSetGroups, 'YEAR')
    for year in Years:
        # Cannot use the same function as other sets as YEAR does not have a 'name' field and this crashes MoManI...
        NewSetItems[SetNames.index('YEAR')].append({'value': year, 'color': '#000000'})
       
    # Create set EMISSIONS
    # First create the new set name for year and add space for groups and items for this set
    create_set(SetNames, NewSetItems, NewSetGroups, 'EMISSION')
    for emission in Emissions:
        Fill_Set(NewSetItems, SetNames, "EMISSION", emission, Emissions[emission][1], Emissions[emission][0])

    # Create set REGION
    # First create the new set name for year and add space for groups and items for this set
    create_set(SetNames, NewSetItems, NewSetGroups, 'REGION')
    
    for Region in Regions:
        Fill_Set(NewSetItems, SetNames, "REGION", Region, Regions[Region][1], Regions[Region][0])

    # Create empty set TECHNOLOGY
    create_set(SetNames, NewSetItems, NewSetGroups, 'TECHNOLOGY')

    # Create empty set FUEL
    create_set(SetNames, NewSetItems, NewSetGroups, 'FUEL') # Legacy name was "FUEL"


    # Create sectoral demand technologies, Fuels, Ip and Op Activity ratios
    for sector in EndUseFuels:
        for fuel in EndUseFuels[sector]:
            # Create the demand fuel:
            Fill_Set(NewSetItems, SetNames, "FUEL", sector + fuel, "#000000", "")
            # Create the demand technology
            Fill_Set(NewSetItems, SetNames, "TECHNOLOGY", "DEM" + sector + fuel, "#000000", "Demand technology for ")
            # Create the input fuel (if it doesn't exist)
            if not fuel in [li['value'] for li in NewSetItems[SetNames.index("FUEL")]]:
                Fill_Set(NewSetItems, SetNames, "FUEL", fuel, "#000000", "")

            # Create the input and output activity for that combination:
            AddActivityListItems(Years, Region, "DEM" + sector + fuel, sector + fuel, OARList, value = "1")
            AddActivityListItems(Years, Region, "DEM" + sector + fuel, fuel, IARList, value = "1")

    # Create powerplant technologies, Fuels, Ip and Op Activity ratios
    for powerplant in PowerPlants:
        if not powerplant[3:6] in [li['value'] for li in NewSetItems[SetNames.index("FUEL")]]:
            Fill_Set(NewSetItems, SetNames, "FUEL", powerplant[3:6], "#000000", "")
        if not "PWR" + powerplant[3:6] in [li['value'] for li in NewSetItems[SetNames.index("FUEL")]]:
            Fill_Set(NewSetItems, SetNames, "FUEL", "PWR" + powerplant[3:6], "#000000", "")

            AddActivityListItems(Years, Region, "DEMPWR" + powerplant[3:6], powerplant[3:6], IARList, value = "1")
            AddActivityListItems(Years, Region, "DEMPWR" + powerplant[3:6], "PWR" + powerplant[3:6], OARList, value = "1")
            
        if not "DEMPWR" + powerplant[3:6] in [li['value'] for li in NewSetItems[SetNames.index("TECHNOLOGY")]]:
            Fill_Set(NewSetItems, SetNames, "TECHNOLOGY", "DEMPWR" + powerplant[3:6], "#000000", "")

        # Create ELC001 commodity if not already created.  But do this per land region (using the first character of the last three digits of the power plant as the key):
        if not "ELC" + powerplant[6:7] + "01" in [li['value'] for li in NewSetItems[SetNames.index("FUEL")]]:
            Fill_Set(NewSetItems, SetNames, "FUEL", "ELC" + powerplant[6:7] + "01", "#000000", "")
        Fill_Set(NewSetItems, SetNames, "TECHNOLOGY", powerplant, "#000000", PowerPlants[powerplant][0])

        AddActivityListItems(Years, Region, powerplant, "PWR" + powerplant[3:6], IARList, value = str(PowerPlants[powerplant][1]),
                v = str(PowerPlants[powerplant][1]))
        AddActivityListItems(Years, Region, powerplant, "ELC" + powerplant[6:7] + "01", OARList, value = "1")

        # Create input surface water.
        Land2Grid= [k for k, v in LandToGridMap.items() if v == powerplant[6:7]][0]
        
        if not "DEMPWRSUR" + Land2Grid in [li['value'] for li in NewSetItems[SetNames.index("TECHNOLOGY")]]:
            Fill_Set(NewSetItems, SetNames, "TECHNOLOGY","DEMPWRSUR" + Land2Grid,
            "#000000",  "", "Surface water demand for power in " + Land2Grid)
        if not "PWRWAT" + Land2Grid in [li['value'] for li in NewSetItems[SetNames.index("FUEL")]]:
            Fill_Set(NewSetItems, SetNames, "FUEL","PWRWAT" + Land2Grid,
            "#000000",  "", "Surface water demand for power in " + Land2Grid)

            AddActivityListItems(Years, Region, "DEMPWRSUR" + Land2Grid, "WTRSUR" + Land2Grid, IARList, value = "1")
            AddActivityListItems(Years, Region, "DEMPWRSUR" + Land2Grid, "PWRWAT" + Land2Grid, OARList, value = "1")


        AddActivityListItems(Years, Region, powerplant, "PWRWAT" + Land2Grid, IARList, value = str(PowerPlants[powerplant][2]),
                v = str(PowerPlants[powerplant][2]))
        AddActivityListItems(Years, Region, powerplant, "WTRSUR" + Land2Grid, OARList, value = str(PowerPlants[powerplant][3]),
                v = str(PowerPlants[powerplant][3]))

    # Create storage technologies, Fuels, Ip and Op Activity ratios
    for storage in Storages:
        if 'BATTERY' in storage:
            # add this new TECHNOLOGY
            if storage not in [li['value'] for li in NewSetItems[SetNames.index("TECHNOLOGY")]]:
                Fill_Set(NewSetItems, SetNames, "TECHNOLOGY",Storages[storage]['technology_from_storage'], "#000000", "")
                
            AddActivityListItems(Years, Region,Storages[storage]['technology_from_storage'], 
                                "ELCB"+"02",IARList,g=str(Storages[storage]['mode_of_operation_charge']),v='1')
            
            AddActivityListItems(Years,Region,Storages[storage]['technology_to_storage'], 
                                "ELCB"+"02",OARList,g=str(Storages[storage]['mode_of_operation_discharge']),v='1') 
        if 'HYDRODAM' in storage:
            water_storage_fuel="WATER_STORAGE"+"01"
            # ADD new Fuel
            if water_storage_fuel not in [li['value'] for li in NewSetItems[SetNames.index("FUEL")]]:
                Fill_Set(NewSetItems, SetNames, "FUEL", water_storage_fuel, "#000000", "")
                
            AddActivityListItems(Years, Region,Storages[storage]['technology_from_storage'], 
                                water_storage_fuel,IARList,g=str(Storages[storage]['mode_of_operation_charge']),v='1')
            
            AddActivityListItems(Years,Region,Storages[storage]['technology_to_storage'], 
                                water_storage_fuel,OARList,g=str(Storages[storage]['mode_of_operation_charge']),v='1')
            
            AddActivityListItems(Years,Region,Storages[storage]['technology_from_storage'], 
                    water_storage_fuel,OARList,g=str(Storages[storage]['mode_of_operation_discharge']),v='1')

    
    # Create Transformation Techs
    # surface water.
    TransformationTechnologies=get_transformation_techs_power()
    
    for transformationtech in TransformationTechnologies: 
        """ Structure Description: # EL
        
        TransformationTechnologies[x]; x= 0....6
            0: 'Tech name and description',
            1: 'input fuel',
            2: 'input activity ratio: for 1PJ of output how much land will be needed',
            3: 'output fuel' - default to blank,
            4: 'output activity ratio' - default to blank,
            5: 'description' - default to blank,
            6: 'mode of operation'
            
            """

        if not transformationtech[0] in [li['value'] for li in NewSetItems[SetNames.index("TECHNOLOGY")]]:
            NewSetItems[SetNames.index("TECHNOLOGY")].append(
                {"value": transformationtech[0], "name": transformationtech[5], "color": "#000000"})

        if transformationtech[1] != '':  # 'input fuel'
            AddActivityListItems(Years, 
                                 Region, 
                                 transformationtech[0], 
                                 transformationtech[1], 
                                 IARList, 
                                 value = str(transformationtech[2]),
                                 g = transformationtech[6],
                                 v = str(transformationtech[2]))

        if transformationtech[3] != '': # 'output fuel' - default to blank,
            AddActivityListItems(Years, 
                                 Region, 
                                 transformationtech[0], 
                                 transformationtech[3], 
                                 OARList, 
                                 value = str(transformationtech[4]),
                                 g = transformationtech[6], 
                                 v = str(transformationtech[4]))



    # Create import fuels
    for fuel in ImportFuels:
        if not fuel in [li['value'] for li in NewSetItems[SetNames.index("FUEL")]]:
            utils.print_warning("\x1b[0;30;41mWarning:  Import fuel " + fuel + " created for fuel that is not used in any sector.\x1b[0m")
            Fill_Set(NewSetItems, SetNames, "FUEL", fuel, "#000000",  "")
        Fill_Set(NewSetItems, SetNames, "TECHNOLOGY", "IMP" + fuel, "#000000",  "")
        AddActivityListItems(Years, Region, "IMP" + fuel, fuel, OARList, value = "1")

    # Create domestic supply of fuels
    for fuel in DomesticMining:
        if not fuel in [li['value'] for li in NewSetItems[SetNames.index("FUEL")]]:
            utils.print_warning(
                "\x1b[0;30;41mWarning:  Mining of fuel " + fuel + " created for fuel that is not used in any sector.\x1b[0m")
            Fill_Set(NewSetItems, SetNames, "FUEL", fuel, "#000000",  "")
        Fill_Set(NewSetItems, SetNames, "TECHNOLOGY", "MIN" + fuel, "#000000",  "")
        AddActivityListItems(Years, Region, "MIN" + fuel, fuel, OARList, value = "1")

    # Create domestic supply of renewables
    for fuel in DomesticRenewables:
        if not fuel in [li['value'] for li in NewSetItems[SetNames.index("FUEL")]]:
            utils.print_warning(
                "\x1b[0;30;41mWarning:  Renewable fuel " + fuel + " created for fuel that is not used in any sector.\x1b[0m")
            Fill_Set(NewSetItems, SetNames, "FUEL", fuel, "#000000",  "")
        Fill_Set(NewSetItems, SetNames, "TECHNOLOGY", "RNW" + fuel, "#000000",  "")
        AddActivityListItems(Years, Region, "RNW" + fuel, fuel, OARList, value = "1")

    # Create export fuels
    for fuel in ExportFuels:
        if not fuel in [li['value'] for li in NewSetItems[SetNames.index("FUEL")]]:
            utils.print_warning(
                "\x1b[0;30;41mWarning:  Export fuel " + fuel + " created for fuel that is not used/produced in any sector.\x1b[0m")
            Fill_Set(NewSetItems, SetNames, "FUEL", fuel, "#000000",  "")
        Fill_Set(NewSetItems, SetNames, "TECHNOLOGY", "EXP" + fuel, "#000000",  "")
        AddActivityListItems(Years, Region, "EXP" + fuel, fuel, IARList, value = "1")


    # ******************************************** #
    # AGRICULTURAL TECHNOLOGIES, FUELS AND IAR/OAR #
    # ******************************************** #

    # Create groups for sets to track commodities, technologies
    # Don't need groups for these for agriculture - can add later if needed...
    # Make all set colour black for the time being - can change later if needed...

    CropList = {}
    CropNumber = 1
    CropComboList = {}
    ModeList = []
    ModeNumber = 1
  

    for LandRegion in LandRegions:
        
        ###############################
        # Inputs for agricultural groundwater and electricity for pumping:
        Fill_Set(NewSetItems, SetNames, "TECHNOLOGY", "DEMAGRGWT" + LandRegion, "#000000", "Agricultural groundwater supply.")
        Fill_Set(NewSetItems, SetNames, "TECHNOLOGY", "DEMAGRSUR" + LandRegion, "#000000", "Agricultural groundwater supply.")
        Fill_Set(NewSetItems, SetNames, "FUEL", "AGRWAT" + LandRegion, "#000000", "Agricultural water for irrigation.")
        Fill_Set(NewSetItems, SetNames, "FUEL", "WTREVT" + LandRegion, "#000000", "Water lost to evapotranspiration.")
        Fill_Set(NewSetItems, SetNames, "FUEL", "WTRGRC" + LandRegion, "#000000", "Water lost to evapotranspiration.")
        Fill_Set(NewSetItems, SetNames, "TECHNOLOGY", "DEMPUBGWT" + LandRegion, "#000000", "Agricultural water for irrigation.")
        Fill_Set(NewSetItems, SetNames, "TECHNOLOGY", "DEMPUBSUR" + LandRegion, "#000000", "Agricultural water for irrigation.")
        Fill_Set(NewSetItems, SetNames, "FUEL", "PUBWAT" + LandRegion, "#000000", "Water lost to evapotranspiration.")

        # Creation of agricultural water supply from grownwater
        # 1.73 number taken from Bolivia - Should be 0.0173
        
        if 'AGR' in EndUseFuels.keys():
            # NEED TO ADJUST THE IAR TO MATCH THE CORRECT VALUE FOR THE DEMAGRGWT...
            AddActivityListItems(Years, Region, "DEMAGRGWT" + LandRegion, "AGRELC" + LandToGridMap[LandRegion] + "02", IARList, value = "0.0173",
                    v = "0.0173")

        # for year in Years:
        # Sets = [Region, "DEMAGRGWT"+LandRegion, "WTRGWT"+LandRegion, "1", year]
        # Value = "1"
        # Item = {"c":Sets, "v":Value}
        # IARList.append(Item)
        AddActivityListItems(Years, Region, "DEMAGRGWT" + LandRegion, "AGRWAT" + LandRegion, OARList, value = "1")

        # Creation of agricultural water supply from surface water
        # for year in Years:
        # Sets = [Region, "DEMAGRSUR"+LandRegion, "AGRELC"+LandToGridMap[LandRegion], "1", year]
        # Value = "0.0173"
        # # 1.73 number taken from Bolivia
        # # NEED TO ADJUST THE IAR TO MATCH THE CORRECT VALUE FOR THE DEMAGRGWT...
        # Item = {"c":Sets, "v":Value}
        # IARList.append(Item)
        AddActivityListItems(Years, Region, "DEMAGRSUR" + LandRegion, "WTRSUR" + LandRegion, IARList, value = "1")
        AddActivityListItems(Years, Region, "DEMAGRSUR" + LandRegion, "AGRWAT" + LandRegion, OARList, value = "1")


        # Creation of public water supply from surface water
        # for year in Years:
        # Sets = [Region, "DEMPUBSUR"+LandRegion, "COMELC"+LandToGridMap[LandRegion], "1", year]
        # Value = "0.0173"
        # # 1.73 number taken from Bolivia
        # # NEED TO ADJUST THE IAR TO MATCH THE CORRECT VALUE FOR THE DEMAGRGWT...
        # Item = {"c":Sets, "v":Value}
        # IARList.append(Item)
        AddActivityListItems(Years, Region, "DEMPUBSUR" + LandRegion, "WTRSUR" + LandRegion, IARList, value = "1")
        AddActivityListItems(Years, Region, "DEMPUBSUR" + LandRegion, "PUBWAT" + LandRegion, OARList, value = "1")

        # Creation of public water supply from groundwater water
        # 1.73 number taken from Bolivia
        # NEED TO ADJUST THE IAR TO MATCH THE CORRECT VALUE FOR THE DEMAGRGWT...
        AddActivityListItems(Years, Region, "DEMPUBGWT" + LandRegion, "COMELC" + LandToGridMap[LandRegion] + "02", IARList, value = "0.0173",
                v = "0.0173")

        # for year in Years:
        # Sets = [Region, "DEMPUBGWT"+LandRegion, "WTRGWT"+LandRegion, "1", year]
        # Value = "1"
        # Item = {"c":Sets, "v":Value}
        # IARList.append(Item)
        AddActivityListItems(Years, Region, "DEMPUBGWT" + LandRegion, "PUBWAT" + LandRegion, OARList, value = "1")


        ###############################
        # Precipitation sources
        Fill_Set(NewSetItems, SetNames, "TECHNOLOGY", "MINPRC" + LandRegion, "#000000", "Agricultural groundwater supply.")
        Fill_Set(NewSetItems, SetNames, "FUEL", "WTRPRC" + LandRegion, "#000000", "Agricultural water for irrigation.")
        AddActivityListItems(Years, Region, "MINPRC" + LandRegion, "WTRPRC" + LandRegion, OARList, value = "1")

        ###############################
        # Groundwater sources
        # NewSetItems[SetNames.index("TECHNOLOGY")].append({"value":"MINGWT"+LandRegion, "name":"Agricultural groundwater supply.", "color":"#000000"})
        # NewSetItems[SetNames.index("FUEL")].append({"value":"WTRGWT"+LandRegion, "name":"Agricultural water for irrigation.", "color":"#000000"})
        # for year in Years:
        # Sets = [Region, "MINGWT"+LandRegion, "WTRGWT"+LandRegion, "1", year]
        # Value = "1"
        # Item = {"c":Sets, "v":Value}
        # OARList.append(Item)    ###############################
        # Surfce water sources
        #    NewSetItems[SetNames.index("TECHNOLOGY")].append({"value":"MINSUR"+LandRegion, "name":"Agricultural groundwater supply.", "color":"#000000"})
        Fill_Set(NewSetItems, SetNames, "FUEL", "WTRSUR" + LandRegion, "#000000", "Agricultural water for irrigation.")
        #    for year in Years:
        #        Sets = [Region, "MINSUR"+LandRegion, "WTRSUR"+LandRegion, "1", year]
        #        Value = "1"
        #        Item = {"c":Sets, "v":Value}
        #        OARList.append(Item)    ###############################
        # Land resource
        Fill_Set(NewSetItems, SetNames, "TECHNOLOGY", "MINLND" + LandRegion, "#000000", "Land suuply in ")
        Fill_Set(NewSetItems, SetNames, "FUEL", "L" + LandRegion, "#000000", "Land resource in " + LandRegion + ".")
        AddActivityListItems(Years, Region, "MINLND" + LandRegion, "L" + LandRegion, OARList, value = "1")

        ###############################
        # Cluster specific technologies for different crops, etc...
        Clusters = open(os.path.join(LandCluster_data['root'], ClusterBaseFileName + LandRegion + '.csv'), 'r').readlines()
        PrecipitationClusters = open(os.path.join(LandCluster_data['root'], PrecipitationClusterBaseFileName + LandRegion + '.csv'),
                                     'r').readlines()
        EvapotranspirationClusters = open(os.path.join(LandCluster_data['root'], EvapotranspirationClusterBaseFileName + LandRegion + '.csv'),
                                          'r').readlines()
        IrrigationWaterDeficitClusters = open(
            os.path.join(LandCluster_data['root'], IrrigationWaterDeficitClusterBaseFileName + LandRegion + '.csv'), 'r').readlines()
        # Create list of crops (or add crops to list), intensities, technology
        for Combo in Clusters[0].split(",")[10:]:
            Crop = ' '.join(Combo.split(' ')[:-2])
            IrrigationType = Combo.split(' ')[-2][0]
            Intensity = Combo.split(' ')[-1][0]
            # We have a crop combination.  We need to check if we have the crop already, and if not add a new crop.
            if Crop in CropList:  # We have already dealt with this crop in another situation...
                CropCode = CropList[Crop]
            else:
                # CropCode = "CP" + str(CropNumber).zfill(2)
                CropCode = Crop
                CropNumber = CropNumber + 1
                CropList[Crop] = CropCode
                # And create the crop commodity for final output:
                Fill_Set(NewSetItems, SetNames, "FUEL", "CRP" + CropCode, "#000000", Crop)
            # And then we need to check if we have the combination already, and if not add it to the list.
            if CropCode + Intensity + IrrigationType in CropComboList:
                CropCombo = CropComboList[CropCode + Intensity + IrrigationType]
            else:
                # We don't have this one yet:
                CropCombo = CropCode + Intensity + IrrigationType
                CropComboList[CropCode + Intensity + IrrigationType] = CropCombo
                ModeList.append(CropCombo)
                ModeNumber = ModeNumber + 1
            # This crop combo might exist in other regions, but we need to add it to this region...
            Fill_Set(NewSetItems, SetNames, "TECHNOLOGY", "LND" + CropCombo + LandRegion, "#000000",
            "Land resource technology for crop combo " + Combo)
            Fill_Set(NewSetItems, SetNames, "FUEL", "L" + CropCombo + LandRegion, "#000000",
            "Land resource commodity for crop combo " + Combo)
            AddActivityListItems(Years, Region, "LND" + CropCombo + LandRegion, "L" + LandRegion, IARList, value = "1")
            AddActivityListItems(Years, Region, "LND" + CropCombo + LandRegion, "L" + CropCombo + LandRegion, OARList, value = "1")

        # Crops and land tracking commodities have been created.  Now create land technologies to connect them together.
        for clustercount in range(1, len(Clusters)):
            # Add the agricultural land use technologies
            Fill_Set(NewSetItems, SetNames, "TECHNOLOGY", "LNDAGR" + LandRegion + "C" + Clusters[clustercount].split(',')[0].zfill(2),
            "#000000","Land resource in " + LandRegion + ".")
            # And add a mode for each crop combination and create the IAR and OAR
            for mode, modeCombo in enumerate(ModeList):
                # Add the IAR for the combo into the correct mode.
                AddActivityListItems(Years, Region, "LNDAGR" + LandRegion + "C" + Clusters[clustercount].split(',')[0].zfill(2),
                "L" + modeCombo + LandRegion, IARList, value = "1",  g = str(mode + 1))

                # And add the OAR for the output crop:
                # Lookup the OAR from the cluster data:
                for CropCode2, cropcombo2 in CropList.items():
                    if modeCombo[:-2] == cropcombo2:
                        # IAR for Precipitation - Should only be entered if the combination exists
                        PrecipitationValue = float(PrecipitationClusters[clustercount].split(',')[
                                                       1])  # Precipitation values are constant across all technologies/crops in a region.
                        PrecipitationValue = format(ctx.create_decimal(repr(PrecipitationValue)), 'f')

                        AddActivityListItems(Years, Region,
                        "LNDAGR" + LandRegion + "C" + PrecipitationClusters[clustercount].split(',')[0].zfill(2),
                        "WTRPRC" + LandRegion, IARList, g = str(mode + 1), v = str(PrecipitationValue))

                        # Find the right OAR for this technology and put it into the OAR list:

                        CropComboLabel = CropCode2 + " " + IrrigationTypeList[modeCombo[-1]] + " " + IntensityList[
                            modeCombo[-2]]
                        Location = Clusters[0].strip().split(',').index(CropComboLabel)
                        Value = float(Clusters[clustercount].split(',')[Location]) * CropYieldFactors[CropComboLabel[0:3]]
                        Value = format(ctx.create_decimal(repr(Value)), 'f')

                        AddActivityListItems(Years, Region,
                        "LNDAGR" + LandRegion + "C" + Clusters[clustercount].split(',')[0].zfill(2),
                        "CRP" + modeCombo[:-2], OARList, g = str(mode + 1), v = str(Value))

                        # IAR for Irrigation
                        Location = IrrigationWaterDeficitClusters[0].strip().split(',').index(CropComboLabel)
                        IrrigationValue = float(IrrigationWaterDeficitClusters[clustercount].split(',')[Location])
                        if IrrigationTypeList[modeCombo[-1]] == 'Rain-fed':
                            IrrigationValue = 0.
                        IrrigationValue = format(ctx.create_decimal(repr(IrrigationValue)), 'f')
                        if float(
                                IrrigationValue) < 0.0001:  # fix to prevent scientific e-8 numbers from breaking the system.
                            IrrigationValue = '0'

                        AddActivityListItems(Years, Region,
                        "LNDAGR" + LandRegion + "C" + IrrigationWaterDeficitClusters[clustercount].split(',')[0].zfill(2),
                        "AGRWAT" + LandRegion, IARList, g = str(mode + 1), v = str(IrrigationValue))

                        # OAR for Evapotranspiration
                        Location = EvapotranspirationClusters[0].strip().split(',').index(CropComboLabel)
                        EvapotranspirationValue = float(EvapotranspirationClusters[clustercount].split(',')[Location])
                        EvapotranspirationValue = format(ctx.create_decimal(repr(EvapotranspirationValue)), 'f')
                        # print(CropComboLabel+" "+line.split(',')[0] + " " + Value)
                        # print(str(mode)+" "+modeCombo+ " "+CropCode2+ " "+cropcombo2)

                        AddActivityListItems(Years, Region,
                        "LNDAGR" + LandRegion + "C" + EvapotranspirationClusters[clustercount].split(',')[0].zfill(2),
                        "WTREVT" + LandRegion, OARList, g = str(mode + 1), v = str(EvapotranspirationValue))

                        # OAR for Groundwater
                        GroundwaterValue = (float(PrecipitationValue) + float(IrrigationValue) - float(
                            EvapotranspirationValue)) * GroundwaterPercentofExcess
                        GroundwaterValue = format(ctx.create_decimal(repr(GroundwaterValue)), 'f')
                        RunoffValue = (float(PrecipitationValue) + float(IrrigationValue) - float(
                            EvapotranspirationValue)) * (1 - GroundwaterPercentofExcess)
                        RunoffValue = format(ctx.create_decimal(repr(RunoffValue)), 'f')

                        AddActivityListItems(Years, Region,
                        "LNDAGR" + LandRegion + "C" + EvapotranspirationClusters[clustercount].split(',')[0].zfill(2),
                        "WTRGRC" + LandRegion, OARList, g = str(mode + 1), v = str(GroundwaterValue))

                        # OAR for Runoff
                        AddActivityListItems(Years, Region,
                        "LNDAGR" + LandRegion + "C" + EvapotranspirationClusters[clustercount].split(',')[0].zfill(2),
                        "WTRSUR" + LandRegion, OARList, g = str(mode + 1), v = str(RunoffValue))

    # Need a new for loop so we don't add the IAR values for the last few modes to the IAR and OAR above...
    for LandRegion in LandRegions:
        # ADD LAST FEW MODES, AND IAR FOR THEM IN LNDAGR technologies
        for LandUseCode, LandUse in LandUseCodes.items():
            if LandUse in ModeList:
                ModeNum = ModeList.index(LandUse)
                # Mode exists, use this one...
                # print(str(ModeNum)+LandUse+ModeList[ModeNum])
            else:
                # Mode doesn't exist, create new mode.
                ModeList.append(LandUse)
                ModeNum = ModeNumber - 1
                ModeNumber = ModeNumber + 1
                # print(str(ModeNum)+LandUse+ModeList[ModeNum])
            # print(str(ModeNum)+LandUse+ModeList[ModeNum])
            # Now add the land use sets, IAR and OAR to connect to the LNDAGR technologies...
            Fill_Set(NewSetItems, SetNames, "TECHNOLOGY", "LND" + LandUseCode + LandRegion, "#000000",
            LandUse + " technology in " + LandRegion + ".")
            Fill_Set(NewSetItems, SetNames, "FUEL", "L" + LandUseCode + LandRegion, "#000000",
            LandUse + " commodity in " + LandRegion + ".")

            # LSOU becomes LNDFORSOU, etc. in mode 1
            AddActivityListItems(Years, Region, "LND" + LandUseCode + LandRegion, "L" + LandRegion, IARList, value = "1")

            # LNDFORSOU becomes LFORSOU, etc. in mode 1
            AddActivityListItems(Years, Region, "LND" + LandUseCode + LandRegion, "L" + LandUseCode + LandRegion, OARList, value = "1")

            for line in Clusters[1:]:  # Have to have the output for all lines...
                # LSOU becomes LNDFORSOU, etc. in specified mode
                AddActivityListItems(Years, Region, "LNDAGR" + LandRegion + "C" + line.split(',')[0].zfill(2),
                "L" + LandUseCode + LandRegion, IARList, value = "1", g = str(ModeNum + 1)) # print(Sets)


                # Now add precipitation and water balance inputs and outputs
                PrecipitationValue = float(PrecipitationClusters[int(line.split(',')[0])].split(',')[
                                               1])  # Precipitation values are constant across all technologies/crops in a region.
                PrecipitationValue = format(ctx.create_decimal(repr(PrecipitationValue)), 'f')

                AddActivityListItems(Years, Region,
                        "LNDAGR" + LandRegion + "C" + line.split(',')[0].zfill(2),
                        "WTRPRC" + LandRegion, IARList, g = str(ModeNum + 1), v = str(PrecipitationValue))



                # IAR for Irrigation doesn't exist - there is no irrigation for these technologies as they are not agricultural.
                # OAR for Evapotranspiration
                EvapotranspirationValue = float(PrecipitationValue) * EvapotranspirationPercentPRCOtherLandUse[LandUseCode]
                EvapotranspirationValue = format(ctx.create_decimal(repr(EvapotranspirationValue)), 'f')
                # print(CropComboLabel+" "+line.split(',')[0] + " " + Value)
                # print(str(mode)+" "+modeCombo+ " "+CropCode2+ " "+cropcombo2)

                AddActivityListItems(Years, Region,
                        "LNDAGR" + LandRegion + "C" + line.split(',')[0].zfill(2),
                        "WTREVT" + LandRegion, OARList, g = str(ModeNum + 1), v = str(EvapotranspirationValue))

                # OAR for Groundwater
                GroundwaterValue = (float(PrecipitationValue) - float(EvapotranspirationValue)) * \
                                   GroundwaterPercentofExcessOtherLandUse[LandUseCode]
                GroundwaterValue = format(ctx.create_decimal(repr(GroundwaterValue)), 'f')
                RunoffValue = (float(PrecipitationValue) - float(EvapotranspirationValue)) * (
                            1 - GroundwaterPercentofExcessOtherLandUse[LandUseCode])
                RunoffValue = format(ctx.create_decimal(repr(RunoffValue)), 'f')

                AddActivityListItems(Years, Region,
                        "LNDAGR" + LandRegion + "C" + line.split(',')[0].zfill(2),
                        "WTRGRC" + LandRegion, OARList, g = str(ModeNum + 1), v = str(GroundwaterValue))

                # OAR for Runoff
                AddActivityListItems(Years, Region,
                        "LNDAGR" + LandRegion + "C" + line.split(',')[0].zfill(2),
                        "WTRSUR" + LandRegion, OARList, g = str(ModeNum + 1), v = str(RunoffValue))


    # ************************* #
    # CREATE MODES OF OPERATION #
    # ************************* #

    SetNames.append("MODE_OF_OPERATION")
    NewSetItems.append([])
    NewSetGroups.append([])
    
    # Storage
    for storage in Storages:
        storage_charging_mode= Storages[storage]['mode_of_operation_charge']
        storage_discharging_mode=Storages[storage]['mode_of_operation_discharge']
        if  storage_charging_mode > len(ModeList):
            ModeList.append('Storage Charging Mode')
        # storage_discharging_mode is a number (1-based), ModeList's index+1 should be checked
        if storage_discharging_mode > len(ModeList):
            ModeList.append('Storage Discharging Mode')
    
    for index, Mode in enumerate(ModeList):
        Fill_Set(NewSetItems, SetNames, "MODE_OF_OPERATION", str(index + 1), "#000000", Mode)

    

    # ******************************* #
    # Remove any 0's from IAR and OAR #
    # ******************************* #

    for i, dic in enumerate(IARList):
        if float(dic['v']) == float('0'):
            IARList.pop(i)

    for i, dic in enumerate(OARList):
        if float(dic['v']) == float('0'):
            OARList.pop(i)

    #Handle Landuse intensity fuel
    if LandUseIntensity not  in [li['value'] for li in NewSetItems[SetNames.index("FUEL")]]:
        Fill_Set(NewSetItems, SetNames, "FUEL", LandUseIntensity, "#000000", "Land use intensity fuel for tracking land use intensity.")
    for CarbonCaptureFuel in CarbonCaptureFuels:
        if CarbonCaptureFuel not  in [li['value'] for li in NewSetItems[SetNames.index("FUEL")]]:
            Fill_Set(NewSetItems, SetNames, "FUEL", CarbonCaptureFuel, "#000000", "Carbon capture fuel for tracking carbon capture from land use change.")
    
    
    # update_transformation_tech_OAR(OARList)
    
    return (SetNames, 
            NewSetItems, 
            IARList, 
            OARList,
            ModeList)
    
    
def build(save_to='SETs'):
    save_to:Path=utils.ensure_path(save_to)
    utils.print_banner("Building CLEWs SETs")
    utils.print_info(f"Saving to directory: {save_to}")
    utils.print_info("Model Structure: 'bcnexus/clews/model_structure.py'")
    SetNames, NewSetItems, IARList, OARList,ModeList=BuildCLEWsModel()
    
    OARextender = OAR_Extender(OARList) # EL_20251119 developed this class to add missing rows to OARList based on transformation technologies
    OARList = OARextender.apply() # Add missing rows (if any) from transformation technologies

    with open(save_to / 'ModeList.txt', 'w') as ModeFile:
        for idx, mode in enumerate(ModeList, 1):
            ModeFile.write(f"{idx}: {mode}\n")
    
    UpdateSETS(SetNames,
                NewSetItems, 
                IARList, 
                OARList, 
                save_to)
    
    clews_set_builder_limitaitons=clews_const.Limitations
    utils.print_banner("Limitations of build SETs:")
    for limitation in clews_set_builder_limitaitons :
        utils.print_warning(f'{clews_set_builder_limitaitons[limitation]}')
        
    return (SetNames, 
            NewSetItems, 
            IARList, 
            OARList)

def check_landcluster_data(landcluser_config:dict,
                           land_to_grid_map:dict):

    root = landcluser_config['root']
    utils.print_update(level=PRINT_LEVEL_BASE+2,message=f"landcluser data source: {root}")

    for landRegion in land_to_grid_map.keys():
        missing = []  # reset for each region

        for key, prefix in landcluser_config.items():
            if key == 'root':
                continue

            expected_file = os.path.join(root, f"{prefix}{landRegion}.csv")

            if not os.path.isfile(expected_file):
                missing.append((key, expected_file))

        # --- reporting for this region ---
        if missing:
            msg = "\n".join([f"{k}: {f}" for k, f in missing])
            raise AssertionError(
                f"Missing required cluster files for region '{landRegion}':\n{msg}"
            )
        else:
            utils.print_update(level=PRINT_LEVEL_BASE+3,message=f"✔ All cluster files for land region '{landRegion}' found.")

# if __name__ == "__main__":
#     # logging.basicConfig(level=logging.DEBUG)
#     datafile = sys.argv[1]
#     build(yamlfile)



class OAR_Extender:
    """
    Extends the OARList by adding missing rows based on the CLEWs model structure and clews_builder config file. 
    Clews_builder config file is loaded to get the expanded technology variants and aggregations.
    
    Attributes:
        OARList (list): Original OARList to be extended.
        updated_resources (dict): Loads clews_builder configuration from the path defined in model_structure.
        transformation_tech_schema (list): Schema of TransformationTechnologies (which item represents what in the list) from model_structure.
            loc_fuel (int): Index of 'FUEL_output' in transformation_tech_schema.
            loc_tech (int): Index of 'TECHNOLOGY' in transformation_tech_schema.
    Methods:
        get_missing_fuels(): Identifies fuels present in the system but missing in the OARList.
        get_expanded_techs(fuel): For a given fuel, retrieves all associated technologies including variants.
        build_missing_rows(): Constructs missing OAR rows for each combination of region, technology, fuel, and year.
        apply(): Extends the OARList with the newly built missing rows.
        to_dataframe(): Converts the OARList into a pandas DataFrame for easier manipulation and analysis.
        find_duplicates(): Identifies duplicate entries in the OARList DataFrame.
        remove_duplicates(): (Optional) Safely removes duplicate entries from the OARList.
    """
    
    def __init__(self, OARList):
        from bcnexus.clews import model_structure as clews_const
        self.OARList:list[list] = OARList
        self.updated_resources:dict= utils.load_config(clews_const.clews_builder_cfg_path)
        self.transformation_tech_schema= clews_const.TransformationTechnologies_schema
        self.loc_fuel = self.transformation_tech_schema.index('FUEL_output')
        self.loc_tech = self.transformation_tech_schema.index('TECHNOLOGY')

    # --- 1. Fuel detection -----------------------------------------
    def get_missing_fuels(self):
        fuels_in_system = {attrs[self.loc_fuel] for attrs in clews_const.TransformationTechnologies if attrs[self.loc_fuel]}
        fuels_in_OAR = {item['c'][2] for item in self.OARList}
        return fuels_in_system - fuels_in_OAR

    # --- 2. Tech expansion -----------------------------------------
    def get_expanded_techs(self, fuel):
        base_techs = [
            attrs[self.loc_tech]
            for attrs in clews_const.TransformationTechnologies
            if attrs[self.loc_fuel] == fuel
        ]
        return [
            variant
            for tech in base_techs
            for variant in (list(self.updated_resources['TECHNOLOGIES'].get(tech, {}).keys()) or [tech])
        ]

    # --- 3. Build missing OAR rows ---------------------------------
    def build_missing_rows(self):
        start, end = clews_const.snapshot['start'], clews_const.snapshot['end']
        regions = clews_const.Regions.keys()

        for fuel in self.get_missing_fuels():
            for tech in self.get_expanded_techs(fuel):
                for region in regions:
                    for year in range(start, end + 1):
                        yield {'c': [region, tech, fuel, 1, year], 'v': 1}

    # --- 4. Extend existing OARList --------------------------------
    def apply(self):
        self.OARList.extend(self.build_missing_rows())
        
        duplicates = self.find_duplicates()
        if duplicates.empty:
            return self.OARList
        else:
            # utils.print_error("Duplicates detected in OutputActivityRatio:")
            # utils.print_error(duplicates)
            self.OARList = self.remove_duplicates()  # optional cleanup
            return self.OARList

    # --- 5. Convert to DataFrame -----------------------------------
    def to_dataframe(self):
        return pd.DataFrame([
            {'REGION': c[0], 'TECHNOLOGY': c[1], 'FUEL': c[2],
             'MODE_OF_OPERATION': c[3], 'YEAR': c[4], 'VALUE': v}
            for item in self.OARList
            for c, v in [(item['c'], item['v'])]
        ])

    # --- 6. Duplicate detection ------------------------------------
    def find_duplicates(self):
        df = self.to_dataframe()
        return df[df.duplicated(
            subset=['REGION', 'TECHNOLOGY', 'FUEL', 'MODE_OF_OPERATION', 'YEAR'], 
            keep=False
        )]

    # --- 7. (Optional) Remove duplicates safely ---------------------
    def remove_duplicates(self):
        df = self.to_dataframe().drop_duplicates(
            subset=['REGION', 'TECHNOLOGY', 'FUEL', 'MODE_OF_OPERATION', 'YEAR'],
            keep='first'
        )
        self.OARList = [
            {'c': [row.REGION, row.TECHNOLOGY, row.FUEL, row.MODE_OF_OPERATION, row.YEAR],
             'v': row.VALUE}
            for row in df.itertuples()
        ]
        return self.OARList
