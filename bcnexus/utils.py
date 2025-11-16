import os
import shutil
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import yaml
from colorama import Fore, Style

from bcnexus import constants as bcnexus_const
from bcnexus.clews import model_structure


def print_update(level: int=None,
                 message: str="--",
                 alert:Optional[bool]=False):
    if alert:
            level=level or 2
            color = Fore.RED
            prefix=" └ ❌ "
    elif level is not None:
        if level == 1:
            color = Fore.YELLOW
            prefix="└"
        elif level == 2:
            color = Fore.CYAN
            prefix=" └"
        elif level == 3:
            color = Fore.LIGHTWHITE_EX + Style.DIM
            prefix="  └"
        elif level > 3:
            color = Fore.LIGHTBLACK_EX + Style.DIM
            prefix="  └─"
    else:
        color = Fore.LIGHTMAGENTA_EX + Style.DIM
        prefix=" ─"
    
    print(f"{color}{prefix}> {message}{Style.RESET_ALL}")

def print_error(message):
    print(f"{Fore.RED} └ ❌ > {message}{Style.RESET_ALL}")

def print_module_title(text, Length_Char_inLine=100):
    print(f"{Fore.LIGHTCYAN_EX}{Length_Char_inLine * '_'}{Style.RESET_ALL}\n"
          f"{Fore.LIGHTGREEN_EX}{5 * ' '}{text}{Style.RESET_ALL}\n"
          f"{Fore.LIGHTCYAN_EX}{Length_Char_inLine * '_'}{Style.RESET_ALL}")
    
def print_banner(message: str):
    line = "*" * len(message)
    print(f"{Fore.GREEN}{Style.BRIGHT}{line}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{Style.BRIGHT}{message}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{Style.BRIGHT}{line}{Style.RESET_ALL}")

def print_info(info:str):
    print(f"{Fore.LIGHTBLACK_EX}{Style.BRIGHT}ℹ️  {info}{Style.RESET_ALL}")

def print_warning(info: str):
    print(f"{Fore.LIGHTYELLOW_EX}{Style.BRIGHT}⚠️  {info}{Style.RESET_ALL}")
    
def copy_csv_files(
    src_folder: str, 
    dest_folder: str,
    all_files:bool=False
    ) -> None:
    """
    Copies only missing CSV files from the source folder to the destination folder.

    Args:
        src_folder (str): Path to the source folder containing CSV files.
        dest_folder (str): Path to the destination folder where CSV files will be copied.
        all_files (bool) : If True, copies all files, otherwise copies the missing files only.

    Returns:
        None: The function does not return any value.
    """
    # Convert paths to Path objects
    src_path = Path(src_folder)
    dest_path = ensure_path(dest_folder)
    if all_files:
        print_update(level=2,message=f"Copying all CSV files : '{src_path}' >> '{dest_path}'")
    else:
        print_update(level=2,message=f"Copying missing CSV files : '{src_path}' >> '{dest_path}'")

    # Iterate through all CSV files in the source folder
    for src_file in src_path.glob("*.csv"):
        # Destination file path
        dest_file = dest_path / src_file.name
        if all_files:
            shutil.copy(src_file, dest_file)
            print_update(level=3,message=f"Copied: {src_file.name}")
        else:
            # Copy only if the file is missing in the destination folder
            if not dest_file.exists():
                shutil.copy(src_file, dest_file)
                print_update(level=4,message=f"Copied: {src_file.name}")
            else:
                pass
                print_update(level=4,message=f"Skipped (already exists): {src_file.name}")

def ensure_path(save_to: str | Path) -> Path:
    """
    Ensures that the given argument is a Path object. If the user provides a string,
    it converts it to a Path object to facilitate operations like directory creation.
    
    ## Args:
    - save_to (str | Path): The path input, either as a string or a Path object.

    ## Returns:
    - Path: The input converted (if necessary) to a Path object.
    """
    if not isinstance(save_to, Path):
        Warning(f">> Given instance for 'destination (save_to)' is of type: {type(save_to)}. Converting it to a Path")
        save_to = Path(save_to)
    save_to.mkdir(parents=True, exist_ok=True)
    return save_to
    
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