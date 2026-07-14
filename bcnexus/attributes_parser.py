from datetime import datetime

import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict
import logging as log
from datetime import datetime
# Local Package
from bcnexus.clews import model_structure as clews_const
from bcnexus import utils

# Logging Configuration
log.basicConfig(level=log.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

"""
# Key Changes and Benefits over v1
    The @dataclass decorator simplifies class creation and automatically generates the __init__, __repr__, and other methods.

## Field Initialization:
    Attributes that require processing during initialization (like reading configurations) are defined with init=False and processed in the __post_init__ method.

## Default Values:
    The resource_type has a default value specified directly in the field declaration, which simplifies the __init__ method.

## Type Annotations:
    Type hints enhance code readability and help with type checking tools.
"""

CONFIG_ROOT=Path('config')

@dataclass
class AttributesParser:
    """ 
    This is the parent class that will extract the core attributes from the User Config file. Default is set to 'config/scenarios_bcnexus.yaml'.
    
    ## Remarks:
        - Handles the clews_builder.yaml file creation and updates under-the hood.  
        - The clews_builder.yaml file if not exists will mirror the skeleton file sourced from 'models/BC_Nexus/config/clews_builder_skeleton.yaml'
    """
    scenarios_cfg_path: Path | str = field(
        default_factory=lambda: CONFIG_ROOT / "scenarios_bcnexus.yaml"
        )
    
    def __post_init__(self):
        # Handle explicit None from caller
        if self.scenarios_cfg_path is None:
            self.scenarios_cfg_path = CONFIG_ROOT / "scenarios_bcnexus.yaml"

        self.scenarios_cfg_path = Path(self.scenarios_cfg_path)
        
    # Define constants for defaults
        self.DEFAULT_STORAGE_ALGORITHM:str = "Kotzur"
        self.supported_storage_algorithms:list = ["Kotzur", "Niet"]
        self.runtag:str = datetime.now().strftime("%Y%m%d")  # Timestamp for tagging runs
      
    # CLEWs Builder related paths
        self.clews_data_root=utils.ensure_path('data/clews_data')
        self.clews_build_data_root=utils.ensure_path(self.clews_data_root / 'clews_build_data')
        self.clews_build_inputs=utils.ensure_path(self.clews_build_data_root / 'input_csvs')
        self.clews_build_CF_source_path= utils.ensure_path(self.clews_build_data_root / 'inputs_csv_8760')
    
    # Configuration files paths
        self.data_cfg_path:str|Path=(CONFIG_ROOT/'data_sources.yaml')
        self.clews_builder_config_path:str|Path=CONFIG_ROOT/'clews_builder.yaml' # Kept it as under the hood config file build and updated automatically.
        self.clews_builder_skeleton_source:str|Path=Path('models/clews_builder_skeleton.yaml')

    # Results paths
        self.clews_results_root=utils.ensure_path('results/clews')    
        
    # Handles BC Combined Model submodule paths
        self.bcnexus_as_bccm_submodule_path=Path('models/BC_Nexus')
        if not self.clews_builder_skeleton_source.exists():
            self.clews_builder_skeleton_source = self.bcnexus_as_bccm_submodule_path/ self.clews_builder_skeleton_source
        
        self.build_clews_builder_skeleton()
        
    # Load the user configuration master file by using the method
        self.data_cfg:Dict[str:dict]=AttributesParser.load_config(self.data_cfg_path)
        self.scenario_dict:Dict[str,dict] = AttributesParser.load_config(self.scenarios_cfg_path)
        self.clewsb_config:Dict[str,dict] = AttributesParser.load_config(self.clews_builder_config_path)
        
        self.log = log.getLogger(__name__)
    
    def get_runtag(self):
        """
        Generates a timestamp string in the format "YYYY_DD_MM_HHMM" for tagging runs.
        """
        self.runtag = datetime.now().strftime("%Y_%d_%m_%H%M")  

    
    def build_clews_builder_skeleton(self):
        """
        Builds the _*clews_builder.yaml*_ file if not exists from the skeleton source.
        """
        if not self.clews_builder_config_path.exists():
            self.clews_builder_skeleton: dict = AttributesParser.load_config(self.clews_builder_skeleton_source)
            with self.clews_builder_config_path.open('w') as file:
                yaml.dump(self.clews_builder_skeleton, file)
                utils.print_update(level=2,message=f"{__name__} | clews builder config was missing, created at {self.clews_builder_config_path} with the skeleton.")
        else:
            pass
    
    def get_LandCluster_paths(self)->tuple:
        """
        Collects the LandCluster data source and destination paths.
        Returns:
            tuple: _description_
        """
        source=Path('models/LandClusterData')
        dest=utils.ensure_path(self.clews_data_root/'LandClusterData')
        
        if not source.exists():
            source= self.bcnexus_as_bccm_submodule_path/ source
            if not source.exists():
                utils.print_error(f"{__name__} | LandCluster source data path does not exist. Please check the data source at : {source}")
        else:
            pass
        return (source,dest)
    
    def get_SETs_Path(self):
        return Path('data/clews_data/SETs')
    
    def get_plots_save_to(self)->Path:
        return utils.ensure_path('vis/plots')
    
    def get_SETs_save_to(self):
        SETS_save_to:Path=Path('data/clews/SETs')
        return SETS_save_to
    
    def get_visual_configs(self)->dict:
        visual_configs_path=self.config_root/'visualization_config.yaml'
        try:
            return AttributesParser.load_config(visual_configs_path)
        except Exception as e:
            raise ValueError(f"{__name__} | Error loading visual configuration from {visual_configs_path}: {e}")
    
    def get_clews_snapshot(self) -> tuple[int, int]:
        clews_snapshot: dict=clews_const.snapshot
        try:
            start_year=int(clews_snapshot['start'])
            last_year=int(clews_snapshot['end'])
            print(f"{__name__} | CLEWs snapshot configuration: start_year={start_year}, last_year={last_year}")
            return (start_year, last_year)
        except (KeyError, TypeError, ValueError) as e:
            raise ValueError(f"{__name__} | Invalid snapshot configuration at 'bcnexus/clews/model_structure.py': {e}")

    def get_region(self):
        # region=self.clews_cm['GENERAL'].get('region','REGION1')
        clews_regions:dict=clews_const.Regions
        current_region=next(iter(clews_regions)) # Get the first region as default
        utils.print_info(f"{__name__} | BCNexus CLEWs model is structured as SINGLE region model. Current region set to: {current_region}.")
        return current_region
    
    def get_default_csv_template_path(self)->Path:
        # csv_template_path=Path(self.clewsb_config.get('clews_datapackage_template','models/BC_Nexus/csv_template'))
        csv_template_path=Path('data/clews_data/csv_template')
        if not csv_template_path.exists():
            utils.print_error(f"{__name__} | CSV template path does not exist. Please check the data source at : {csv_template_path}")
        return csv_template_path
    
    
    def get_otoole_yaml_file(self,
                             storage_algorithm:str=None)->Path:
        
        if storage_algorithm is None:
            storage_algorithm = self.DEFAULT_STORAGE_ALGORITHM
            utils.print_info(f"{__name__} | No storage_algorithm specified. Using default: {storage_algorithm}.")
        else:
            storage_algorithm=storage_algorithm.capitalize()
        
        if storage_algorithm not in self.supported_storage_algorithms:
            raise ValueError(f"{__name__} | Unsupported storage_algorithm: {storage_algorithm}. Supported algorithms are: {self.supported_storage_algorithms}")

        otoole_config_path=Path(f'models/model_{storage_algorithm}/otoole_config_{storage_algorithm}.yaml')
        
        if not otoole_config_path.exists():
            otoole_config_path = self.bccm_dir_prefix/ otoole_config_path
        utils.print_info(f"{__name__} | Fetching OTOOLE config from : {otoole_config_path}")    
            
        return otoole_config_path
    
    def get_RESource_results_path(self):
        RESource_results_path=self.data_cfg.get('RESource',{}).get('results_root','data/RESource')
        RESource_results_path=Path(RESource_results_path)
        if RESource_results_path.exists():
            return RESource_results_path
        else:
            utils.print_error(f"{__name__} | RESource results path does not exist at {RESource_results_path}. Please collect RESource model results first.")

        
    def get_DEFAULT_CLUSTERING_ATTRIBUTES(self)->dict:
        """
        Returns the default clustering attributes if none are provided.
        
        ## Args:
            - clustering_attributes (dict, optional): User-defined clustering attributes. Defaults to None.
        
        ## Returns:
            - dict: Clustering attributes with defaults applied if necessary.
        """
        utils.print_info("Using default clustering attributes: {'hour_grouping': 6, 'n_clusters': 2}")
        return dict(hour_grouping=6,
                    n_clusters=2)

    def get_data_path_attributes(self):
        """
        ## Returns:
        
            - tuple: A tuple containing the following elements in order:  

            0 → `StorageMaxCapacity` (dict)  
                - Maximum storage capacity available for different regions or technologies.  

            1 → `ResidualStorageCapacity` (dict)  
                - Remaining or existing storage capacity after accounting for prior allocations.  

            2 → `ext_wind_CF` (pd.DataFrame)  
                - External wind capacity factors, providing wind resource availability over time.  

            3 → `ext_solar_CF` (pd.DataFrame)  
                - External solar capacity factors, representing solar generation potential over time.  

            4 → `demand_profile` (pd.DataFrame)  
                - Time-series data of energy demand across different regions or sectors.  

            5 → `hydro_res_CF` (pd.DataFrame)  
                - Capacity factors for hydro reservoir plants, indicating generation potential.  

            6 → `hydro_ror_ts` (pd.DataFrame)  
                - Time-series data for run-of-river hydro generation availability.  

            7 → `future_wind_CF` (pd.DataFrame)  
                - Projected wind capacity factors for future resource options.  

            8 → `future_solar_CF` (pd.DataFrame)  
                - Projected solar capacity factors for future resource options.  

            9 → `committed_wind_CF` (pd.DataFrame)  
                - Wind capacity factors for already committed wind projects.  

            10 → `committed_solar_CF` (pd.DataFrame)  
                - Solar capacity factors for already committed solar projects.  

            11 → `clews_CF_csv_file` (str)  
                - Path to the CLEWs capacity factor CSV file containing processed capacity factor data.  

            12 → `clews_demand_profile` (str)  
                - Path to the CLEWs demand profile CSV file with processed demand data. ` 
        """


    
    # =======================Battery Storage Attributes=============================
        battery_storage_cfg:dict= self.clewsb_config.get('STORAGE',{}).get('BATTERY',{})
        try:
            if not battery_storage_cfg:
                raise ValueError(f"{__name__} | Battery storage configuration is missing in clews_builder.yaml under STORAGE -> BATTERY.")
            StorageMaxCapacity =  int(battery_storage_cfg.get('storage_max_capacity', 9999999999))
            ResidualStorageCapacity =  int(battery_storage_cfg.get('residual_storage_capacity', 0))
        except Exception as e:
            utils.print_error(f"{__name__} | Error retrieving battery storage configuration: {e}")
            
    # ==============================Existing Resources' Data=============================
        pypsa_outputs_cfg:dict= self.data_cfg.get('output',{})
        
        ext_wind_CF = pypsa_outputs_cfg['create_ext_wind_ts']['fname'] # Path('data/processed_data/wind/existing/bc_ext_wind_ts.csv') 
        ext_solar_CF = pypsa_outputs_cfg['create_ext_solar_ts']['fname'] # Path('data/processed_data/solar/existing/bc_ext_solar_ts.csv') 

        hydro_res_CF = pypsa_outputs_cfg['reservoir_inflows']['fname']
        hydro_ror_ts=pypsa_outputs_cfg['ror_ps']['fname']
    
    # Demand Profile
        CODERS_data_paths:dict=self.data_cfg['CODERS']['datafiles']
        CODERS_root:Path=Path(CODERS_data_paths.get('root','data/downloaded_data/CODERS'))
        demand_profile = CODERS_root / CODERS_data_paths['demand_profile']
    
    ############# Future and Committed Resource Options from RESource Model ################
        RESource_results_cfg:Path=self.data_cfg.get('RESource',{})
        RESource_results_root:Path=Path(RESource_results_cfg.get('results_root','data/RESource'))
        # Future Resource Options (Committed/Planned)
        future_wind_CF=RESource_results_root / RESource_results_cfg.get('future_wind_CF','resource_options_wind_BC_timeseries.csv')
        future_solar_CF=RESource_results_root / RESource_results_cfg.get('future_solar_CF','resource_options_solar_BC_timeseries.csv')
        
        # Committed Resource Options, contracted but not existing (i.e. we don't have existing profiles for them)
        committed_wind_CF=RESource_results_root / RESource_results_cfg.get('committed_wind_CF','BCH_CFP24_wind_ts.csv')
        committed_solar_CF=RESource_results_root / RESource_results_cfg.get('committed_solar_CF','BCH_CFP24_solar_ts.csv')
        
    # Profiles (Capacity Factor, Specific Demand) from Existing Resources, formatted in CLEWs schema
        clews_CF_csv_file =  self.clews_build_CF_source_path / 'CapacityFactor.csv'
        clews_demand_profile =  self.clews_build_CF_source_path / 'SpecifiedDemandProfile.csv' 
        
        return (
            StorageMaxCapacity,
            ResidualStorageCapacity,
            ext_wind_CF,
            ext_solar_CF,
            demand_profile,
            hydro_res_CF,
            hydro_ror_ts,
            future_wind_CF,
            future_solar_CF,
            committed_wind_CF,
            committed_solar_CF,
            clews_CF_csv_file,
            clews_demand_profile       
        )
    
    def get_storage_case_input_csvs_path(
        self, 
        storage_algorithm: str
    ):

        return utils.ensure_path(self.clews_build_data_root/f'Model_{storage_algorithm}/storage_case_input_csvs')
    
    def get_scenario_results_path(self, 
                                  scenario:str,
                                  storage_algorithm:str,):
        return utils.ensure_path(self.clews_results_root/f'Model_{storage_algorithm}_{scenario}')
    
    def get_scenario_inputs_path(self,
                                scenario:str,
                                storage_algorithm:str,
                               ):
        
        case_ip_csvs=self.get_storage_case_input_csvs_path(storage_algorithm)
        # scenario_inputs_root=utils.ensure_path(case_ip_csvs/'scenarios'/scenario)
        return  case_ip_csvs
        
    def get_model_file_path(self,
                            storage_algorithm:str=None):

        if storage_algorithm is None:
            storage_algorithm=self.DEFAULT_STORAGE_ALGORITHM
            utils.print_info(f"{__name__} | No storage_algorithm specified. Using default: {storage_algorithm}.")
        else:
            storage_algorithm=storage_algorithm.capitalize()

        org_model_file = Path(f'models/model_{storage_algorithm}/model_BCNexus_{storage_algorithm}.m')
        if not org_model_file.exists():
            utils.print_info(f"{__name__} | Model file not found at {org_model_file}. Trying to fetch from BC Combined Model submodule path.")
            org_model_file = self.bccm_dir_prefix/ org_model_file
            if not org_model_file.exists():
                raise FileNotFoundError(f"Model file not found: {org_model_file}")
        return org_model_file
    
    @staticmethod
    def load_config(config_file_path: str|Path):
        """
        Loads a YAML configuration file and returns a dictionary.
        Includes robust error handling and clear logging.
        """

        config_file_path = Path(config_file_path)

        # ---- Check existence early ----
        if not config_file_path.exists():
            raise FileNotFoundError(
                f"Config file does not exist: {config_file_path}"
            )

        # ---- Attempt to load using your utility function first ----
        try:
            cfg_dict = utils.load_config(config_file_path)
            return cfg_dict
        except Exception as e:
            log.warning(
                f"utils.load_config failed at {config_file_path}. "
                f"Falling back to direct YAML load.\nError: {e}"
            )

        # ---- Fallback: direct YAML loading ----
        try:
            with open(config_file_path, "r") as f:
                cfg_dict = yaml.safe_load(f)
            return cfg_dict
        except Exception as e:
            log.error(
                f"Failed to parse YAML configuration at {config_file_path}.\n{e}"
            )
            raise