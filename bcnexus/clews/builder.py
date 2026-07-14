# from typing import Optional
import argparse
import warnings
from pathlib import Path

import pandas as pd

# local packages
from bcnexus import utils
from bcnexus.attributes_parser import AttributesParser
from bcnexus.clews import datapackage as clews_data_module
from bcnexus.clews import livestock as bcnexus_lvs
from bcnexus.clews import schema as schema_processor
from bcnexus.clews import sets_n_ratios, update_global_params, update_yearly_params

warnings.filterwarnings("ignore")

PRINT_LEVEL_BASE:int=1

class BuildModel:
    """ 
    BuildModel is a class that handles the configuration, processing, and execution of a combined model for CLEWs (Climate, Land, Energy, and Water systems).
    """
    def __init__(self,
                run_scenario:str,
                storage_algorithm:str=None,
                clustering_attributes:dict=None,
                scenario_config_path:str|Path=None):

        self.scenario=str(run_scenario)
        

        # The Attributes Parser handles all sorts of parsing from the User Config file and implements necessary checks, validation and sets suitable defaults if any field is missing.
        self.aparser=AttributesParser(scenario_config_path)
        
        self.storage_algorithm=storage_algorithm if storage_algorithm else self.aparser.DEFAULT_STORAGE_ALGORITHM
        self.scenario_cfg_path:Path=self.aparser.scenarios_cfg_path
        self.clustering_attributes=clustering_attributes if clustering_attributes else self.aparser.get_DEFAULT_CLUSTERING_ATTRIBUTES()
        
        utils.print_module_title("CLEWs Model Builder")
        utils.print_banner(f"Scenario: {self.scenario}")
        utils.print_info(f"Using configuration file at: {self.scenario_cfg_path}")
        utils.print_info(f"Clustering attributes: {self.clustering_attributes}")
        utils.print_info(f"Storage Algorithm: {self.storage_algorithm}")
        
        # Prepares all class attributes (e.g. directories, static values/ranges, constants etc.)
        self.get_model_builder_attributes() 
        
        # collects the template files from the CLEWS model repository and dumps to "data/clews_data/input_csvs" folder. The folder creation inside data will be handled by the method.
        self.get_csv_template(force_replace=False)
        
    def get_model_builder_attributes(self):
        
        utils.print_update(level=2,
            message="Extracting class attributes e.g. directories, static values/ranges, constants etc.")
        
        # Get clews builder config via AttributesParser's instance
        self.clews_builder_config_path:Path=self.aparser.clews_builder_config_path
        self.clewsb_config:dict=self.aparser.clewsb_config
    
        #Load Combined Model Config
        self.scenarios_dict:dict=self.aparser.scenario_dict

        (self.start_year, self.last_year)=self.aparser.get_clews_snapshot()
         
        self.region=self.aparser.get_region()

        # self.SETs_save_to=self.aparser.get_SETs_save_to()

        (self.StorageMaxCapacity,
        self.ResidualStorageCapacity,
        self.ext_wind_CF,
        self.ext_solar_CF,
        self.demand_profile,
        self.hydro_res_CF,
        self.hydro_ror_ts,
        self.future_wind_CF,
        self.future_solar_CF,
        self.committed_wind_CF,
        self.committed_solar_CF,
        self.clews_CF_csv_file,
        self.clews_demand_profile 
        )=self.aparser.get_data_path_attributes()
    
        self.scenario_inputs_root=self.aparser.get_scenario_inputs_path(self.scenario,
                                               self.storage_algorithm)
        

        (self.LandCluster_data_source,self.LandCluster_data_dest)=self.aparser.get_LandCluster_paths()
        self.SETs_save_to=self.aparser.get_SETs_Path()
        
        # We keep the REF/BASE intact and apply the aggregation/updates on a cloned version inside 'data/clews_data/input_csvs'.
        self.clews_build_input_csv_dir = self.aparser.clews_build_inputs # Path('data/clews_data/input_csvs')
        self.input_csv_templates = self.aparser.get_default_csv_template_path()
        
        # Ideally from BASE/REF case template to a temp and reproducible folder i.e. 'data/clews_data/input_csvs'
        self.storage_case_input_csvs=self.aparser.get_storage_case_input_csvs_path(self.storage_algorithm)
        self.otoole_yaml_file=self.aparser.get_otoole_yaml_file(self.storage_algorithm)
        
    def clean_up_SETs_and_Params_definitions(self,
                                             csvs_dir:str|Path=None):
        if csvs_dir is None:
            csvs_dir=Path(self.clews_build_input_csv_dir)
        else:
            csvs_dir=Path(csvs_dir)
            
        clews_Data=clews_data_module.GetDataPackage(csvs_dir)
        
        SETS_dfs, Params_dfs=clews_Data.load_data()
        for set,df in SETS_dfs.items():
            for param, df in Params_dfs.items():
                if 'TECHNOLOGY' in Params_dfs[param].columns:
                    valid_technologies = list(SETS_dfs['TECHNOLOGY']['VALUE'])
                    Params_dfs[param] = Params_dfs[param][Params_dfs[param]['TECHNOLOGY'].isin(valid_technologies)]
                    Params_dfs[param].to_csv(csvs_dir/f"{param}.csv", index=False)
                else:
                    continue
        return SETS_dfs,Params_dfs

    def get_LandCluster_data(self):
        utils.print_update(level=PRINT_LEVEL_BASE+1,
            message="Collecting LandCluster data files...")
        utils.print_warning("This model usages prepared LandCluster data. Ensure the data is prepared for the scenario being modelled.")
        utils.print_info(f"Landcluster data source: {self.LandCluster_data_source}")
        utils.copy_csv_files(src_folder=self.LandCluster_data_source,
                                dest_folder=self.LandCluster_data_dest,
                                all_files=True)
    
    
    def build_SETs_and_ratios(self,
                              include_livestock:bool=False):
        utils.print_update(level=PRINT_LEVEL_BASE,
            message="Building SETs and Ratios data...")
            
    #1. Collect LandCluster data files
        self.get_LandCluster_data()
    
    #2. Build base SETs and Ratios
        SetNames,NewSetItems,IARList,OARList=    sets_n_ratios.build(self.SETs_save_to)
    
    #3. Collect Livestock data and build SETs including livestock data
        if include_livestock:
            utils.print_banner("Building Livestock SETs and Ratios data...")
            bcnexus_lvs.main(csv_save_to=self.SETs_save_to) # handles all sets including livestock

    ## NOT NEEDED : EL_20251115
    # ---------------------------
        # Update STORAGE TECHNOLOGY in TECHNOLOGY SET
        # TECHNOLOGY_set_file_path=Path(self.SETs_save_to / 'TECHNOLOGY.csv')
        
        # TECHNOLOGY_df=pd.read_csv(TECHNOLOGY_set_file_path)
        # storage_techs = list(self.clewsb_config['STORAGE_TECHNOLOGY'].keys())
        # tech_sets = list(TECHNOLOGY_df['VALUE'])
        # for tech in storage_techs:
        #     if tech not in tech_sets:
        #         tech_sets.append(tech)

        # if tech_sets:
        #     tech_sets_df = pd.DataFrame(tech_sets, columns=['VALUE'])
        #     tech_sets_df.to_csv(TECHNOLOGY_set_file_path, index=False)
        #     utils.print_update(level=3,
        #     message=f"File Updated with STORAGE TECHNOLOGY: {self.input_csv_dir / 'TECHNOLOGY.csv'}")
        # else:
        #     pass
    # ---------------------------
        #4. Handle missing FUELs in FUEL SET
            # Handles the missing fuel LND4PWR in FUELs
            FUEL_set_file_path=Path(self.SETs_save_to / 'FUEL.csv')
            FUEL_df=pd.read_csv(FUEL_set_file_path)
            
            new_fuels = ['LND4PWR', 'CO2CCS',]
            for fuel in new_fuels:
                if fuel not in FUEL_df['VALUE'].values:
                    new_row = pd.DataFrame([{'VALUE': fuel}])
                    FUEL_df = pd.concat([FUEL_df, new_row], ignore_index=True)
                    FUEL_df.to_csv(FUEL_set_file_path, index=False)
                    utils.print_update(level=3,
                    message=f"File Updated with FUEL: {fuel}")
        
        # Handle additional MODE_OF_OPERATION 
        # MOP_set_file_path=Path(self.SETs_save_to / 'MODE_OF_OPERATION.csv')
        # MOP_df=pd.read_csv(MOP_set_file_path)
        # if 57 not in MOP_df['VALUE'].values:
        #     new_row = pd.DataFrame([{'VALUE': '57'}])
        #     MOP_df = pd.concat([MOP_df, new_row], ignore_index=True)
        #     MOP_df.to_csv(MOP_set_file_path, index=False)
        #     utils.print_update(level=3,
        #         message=f"File Updated with FUEL: {MOP_set_file_path}")
        # else:
        #     pass
        
    def get_csv_template(self,
                         force_replace:bool=False):
        
        utils.print_update(level=2,message= "checking input CSVs...")
        ### Copying CSV Templates  >>> This should be done before other param update scripts, make it part of workflow
        utils.copy_csv_files(self.input_csv_templates, 
                                      self.clews_build_input_csv_dir,
                                      all_files=force_replace)
        utils.print_update(level=2,
                           message=f"Checked and copied missing CSV files from {self.input_csv_templates} to {self.clews_build_input_csv_dir}")
    
            
    def get_clews_builder_attributes(self):
        """
        Updates the CLEWS builder configuration and returns the updated information as a dictionary. It's a wrapper of 'update_clews_builder_config' function from clews_builder.py.
            > Currently support TECHNOLOGY aggregation for POWERPLANTS and STORAGE.
        ## Returns:
            `resources_structure`: A dictionary where each key represents a resource type (e.g., solar, wind, tpp, hydro)
                - Each key (resource type) constrains the updated schema (dictionary) for that resources as following :
                    - `capacity`: A string representing the resource's capacity (e.g., '100 MW')
                    - `operational_life`: An integer indicating the resource's operational life in years
                    - `capital_cost`: A float value representing the initial cost to set up the resource (e.g., 1,000,000)
                    - `variable_cost`: A float value representing the cost to operate the resource per unit of output (e.g., 50)
                    - `efficiency`: A float representing the efficiency of the resource (e.g., 0.85)
                    - `availability_factor`: A float representing how often the resource is available for use (e.g., 0.9)
                """
        utils.print_update(level=2,message="Updating CLEWS Builder configuration file...")
        _structure_= schema_processor.update_clews_builder_config(self.clews_builder_config_path)
        """ 
        `_structure_` is a complex tuple containing dictionaries (dict) of resources schema in the following order: \
            0 → new_pwrwnd_structure 
            1 → new_pwrwnd_future_structure 
            2 → new_pwrsol_structure
            3 → `new_pwrsol_future_structure
            4 → new_inflow_structure 
            5 → new_hydro_structure 
            6 → new_tpp_bio_structure 
            7 → new_tpp_ngs_structure
        
        `resources_structure` is a dictionary to assign these tuples under 'keys' e.g. `wind` : `new_pwrwnd_structure` , `wind_future` : `new_pwrwnd_future_structure` etc.
        """
        # We map resource names to the tuple of structures for clarity and easy navigation to data
        self.resources_structure = {
            "wind": _structure_ [0],
            "wind_future": _structure_ [1],
            "solar": _structure_ [2],
            "solar_future": _structure_[3],
            "hydro_inflow": _structure_ [4],
            "hydro":_structure_ [5],
            "tpp_bio": _structure_ [6],
            "tpp_ngs": _structure_ [7],
        }
        return self.resources_structure

    def update_global_params(self):
        utils.print_update(level=2,
                           message="Updating Global params' data")
        update_global_params.update_capacity_to_activity_unit(self.clews_build_input_csv_dir)
         
    def update_set_TECHNOLOGY(self):
        """
        If the clews_builder.yaml gets updated (typically with updated power technologies, different aggregation level, new resource options) 
        then the TECHNOLOGY set needs an update to harmonize input data.
        
        Assuming input_csv_dir ='data/clews_data' 
            - 1 Reads the input_csv_dir/'TECHNOLOGY.csv',
            - 2 Loads the updated clews_builder.yaml 
            - 3 Adds new TECHNOLOGY in the SET csv if any missing.
        """
        # Read the CSV file
        SET_file_path=self.clews_build_input_csv_dir/'TECHNOLOGY.csv'
        SET_df = pd.read_csv(SET_file_path)
        utils.print_update(level=3,
                    message=f"Harmonizing {SET_file_path} with clews builder configuration")
        # clews builder dict (already loaded, existing file/skeleton) should not be loaded via attributes parser instance,
        # rather needs to be loaded again directly from yaml to reflect changes in that dictionary after the `Update_clews_builder` method.
        self.clewsb_config:dict=self.aparser.load_config(self.clews_builder_config_path) 
        
        # Create a list to accumulate new keys
        new_keys = []
        
        # Iterate through each technology and its keys
        for tech in self.clewsb_config['TECHNOLOGIES'].keys():
            tech_keys = self.clewsb_config['TECHNOLOGIES'][tech].keys()
            for key in tech_keys:
                if key not in SET_df['VALUE'].values:
                    new_keys.append(key)
        
        # Add new keys to the 'VALUE' column if any
        if new_keys:
            new_keys_df = pd.DataFrame(new_keys, columns=['VALUE'])
            SETs_updated_df = pd.concat([SET_df, new_keys_df], ignore_index=True)
        
            # Save the updated CSV
            SETs_updated_df.to_csv(SET_file_path, index=False)
            utils.print_update(level=4,
                    message=f"Updated {SET_file_path} with new keys {new_keys}")
        else:
            utils.print_update(level=4,
                    message=f"{SET_file_path} checked.")

    def update_set_STORAGE(self):
        """
        If the clews_builder.yaml gets updated (typically with updated power technologies, different aggregation level, new resource options) 
        then the STORAGE set needs an update to harmonize input data.
        
        Assuming input_csv_dir ='data/clews_data' 
            - 1 Reads the input_csv_dir/'STORAGE.csv',
            - 2 Loads the updated clews_builder.yaml 
            - 3 Adds new STORAGE in the SET csv if any missing.
        """
        # Read the CSV file
        SET_file_path=self.clews_build_input_csv_dir/'STORAGE.csv'
        SET_df = pd.read_csv(SET_file_path)
        utils.print_update(level=3,
                    message=f"Harmonizing {SET_file_path} with clews builder configuration")
        # clews builder dict (already loaded, existing file/skeleton) should not be loaded via attributes parser instance,
        # rather needs to be loaded again directly from yaml to reflect changes in that dictionary after the `Update_clews_builder` method.
        self.clewsb_config:dict=self.aparser.load_config(self.clews_builder_config_path) 
        
        # Create a list to accumulate new keys
        new_keys = []
        
        # Iterate through each technology and its keys
        for tech in self.clewsb_config['STORAGE'].keys():
          if tech not in SET_df['VALUE'].values:
                new_keys.append(tech)
        
        # Add new keys to the 'VALUE' column if any
        if new_keys:
            new_keys_df = pd.DataFrame(new_keys, columns=['VALUE'])
            SETs_updated_df = pd.concat([SET_df, new_keys_df], ignore_index=True)
            # Save the updated CSV
            SETs_updated_df.to_csv(SET_file_path, index=False)
            utils.print_update(level=3,
                    message=f"Updated {SET_file_path} with new keys {new_keys}")
        else:
            utils.print_update(level=4,
                    message=f"{SET_file_path} checked.")
    
    def update_yearly_params(self):
        """
        Updates yearly parameters by calling the "clews_yearly_params" module.
        """
        utils.print_update(level=2,
                    message="Updating yearly params' data")
        update_yearly_params.main(self.clewsb_config)
    
    def get_capacity_factor_profiles(self,
                                     resources_structure:dict=None) -> pd.DataFrame:
        """
        This method generates the Capacity Factor (CF) data with 1-hour resolution, 
        i.e., 8760 time slices for a year, and saves it as a CSV file.
        
        ### Key Features:
            - Supports multiple resources like wind, solar, and hydro.
            - Produces consistent outputs for integration with CLEWS tools.

        ### Example of Future Extension:
            - To include a new resource, e.g., "__offshore wind__":
                1. Update the `update_clews_builder` method to include its structure.
                2. Add the corresponding time series data and its file path to `file_paths` and `time_series_data`.
                3. Map the new structure to its time series data in `clews_structure_mapping`.

        ### Benefits of this Structure:
            - Modular design ensures straightforward extensibility.
            - Centralized configuration for file paths and data mapping reduces redundancy.
        """

        
        # File paths for input and output
        file_paths = {
            "wind_ts": self.ext_wind_CF,
            "future_wind_ts": self.future_wind_CF, 
            "committed_wind_ts": self.committed_wind_CF,
            "solar_ts": self.ext_solar_CF ,
            "future_solar_ts": self.future_solar_CF,
            "committed_solar_ts": self.committed_solar_CF,
            "hydro_reservoir_ts": self.hydro_res_CF,
            "hydro_ror_ts" :self.hydro_ror_ts,
            "capacity_factor_out": self.clews_CF_csv_file ,
        }
        
        # Load and parse datetime index
        future_wind_ts = pd.read_csv(file_paths["future_wind_ts"], index_col=0, parse_dates=True)
        # future_wind_ts = future_wind_ts[~future_wind_ts.index.duplicated()]  # Handle duplicates

        committed_wind_ts = pd.read_csv(file_paths["committed_wind_ts"])
        # committed_wind_ts = committed_wind_ts[~committed_wind_ts.index.duplicated()]  # Handle duplicates
        committed_wind_ts.index = future_wind_ts.index

        # Concatenate after ensuring unique indices
        future_wind_df = pd.concat([future_wind_ts, committed_wind_ts], axis=1)
        future_wind_df.drop(columns=['time'], inplace=True)
   
        
        # Load and parse datetime index
        future_solar_ts = pd.read_csv(file_paths["future_solar_ts"], index_col=0, parse_dates=True)
        # future_solar_ts = future_solar_ts[~future_solar_ts.index.duplicated()]  # Handle duplicates

        committed_solar_ts = pd.read_csv(file_paths["committed_solar_ts"])
        committed_solar_ts.index = future_solar_ts.index

        # committed_solar_ts = committed_solar_ts[~committed_solar_ts.index.duplicated()]  # Handle duplicates

        # Concatenate after ensuring unique indices
        future_solar_df = pd.concat([future_solar_ts, committed_solar_ts], axis=1)
        future_solar_df.drop(columns=['time'], inplace=True)

        
        # Read all required time series data
        time_series_data = {
            "wind": pd.read_csv(file_paths["wind_ts"]),
            "future_wind": future_wind_df,
            "solar": pd.read_csv(file_paths["solar_ts"]),
            "future_solar":future_solar_df,
            "hydro_reservoir": pd.read_csv(file_paths["hydro_reservoir_ts"]),
            "hydro_ror": pd.read_csv(file_paths["hydro_ror_ts"]),
        }

        # Update CLEWS builder structures

        # Map CLEWS builder structures to time series data
        structure_mapping = {   #make it inline with returns from 'self.update_clews_builder()' method
            "wind": time_series_data["wind"],
            "wind_future": time_series_data["future_wind"],
            "solar": time_series_data["solar"],
            "solar_future": time_series_data["future_solar"],
            "hydro_inflow": time_series_data["hydro_reservoir"],
            "hydro": time_series_data["hydro_ror"], # adopts ror ts only
        }

        # Generate capacity factor rows
        rows = []
        for resource, ts_data in structure_mapping.items():
            resources_structure_dict = resources_structure[resource] if resources_structure else self.resources_structure[resource]  # Get the corresponding structure
            rows.extend(
                schema_processor.generate_capacity_factor(
                    resources_structure_dict, 
                    ts_data, 
                    self.region, 
                    self.start_year
                )
            )

        # Create DataFrame and save to CSV
        capacity_factor_df = pd.DataFrame(rows)
        capacity_factor_file_out = Path(file_paths["capacity_factor_out"])
        capacity_factor_df.to_csv(capacity_factor_file_out, index=False)
        utils.print_update(level=3,
                    message=f"Capacity factor CSV file saved at: {capacity_factor_file_out}")

        return capacity_factor_df
    
    def get_specified_demand_profiles(self)-> pd.DataFrame:
        """
        Generates specified demand profile CSV files with 1-hour resolution for a year.
        """

        # File paths
        file_paths = {
            "demand_data": self.demand_profile,
            "specified_demand_out":  self.clews_demand_profile,
        }
        # Define demands
        demands = ['COMELCB02', 'INDELCB02', 'RESELCB02', 'TRAELCB02'] # don't have data for 'xx'
        
        # Load and preprocess demand data
        df = pd.read_csv(file_paths["demand_data"])
        df_filtered = schema_processor.preprocess_demand_data(df)  # Preprocesses the demand data by filtering outlier days like leap-year, normalizing, and ensuring data integrity.

        # Generate demand profile rows
        demand_rows = schema_processor.generate_demand_profile(demands, 
                                                            df_filtered, 
                                                            self.region, 
                                                            self.start_year)

        # Combine rows into a DataFrame
        specified_demand_profile_df = pd.concat(demand_rows, 
                                                ignore_index=True)

        # Save the DataFrame to a CSV file
        specified_demand_profile_file_out = Path(file_paths["specified_demand_out"])
        specified_demand_profile_df.to_csv(specified_demand_profile_file_out, index=False)
        utils.print_update(level=3,
                    message=f"Specified demand profile CSV file saved at: {specified_demand_profile_file_out}")

        return specified_demand_profile_df
    
    def get_clustering_attributes(self):
        """
        Calculates the clustering attributes to scale (downscale) the profiling parameters' data.
        
        # Jobs:
            - Calculates `BuildModel` Class attributes associated to temporal clustering e.g.
                - `timeslices`
                - `representative_days`
                - `chronological_sequence`
                - `daytypes`
                - `year_split`
                - `day_split`
                
        """

        utils.print_update(level=2,
                           message="Calculating clustering attributes")
        #1. Get Clustering attributes from user configuration e.g. timeslices,chronological_timeslices, year_split, day_split, daytypes, chronological_timeslices
        self.n_clusters = (self.clustering_attributes.get('n_clusters') if self.clustering_attributes else None)
        self.hour_grouping = (self.clustering_attributes.get('hour_grouping') if self.clustering_attributes else None) 
        
        self.days_in_year = 365  # assuming non-leap year for clustering purposes
        # Number of blocks per day based on the hour grouping
        self.blocks_per_day = 24 // self.hour_grouping
        
        #2. Scale profiles (CF, Demand) as per Clustering attributes and revise the clews data for CF and Demand profiles
        self.representative_days, self.chronological_sequence = schema_processor.cluster_data(self.ext_wind_CF, 
                                                                                        self.ext_solar_CF, 
                                                                                        self.demand_profile, 
                                                                                        self.n_clusters)
        
        # Total timeslices considering the representative days
        self.timeslices = len(self.representative_days) * self.blocks_per_day
        
        utils.print_update(level=2,
                           message=f"No. of Timeslices configured= {self.timeslices}")
        
        # Chronological timeslices is number of days in year * blocks per day. If hourly analysis, chronological timeslices is 8760
        self.chronological_timeslices = self.days_in_year * self.blocks_per_day
        self.daytypes = len(self.representative_days)
        self.year_split = 1 / self.timeslices
        self.day_split = self.hour_grouping / (24 * 365)
        utils.print_update(level=4,
                    message=f"Representative days: {self.representative_days}")
    
    def get_profiles(self,
                     force_update:bool=False):
        """
        Prepares the profiling params data harmonized with CLEWs schema.
         > Currently supports Capacity Factors (CF), Specific Demand Profile (SDP) parameter data.
         
        ## Job:
            - 1 Applies separated methods to collect CF, SDP data. 
            - 2 Drops in inside hourly data point sub-directory of input_csvs (e.g. data/clews_data/inputs_csv_8760).
        
        """
        utils.print_update(level=2,message="Preparing profiling parameters for BCNexus")
        #2 Checks the CF source data and collects highest resolution (1hour) data and refactors to clews schema profiles
        if self.clews_CF_csv_file.exists():
            if force_update:
                utils.print_warning("Forcing update of Capacity Factor profiles...")
                self.get_capacity_factor_profiles()
            else:
                utils.print_info("Capacity Factor profiles file already exists. Skipping update.")
        else:
            self.get_capacity_factor_profiles()
        
        if self.clews_demand_profile.exists():
            if force_update:
                utils.print_warning("Forcing update of Demand profiles...")
                self.get_specified_demand_profiles()
            else:
                utils.print_info("Demand profiles file already exists. Skipping update.")
        else:        
            #3 Checks the Demand source data and collects highest resolution (1hour) data and refactors to clews schema profiles
            self.get_specified_demand_profiles()
    
    
    def update_storage_case_temporal_schema(self):
        # Updating TIMESLICE
    
        self.timeslice_csv_file = self.storage_case_input_csvs/'TIMESLICE.csv' #config['FILES']['timeslice_file']
        schema_processor.new_list(self.timeslices, self.timeslice_csv_file)

        # Updating daytype
        self.daytype_csv_file =  self.storage_case_input_csvs/'DAYTYPE.csv' #config['FILES']['daytype_file']
        schema_processor.new_list(self.daytypes, self.daytype_csv_file)
    
        ### Updating YEARSPLIT
        self.yearsplit_csv_file =  self.storage_case_input_csvs/'YearSplit.csv' #config['FILES']['yearsplit_file']
        
        schema_processor.yearsplit(self.timeslices, 
                                self.representative_days,  
                                self.chronological_sequence, 
                                self.days_in_year, 
                                self.start_year, 
                                self.yearsplit_csv_file)
        schema_processor.replication(self.yearsplit_csv_file, 
                                  self.start_year, 
                                  self.last_year)
        
        ### Updating storage sets
        if self.storage_algorithm == 'Kotzur':
            # Updating dayscro
            output_dayscro_csv_file = self.storage_case_input_csvs/'DAYSCRO.csv'
            schema_processor.new_list(self.days_in_year, output_dayscro_csv_file)
        
            # Updating conversionld
            output_conversionld_csv_file =self. storage_case_input_csvs/'Conversionld.csv' # case_info['input_otoole_csv']['conversionld']
            schema_processor.conversionld(self.timeslices, len(self.representative_days), output_conversionld_csv_file)
            # Updating conversionldc
            output_conversionldc_csv_file =  self.storage_case_input_csvs/'Conversionldc.csv' # case_info['input_otoole_csv']['conversionldc']
            schema_processor.conversion(self.chronological_sequence, self.representative_days, self.days_in_year, output_conversionldc_csv_file)
            
    def get_profiling_Params(self):
        
        """
        Wrapper to load the highest resolution profiling data (CF, SDP) and 

        
        # Jobs: 
        Wrapped around 'CF_and_SDP" function from clews_builder.py
            - Takes in:
                - highest resolution profile from `data/clews_data/inputs_csv_8760`
                - clustering attributes: `representative_days' , `hour_grouping'
            - Creates the clustered data in CLEWs schema @ `data/clews-data/inputs_csv`.
        """
        utils.print_update(level=2,
                           message="Updating profiling parameters (CF,SDP) with user configured clusters")
        ### Update profiling Params (CF, Specific Demand Profile)
        self.CF_csv_file = self.clews_build_input_csv_dir/'CapacityFactor.csv' # config['FILES']['capacity_factor_file']
     
        # Updating capacity factor (averaging the values)
        schema_processor.CF_and_SDP(self.clews_CF_csv_file,
                        self.representative_days,
                        self.hour_grouping,
                        self.CF_csv_file,
                        operation='mean')

        # Data formatting
        schema_processor.replication(self.CF_csv_file,
                            self.start_year,
                            self.last_year,
                            group_by='TECHNOLOGY')

        # Updating specified demand profile (summing the values)
        self.SDP_csv_file =  self.clews_build_input_csv_dir/'SpecifiedDemandProfile.csv' #config['FILES']['specified_demand_profile_file']
        schema_processor.CF_and_SDP(self.clews_demand_profile, 
                            self.representative_days, 
                            self.hour_grouping, 
                            self.SDP_csv_file, 
                            operation='sum')
        
        schema_processor.replication(self.SDP_csv_file,
                                self.start_year, 
                                self.last_year, 
                                group_by='FUEL')
    
    def update_otoole_config(self):
        ### Updating otoole yaml file
        utils.print_update(level=1,message="Updating Otoole config file...")
        
        # Updating day split in yaml file
        schema_processor.new_yaml_param(self.otoole_yaml_file, 'DaySplit', self.day_split)
        utils.print_update(level=2,message=f"DaySplit param added to {self.otoole_yaml_file}")

        # schema_processor.new_yaml_param(self.otoole_yaml_file, 'StorageMaxCapacity', self.StorageMaxCapacity)
        schema_processor.new_yaml_param(self.otoole_yaml_file, 'ResidualStorageCapacity', self.ResidualStorageCapacity)
        utils.print_update(level=2,message=f"ResidualStorageCapacity param added to {self.otoole_yaml_file}")
        
    def collect_input_checker_report(self,
                                     case_datafiles:Path):
            # Create an instance of the class with the directory containing CSV files
            clews_data_checker:clews_data_module = clews_data_module.GetDataPackage(case_datafiles)

            # Get all DataFrames in the dictionary
            SETS_dfs,Params_dfs = clews_data_checker.load_data()

            checker=clews_data_module.Checker(SETS_dfs,Params_dfs)
            checker.get_summary_report(self.scenario_inputs_root/'Input_checker_summary_report.txt')
 
    def trim_snapshot_data(self,csvs_dir=None):
        
        utils.print_update(level=2,
                    message=f"Harmonizing the snapshot [{self.start_year}-{self.last_year}] for YEAR set and all Params associated to this set.")
        utils.print_update(level=3,
                    message="[i] The snapshot is configured via clews_model_constraint.py module's 'snapshot' dictionary.")
        
        if csvs_dir is None:
            csvs_dir=Path(self.clews_build_input_csv_dir)
        else:
            csvs_dir=Path(csvs_dir)
        
        SETS_dfs,Params_dfs=self.clean_up_SETs_and_Params_definitions(csvs_dir)
        
        for index, row in SETS_dfs['YEAR'].iterrows():
            if row['VALUE'] < self.start_year or row['VALUE'] > self.last_year:
                SETS_dfs['YEAR'].drop(index, inplace=True)
        SETS_dfs['YEAR'].to_csv(csvs_dir / 'YEAR.csv', index=False)

        for k_param, v_df in Params_dfs.items():
                    if 'YEAR' in v_df.columns:
                        for index, row in v_df.iterrows():
                            if int(row['YEAR']) < self.start_year or int(row['YEAR']) > self.last_year:
                                v_df.drop(index, inplace=True)
                        v_df.to_csv(csvs_dir / f'{k_param}.csv', index=False)
        """ 
        >>> Error Handling, Temp code
        if 'ReserveMarginTagFuel' not in Params_dfs.keys():
            v_df=pd.read_csv(csvs_dir / 'ReserveMarginTagFuel.csv')
            if 'YEAR' in v_df.columns:
                for index, row in v_df.iterrows():
                    if int(row['YEAR']) < self.start_year or int(row['YEAR']) > self.last_year:
                        v_df.drop(index, inplace=True)
                v_df.to_csv(csvs_dir / f'{k_param}.csv', index=False)
                utils.print_update(level=3,message='ReserveMarginTagFuel.csv updated @ {csvs_dir}')
            
        return SETS_dfs, Params_dfs
        """
    def update_TotalAnnualMaxCapacityInvestment(self, 
                                                tech_prefix:str,
                                                input_csv_dir:Path|str=None      
                                                ):
        """
        Updates the TotalAnnualMaxCapacityInvestment CSV filebased on the provided technology prefix (3 characters) and input CSV directory.
        # Args:
            tech_prefix (str): The prefix of the technology (e.g. `HDG`,`CCS`) types to filter. Defaults to None.
            input_csv_dir (Path or str): The directory containing the input CSV file. Defaults to None.
        # Returns:
            None
            
        This function reads the 'TotalAnnualMaxCapacityInvestment.csv' file from the specified input directory,
        appends new rows for future technologies starting from their start year up to 2050, and writes the updated
        DataFrame back to 'models/BC_Nexus/csv_template/TotalAnnualMaxCapacityInvestment.csv'.
        """
        utils.print_update(level=1,message="Updating Total Annual Max Capacity investment")
        input_csv_dir=Path(input_csv_dir)
            
        file_path=input_csv_dir/'TotalAnnualMaxCapacityInvestment.csv'
        
        TotalAnnualMaxCapacityInvestment_df = pd.read_csv(file_path)
        # Create a list to store new rows
        new_rows = []
        for k_tech_type, k_techs_info in self.clewsb_config.get('TECHNOLOGIES', {}).items():
            if k_tech_type[:3] == tech_prefix:
                for k_tech_id, k_tech_id_info in k_techs_info.items():
                    if k_tech_id[0:3]=="HDG" or k_tech_id[0:3]=="CCS":
                        for year in range(k_tech_id_info.get('start_year', self.start_year), self.last_year + 1):
                            total_annual_max_capacity = k_tech_id_info.get('total_annual_max_capacity', 1)
                            total_annual_min_capacity = k_tech_id_info.get('total_annual_min_capacity', '0')
                            if isinstance(total_annual_min_capacity, str) and total_annual_min_capacity.startswith('['):
                                min_capacity_values = eval(total_annual_min_capacity)
                                for i, min_capacity in enumerate(min_capacity_values):
                                    new_rows.append({
                                        'REGION': 'REGION1',
                                        'TECHNOLOGY': k_tech_id,
                                        'YEAR': year + i,
                                        'VALUE': min(min_capacity, total_annual_max_capacity)  # GW
                                    })
                            else:
                                new_rows.append({
                                    'REGION': 'REGION1',
                                    'TECHNOLOGY': k_tech_id,
                                    'YEAR': year,
                                    'VALUE': min(1, total_annual_max_capacity)  # GW
                                })
                    else:
                        if k_tech_id_info.get('status') == "future":
                            for year in range(k_tech_id_info.get('start_year', 2032), 2051):
                                new_rows.append({
                                    'REGION': 'REGION1',
                                    'TECHNOLOGY': k_tech_id,
                                    'YEAR': year,
                                    'VALUE': min(1, k_tech_id_info.get('potential', 1))  # GW
                            })

        # Convert list to DataFrame and concatenate
        TotalAnnualMaxCapacityInvestment_df = pd.concat([TotalAnnualMaxCapacityInvestment_df, pd.DataFrame(new_rows)], ignore_index=True)
        TotalAnnualMaxCapacityInvestment_df.to_csv(file_path, index=False)
        utils.print_update(level=2,message=f"File updated for {k_tech_id} : {file_path}")
    
    
    def update_temporal_profiles(self):
        # Apply Methods to modify template input files on set configs (currently supports: simplified temporal clustering, power technology aggregation)
        
    #1  
        self.get_profiles()
            
    #2
        utils.print_update(level=1,
            message='updating temporal profiles')
        self.get_clustering_attributes()
        self.get_profiling_Params()
    
    def build(self,
            include_livestock:bool=True,
            update_clews_builder: bool=True):

    # Builds SETs and Ratios (input/output activities) if the Model structure/connection needs to be changed.
        # EL_20251116 , spotted bugs in outputs
        self.build_SETs_and_ratios(include_livestock) # has bugs
        utils.copy_csv_files(src_folder=self.SETs_save_to, 
                             dest_folder=self.clews_build_input_csv_dir, 
                             all_files=True)
        # self.clean_up_SETs_and_Params_definitions()
    
    #------------------------------------------------------------ 
    # @config/clews_builder.config
    #---------------------------------------------------------------
    #1
        if update_clews_builder:
            utils.print_update(level=2,
            message="Updating 'clews_builder.config' to match data and user configurations (aggregation and naming of the TECHNOLOGIES).")
            self.get_clews_builder_attributes() # Currently supports simplified power technology aggregation.
            utils.print_info("Reloading the updated clews_builder configuration...")
            self.clewsb_config:dict=utils.load_config(self.clews_builder_config_path)
        else:
            utils.print_update(level=2,
            message="Skipping clews_builder update due to default setting (recommended). Developers may change 'update_clews_builder':bool to 'True' to force update.")
            pass
        
        utils.print_update(level=2,
            message=f'updating SETs and Parameters inside {self.storage_case_input_csvs}')
        
    #------------------------------------------------------------ 
    # @ data/clews_data/inputs_csv   
    #--------------------------------------------------------------
    
    #2 Get clustered profiles (CF, Demand) i.e. scaling the highest resolution CF, Demand profile (clews schema)
        self.update_temporal_profiles()  
    #3 Update SETs, to make sure it's harmonized with the current clews_builder.yaml

        utils.print_update(level=2,message="Checking SETs (TECHNOLOGY, STORAGE) to harmonize clews builder configuration")
        self.update_set_TECHNOLOGY()
        self.update_set_STORAGE()
        
    #4 Updates OperationalLife,OperationalLifeStorage,AvailabilityFactor,CapitalCost,CapitalCostStorage,TechnologyToStorage,TechnologyFromStorage,TotalAnnualMaxCapacity
        self.update_yearly_params() # Updates the associated parameters affected due to technology aggregation          
    #5 Updates CapacityToActivityUnit
        self.update_global_params()
    #6
        self.trim_snapshot_data(self.clews_build_input_csv_dir)
        
    # #5  Transfer processed files to data/clews_data/inputs_csv/Model_Kotzur or Model_Niet
    #     utils.copy_csv_files(src_folder=self.clews_build_input_csv_dir,
    #                        dest_folder=self.storage_case_input_csvs,
    #                        all_files=True)
        
    #5 @ data/clews_data/inputs_csv/Model_Kotzur or Model_Niet
        # self.update_storage_case_SETs()
    
    # 6 
        self.update_otoole_config()
        
    


    # def build(self,
    #           include_livestock:bool=True,
    #         update_clews_builder:bool=False):
    #     # Apply Methods to modify template input files on set configs (currently supports: simplified temporal clustering, power technology aggregation)

    # #1  
    #     utils.print_update(level=1,
    #         message='updating CLEWs builder config, SETs and Parameters')
    #     self.update_sets_params(include_livestock,
    #                             update_clews_builder)
        
    #     utils.print_update(level=1,
    #                 message='Preparing the summary reports for input data')
    #     self.collect_input_checker_report(self.storage_case_input_csvs)
    

# if __name__ == "__main__":
#     # Set up argument parsing
#     parser = argparse.ArgumentParser(description='Run CLEWs parameter update script')

#     # Optional arguments with default values
#     parser.add_argument('--combined_model_config', 
#                         type=str, 
#                         default=str(Path("config/config.yaml")), 
#                         help="Path to the combined model configuration file (default: 'default_combined_model_config.yml')")
    
#     # Optional arguments with default values
#     parser.add_argument('--scenario', 
#                         type=str, 
#                         default=str('Base'), 
#                         help="Scenario names that are already defined via config.yaml")
    
        
#     # Optional arguments with default values
#     parser.add_argument('--storage_algorithm', 
#                         type=str, 
#                         default=str('Kotzur'), 
#                         help="Storage Algorithm name (supports Niet, Kotzur). Defaults to 'Kotzur'")
    
#     # Parse the arguments
#     args = parser.parse_args()

#     clews_module = BuildModel(args.combined_model_config,
#                               args.scenario,
#                               args.storage_algorithm)
#     clews_module.build()
                    
   