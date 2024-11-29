import pandas as pd
import argparse
import yaml
from bc_combined_modelling import utils
from bc_combined_modelling import clews_builder
from pathlib import Path
from bc_combined_modelling.AttributesParser_cm import AttributesParserExtended

   
def update_clews_builder_config(combined_model_config_path:Path,
                                clews_builder_config_path:Path,
                                )->tuple[dict]:
    """
    This function reads the existing CLEWS Builder Config file, takesn in required data files to identify existing and future resource options and updates the technology and other SET and PARAMETERS.
    ## Args:
        - combined_model_config_path
        - clews_builder_config_path
    """
    ##################################################################################################
    
    # Read the existing YAML file
    print(f"\n>> Updating CLEWS Builder configuration file...")
    cm_config:dict=utils.load_config(combined_model_config_path)
    clewsb_config:dict=utils.load_config(clews_builder_config_path)

    # Load data file directories
    wind_csv_file_path = cm_config['pypsa']['output']['create_ext_wind_assets'] ['fname']  # data_cfg['wind_file']
    wind_future_pkl_file_path = Path (cm_config['results']['linking']['root'])/ cm_config['results']['linking']['clusters_topSites']['wind'] #data_cfg['wind_future_file']
    solar_csv_file_path = cm_config['pypsa']['output']['create_ext_solar_assets'] ['fname']  # data_cfg['solar_file']
    solar_future_pkl_file_path = Path (cm_config['results']['linking']['root'])/ cm_config['results']['linking']['clusters_topSites']['solar'] # data_cfg['solar_future_file']
    tpp_csv_file_path = cm_config['pypsa']['output']['create_ext_tpp_assets'] ['fname']  #data_cfg['tpp_file']
    hydro_generation_csv_file_path = cm_config['pypsa']['output']['create_hydro_assets'] ['hydro_generation']  #  data_cfg['hydro_generation_file']
    hydro_resevoir_csv_file_path = cm_config['pypsa']['output']['create_hydro_assets'] ['hydro_reservoir']  # data_cfg['hydro_reservoir_file']
    hydro_reservoir_ts_file_path =  cm_config['pypsa']['output']['reservoir_inflows'] ['fname']  # data_cfg['data_8760']['CF_hydro_reservoir']

    # Define cascade groups from the YAML file
    cascade_group = cm_config['clews']['HYDRO_GENERATION']#['cascade_group_1']

    # Read the CSV files
    wind_df = pd.read_csv(wind_csv_file_path)
    wind_future_df = pd.read_pickle(wind_future_pkl_file_path)
    solar_df = pd.read_csv(solar_csv_file_path)
    solar_future_df = pd.read_pickle(solar_future_pkl_file_path)
    tpp_df = pd.read_csv(tpp_csv_file_path)
    hydro_generation_df = pd.read_csv(hydro_generation_csv_file_path)
    hydro_resevoir_df = pd.read_csv(hydro_resevoir_csv_file_path)
    hydro_reservoir_ts_df = pd.read_csv(hydro_reservoir_ts_file_path)

    # Create new PWRWND, PWRSOL, INFLOW and PWRHYD structures
    new_pwrwnd_structure = clews_builder.create_schema(wind_df, 
                                                       id_prefix='PWRWNDB')
    
    new_pwrwnd_future_structure = clews_builder.create_schema(wind_df, 
                                                                id_prefix='PWRWNDB', 
                                                                start_index=len(wind_df), 
                                                                future_df=wind_future_df)
    
    new_pwrsol_structure = clews_builder.create_schema(solar_df, id_prefix='PWRSOLB')
    
    new_pwrsol_future_structure = clews_builder.create_schema(solar_df, 
                                                                id_prefix='PWRSOLB', 
                                                                start_index=len(solar_df), 
                                                                future_df=solar_future_df)
    
    new_tpp_bio_structure = clews_builder.create_schema_tpp(tpp_df, 
                                                            id_prefix='PWRBIOB')
    
    new_tpp_ngs_structure = clews_builder.create_schema_tpp(tpp_df, 
                                                            id_prefix='PWRNGSB')
    
    new_inflow_structure = clews_builder.create_schema_inflow(hydro_generation_df, 
                                                                 hydro_resevoir_df, 
                                                                 hydro_reservoir_ts_df, 
                                                                 cascade_group, 
                                                                 'INFLOW')
    
    new_hydro_structure = clews_builder.create_schema_hydro(hydro_generation_df, 
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

    print(f"Updated YAML file saved at: {clews_builder_config_path}")
    
    return (new_pwrwnd_structure,
            new_pwrwnd_future_structure,
            new_pwrsol_structure,
            new_pwrsol_future_structure,
            new_inflow_structure,
            new_hydro_structure)

def main(
    combined_model_config:Path,
    clews_builder_config:Path
):
    # --------------------------------- Update the CLEWS builder config dict---------------------------------------------------------------
    print(f"\n>> Updating CLEWS Builder configuration file...")
    # (new_pwrwnd_structure,
    #  new_pwrwnd_future_structure,
    #  new_pwrsol_structure,
    #  new_pwrsol_future_structure,
    #  new_inflow_structure,
    #  new_hydro_structure) =update_clews_builder_config(combined_model_config,clews_builder_config)
    
    update_clews_builder_config(combined_model_config,clews_builder_config)
    
    print(f" CLEWS technology data schema updated.")
    
    return 


if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Run data preparation script')
    
    # Positional arguments (without default values)
    parser.add_argument('combined_model_config', 
                        type=str, 
                        help="Path to the combined model configuration file")
    
    parser.add_argument('clews_builder_config', 
                        type=str, 
                        help="Path to the CLEWs builder configuration file")
    
    # Parse the arguments
    args = parser.parse_args()
    
    main(args.combined_model_config, args.clews_builder_config)
    # """
    #----------------------- for notebook run/Debugging------------------------------------
    # config_file_path='config/config.yaml'
    # main(config_file_path)
