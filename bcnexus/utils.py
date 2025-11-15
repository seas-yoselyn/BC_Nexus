import yaml
import os
import pandas as pd
from colorama import Fore, Style
from typing import Optional
from pathlib import Path
import numpy as np
from bcnexus.clews import model_structure
from bcnexus import constants as bcnexus_const

def print_module_title(text, Length_Char_inLine=60):
    print(f"{Fore.LIGHTCYAN_EX}{Length_Char_inLine * '_'}{Style.RESET_ALL}\n"
          f"{Fore.LIGHTGREEN_EX}{5 * ' '}{text}{Style.RESET_ALL}\n"
          f"{Fore.LIGHTCYAN_EX}{Length_Char_inLine * '_'}{Style.RESET_ALL}")


def print_update(level: int=None,
                 message: str="--",
                 alert:Optional[bool]=False):
    if level is not None:
        if level == 1:
            color = Fore.YELLOW
            prefix="└"
        elif level == 2:
            color = Fore.CYAN
            prefix=" └"
        elif level == 3:
            color = Fore.LIGHTMAGENTA_EX
            prefix="  └"
        elif level > 3:
            color = Fore.LIGHTBLACK_EX + Style.DIM
            prefix="  └─"
        elif alert:
            level=2
            color = Fore.RED
            prefix=" └ X "
    else:
        color = Fore.LIGHTRED_EX + Style.DIM
        prefix="  !!!"
    
    print(f"{color}{prefix} {message}{Style.RESET_ALL}")
    
def process_demand_data(scenario:str,
                        AccumulatedAnnualDemand_scenario_filepath:str|Path,
                        SpecificAnnualDemand_scenario_filepath:str|Path,
                        ):
    """
    This function loads the demand data for a given scenario and processes it.
    It reads the accumulated and specific annual demand data from CSV files,
    merges them, and adds helper columns for plotting.
    Args:
        AccumulatedAnnualDemand_scenario_filepath (str|Path): Path to the accumulated annual demand CSV file.
        SpecificAnnualDemand_scenario_filepath (str|Path): Path to the specific annual demand CSV file.
        scenario (str): The scenario name.
    """

    annual_demand_CZ = pd.read_csv(Path(AccumulatedAnnualDemand_scenario_filepath))
    specific_demand_CZ = pd.read_csv(Path(SpecificAnnualDemand_scenario_filepath))
    total_demand_CZ = pd.concat([specific_demand_CZ, annual_demand_CZ], ignore_index=True)

    
    # Initialize the column with default values
    total_demand_CZ['sector'] = total_demand_CZ['FUEL'].str[:3]
    total_demand_CZ['end_use_fuel'] = total_demand_CZ['FUEL'].str[3:]
    total_demand_CZ['scenario'] = scenario

    # Overwrite with None where 'FUEL' contains 'LND', 'CRP', or 'PUB'
    mask = total_demand_CZ['FUEL'].str.contains('LND|CRP|PUB')
    total_demand_CZ.loc[mask, 'end_use_fuel'] = None
    # total_demand_CZ.loc[mask, 'sector'] = None
    
    # Helper function to get the columns needed for plotting
    return total_demand_CZ

def parse_data_value(value):
    """
    Attempts to convert strings that represent lists (e.g. '[100, 200, 300]')
    into actual lists. If not possible, returns the value as-is.
    """
    if isinstance(value, str):
        try:
            value = eval(value)
        except (SyntaxError, NameError):
            # If eval fails, keep the original string
            pass
    return value


def load_config(config_file):
    '''
    This function loads the configuration file for PyPSA_BC
    config_file: Path + filename of the configuration file. (i.e. ../config/config.yaml)
    '''
    with open(config_file, 'r') as file:
        cfg = yaml.safe_load(file)
    return cfg

def create_folder(folder):
    '''
    This functions creates a folder if not already created.
    If the folder is already created it takes no action
    folder: Path + folder name.
    '''
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"Created folder @ {folder}")

def write_pickle(data_dict, filepath):
    '''
    Write a pickle file based on a dictionary.
    '''
    with open(filepath,"wb") as f:
        pd.to_pickle(data_dict, f)
    f.close()
    print(f'Wrote pickle file {filepath}')

def read_pickle(filepath):
    '''
    Read a json file based on a dictionary.
    '''
    with open(filepath, 'rb') as f:
        data_dict = pd.read_pickle(f) 
    return data_dict

def fix_df_ts_index(
    df:pd.DataFrame, 
    start_date:str='2021-01-01 00:00:00', 
    end_date:str='2021-12-31 23:00:00'):
    '''
    This function hardcodes and fixes the timeseries to be an 8760 timeseries
    beginning in 2021-01-01.
    '''
    new_indices = pd.date_range(start = start_date, end = end_date, freq='h')
    
    df.index = new_indices

    return df

global det_col
global color_dict
det_col = None
color_dict = None

def add_power_tech_labels(df:pd.DataFrame,
                          tech_key:str):
    # Assign power_techs and filter
    df.loc[:, 'power_techs'] = df['TECHNOLOGY'].apply(
        lambda x: 'BATTERY_STORAGE' if (x == 'BATTERY_STORAGE' and (tech_key == 'capacity' or tech_key == 'energy')) else (
            x[:6] if x[:6] in bcnexus_const.technologies[tech_key] else None
        )
    )
    df.loc[:, 'power_techs_labels'] = df['power_techs'].map(bcnexus_const.legend_labels)
    return df

def df_years(df, years):
    new_df = pd.DataFrame()
    new_df['y'] = years
    new_df['y'] = new_df['y'].astype(int)
    df['y'] = df['y'].astype(int)
    new_df = pd.merge(new_df, df, how='outer', on='y').fillna(0)
    return new_df

    
def get_PJ_to_GWh_conversion_factor(timeslices_in_a_year: int = None) -> float:
    """
    Returns the conversion factor to convert energy in PJ (Petajoules) to 
    GWh (Gigawatt-hours), either total or average per timeslice.

    Parameters:
    - timeslices_in_a_year (int, optional): Number of equal-length timeslices in a year.
      If None, returns the direct conversion factor: 1 PJ = 277.778 GWh.
      If provided, returns the factor for average GWh per timeslice.

    Returns:
    - float: Conversion factor (multiply PJ by this factor to get GWh or average GWh per timeslice)
    """
    
    
    PJ_TO_GWh = 277.778 #GWh  # 1 PJ=277.778 GWh=277,778MWh

    if timeslices_in_a_year is None:
        return PJ_TO_GWh
    else:
        return PJ_TO_GWh / timeslices_in_a_year

def get_labels(df:pd.DataFrame):

    df.loc[:,'sector'] = np.where(
        df['TECHNOLOGY'].str.contains("CCS"),
        None,
        df['TECHNOLOGY'].str[3:6]
    )
    
    df.loc[:,'end_use_fuel']= np.where(
        df['TECHNOLOGY'].str.contains("CCS"),
        None,
        df['TECHNOLOGY'].str[6:9])

    df['end_use_fuel_label'] = df['end_use_fuel'].map(model_structure.NamingConvention)
    df['sector_label'] = df['sector'].map(model_structure.NamingConvention)
    return df