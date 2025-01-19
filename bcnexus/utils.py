import yaml
import os
import pandas as pd
from colorama import Fore, Style
from typing import Optional

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
        elif level > 2:
            color = Fore.LIGHTBLACK_EX + Style.DIM
            prefix="  └─"
        elif alert:
            level=2
            color = Fore.RED
            prefix=" └ X "
    else:
        color = Fore.LIGHTMAGENTA_EX + Style.DIM
        prefix=" ─"
    
    print(f"{color}{prefix}> {message}{Style.RESET_ALL}")
    

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

