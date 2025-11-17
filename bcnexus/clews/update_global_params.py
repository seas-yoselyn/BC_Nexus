import pandas as pd
from pathlib import Path
from bcnexus.clews import model_structure as clews_const
from bcnexus import utils

REGIONS=clews_const.Regions
# Constants for file paths
try:
    from bcnexus.attributes_parser import AttributesParser
    aparser=AttributesParser()
    CLEWS_BUILDER_CFG:dict=aparser.clewsb_config
    CLEWS_BUILD_DATA_DIR:Path=aparser.clews_build_data_root
except Exception as e:
    utils.print_update(level=1,message=f"Error loading Attributes Parser or CLEWs Builder Config: {e}")

def update_capacity_to_activity_unit(input_csv_dir:str|Path):
    if input_csv_dir is None:
        input_csv_dir = CLEWS_BUILD_DATA_DIR
    else:
        input_csv_dir=Path(input_csv_dir)
        

    CapacityToActivityUnit:pd.DataFrame=pd.read_csv(input_csv_dir/'CapacityToActivityUnit.csv')
    TECHNOLOGY:pd.DataFrame=pd.read_csv(input_csv_dir/'TECHNOLOGY.csv')
    PWR_TECHNOLOGY = TECHNOLOGY[TECHNOLOGY['VALUE'].str.startswith('PWR')]
    
    # Find missing technologies
    missing_techs_in_C2AU :pd.DataFrame= PWR_TECHNOLOGY[~PWR_TECHNOLOGY['VALUE'].isin(CapacityToActivityUnit['TECHNOLOGY'])]

    for k,v in REGIONS.items():
        # Assign default value for the missing technologies
        missing_techs:pd.DataFrame = missing_techs_in_C2AU.assign(
            TECHNOLOGY=missing_techs_in_C2AU['VALUE'],
            VALUE=31.536,
            REGION=k
        )

    # Append missing technologies to c2a
    CapacityToActivityUnit_updated = pd.concat([CapacityToActivityUnit, missing_techs[['REGION','TECHNOLOGY', 'VALUE']]], ignore_index=True)
    CapacityToActivityUnit_updated = CapacityToActivityUnit_updated.loc[:, ['REGION', 'TECHNOLOGY', 'VALUE']]
    CapacityToActivityUnit_updated.to_csv(input_csv_dir/'CapacityToActivityUnit.csv',index=False)
    utils.print_update(level=3, message=f"File updated: {input_csv_dir/'CapacityToActivityUnit.csv'}")
    