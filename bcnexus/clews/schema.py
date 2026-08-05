
# Load packages
import math
import shutil
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np
import pandas as pd
import yaml
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances_argmin_min
from sklearn.preprocessing import MinMaxScaler

# Local Packages
from bcnexus import utils
from bcnexus.attributes_parser import AttributesParser
from bcnexus.clews import model_structure as clews_const
PRINT_LEVEL_BASE=3

""" 
Developers : 
  Bruno_Borba: 
    -concept build and original code development 
  Elias_Islam:
    - coding restructure and refactoring to fit BC Combined modelling package.
    - refactoring to convert a hybrid of OOP and FP.

Acknowledgements:
    Pierre_McWhannel:
        - Storage and Hydro modelling, Timeslice aggregation
    Dr_Taco_Niet:
        - PI of the project, overall supervision of the development, project development and funding arrangements from PICS. 

Affiliation: 
    - Delta E+ Research Lab, SFU

Version :
    No: 1
    Release: 202409
    
Developer_Remarks:
 Key_upgrade:
    - Input data preparation automation add-on to CLEWs framework (tailored for BCNexus Model).
 New_components:
   - Battery and Hydro Storage, Timeslice up/down scaling upto 1-hour resolution, cascaded hydro power.
"""

"""
FP
"""
def get_VRE_committed_candidate_combine(future_df:pd.DataFrame,
                                        committed_df:pd.DataFrame,
                                        force_start_year:Optional[int]=None):
    """
    Combines future power plant resources with committed power plant resources. Provides a complete DataFrame with the 'start_year' column filled correctly.
    
    # Assumption:
        - The committed power plant resources are contraced to come online before the future power plant resources.
        - Will fill in the 'strat_year' column for the future power plant resource only if the column is not present or have NaN values.
        
    # Args:
        future_df: DataFrame containing future power plant resources. Ideally from Resource Options Database.
            - it may/may not contain 'start_year' column
        committed_df: DataFrame containing committed power plant resources.
            -Expected Columns:
                - 'start_year' (int): Start year of the power plant.
    # Returns:
        A complete DataFrame with the 'start_year' column filled correctly.
    """
    
    if force_start_year is not None:
        recommended_start_year=force_start_year
    else:
        recommended_start_year=committed_df['start_year'].max()+1 #1 year after the last committed plant comes online
    
    # Ensure 'start_year' is present and filled correctly (if NaN values, doesn't alter values if non NaN)
    if 'start_year' not in future_df.columns or future_df['start_year'].isnull().all(): # start_year column is not in future_df
        future_df['start_year'] = recommended_start_year
    else:
        future_df['start_year'].fillna(recommended_start_year, inplace=True)
    
    future_with_committed_df= pd.concat([committed_df, future_df]).sort_values(by='start_year')
    future_with_committed_df.reset_index(drop=True, inplace=True) # crucial to reset index to avoid duplicate index
    
    return future_with_committed_df

def update_clews_builder_config(scenario_config_path:Path)->tuple:
    """
    Reads the existing CLEWs Builder Config file (skeleton), processes required data files to identify 
    existing and future resource options, and updates technologies, SETS, and PARAMETERS.  
    Useful for updating baseline and resource options.

    ## Args:
        scenario_config_path (str):  
            Path to the combined model configuration file.  

    ## Returns:
        - tuple: A tuple containing dictionaries (`dict`) in the following order:  
            0 → `new_pwrwnd_structure`
            1 → `new_pwrwnd_future_structure`  
            2 → `new_pwrsol_structure`
            3 → `new_pwrsol_future_structure`
            4 → `new_inflow_structure`
            5 → `new_hydro_structure`
            6 → `new_tpp_bio_structure`
            7 → `new_tpp_ngs_structure`

        - Each dictionary contains processed facility data with the following keys:  
            - `name` (str): Facility name.  
            - `capacity` (float): Installed capacity in MW.  
            - `operational_life` (int): Computed as `closure_year - start_year`.  
            - `capital_cost` (float): Capital cost in $/kW.  
            - `variable_cost` (float): Variable O&M cost in $/kW-yr.  
            - `closure_year` (int): Year of closure.  
            - `status` (str): `"existing"` or `"future"`.  
    """

    ##################################################################################################
    
    # Read the existing YAML file
    aparser=AttributesParser(scenario_config_path)
    clews_builder_config_path=aparser.clews_builder_config_path
    clewsb_config:dict=aparser.clewsb_config
    data_cfg:dict=aparser.data_cfg

    # Load data file directories, the data files should be harmonized to PyPSA
    wind_csv_file_path :str|Path = data_cfg['output']['create_ext_wind_assets'] ['fname']  # data_cfg['wind_file']
    solar_csv_file_path:str|Path = data_cfg['output']['create_ext_solar_assets'] ['fname']  # data_cfg['solar_file']
    tpp_csv_file_path :str|Path= data_cfg['output']['create_ext_tpp_assets'] ['fname']  #data_cfg['tpp_file']
    hydro_generation_csv_file_path:str|Path = data_cfg['output']['create_hydro_assets'] ['hydro_generation']  #  data_cfg['hydro_generation_file']
    hydro_resevoir_csv_file_path :str|Path= data_cfg['output']['create_hydro_assets'] ['hydro_reservoir']  # data_cfg['hydro_reservoir_file']
    hydro_reservoir_ts_file_path :str|Path =  data_cfg['output']['reservoir_inflows'] ['fname']  # data_cfg['data_8760']['CF_hydro_reservoir']
    
    # Load RESource data config
    RESource_data_cfg=data_cfg.get('RESource',{})
    RESource_data_root=Path(RESource_data_cfg.get('results_root','data/RESource'))
    
    # Define cascade groups from the YAML file
    cascade_group:dict= clews_const.HYDRO_GENERATION # cm_config['clews']['HYDRO_GENERATION']#['cascade_group_1']

    # Read the data files
    wind_df = pd.read_csv(wind_csv_file_path)
    wind_future_df = pd.read_csv(RESource_data_root / RESource_data_cfg['future_wind_sites'])
    wind_committed_df = pd.read_csv(RESource_data_root / RESource_data_cfg['committed_wind_sites'])
    wind_future_with_committed_df = get_VRE_committed_candidate_combine(wind_future_df, 
                                                                        wind_committed_df)

    solar_df = pd.read_csv(solar_csv_file_path)
    solar_future_df = pd.read_csv(RESource_data_root / RESource_data_cfg['future_solar_sites'])
    solar_committed_df = pd.read_csv(RESource_data_root / RESource_data_cfg['committed_solar_sites'])
    solar_future_with_committed_df = get_VRE_committed_candidate_combine(solar_future_df,    
                                                                            solar_committed_df)

    
    tpp_df :pd.DataFrame= pd.read_csv(tpp_csv_file_path)
    hydro_generation_df :pd.DataFrame= pd.read_csv(hydro_generation_csv_file_path)
    hydro_resevoir_df:pd.DataFrame = pd.read_csv(hydro_resevoir_csv_file_path)
    hydro_reservoir_ts_df :pd.DataFrame= pd.read_csv(hydro_reservoir_ts_file_path)

    # Create new PWRWND, PWRSOL, INFLOW and PWRHYD structures

    
    new_pwrsol_structure = create_schema_VRE(solar_df, id_prefix='PWRSOLB')
    
    new_pwrsol_future_structure = create_schema_VRE(solar_df, 
                                                id_prefix='PWRSOLB', 
                                                start_index=len(solar_df), 
                                                future_df=solar_future_with_committed_df)

    new_pwrwnd_structure = create_schema_VRE(wind_df,
                                         id_prefix='PWRWNDB')
    
    new_pwrwnd_future_structure = create_schema_VRE(wind_df, 
                                                id_prefix='PWRWNDB', 
                                                start_index=len(wind_df), 
                                                future_df=wind_future_with_committed_df)

    
    new_tpp_bio_structure = create_schema_tpp(tpp_df, 
                                            id_prefix='PWRBIOB')
    
    new_tpp_ngs_structure = create_schema_tpp(tpp_df, 
                                                id_prefix='PWRNGSB')
    
    new_inflow_structure = create_schema_inflow(hydro_generation_df, 
                                                hydro_resevoir_df, 
                                                hydro_reservoir_ts_df, 
                                                cascade_group, 
                                                'INFLOW')
    
    new_hydro_structure = create_schema_hydro(hydro_generation_df, 
                                            cascade_group, 
                                            'PWRHYDB')

    merged_pwrsol_structure = {**new_pwrsol_structure, 
                               **new_pwrsol_future_structure}
    
    merged_pwrwnd_structure = {**new_pwrwnd_structure, 
                               **new_pwrwnd_future_structure}

    # Update the TECHNOLOGIES section
    if 'TECHNOLOGIES' not in clewsb_config:
        clewsb_config['TECHNOLOGIES'] = {}

    clewsb_config['TECHNOLOGIES']['PWRWND'] = merged_pwrwnd_structure
    clewsb_config['TECHNOLOGIES']['PWRSOL'] = merged_pwrsol_structure
    clewsb_config['TECHNOLOGIES']['PWRBIO'] = new_tpp_bio_structure
    clewsb_config['TECHNOLOGIES']['PWRNGS'] = new_tpp_ngs_structure
    clewsb_config['TECHNOLOGIES']['INFLOW'] = new_inflow_structure
    clewsb_config['TECHNOLOGIES']['PWRHYD'] = new_hydro_structure

    # Save the updated YAML back to the same file
    with open(clews_builder_config_path, 'w') as file:
        yaml.dump(clewsb_config, file, default_flow_style=False)

    utils.print_update(level=3,message=f"File Updated : {clews_builder_config_path}")
    
    return (new_pwrwnd_structure,
            new_pwrwnd_future_structure,
            new_pwrsol_structure,
            new_pwrsol_future_structure,
            new_inflow_structure,
            new_hydro_structure,
            new_tpp_bio_structure,
            new_tpp_ngs_structure)

def preprocess_demand_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocesses the demand data by filtering, normalizing, and ensuring data integrity.

        Args:
            df (pd.DataFrame): Original demand data.

        Returns:
            pd.DataFrame: Preprocessed demand data.
        """
        # Identify leap year dates (February 29)
        leap_days = df['local_time'].str.contains(r'(\d{4})-02-29')

        # Filter out all February 29 instances, regardless of the year
        df_filtered = df[~leap_days].copy()

        # Ensure 'demand_MWh' is of type float64
        df_filtered['demand_MWh'] = df_filtered['demand_MWh'].astype(float)

        # Normalize 'demand_MWh' column
        df_filtered.loc[:, 'demand_MWh'] = df_filtered['demand_MWh'] / df_filtered['demand_MWh'].sum()

        return df_filtered


def add_technologies(
    filtered_df:pd.DataFrame, 
    key:str, 
    info:dict, 
    start_year:int=None, 
    last_year:int=None, 
    region:str=None, 
    column_name:str=None, 
    attribute_name:str=None,
    additional_columns:str=None
):
    """
    Adds technology or scenario attribute data to a DataFrame based on the provided scenario information.

    This function:
    - Verifies that the desired attribute exists in 'info'.
    - Parses the attribute value (converting strings like '[100,200]' to [100,200] if needed).
    - If start_year and last_year are provided, expands a single value into a full time series.
    - Adds rows for each year in the time series, or a single row if no time series is required.
    - Appends the new rows to the existing DataFrame and returns the updated result.

    Parameters:
        filtered_df (pd.DataFrame): The existing DataFrame to which new rows will be appended.
        key (str): The scenario key or technology name (e.g., 'CCS01').
        info (dict): The YAML-derived dictionary containing scenario attributes.
        start_year (int, optional): Starting year of the time series (if applicable).
        last_year (int, optional): Ending year of the time series (if applicable).
        region (str, optional): The region name to be assigned to all new rows.
        column_name (str, optional): Column name that should hold 'key' (e.g., 'TECHNOLOGY').
        attribute_name (str, optional): The specific attribute to extract from 'info' (e.g., 'capital_cost').
        additional_columns (dict, optional): Extra columns and values to add to each row.

    Returns:
        pd.DataFrame: The updated DataFrame including the newly added rows.
    """

    # If no attribute is specified or doesn't exist, return original DataFrame
    if not attribute_name or attribute_name not in info:
        return filtered_df

    data_value = utils.parse_data_value(info[attribute_name])
    new_rows = []

    # If time series parameters are provided and data_value is numeric or list-like
    if start_year is not None and last_year is not None and isinstance(data_value, (int, float, list)):
        if isinstance(data_value, (int, float)):
            data_value = [data_value]
        expanded = expand_timeseries(data_value, start_year, last_year)
        for year, val in expanded.items():
            row = {
                'REGION': region,
                'YEAR': year,
                'VALUE': val
            }
            if column_name:
                row[column_name] = key
            if additional_columns:
                row.update(additional_columns)
            new_rows.append(row)
    elif isinstance(data_value, (int, float)):
        # Single value (no time series)
        row = {
            'REGION': region,
            'VALUE': data_value
        }
        if column_name:
            row[column_name] = key
        if additional_columns:
            row.update(additional_columns)
        new_rows.append(row)

    if not new_rows:
        return filtered_df

    df_new_rows = pd.DataFrame(new_rows)
    return pd.concat([filtered_df, df_new_rows], ignore_index=True)

def merge_assets(df,subset,sum_list):
    '''
    Function used to reduce hydroelectric datasets from turbines to an aggregate asset.
    This aggregation operator is currently applied only to the installed capacities for the units and
    the annual_avg_energy.
    df: Dataframe which is passed via a groupby operation.
    subset: Name of columns to use for deduplication
    sum_list: Name of parameters/columns to aggegtate using the sum operation.
    Example:
    Input dataframe has following entries below:
    component_id | asset_id | capacity | annual_avg_energy
    BC_MCA01_GEN | BC_MCA_GSS | 492 | 1936.79
    BC_MCA02_GEN | BC_MCA_GSS | 492 | 1936.79
    BC_MCA03_GEN | BC_MCA_GSS | 494 | 1942.7
    BC_MCA04_GEN | BC_MCA_GSS | 494 | 1942.7
    BC_MCA05_GEN | BC_MCA_GSS | 500 | 1968.45
    BC_MCA06_GEN | BC_MCA_GSS | 500 | 1968.45

    Output dataframe will have the following:
    asset_id | capacity | annual_avg_energy
    BC_MCA_GSS | 2972 | 11695.88

    '''
    # Other columns don't matter here for calcualting inflow and associated power production.
    df_out = df.drop_duplicates(subset=subset).set_index("connecting_node_code").copy()
    for param in sum_list:
        df_out[param] = df[param].sum()
    return df_out

def expand_timeseries(data, start_year, last_year):
    """
    Expands a single value or a short list into a full time series from start_year to last_year.
    If the list is shorter than the number of years, the last value is repeated.
    """
    if not isinstance(data, list):
        data = [data]
    year_range = last_year - start_year + 1
    if len(data) < year_range:
        data.extend([data[-1]] * (year_range - len(data)))
    return {year: val for year, val in zip(range(start_year, last_year + 1), data)}

def pre_process_input_activity_ratio(scenario_key, scenario_info):
    """
    Pre-processing logic for input_activity_ratio attribute:
    If both 'efficiency' and 'input_fuel' exist, compute 'input_activity_ratio' = 1.0 / efficiency.
    Returns True if successful, False otherwise.
    """
    efficiency = scenario_info.get('efficiency')
    input_fuel = scenario_info.get('input_fuel')
    if efficiency is not None and input_fuel is not None:
        scenario_info['input_activity_ratio'] = 1.0 / efficiency
        return True
    return False

def process_scenario_attribute(
    file_path:str |Path, 
    scenario_cfg:dict, 
    attribute_name:str, 
    column_name:str, 
    start_year:int, 
    last_year:int, 
    region:str, 
    delete_technologies_func:callable,
    add_technologies_func:callable,
    pre_process:Optional[callable]=None, 
    additional_columns:Optional[str]=None
):
    """
    Generic function that processes a given attribute for all scenarios.

    Steps:
    1. Iterate over each scenario and technology in 'scenarios'.
    2. Check if the attribute already exists or can be created via pre_process.
    3. If the attribute can be processed, call 'delete_technologies' for the given file and tech.
    4. Dynamically update additional_columns if needed (e.g., setting FUEL from scenario_info).
    5. Call 'add_technologies' to insert the attribute data into the DataFrame.
    6. At the end, save the updated DataFrame to the provided file_path.

    Parameters:
        file_path (str): Path to the CSV file to be updated.
        scenarios (dict): Dictionary of scenarios from the YAML config.
        attribute_name (str): The name of the attribute to process (e.g., 'capital_cost').
        column_name (str): The column name in the CSV representing the entity (e.g., 'TECHNOLOGY' or 'FUEL').
        start_year (int): Starting year of the time series data (if applicable).
        last_year (int): Ending year of the time series data (if applicable).
        region (str): Region name.
        delete_technologies_func (callable): Function to delete technologies from the DataFrame.
        add_technologies_func (callable): Function to add attribute data to the DataFrame.
        pre_process (callable, optional): A function that pre-processes scenario_info if the attribute doesn't exist.
                                           Should return True if the attribute was created successfully.
        additional_columns (dict, optional): Extra columns to be added to the new rows (default static values).

    Returns:
        None. The updated DataFrame is saved to 'file_path'.
    """
    df_filtered = None
    for category, scenario_details in scenario_cfg.items():
        if scenario_details is None:
            continue
        utils.print_update(level=PRINT_LEVEL_BASE, message=f"Processing category: {category}")
        for scenario_key, scenario_info in scenario_details.items():
            # Check if the attribute exists
            attr_exists = attribute_name in scenario_info
            can_process = False
            
            # If not found, try pre-processing (if provided)
            if pre_process and not attr_exists:
                can_process = pre_process(scenario_key, scenario_info)
            else:
                can_process = attr_exists

            if can_process:
                # Delete existing technologies related to the scenario_key
                df_filtered = delete_technologies_func(file_path, 
                                                    {scenario_key: scenario_info}, 
                                                    column_name=column_name)

                # Dynamically update additional_columns if needed
                updated_additional_columns = additional_columns.copy() if additional_columns else {}
    
                # For input_activity_ratio, we need to set the FUEL from scenario_info if it exists
                if attribute_name == 'input_activity_ratio':
                    fuel = scenario_info.get('input_fuel')
                    if fuel is not None:
                        updated_additional_columns['FUEL'] = fuel

                # Call add_technologies to insert the data
                df_filtered = add_technologies_func(
                                                    filtered_df=df_filtered,
                                                    key=scenario_key,
                                                    info=scenario_info,
                                                    start_year=start_year,
                                                    last_year=last_year,
                                                    region=region,
                                                    column_name=column_name,
                                                    attribute_name=attribute_name,
                                                    additional_columns=updated_additional_columns
                                                )
            # Save if we modified anything
            if df_filtered is not None:
                df_filtered.to_csv(file_path, index=False)
                utils.print_update(level=PRINT_LEVEL_BASE+1,
                    message=f"Data updated for {scenario_key} in : {file_path}")
            else:
                # utils.print_update(level=3,message=f"No changes made for {attribute_name}")
                pass
            

def conversion(chronological_sequence, 
               representative_days, 
               days_in_year, 
               output_file):
    
    # 3 VECTOR CREATION #
    # Tile: [1, 2,..., timeslice, 1, 2, ..., timeslice ... ] repeated (Chronological timeslice) times
    Representative_days_vector = np.tile(np.arange(1, len(representative_days) + 1), days_in_year)
    
    # Repeat: [1, 1, 1, 1, ... (timeslice) times, 2, 2, 2, 2, ... (timeslice) times, ... (Chronological timeslices), (Chronological timeslices), ... (timeslice) times]
    chronological_days_vector = np.repeat(np.arange(1, days_in_year + 1), len(representative_days))
    
    # Vector (days_in_year * blocks_per_day * timeslices) with zeros
    values_vector = np.zeros(days_in_year * len(representative_days), dtype=int)

    # MAp each day in chronological_sequence to its corresponding timeslice block
    for day_idx, rep_day in enumerate(chronological_sequence):
        # The index in representative_days determines the block of timeslices
        representative_days_index = representative_days.index(rep_day)
        index = representative_days_index + (day_idx * len(representative_days))
        values_vector[index] = 1
    
    df = pd.DataFrame({
        'DAYTYPE': Representative_days_vector,
        'DAYSCRO': chronological_days_vector,
        'VALUE': values_vector
    })

    # Order the DataFrame based on the TIMESLICE_NUMBER column and re-index
    df = df.sort_values(by=['DAYTYPE', 'DAYSCRO']).reset_index(drop=True)

    # Save to CSV
    df.to_csv(output_file, index=False)
    utils.print_update(level=3,
                    message=f"File Updated: {output_file}")

    return output_file

def add_technologies_max_cap(
    filtered_df: pd.DataFrame, 
    tech_key: str, 
    tech_info: dict, 
    default_start_year: int, 
    last_year: int,
    region: str
) -> pd.DataFrame:
    """
    Add new rows to the filtered DataFrame based on the technology details from the YAML.

    Parameters:
    - filtered_df (pd.DataFrame): Existing DataFrame to append rows to.
    - tech_key (str): The technology identifier (key from the YAML).
    - tech_info (dict): Technology information from the YAML, including 'status', 
                        'potential', and 'operational_life'.
    - start_year (int): The year from which the calculation starts.
    - last_year (int): The final year (inclusive) to consider for adding rows.
    - region (str): The region associated with the technology.

    Returns:
    - pd.DataFrame: A new DataFrame with the additional rows appended.
    """
    if tech_info.get('status') == 'future':
        potential_capacity = tech_info.get('potential', 0)
        operational_life =  tech_info.get('operational_life', 0)
        start_year=  tech_info.get('start_year', default_start_year+5) # if start year is not provided, default to 5 years (lead time) after the planning strat year
        closure_year = int(start_year + operational_life)

        new_rows = []
        for year in range(start_year, closure_year + 1):
            if year > last_year:  # Ensure 'YEAR' does not exceed last_year
                break
            if potential_capacity > 0:  # Add only if capacity value is greater than 0
                new_rows.append({
                    'REGION': region,
                    'TECHNOLOGY': tech_key,
                    'YEAR': year,
                    'VALUE': potential_capacity
                })

        # Create a DataFrame with the new rows
        df_new_rows = pd.DataFrame(new_rows)

        # Append the new rows to the original DataFrame
        return pd.concat([filtered_df, df_new_rows], ignore_index=True)
    
    # If not 'future', return the original DataFrame unchanged
    return filtered_df

def create_schema_VRE(df:pd.DataFrame, 
                  id_prefix:str, 
                  start_index:int=1, 
                  future_df: Union[pd.DataFrame, None]=None )->Dict:
    """
    Processes power plant data and generates a structured dictionary for CLEWs modeling.

    This function handles all power plants except Thermal Power Plants (e.g., NGS and Biofuels). 
    For thermal plants, see `create_schema_tpp`.

    **Note:** Ensure consistent intake and offtake data units to prevent cascading miscalculations.

    # Args:
        df (pd.DataFrame): DataFrame of existing power plant resources (residual capacities).  
            Expected columns:  
            - `generation_unit_code` (str): Unique identifier for the generation unit.  
            - `facility_installed_capacity` (float): Installed capacity in MW.  
            - `overnight_capital_cost_CAD_per_kW` (float): Capital cost per kW in CAD.  
            - `variable_om_cost_CAD_per_MWh` (float): Variable O&M cost per MWh in CAD.  
            - `closure_year` (float, optional): Year of closure (NaN if unknown).  
            - `possible_renewal_year` (float, optional): Possible renewal year (NaN if unknown).  
            - `service_life_years` (float, optional): Service life in years (NaN if unknown).  
            - `start_year` (float, optional): Start year (NaN if unknown).  

        id_prefix (str): Three-letter prefix for facility naming, following CLEWs conventions.

        start_index (int, optional): Initial index for numbering plants of the same technology.  
            Defaults to `1`.

        future_df (pd.DataFrame, optional): DataFrame of committed/planned power plant resources.  
            Defaults to `None`.  
            Expected columns:  
            - `cluster_id` (str): Cluster identifier.  
            - `Operational_life` (int): Operational life in years.  
            - `capex` (float): Capital expenditure in $/MW.  
            - `vom` (float): Variable O&M cost in $/MW.  
            - `potential_capacity` (float): Potential capacity in MW.  

    # Returns:
        dict: Dictionary containing processed facility data with the following keys:  
        - `name` (str): Facility name.  
        - `capacity` (float): Installed capacity in MW.  
        - `operational_life` (int): Computed as `closure_year - start_year`.  
        - `capital_cost` (float): Capital cost in $/kW.  
        - `variable_cost` (float): Variable O&M cost in $/kW-yr.  
        - `closure_year` (int): Year of closure.  
        - `status` (str): `"existing"` or `"future"`.  
    """


    data:dict = {}

    # Prepares existing facilities data, if future_df is None
    if future_df is None:
        for i, row in df.iterrows():
            
            item_id :int = f'{id_prefix}{start_index + i:02d}'
            
            start_year = int(row['start_year']) if not math.isnan(row['start_year']) else 0
            
            if not math.isnan(row['closure_year']): # handles None values
                closure_year = int(row['closure_year']) # converts to int
            elif not math.isnan(row['possible_renewal_year']):  # if closure_year is not there checks for possible_renewal_year and also handles None values of possible_renewal_year
                closure_year = int(row['possible_renewal_year']) # converts to int
            else: # If both closure_year,possible_renewal_year datafield is not there takes in service_life_years
                closure_year =  int(row['service_life_years']) + start_year
            
            data[item_id] = {
                'name': row['generation_unit_code'], 
                'capacity': row['facility_installed_capacity'] / 1000, # GW
                'operational_life': closure_year - start_year,
                'capital_cost': row['overnight_capital_cost_CAD_per_kW'], # $/kW
                'variable_cost': row['variable_om_cost_CAD_per_MWh'],
                'closure_year': closure_year,
                'status': 'existing'
            }
    
    # Prepares future data if provided
    if future_df is not None:
        for j, row in future_df.iterrows():
            item_id:int = f'{id_prefix}{start_index + 1 + j:02d}'  
  
            data[item_id] = {
                            'name': row.get('project_name') if pd.notna(row.get('project_name')) else row.get('cluster_id', 'Future_Project'),  # Str
                            'start_year': int(row['start_year']),  # int
                            'operational_life': row['Operational_life'],  # Years
                            'capital_cost': row['capex'],  # in $/kW, same as NREL's ATB
                            'variable_cost': row['vom'],  # $/kW-yr, same as NREL's ATB
                            'potential': row['potential_capacity'] / 1E3,  # need to be in GW to harmonize units
                            'status': 'future'  # Str
                        }
    return data

def create_schema_inflow(df_gen: pd.DataFrame, 
                        df_reservoir: pd.DataFrame, 
                        df_ts: pd.DataFrame, 
                        cascade_groups: dict, 
                        id_prefix: str) -> dict:
    """
        Create a schema for inflow data based on the provided dataframes and cascade groups.
        
        # Args:
            df_gen (pd.DataFrame): DataFrame containing general information about the reservoirs.

            df_reservoir (pd.DataFrame): DataFrame containing specific information about the reservoirs.
                -Expected Columns:
                   asset_id,
                   latitude,
                   longitude,
                   min_storage,
                   max_storage,
                   min_level,
                   max_level,
                   cascade_group,
                   cascade_order
            df_ts (pd.DataFrame): DataFrame containing time series data for the reservoirs.
            cascade_groups (dict): Dictionary containing cascade group names and their corresponding reservoir IDs. Typically defined via the user config.
            id_prefix (str): Prefix to be used for generating item IDs.
            
        # Returns:
            data: A dictionary containing the schema for inflow data with calculated capacities and other attributes.
        """
                     
    data:dict = {}
       
    idx:int = 1
    
    # Verify and convert the values in the 'max_water_discharge' column to numeric (float)
    df_gen['max_water_discharge'] = pd.to_numeric(df_gen['max_water_discharge'], errors='coerce').fillna(0)

    # Iterate over each cascade group
    for group_name, group_data in cascade_groups.items():
        # Ensure group_data is a list, even if it's a single string
        if isinstance(group_data, str):
            group_data = [group_data]
        
        # Filter the DataFrame based on the current cascade_group and hydro_type == 'reservoir' or 'reservoir_impute'
        df_filtered = df_gen[(df_gen['cascade_group'].isin(group_data)) & (df_gen['hydro_type'].isin(['reservoir', 'reservoir-impute']))]

        df_filtered_reservoir = df_reservoir[df_reservoir['cascade_group'].isin(group_data)]
          
        # Initialize capacity_storage to accumulate the storage capacities
        capacity_storage_m3 = 0 
        total_capacity = 0
        total_max_water_discharge = 0
        
        # Iterate over each unique reservoir in the filtered DataFrame
        for reservoir in df_filtered['upper_reservoir_id'].unique():
            # Apply filter for the current reservoir
            df_filtered2 = df_filtered[df_filtered['upper_reservoir_id'] == reservoir]
            
            # Iterate over the rows and accumulate the capacity
            for _, row in df_filtered2.iterrows():
                total_capacity += row['capacity'] / 1000  
                total_max_water_discharge += row['max_water_discharge']

            # Calculate capacity_storage by summing the max_storage for the current reservoir group
            capacity_storage_m3 += df_filtered_reservoir[df_filtered_reservoir['asset_id'] == reservoir]['max_storage'].sum()

        # Calculate the input_ratio
        capacity_storage_PJ = (capacity_storage_m3 / total_max_water_discharge) * (total_capacity / 1000000)

        # Get the list of reservoir names
        reservoir_names = df_filtered['upper_reservoir_id'].unique().tolist()
        
        # Calculate the sum of inflows for the corresponding reservoirs in df_ts
        inflow_sum = df_ts[reservoir_names].sum(axis=1)
        
        # Get the maximum inflow sum
        max_inflow_sum = inflow_sum.max() / (3600 * 1000)              

        # Generate item ID based on the prefix and index
        item_id = f'{id_prefix}{idx:02d}'
        
        # Store values 
        data[item_id] = {
            'name': df_filtered['upper_reservoir_id'].unique().tolist(),
            'capacity_storage': float(capacity_storage_PJ), # PJ
            'capacity': float(max_inflow_sum), # PJ
            'closure_year': 2050,
            'operational_life': 99,  # Set operational life to 99
            'capital_cost': 0  # Set capital cost to 0, already built
        }
        
        # Increment the index for the next group
        idx += 1
    
    return data


def create_schema_tpp(df: pd.DataFrame, 
                      id_prefix: str) -> Dict:
    """
    Create a schema for thermal power plants (TPP) based on the provided DataFrame and ID prefix.
    
    # Args
        df (pd.DataFrame): The input DataFrame containing power plant data.
        id_prefix (str): The prefix to use for generating item IDs.
    
    # Returns:
        Dict: A dictionary containing the schema for each unique generation type in the DataFrame.
        The schema includes the following information for each generation type:
            - capacity: A string representation of the cumulative capacity vector over the years 2020 to 2050.
            - operational_life: The operational life of the power plant in years.
            - capital_cost: The overnight capital cost in CAD per kW.
            - variable_cost: The variable O&M cost in CAD per MWh.
            - efficiency: The efficiency of the power plant as a percentage.
            - availability_factor: The weighted average availability factor of the power plant.
    
    The function applies initial filters based on the arg (given) ID prefix to select specific generation types.
    It then iterates over each unique generation type, calculates the required parameters, and stores them in the schema.
    """

    # Apply initial filter based on id_prefix
    if id_prefix == 'PWRBIOB':
        df = df[df['gen_type_copper'].str.contains('biomass', case=False)] # if breaks or returns none check CODER's Datafields
    elif id_prefix == 'PWRNGSB':
        df = df[df['gen_type_copper'].str.contains('NG_CC', case=False, na=False)] # if breaks or returns none check CODER's Datafields
    
    years = np.arange(2020, 2051)
    
    data = {}
    
    # Iterate over each unique generation_type in the filtered DataFrame
    for idx, gen_type in enumerate(df['gen_type'].unique(), start=1): # aggregates to unique 
        # Apply filter for the current generation_type
        df_gen_type = df[df['gen_type'] == gen_type]
        
        # Initialize the capacity vector and other accumulators
        capacity_vector = np.zeros_like(years, dtype=float)
        total_capacity = 0
        weighted_capacity_factor = 0

        # Iterate over the rows and accumulate the capacity and availability factor
        for _, row in df_gen_type.iterrows():
            for i, year in enumerate(years):
                if year <= row['closure_year']:
                    capacity_vector[i] += row['facility_installed_capacity'] / 1000 # GW
            total_capacity += row['facility_installed_capacity'] / 1000 # GW
            weighted_capacity_factor += row['capacity_factor'] * row['facility_installed_capacity'] / 1000 # GW
         
        # Calculate the weighted average availability factor
        availability_factor = weighted_capacity_factor / total_capacity if total_capacity != 0 else 0
        
        # Get the first row to extract other parameters
        first_row = df_gen_type.iloc[0]
        
        # Calculate efficiency as a percentage
        efficiency = (1 / (first_row['heat_rate'] * 0.29307107))
        
        # Generate item ID based on the prefix and index
        item_id = f'{id_prefix}{idx:02d}'
        start_year = int(row['start_year']) if not math.isnan(row['start_year']) else 0
        
        if not math.isnan(row['closure_year']):
            closure_year = int(row['closure_year'])
        elif not math.isnan(row['possible_renewal_year']):
            closure_year = int(row['possible_renewal_year'])
        else:
            closure_year = start_year+int(row['economic_life'])

        # Store values 
        data[item_id] = {
            'capacity': str(capacity_vector.tolist()),  # Store the cumulative capacity as a compact string
            'operational_life':closure_year- start_year,
            'capital_cost': float(first_row['overnight_capital_cost_CAD_per_kW']), # Converted to $/kW
            'variable_cost': float(first_row['variable_om_cost_CAD_per_MWh']),
            'efficiency': float(efficiency),
            'availability_factor': float(availability_factor)
        }
    
    return data

def yearsplit(
    timeslices: int, 
    representative_days: list[int],  # List of representative days, assuming these are integers
    chronological_sequence: list[int],  # List representing the sequence of days
    days_in_year: int,  # Number of days in a year (likely 365 or 366)
    start_year: int,  # Starting year (e.g., 2024)
    output_file: str  # File path for the output CSV file
) -> str:  # The function returns the output file path as a string
    
    timeslice_vector = np.arange(1, timeslices + 1)
    year_vector = np.repeat(start_year, timeslices)

    # Count the frequency of each representative day in the chronological_sequence vector
    count = Counter(chronological_sequence)
    count_representative_days = {day: count[day] for day in representative_days}
    
    # Calculate the number of repetitions per representative day
    blocks_per_day = timeslices // len(representative_days)
    value_vector = []

    # For each representative day, the year_split is = (repetition of the representative day * 24 / blocks_per_day) / (365 * 24)
    # Since 24 cuts with 24, it is = (repetition of the representative day / blocks_per_day) / (365)
    for day in representative_days:
        year_split = count_representative_days[day] / blocks_per_day / days_in_year
        value_vector.extend([year_split] * blocks_per_day)
    
    value_vector = np.array(value_vector)

    df = pd.DataFrame({
        'TIMESLICE': timeslice_vector,
        'YEAR': year_vector,
        'VALUE': value_vector
    })

    df.to_csv(output_file, index=False)

    return output_file


def new_yaml_param(
    yaml_file: str, 
    param_name: str, 
    new_value: Any
) -> None:
    """
    Update the value of a parameter in a YAML file.

    Args:
        yaml_file (str): Path to the YAML file.
        param_name (str): The name of the parameter to update.
        new_value (Any): The new value to assign to the parameter.

    Raises:
        FileNotFoundError: If the YAML file cannot be found.
        KeyError: If the param_name is not found in the YAML data.
    """
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
    
    if param_name in data:
        data[param_name]['default'] = new_value
        with open(yaml_file, 'w') as file:
            yaml.safe_dump(data, file)

def new_list(
    length: int, 
    output_file: str
)-> str:
    """
    Generate a list from 1 to 'length' and save it to a CSV file.

    Args:
        length (int): The length of the list to generate.
        output_file (str): Path to the output CSV file.

    Returns:
        str: The path to the output CSV file.
    """
    # try:
        # Create the list
    value = list(range(1, length + 1))
    
    # Convert list to DataFrame
    df = pd.DataFrame({'VALUE': value})
    
    # Save DataFrame to CSV
    df.to_csv(output_file, index=False)
    utils.print_update(level=3,message=f"File Updated: {output_file}")
    
    return output_file
    
    # except Exception as e:
    #     utils.print_update(level=3,message=f"Error: {e}")
    #     raise

def conversionld(
    timeslices: int, 
    representative_days: int, 
    output_file: str, 
    label: str = 'DAYTYPE'
    ) -> str:
    """
    Generate a DataFrame for timeslices, daytype, and value, and save it to a CSV file.

    Args:
        timeslices (int): The number of time slices.
        representative_days (int): The number of representative days.
        output_file (str): The path to the output CSV file.
        label (str): The label for the daytype column (default: 'DAYTYPE').

    Returns:
        str: The path to the output CSV file.
    """

    # Generate vectors
    timeslice_vector = np.arange(1, timeslices + 1)
    daytype_vector = np.repeat(np.arange(1, representative_days + 1), timeslices // representative_days)
    value_vector = np.ones(timeslices)

    # Create DataFrame
    df = pd.DataFrame({
        'TIMESLICE': timeslice_vector,
        label: daytype_vector,
        'VALUE': value_vector
    })

    # Save DataFrame to CSV
    df.to_csv(output_file, index=False)

    utils.print_update(level=3,message=f"File Updated: {output_file}")
    return output_file
    
def CF_and_SDP(
    input_file: Path, 
    representative_days: int, 
    hour_grouping: int, 
    output_file: Path, 
    operation: str = 'mean'
    ) -> str:
    """
    Function to reduce CapacityFactor and SpecifiedDemandProfile data by representative days and hour grouping.

    Args:
        input_file (str): Path to the input CSV file containing CapacityFactor or SpecifiedDemandProfile data.
        representative_days (int): The number of representative days to consider.
        hour_grouping (int): The number of hours per group (e.g., 1 for hourly, 24 for daily).
        output_file (str): Path to the output CSV file.
        operation (str): Operation to perform ('mean' or 'sum'). Defaults to 'mean'.

    Returns:
        str: Path to the output CSV file.
    """
    df = pd.read_csv(input_file)
    result_dfs = []
    
    # Determine the grouping key based on the operation
    if operation == 'sum':
        grouping_key = 'FUEL'
    else:
        grouping_key = 'TECHNOLOGY'

    # Get the list of unique technologies or fuels in the input data
    unique_items = df[grouping_key].unique()

    # Process each technology or fuel separately
    for item in unique_items:
        # Filter data for the current technology or fuel
        item_df = df[df[grouping_key] == item]
        # Calculate the time slices for the representative days
        intervals = [((day - 1) * 24 + 1, day * 24) for day in representative_days]
        # Filter the data for only the time slices of the representative days
        filtered_df = pd.concat([item_df[(item_df['TIMESLICE'] >= start) & (item_df['TIMESLICE'] <= end)] for start, end in intervals])
        # Add a 'Day' column to correctly separate the data by day
        filtered_df['Day'] = ((filtered_df['TIMESLICE'] - 1) // 24) + 1
        # Create an 'Hour_Group' identifier for each record
        filtered_df['Hour_Group'] = ((filtered_df['TIMESLICE'] - 1) % 24 // hour_grouping) + 1
    
        # Apply the specified operation: mean or sum
        if operation == 'sum':
            group_columns = ['REGION', 'FUEL', 'YEAR', 'Day', 'Hour_Group']
            value_column = 'VALUE'
            final_columns = ['REGION', 'FUEL', 'TIMESLICE', 'YEAR', 'VALUE']
        else:
            group_columns = ['REGION', 'TECHNOLOGY', 'YEAR', 'Day', 'Hour_Group']
            value_column = 'VALUE'
            final_columns = ['REGION', 'TECHNOLOGY', 'TIMESLICE', 'YEAR', 'VALUE']
    
        # Perform the operation on the grouped data
        grouped_df = filtered_df.groupby(group_columns, as_index=False)[value_column].agg(operation)
    
        # Normalize the values only if the operation is 'sum'
        if operation == 'sum':
            total_sum = grouped_df[value_column].sum()
            grouped_df[value_column] = grouped_df[value_column] / total_sum
        
        # Remove the 'Day' and 'Hour_Group' columns and assign a new sequential time slice number
        grouped_df['TIMESLICE'] = range(1, grouped_df.shape[0] + 1)
        # Select and reorder the final columns
        final_df = grouped_df[final_columns]
        # Collect the result for the current technology or fuel
        result_dfs.append(final_df)
    
    # Combine all results into a single DataFrame
    final_result_df = pd.concat(result_dfs, ignore_index=True)

    final_result_df.to_csv(output_file, index=False)

    return final_result_df

def replication(
    csv_file: str, 
    start_year: int, 
    last_year: int, 
    group_by: str = None
    ) -> None:
    """
    Expands the values for all technologies or fuels to all years from start_year + 1 up to last_year.
    If group_by is provided, the result is sorted by the specified 'group_by' column, 'YEAR', and 'TIMESLICE'.
    Otherwise, it is sorted only by 'YEAR' and 'TIMESLICE'. The result is saved back to the same CSV file.
    """
    df = pd.read_csv(csv_file)

    df_final = pd.DataFrame()

    # Replicate the data for all years from start_year + 1 to last_year
    for year in range(start_year + 1, last_year + 1):
        df_temp = df.copy()
        df_temp['YEAR'] = year
        df_final = pd.concat([df_final, df_temp])

    # Concatenate the original data with the new years
    df_final = pd.concat([df, df_final])

    # Determine sort order based on whether group_by is provided
    if group_by:
        df_final_sorted = df_final.sort_values(by=[group_by, 'YEAR', 'TIMESLICE'])
    else:
        df_final_sorted = df_final.sort_values(by=['YEAR', 'TIMESLICE'])

    # Save the sorted result back to the same CSV file
    df_final_sorted.to_csv(csv_file, index=False)
    utils.print_update(level=3,
                    message=f"File Updated: {csv_file}")

def generate_demand_profile(
    demands: list[str], 
    df_filtered: pd.DataFrame, 
    region: str, 
    start_year: int
    ) -> list[pd.DataFrame]:
    """
    Generates specified demand profile rows for the given demands.
    Returns a list of DataFrames containing the specified demand profile data.

    Args:
        demands (List[str]): List of demands to generate profiles for.
        df_filtered (pd.DataFrame): DataFrame containing demand data with 'demand_MWh' column.
        region (str): Region for which the demand profile is generated.
        start_year (int): The starting year for the demand profile.

    Returns:
        List[pd.DataFrame]: List of DataFrames, each containing demand profile data for a specific demand.
    """
    new_rows = []
    for demand in demands:
        temp_df = pd.DataFrame({
            'REGION': region,
            'FUEL': demand,
            'TIMESLICE': range(1, 8761),
            'YEAR': start_year,
            'VALUE': df_filtered['demand_MWh'].values
        })
        new_rows.append(temp_df)
    return new_rows

def generate_capacity_factor(
    tech_structure: dict[str, dict[str, Any]], 
    ts_df: pd.DataFrame, 
    region: str, 
    start_year: int
    ) -> list[dict[str, Any]]:
    """
    Generates capacity factor rows for a given technology structure.
    Returns a list of dictionaries, each containing the capacity factor data.

    Args:
        tech_structure (Dict[str, Dict[str, Any]]): Dictionary containing technology information with IDs as keys.
        ts_df (pd.DataFrame): DataFrame with time series data for various technologies.
        region (str): The region for which the capacity factor is being generated.
        start_year (int): The starting year for the capacity factor data.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, each representing a row of capacity factor data.
    """
    rows = []
    for tech_id, tech_info in tech_structure.items():
                
        # Check if the technology is an INFLOW type
        if tech_id.startswith('INFLOW'):
            tech_name = tech_info['name']
            # Sum the time series data for all reservoirs in this INFLOW
            inflow_sum = ts_df[tech_name].sum(axis=1)
            max_inflow_sum = inflow_sum.max()  # Get the maximum value for normalization

            # Generate rows for each timeslice, normalizing by the max inflow sum
            for timeslice in range(1, 8761):
                row = {
                    'REGION': region,
                    'TECHNOLOGY': tech_id,
                    'TIMESLICE': timeslice,
                    'YEAR': start_year,
                    'VALUE': inflow_sum[timeslice - 1] / max_inflow_sum  # Normalize by the max inflow sum
                }
                rows.append(row)
        # Check if the technology starts with PWRHYD
        elif tech_id.startswith('PWRHYD'):
            hydro_type = tech_info.get('type', '')
            
            if hydro_type == 'ror':
                # Ensure all columns in ts_df are numeric, coercing errors to NaN
                ts_df = ts_df.apply(pd.to_numeric, errors='coerce').fillna(0)
                # Sum the time series data for all columns (no filter needed)
                ror_sum = ts_df.sum(axis=1)
                max_ror_sum = ror_sum.max()  # Get the maximum value for normalization

                # Generate rows for each timeslice, normalizing by the max ror sum
                for timeslice in range(1, 8761):
                    row = {
                        'REGION': region,
                        'TECHNOLOGY': tech_id,
                        'TIMESLICE': timeslice,
                        'YEAR': start_year,
                        'VALUE': ror_sum[timeslice - 1] / max_ror_sum  # Normalize by the max ror sum
                    }
                    rows.append(row)
            elif hydro_type == 'reservoir':
                # Do nothing for reservoir type
                continue
        else:
            tech_name = tech_info['name']
            status = tech_info['status'] 
            for timeslice in range(1, 8761):
                if status == 'existing':
                    capacity = tech_info['capacity']
                    value = ts_df[tech_name].iloc[timeslice - 1] / (capacity * 1000)  # Normalize by installed capacity
                else:  # Future technology
                    value = ts_df[tech_name].iloc[timeslice - 1]  # No normalization needed
                row = {
                    'REGION': region,
                    'TECHNOLOGY': tech_id,
                    'TIMESLICE': timeslice,
                    'YEAR': start_year,
                    'VALUE': value 
                }
                rows.append(row)
    return rows

def delete_technologies(
    data: Union[Path, pd.DataFrame], 
    technologies: Dict[str, Any], 
    column_name: str = 'TECHNOLOGY'
    ) -> pd.DataFrame:
    """
    Delete rows from the CSV file or DataFrame that start with the specified technologies from the YAML.

    Args:
        data (Union[str, pd.DataFrame]): Path to the CSV file or a DataFrame from which rows should be deleted.
        technologies (Dict[str, Any]): Dictionary where keys are technology prefixes to be removed.
        column_name (str): Column name in the DataFrame to check for technology prefixes (default is 'TECHNOLOGY').

    Returns:
        pd.DataFrame: Filtered DataFrame with rows removed based on the technology prefixes.
    """
    # Check if the input is a file path or a DataFrame
    if isinstance(data, Path):
        df = pd.read_csv(data)
    else:
        df = data
    
    # Extract the prefixes from the YAML keys
    prefixes = list(technologies.keys())
    
    # Create a regex pattern to match any of the prefixes
    pattern = '|'.join(f'^{prefix}' for prefix in prefixes)
    # Filter rows that do not start with the specified prefixes
    df_filtered = df[~df[column_name].astype(str).str.contains(pattern, regex=True, case=False)]
    
    return df_filtered

    
def add_technologies_availability_factor(
    filtered_df: pd.DataFrame,
    tech_key: str,
    tech_info: Dict[str, Any],
    start_year: int,
    last_year: int,
    region: str,
    column_name: str = 'TECHNOLOGY',
    availability_factor_name: str = 'availability_factor'
    ) -> pd.DataFrame:
    """
    Adds new rows to the filtered DataFrame based on the technology details from the provided dictionary.
    Returns a DataFrame with the new technologies added.

    Args:
        filtered_df (pd.DataFrame): The DataFrame to which new rows will be added.
        tech_key (str): The key for the technology in the tech_info dictionary.
        tech_info (Dict[str, Any]): Dictionary containing technology information including the availability factor.
        start_year (int): The starting year for the new rows.
        last_year (int): The ending year for the new rows.
        region (str): The region for which the new rows are being added.
        column_name (str): The name of the column to be used for the technology (default is 'TECHNOLOGY').
        availability_factor_name (str): The name of the key in tech_info that holds the availability factor (default is 'availability_factor').

    Returns:
        pd.DataFrame: The DataFrame with the new rows added.
    """
     # Check if availability_factor_name exists in tech_info dictionary
    if availability_factor_name not in tech_info:
        return filtered_df  
    
    availability_factor = tech_info[availability_factor_name] 
    
    new_rows = []

    # Generate rows for each year from start_year to last_year
    for year in range(start_year, last_year + 1):
        new_rows.append({
            'REGION': region,
            column_name: tech_key,  # Use the key from the YAML as the technology name
            'YEAR': year,
            'VALUE': availability_factor
        })

    df_new_rows = pd.DataFrame(new_rows)
    
    # Verify that new rows were generated correctly
    #utils.print_update(level=3,message=f"Generated {df_new_rows.shape[0]} new rows for technology {tech_key}")

    # Combine the new rows with the filtered DataFrame
    df_combined = pd.concat([filtered_df, df_new_rows], ignore_index=True)
    
    return df_combined

def add_technologies_capital_cost(
    filtered_df: pd.DataFrame,
    tech_key: str,
    tech_info: Dict[str, Any],
    start_year: int,
    last_year: int,
    region: str,
    column_name: str = 'TECHNOLOGY',
    cost_name: str = 'capital_cost'
    ) -> pd.DataFrame:
    """
    Adds new rows to the filtered DataFrame based on the technology details from the provided dictionary.
    Returns a DataFrame with the new technologies added.

    Args:
        filtered_df (pd.DataFrame): The DataFrame to which new rows will be added.
        tech_key (str): The key for the technology in the tech_info dictionary.
        tech_info (Dict[str, Any]): Dictionary containing technology information including the capital cost.
        start_year (int): The starting year for the new rows.
        last_year (int): The ending year for the new rows.
        region (str): The region for which the new rows are being added.
        column_name (str): The name of the column to be used for the technology (default is 'TECHNOLOGY').
        cost_name (str): The name of the key in tech_info that holds the capital cost (default is 'capital_cost').

    Returns:
        pd.DataFrame: The DataFrame with the new rows added.
    """
    # print(tech_key)
    # Get the necessary details from the tech_info dictionary
    capital_cost = tech_info[cost_name]  # Capital cost from YAML
    # Check if capital_cost is a list
    if isinstance(capital_cost, str) and capital_cost.startswith('[') and capital_cost.endswith(']'):
        capital_cost = eval(capital_cost)  # Convert string to list

    new_rows = []

    # Generate rows for each year from start_year to last_year
    for i, year in enumerate(range(start_year, last_year + 1)):
        if isinstance(capital_cost, list):
            value = capital_cost[i] if i < len(capital_cost) else capital_cost[-1]
        else:
            value = capital_cost
        new_rows.append({
            'REGION': region,
            column_name: tech_key,  # Use the key from the YAML as the technology name
            'YEAR': year,
            'VALUE': value
        })

    df_new_rows = pd.DataFrame(new_rows)
    
    # Verify that new rows were generated correctly
    #utils.print_update(level=3,message=f"Generated {df_new_rows.shape[0]} new rows for technology {tech_key}")

    # Combine the new rows with the filtered DataFrame
    df_combined = pd.concat([filtered_df, df_new_rows], ignore_index=True)
    
    return df_combined



def add_technologies_variable_cost(
    filtered_df: pd.DataFrame,
    tech_key: str,
    tech_info: Dict[str, Any],
    start_year: int,
    last_year: int,
    region: str,
    column_name: str = 'TECHNOLOGY',
    cost_name: str = 'variable_cost'
    ) -> pd.DataFrame:
    """
    Adds new rows to the filtered DataFrame based on the technology details from the provided dictionary.
    Returns a DataFrame with the new technologies added.

    Args:
        filtered_df (pd.DataFrame): The DataFrame to which new rows will be added.
        tech_key (str): The key for the technology in the tech_info dictionary.
        tech_info (Dict[str, Any]): Dictionary containing technology information including the capital cost.
        start_year (int): The starting year for the new rows.
        last_year (int): The ending year for the new rows.
        region (str): The region for which the new rows are being added.
        column_name (str): The name of the column to be used for the technology (default is 'TECHNOLOGY').
        cost_name (str): The name of the key in tech_info that holds the variable cost (default is 'variable_cost').

    Returns:
        pd.DataFrame: The DataFrame with the new rows added.
    """
    # Skip technologies that do not define a variable cost in the builder config
    if cost_name not in tech_info:
        return filtered_df

    variable_cost = tech_info[cost_name]  # Variable cost from YAML
    # Check if variable_cost is a list
    if isinstance(variable_cost, str) and variable_cost.startswith('[') and variable_cost.endswith(']'):
        variable_cost = eval(variable_cost)  # Convert string to list

    new_rows = []

    # Generate rows for each year from start_year to last_year
    for i, year in enumerate(range(start_year, last_year + 1)):
        if isinstance(variable_cost, list):
            value = variable_cost[i] if i < len(variable_cost) else variable_cost[-1]
        else:
            value = variable_cost
        new_rows.append({
            'REGION': region,
            column_name: tech_key,  # Use the key from the YAML as the technology name
            'MODE_OF_OPERATION': 1,  # EL_20260713 default mode; template rows (e.g. land techs) keep their own modes
            'YEAR': year,
            'VALUE': value
        })

    df_new_rows = pd.DataFrame(new_rows)

    # Verify that new rows were generated correctly
    #utils.print_update(level=3,message=f"Generated {df_new_rows.shape[0]} new rows for technology {tech_key}")

    # Combine the new rows with the filtered DataFrame
    df_combined = pd.concat([filtered_df, df_new_rows], ignore_index=True)

    return df_combined

def add_technologies_operational_life(filtered_df, tech_key, tech_info, region, column_name='TECHNOLOGY', operational_name='operational_life'):
    """
    Add new rows to the filtered DataFrame based on the technology details from the YAML.
    Returns a DataFrame with the new technologies added.
    """
    # print(tech_key)
    # Get the necessary details from the tech_info dictionary
    # print(tech_key, tech_info)
    operational_life = tech_info[operational_name]  # Operational life from YAML
    
    new_rows = []

    # Generate a row for the technology with its operational life
    new_rows.append({
        'REGION': region,
        column_name: tech_key,  # Use the key from the YAML as the technology name
        'VALUE': operational_life
    })

    df_new_rows = pd.DataFrame(new_rows)
    
    # Verify that new rows were generated correctly
    #utils.print_update(level=3,message=f"Generated {df_new_rows.shape[0]} new rows for technology {tech_key}")

    # Combine the new rows with the filtered DataFrame
    df_combined = pd.concat([filtered_df, df_new_rows], ignore_index=True)
    
    return df_combined


def add_technologies_residual_cap(
    filtered_df:pd.DataFrame, 
    tech_key:str, 
    tech_info:dict, 
    start_year:int, 
    last_year:int,
    region:str):
    """
    Add new rows to the filtered DataFrame based on the technology details from the YAML.
    Returns a DataFrame with the new technologies added.
    """
    # # Skip technologies that start with "INFLOW"
    # if tech_key.startswith('INFLOW'):
    #     return filtered_df

    # Verify if the technology is NGS, BIO, or HYD
    #if tech_key.startswith('PWRNGS') or tech_key.startswith('PWRBIO') or tech_key.startswith('PWRHYD'):
    if tech_key.startswith('PWRNGS') or tech_key.startswith('PWRBIO'):

        # Extract the list of capacities from the tech_info
        capacities = eval(tech_info['capacity'])  # Convert string to list
        
        # Prepare new rows for insertion usando o vetor de capacidades
        new_rows = []
        for i, capacity_value in enumerate(capacities):
            if capacity_value > 0:  #Add only if capacity value is greater than 0
                year = start_year + i
                new_rows.append({
                    'REGION': region,
                    'TECHNOLOGY': tech_key,  
                    'YEAR': year,
                    'VALUE': capacity_value
                })
        
    else:
        if tech_info.get('status') == 'future':
            return filtered_df  # Skip future technologies

        capacity = tech_info.get('capacity', 0)
        
        closure_year = tech_info.get('closure_year',0)
        new_rows = []

        for year in range(start_year, closure_year + 1):
            if year > last_year:  # Ensure 'YEAR' does not exceed 2050
                break
            if capacity > 0:  #Add only if capacity value is greater than 0
                new_rows.append({
                    'REGION': region,
                    'TECHNOLOGY': tech_key,  
                    'YEAR': year,
                    'VALUE': capacity
                })

    df_new_rows = pd.DataFrame(new_rows)
    
    df_combined = pd.concat([filtered_df, df_new_rows], ignore_index=True)
    
    return df_combined

def add_technology_to_and_from_storage(filtered_df, storage_key, storage_info, region, operation_type='TO'):
    """
    Add new rows to the filtered DataFrame for storage technologies.
    Returns a DataFrame with the new technologies added.

    operation_type can be 'TO' or 'FROM' to determine the correct technology and VALUE for each MODE_OF_OPERATION.
    """
    # Determine the technology based on operation type
    if operation_type == 'TO':
        technology = storage_info['technology_to_storage']
        value_charge = 1
        value_discharge = 0
    else:  # 'FROM'
        technology = storage_info['technology_from_storage']
        value_charge = 0
        value_discharge = 1

    mode_of_operation_charge = storage_info['mode_of_operation_charge']
    mode_of_operation_discharge = storage_info['mode_of_operation_discharge']

    new_rows = [
        {
            'REGION': region,
            'TECHNOLOGY': technology,
            'STORAGE': storage_key,
            'MODE_OF_OPERATION': mode_of_operation_charge,
            'VALUE': value_charge
        },
        {
            'REGION': region,
            'TECHNOLOGY': technology,
            'STORAGE': storage_key,
            'MODE_OF_OPERATION': mode_of_operation_discharge,
            'VALUE': value_discharge
        }
    ]

    df_new_rows = pd.DataFrame(new_rows)

    df_combined = pd.concat([filtered_df, df_new_rows], ignore_index=True)
    
    return df_combined

def cluster_data(wind_capacity_factor_path, solar_capacity_factor_path, demand_profile_path, n_clusters):

    wind_capacity_factor_data = pd.read_csv(wind_capacity_factor_path)
    wind_capacity_factor_data = wind_capacity_factor_data.iloc[:, 1:] # Remove the first column

    solar_capacity_factor_data = pd.read_csv(solar_capacity_factor_path)
    solar_capacity_factor_data = solar_capacity_factor_data.iloc[:, 1:]  # Remove the first column

    # demand_profile_data = pd.read_csv(demand_profile_path)
    demand_profile_data = pd.read_csv(demand_profile_path).set_index('local_time')
    demand_profile_data.index = pd.to_datetime(demand_profile_data.index)

    # Remove February 29th, 2020 (leap year)
    demand_profile_data = demand_profile_data[~((demand_profile_data.index.month == 2) & (demand_profile_data.index.day == 29))]
    # Adjust the 'annual_hour_ending' column so that it goes from 1 to 8760
    demand_profile_data['annual_hour_ending'] = range(1, len(demand_profile_data) + 1)

    # Normalize the data
    scaler_capacity_wind = MinMaxScaler()
    wind_capacity_factor_data = pd.DataFrame(scaler_capacity_wind.fit_transform(wind_capacity_factor_data), columns=wind_capacity_factor_data.columns)
    
    scaler_capacity_solar = MinMaxScaler()
    solar_capacity_factor_data = pd.DataFrame(scaler_capacity_solar.fit_transform(solar_capacity_factor_data), columns=solar_capacity_factor_data.columns)
    
    scaler_demand = MinMaxScaler()
    demand_profile_data['demand_MWh'] = scaler_demand.fit_transform(demand_profile_data[['demand_MWh']])
    
    # Combine the data
    combined_data = pd.concat([demand_profile_data[['annual_hour_ending', 'demand_MWh']].reset_index(drop=True),
                               wind_capacity_factor_data.reset_index(drop=True),
                               solar_capacity_factor_data.reset_index(drop=True)], axis=1)

    # Converte annual_hour_ending in DayOfYear
    combined_data['DayOfYear'] = (combined_data['annual_hour_ending'] - 1) // 24 + 1
    combined_data['HourOfDay'] = (combined_data['annual_hour_ending'] - 1) % 24 + 1


    # Pivot data
    pivot_wind_capacity = {col: combined_data.pivot(index='DayOfYear', columns='HourOfDay', values=col) for col in wind_capacity_factor_data.columns}
    pivot_solar_capacity = {col: combined_data.pivot(index='DayOfYear', columns='HourOfDay', values=col) for col in solar_capacity_factor_data.columns}
    pivot_demand = combined_data.pivot(index='DayOfYear', columns='HourOfDay', values='demand_MWh')

    # Rename columns to reflect the appropriate names
    for col in wind_capacity_factor_data.columns:
        pivot_wind_capacity[col].columns = [f'{col}_wind_timeslice_{i}' for i in pivot_wind_capacity[col].columns]
    for col in solar_capacity_factor_data.columns:
        pivot_solar_capacity[col].columns = [f'{col}_solar_timeslice_{i}' for i in pivot_solar_capacity[col].columns]
    pivot_demand.columns = [f'value_demand_timeslice_{i}' for i in pivot_demand.columns]

    # Concatenate all pivot tables horizontally
    final_data = pd.concat([pivot_demand] + [pivot_wind_capacity[col] for col in wind_capacity_factor_data.columns] +
                           [pivot_solar_capacity[col] for col in solar_capacity_factor_data.columns], axis=1)

    # Visualize the results

    # K-means
    kmeans = KMeans(n_clusters=n_clusters, random_state=0)
    clusters = kmeans.fit_predict(final_data)
    
    # Find the closest day to the center of clusters
    closest, _ = pairwise_distances_argmin_min(kmeans.cluster_centers_, final_data)
    representative_days = final_data.iloc[closest].index.tolist()
    
    # Order the representative days in chronological order
    representative_days_sorted = sorted(representative_days)

    chronological_sequence = [representative_days[i] for i in clusters]
    
    return representative_days_sorted, chronological_sequence

# Function to create the new structure from the DataFrame
def create_schema_hydro(df, cascade_groups, id_prefix):
    data = {}
    
    years = np.arange(2020, 2051) 
    
    idx = 1
    
    # Verify and convert the values in the 'max_water_discharge' column to numeric (float)
    df['max_water_discharge'] = pd.to_numeric(df['max_water_discharge'], errors='coerce').fillna(0)
    
    # Iterate over each cascade group
    for group_name, group_data in cascade_groups.items():
        # Ensure group_data is a list, even if it's a single string
        if isinstance(group_data, str):
            group_data = [group_data]
        
        # Filter the DataFrame based on the current cascade_group and hydro_type == 'reservoir' or 'reservoir_impute'
        df_filtered = df[(df['cascade_group'].isin(group_data)) & (df['hydro_type'].isin(['reservoir', 'reservoir-impute']))]
      
        # Initialize the capacity vector for this entire group
        total_capacity = 0
        
        # Iterate over each unique reservoir in the filtered DataFrame
        for reservoir in df_filtered['upper_reservoir_id'].unique():
            # Apply filter for the current reservoir
            df_filtered2 = df_filtered[df_filtered['upper_reservoir_id'] == reservoir]
            
            # Iterate over the rows and accumulate the capacity
            for _, row in df_filtered2.iterrows():
                # for i, year in enumerate(years):
                #     if year <= row['closure_year']:
                #         capacity_vector[i] += row['capacity'] / 1000
                total_capacity += row['capacity'] / 1000  
                     
        # Get the first row to extract other parameters
        first_row = df_filtered.iloc[0]

        # Generate item ID based on the prefix and index
        item_id = f'{id_prefix}{idx:02d}'
        
        # closure_year = int(row['closure_year']) if not math.isnan(row['closure_year']) else 0
        if not math.isnan(row['closure_year']):
            closure_year = int(row['closure_year'])
        elif not math.isnan(row['service_life_years']):
            closure_year = int(row['service_life_years'])
        else:
            closure_year = int(2100)
            
        start_year = int(row['start_year']) if not math.isnan(row['start_year']) else 0
        # EL_20260713 capacity-weighted variable O&M of the aggregated group, CAD/MWh -> $/GJ (=M$/PJ) via /3.6;
        # fallback 0.001 keeps a nonzero tie-breaker against LP degeneracy (free-energy overproduction)
        vom_CAD_per_MWh = ((df_filtered['variable_om_cost_CAD_per_MWh'] * df_filtered['capacity']).sum()
                           / df_filtered['capacity'].sum())
        data[item_id] = {
            'type': 'reservoir',
            #'capacity': str(capacity_vector.tolist()),
            'capacity': float(total_capacity),
            'operational_life' : 100 if (closure_year - start_year) < 0 else (closure_year - start_year),
            'capital_cost': float(first_row['capital_cost_CAD_per_kW']),
            'closure_year': 2050,
            'input ratio': 1,
            'status': 'existing',
            'variable_cost': round(float(vom_CAD_per_MWh) / 3.6, 4) if pd.notna(vom_CAD_per_MWh) and vom_CAD_per_MWh > 0 else 0.001
        }
        
        # Increment the index for the next group
        idx += 1

    # Additional filter for hydro_type == 'ror_water' or 'ror'
    df_ror_filtered = df[df['hydro_type'].isin(['ror_water', 'ror'])]
    
    # Initialize the capacity vector for this group
    np.zeros_like(years, dtype=float)
    total_capacity_ror = 0
    
    # Accumulate the capacity across all filtered rows
    for _, row in df_ror_filtered.iterrows():
        total_capacity_ror += row['capacity'] / 1000 
       
    # Get the first row to extract other parameters
    first_row_ror = df_ror_filtered.iloc[0]
    
    # Generate item ID based on the prefix and index
    item_id_ror = f'{id_prefix}{idx:02d}'

    # EL_20260713 capacity-weighted variable O&M, CAD/MWh -> $/GJ (=M$/PJ) via /3.6; 0.001 fallback as degeneracy tie-breaker
    vom_ror_CAD_per_MWh = ((df_ror_filtered['variable_om_cost_CAD_per_MWh'] * df_ror_filtered['capacity']).sum()
                           / df_ror_filtered['capacity'].sum())
    data[item_id_ror] = {
        'type': 'ror',

        'capacity': float(total_capacity_ror),
        'operational_life': 100 if (closure_year - start_year) < 0 else (closure_year - start_year),
        'capital_cost': float(first_row_ror['capital_cost_CAD_per_kW']),
        'closure_year': 2050,
        'status': 'existing',
        'variable_cost': round(float(vom_ror_CAD_per_MWh) / 3.6, 4) if pd.notna(vom_ror_CAD_per_MWh) and vom_ror_CAD_per_MWh > 0 else 0.001
    }
    
    return data

def prepare_capacity_factor_data(
    combined_model_config_path:Path,
    clews_builder_config_path:Path,
    new_pwrwnd_structure:dict,
    new_pwrwnd_future_structure:dict,
    new_pwrsol_structure:dict,
    new_pwrsol_future_structure:dict,
    new_inflow_structure:dict,
    new_hydro_structure:dict)->pd.DataFrame:
    
    """
    Generates the Capacity Factor(CF) data with 1 hour resolution i.e. 8760 timeslices for a year.
    """
        
    cm_config:dict=utils.load_config(combined_model_config_path)
    utils.load_config(clews_builder_config_path)
    
    ### GENERATE CAPACITY FACTOR CSV WITH 8760 TIMESLICES FOR 1 YEAR
    ##################################################################################################
    
    # Generate the capacity_factor CSV
    region = cm_config['clews']['GENERAL']['region']
    start_year = cm_config['clews']['GENERAL']['start_year']
    wind_ts_file_path =  cm_config['pypsa']['output']['create_ext_wind_ts'] ['fname']  # config['FILES']['DATA']['data_8760']['CF_wind']
    # wind_future_ts_file_path = Path (cm_config['results']['linking']['root'])/ cm_config['results']['linking']['clusters_CFts_topSites']['wind'] # config['FILES']['DATA']['data_8760']['CF_wind_future']
    wind_future_ts_file_path=Path ('results/RESource/resource_options_wind_timeseries.csv')
    solar_ts_file_path =  cm_config['pypsa']['output']['create_ext_solar_ts'] ['fname'] # config['FILES']['DATA']['data_8760']['CF_solar']
    # solar_future_ts_file_path = Path (cm_config['results']['linking']['root'])/ cm_config['results']['linking']['clusters_CFts_topSites']['solar'] #config['FILES']['DATA']['data_8760']['CF_solar_future']
    solar_future_ts_file_path=Path ('results/RESource/resource_options_solar_timeseries.csv')
    hydro_reservoir_ts_file_path = cm_config['pypsa']['output']['reservoir_inflows'] ['fname']  #  config['FILES']['DATA']['data_8760']['CF_hydro_reservoir']
    hydro_ror_ts_file_path = cm_config['pypsa']['output']['ror_ps'] ['fname']  # config['FILES']['DATA']['data_8760']['CF_hydro_ror']
    
    capacity_factor_file_out = Path ("data/clews_data/inputs_csv_8760/CapacityFactor.csv")


    # data_cfg=clews_builder_config['FILES']['DATA']


    # Read time series data
    wind_ts_df = pd.read_csv(wind_ts_file_path)
    wind_future_ts_df = pd.read_csv(wind_future_ts_file_path) # pd.read_pickle(wind_future_ts_file_path)
    solar_ts_df = pd.read_csv(solar_ts_file_path)
    solar_future_ts_df =  pd.read_csv(solar_future_ts_file_path) # pd.read_pickle(solar_future_ts_file_path)
    hydro_reservoir_ts_df = pd.read_csv(hydro_reservoir_ts_file_path)
    hydro_ror_ts_df = pd.read_csv(hydro_ror_ts_file_path)

    # Generate rows for PWRWND, PWRSOL and INFLOW
    rows = []
    rows.extend(generate_capacity_factor(new_pwrwnd_structure, wind_ts_df, region, start_year))
    rows.extend(generate_capacity_factor(new_pwrwnd_future_structure, wind_future_ts_df, region, start_year))
    rows.extend(generate_capacity_factor(new_pwrsol_structure, solar_ts_df, region, start_year))
    rows.extend(generate_capacity_factor(new_pwrsol_future_structure, solar_future_ts_df, region, start_year))
    rows.extend(generate_capacity_factor(new_inflow_structure, hydro_reservoir_ts_df, region, start_year))
    rows.extend(generate_capacity_factor(new_hydro_structure, hydro_ror_ts_df, region, start_year))

    # Create DataFrame and save to CSV
    capacity_factor_df = pd.DataFrame(rows)
    capacity_factor_file_out=Path ("data/clews_data/inputs_csv_8760/CapacityFactor.csv")
    capacity_factor_df.to_csv(capacity_factor_file_out, index=False)
    utils.print_update(level=3,
                    message=f"Capacity factor CSV file saved at: {capacity_factor_file_out}")
    return capacity_factor_df

def update_specified_demand_profile(
    combined_model_config_path:Path)->pd.DataFrame:
    """
    Generates specified demand profile CSV files with 1 hour resolution for a year.
    """
    ### GENERATE SPECIFIED DEMAND PROFILE CSV WITH 8760 TIMESLICES FOR 1 YEAR
    ##################################################################################################

    cm_config:dict=utils.load_config(combined_model_config_path)
    
    region = cm_config['clews']['GENERAL']['region']
    start_year = cm_config['clews']['GENERAL']['start_year']
    # last_year = cm_config['clews']['GENERAL']['last_year']
    
    # Load the pickle file
    data_file_path = "data/downloaded_data/CODERS/data-pull/demand/BC_provincial_demand_profile.csv"
    
    df = pd.read_csv(data_file_path)

    # Filter the DataFrame to remove February 29, 2020
    df_filtered = df[~((df['local_time'] >= '2020-02-29') & (df['local_time'] < '2020-03-01'))].copy()

    # Ensure the 'demand_MWh' column is of type float64
    df_filtered['demand_MWh'] = df_filtered['demand_MWh'].astype(float)

    # Normalize the 'demand_MWh' column
    df_filtered.loc[:, 'demand_MWh'] = df_filtered['demand_MWh'] / df_filtered['demand_MWh'].sum()

    # Define demands
    demands = ['COMELCB02', 'INDELCB02', 'RESELCB02', 'TRAELCB02'] # don't have data for 'AGRELCB02'

    # Generate demand profile rows
    demand_rows = generate_demand_profile(demands, df_filtered, region, start_year)

    # Concatenate all the new rows into a single DataFrame
    specified_demand_profile_df = pd.concat(demand_rows, ignore_index=True)

    # Save the final DataFrame to a CSV file
    specified_demand_profile_file_out = Path('data/clews_data/inputs_csv_8760/SpecifiedDemandProfile.csv')#clews_builder_config['FILES']['specified_demand_profile_8760_file']
    specified_demand_profile_df.to_csv(specified_demand_profile_file_out, index=False)

    utils.print_update(level=3,message=f"Specified demand profile CSV file saved at: {specified_demand_profile_file_out}")

    return specified_demand_profile_df

"""
def main(
    combined_model_config_path:Path,
    clews_builder_config_path:Path
):

    #step 1: Update the CLEWS builder config
    utils.print_update(level=3,message="\n>> Updating CLEWS Builder configuration file...")
    (new_pwrwnd_structure,new_pwrwnd_future_structure,new_pwrsol_structure,
     new_pwrsol_future_structure,new_inflow_structure,new_hydro_structure) = update_clews_builder_config(combined_model_config_path,
                                                                                                                                  clews_builder_config_path)
    
    
    #step 2: Load the updated CLEWS BUILDER CONFIG
    utils.print_update(level=3,message="\n>> Loading the updated CLEWS Builder config...")
    # config=utils.load_config(config_file_path)
    # clews_builder_config:dict=utils.load_config(clews_builder_config_path)
    # combined_model_config:dict=utils.load_config(clews_builder_config_path)
    
    #step 3: Update CAPACITY FACTOR
    utils.print_update(level=3,message="\n>> Updating CAPACITY FACTOR...")
    prepare_capacity_factor_data(combined_model_config_path,
                                clews_builder_config_path,
                                 new_pwrwnd_structure,
                                 new_pwrwnd_future_structure,
                                 new_pwrsol_structure,
                                 new_pwrsol_future_structure,
                                 new_inflow_structure,
                                 new_hydro_structure)
    
    #step 4: update SPECIFIED DEMAND PROFILE
    utils.print_update(level=3,message="\n>> Updating SPECIFIED DEMAND PROFILE...")
    update_specified_demand_profile(combined_model_config_path,
                                    clews_builder_config_path)
    return
"""