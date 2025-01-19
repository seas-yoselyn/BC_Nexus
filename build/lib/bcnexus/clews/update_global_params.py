import pandas as pd
from pathlib import Path
from . import model_structure as clews_const
from .. import utils

def update_capacity_to_activity_unit(input_csv_dir:str|Path):
    input_csv_dir=Path(input_csv_dir)
    regions=clews_const.Regions
    CapacityToActivityUnit:pd.DataFrame=pd.read_csv(input_csv_dir/'CapacityToActivityUnit.csv')
    
    TECHNOLOGY:pd.DataFrame=pd.read_csv(input_csv_dir/'TECHNOLOGY.csv')
    PWR_TECHNOLOGY = TECHNOLOGY[TECHNOLOGY['VALUE'].str.startswith('PWR')]
    
    # Find missing technologies
    missing_techs_in_C2AU :pd.DataFrame= PWR_TECHNOLOGY[~PWR_TECHNOLOGY['VALUE'].isin(CapacityToActivityUnit['TECHNOLOGY'])]

    for k,v in regions.items():
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
    