# %%
# %matplotlib inline

# %%
import argparse,yaml
import subprocess
from bc_combined_modelling import linking_utility as utils
from bc_combined_modelling import clews_builder
from bc_combined_modelling import clews_datapackage as clews_data_module

from pathlib import Path 
# %%
def main(
    combined_model_config_path:Path, # Not in use, future scope standardized
    clews_builder_config_path:Path
):  
    clewsb_config=utils.load_config(clews_builder_config_path)
    
    # Combined Model Config
    cm_config=utils.load_config(combined_model_config_path)
    
    n_clusters = cm_config['clews']['CLUSTERING']['n_clusters']
    hour_grouping = cm_config['clews']['CLUSTERING']['hour_grouping']
    days_in_year = cm_config['clews']['CLUSTERING']['days_in_year']
    start_year = cm_config['clews']['GENERAL']['start_year']
    last_year = cm_config['clews']['GENERAL']['last_year']
    
    # CLEWS Builder Config
    StorageMaxCapacity = clewsb_config['STORAGE']['BATTERY']['storage_max_capacity']
    ResidualStorageCapacity = clewsb_config['STORAGE']['BATTERY']['residual_storage_capacity']
    
    input_CF_wind_file = Path('data/processed_data/wind/existing/bc_ext_wind_ts.csv') # config['FILES']['DATA']['data_8760']['CF_wind']
    input_CF_solar_file =  Path('data/processed_data/solar/existing/bc_ext_solar_ts.csv') # config['FILES']['DATA']['data_8760']['CF_solar']
    input_SDP_file =  Path('data/downloaded_data/CODERS/data-pull/demand/BC_provincial_demand_profile.csv') #config['FILES']['DATA']['data_8760']['SDP']
    
    input_CF_csv_file =  Path('data/clews_data/inputs_csv_8760_2020/CapacityFactor.csv') #config['FILES']['capacity_factor_8760_file']
    input_CF_csv_file.parent.mkdir(parents=True, exist_ok=True)
    
    input_SDP_csv_file =  Path('data/clews_data/inputs_csv_8760_2020/SpecifiedDemandProfile.csv') #config['FILES']['specified_demand_profile_8760_file']
    input_CF_csv_file.parent.mkdir(parents=True, exist_ok=True)
    
    cases = ['Kotzur'] #,'Niet'  # Storage Algorithms

### CLUSTERING
    representative_days, chronological_sequence = clews_builder.cluster_data(input_CF_wind_file, 
                                                                             input_CF_solar_file, 
                                                                             input_SDP_file, 
                                                                             n_clusters)
    print(f"Representative days: {representative_days}")

### MATHS

    # Number of blocks per day based on the hour grouping
    blocks_per_day = 24 // hour_grouping
    # Total timeslices considering the representative days
    timeslices = len(representative_days) * blocks_per_day
    print(f">>> No. of Timeslices configured= {timeslices}")
    # Chronological timeslices is number of days in year * blocks per day. If hourly analysis, chronological timeslice is 8760
    chronological_timeslices = days_in_year * blocks_per_day
    daytypes = len(representative_days)
    year_split = 1 / timeslices
    day_split = hour_grouping / (24 * 365)

### UPDATING MODEL(CASE) STRUCTURE AND RUNNING MODELS

    for case_name in cases:
        
    ### Copying CSV Templates  >>> This should be done before other param update scripts, make it part of workflow
        input_csv_templates = Path(clewsb_config['clews_datapackage_template'])
        input_csv_dir = Path(f'data/clews_data/inputs_csv')
        input_csv_dir.mkdir(parents=True,exist_ok=True)
        
        clews_builder.copy_csv_files(input_csv_templates, input_csv_dir)
        
    ### Run the Prerequisites to update params
        cmd_schema_params_update = (  # developed CLI cmds to include multiple scripts
            "bccm clews update_tech_schema && " # Updates 'clews_builder_config'
            "bccm clews update_yearly_params && " # Updates yearly params for new techs inside 'input_csv_case_dir'
            "bccm clews update_profiling_params " # Creates 'input_CF_csv_file' , 'input_SDP_csv_file'

        )
        try:
        # Run the command
            subprocess.run(cmd_schema_params_update, shell=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: Command failed with return code {e.returncode}")
            print(f"Command: {e.cmd}")
        
        case_input_csvs=Path(f'data/clews_data/Model_{case_name}/inputs_csv')
        clews_builder.copy_csv_files(input_csv_dir, case_input_csvs)
        
        ### UPDATING CAPACITY FACTOR AND SPECIFIED DEMAND PROFILE
        
        output_CF_csv_file = case_input_csvs/'CapacityFactor.csv' # config['FILES']['capacity_factor_file']
        # """ 
        # Updating capacity factor (averaging the values)
        clews_builder.CFandSDP(input_CF_csv_file, 
                                representative_days, 
                                hour_grouping, 
                                output_CF_csv_file, 
                                operation='mean')
  
        clews_builder.replication(output_CF_csv_file,
                                  start_year, 
                                  last_year, 
                                  group_by='TECHNOLOGY')

        # Updating specified demand profile (summing the values)
        output_SDP_csv_file =  case_input_csvs/'SpecifiedDemandProfile.csv' #config['FILES']['specified_demand_profile_file']
        clews_builder.CFandSDP(input_SDP_csv_file, 
                               representative_days, 
                               hour_grouping, 
                               output_SDP_csv_file, 
                               operation='sum')
        
        clews_builder.replication(output_SDP_csv_file,
                                  start_year, 
                                  last_year, 
                                  group_by='FUEL')

        

        # ### Skip if case_name is 'Niet'
        # if case_name == 'Niet':
        #     continue

        # ### Updating Model Kotzur
        # if case_name == 'Kotzur':
        
        print(f"Updating case: {case_name}")


        
        ### UPDATING TIMESLICE AND DAYTYPE
        # Updating timeslice
    
        output_timeslice_csv_file = case_input_csvs/'TIMESLICE.csv' #config['FILES']['timeslice_file']

        clews_builder.new_list(timeslices, output_timeslice_csv_file)

        # Updating daytype
        output_daytype_csv_file =  case_input_csvs/'DAYTYPE.csv' #config['FILES']['daytype_file']
        clews_builder.new_list(daytypes, output_daytype_csv_file)

    ### UPDATING YEARSPLIT
        # %%
        output_yearsplit_csv_file =  case_input_csvs/'YearSplit.csv' #config['FILES']['yearsplit_file']
        clews_builder.yearsplit(timeslices, representative_days,  chronological_sequence, days_in_year, start_year, output_yearsplit_csv_file)
        clews_builder.replication(output_yearsplit_csv_file, start_year, last_year)
        
        # Updating dayscro
        output_dayscro_csv_file = case_input_csvs/'DAYSCRO.csv'
        clews_builder.new_list(days_in_year, output_dayscro_csv_file)
        
        # Updating conversionld
        output_conversionld_csv_file = case_input_csvs/'Conversionld.csv' # case_info['input_otoole_csv']['conversionld']
        clews_builder.conversionld(timeslices, len(representative_days), output_conversionld_csv_file)

        # Updating conversionldc
        output_conversionldc_csv_file =  case_input_csvs/'Conversionldc.csv' # case_info['input_otoole_csv']['conversionldc']
        clews_builder.conversion(chronological_sequence, representative_days, days_in_year, output_conversionldc_csv_file)
        # """
        # Updating day split in yaml file
        otoole_yaml_file = Path (f'models/BC_Nexus/Model_{case_name}/otoole_config_{case_name}.yaml') #case_info['otoole_config']
        clews_builder.new_yaml_param(otoole_yaml_file, 'DaySplit', day_split)

### Updating otoole yaml file
        clews_builder.new_yaml_param(otoole_yaml_file, 'StorageMaxCapacity', StorageMaxCapacity)
        clews_builder.new_yaml_param(otoole_yaml_file, 'ResidualStorageCapacity', ResidualStorageCapacity)

        # Creating txt from csv using otoole
        output_txt_file = Path(f'data/clews_data/Model_{case_name}/BCNexus_{case_name}.txt')

        print(f"Converting csv to txt with otoole for case: {case_name}")

        command_otoole = f"otoole convert csv datafile {case_input_csvs} {output_txt_file} {otoole_yaml_file}"
        subprocess.run(command_otoole, shell=True, text=True)
     
        # Preprocessing 
        org_model_file = Path(f'models/BC_Nexus/Model_{case_name}/model_BCNexus_{case_name}.txt')
        otoole_preprocessing_script = Path(f'models/BC_Nexus/Model_{case_name}/preprocess_data_{case_name}.py')
        
        output_model_file_preprocessed = Path(f'data/clews_data/Model_{case_name}/model_BCNexus_{case_name}_preprocessed.txt')
        output_txt_file_preprocessed = Path(f'data/clews_data/Model_{case_name}/BCNexus_{case_name}_processed.txt')
             
        print(f"Preprocessing case: {case_name}")
        command_preprocess = f"python {otoole_preprocessing_script} {output_txt_file} {output_txt_file_preprocessed} {org_model_file} {output_model_file_preprocessed}"
        subprocess.run(command_preprocess, shell=True, text=True)
        
### Running model
    #### Define result and LP file directories
        otoole_results_dir= Path(f'results/clews/Model_{case_name}_{timeslices}ts')
        otoole_results_dir.parent.mkdir(parents=True,exist_ok=True)
        
        # data_glp_path = case_info['data_glp']
        data_sol_path = Path(f'data/clews_data/Model_{case_name}/{case_name}.sol')
        # data_sol_cbc_path = case_info['data_sol_cbc']
        LP_file = Path(f'data/clews_data/Model_{case_name}/BCNexus_{case_name}.lp')
        
        print(f"Running case: Model {case_name}")

    ####  Input Checker
        # Create an instance of the class with the directory containing CSV files
        data_package = clews_data_module.GetDataPackage(case_input_csvs)

        # Get all DataFrames in the dictionary
        SETS_dfs,Params_dfs = data_package.load_data()

        checker=clews_data_module.Checker(SETS_dfs,Params_dfs)
        checker.get_summary_report(f'data/clews_data/Model_{case_name}/Input_checker_summary_report.txt')
         
    #### Write LP with GLPSOL
        # command_run = f"glpsol -m {output_model_file_preprocessed} -d {output_txt_file_preprocessed} --wglp {data_glp_path} --write {data_sol_path}"  
        # subprocess.run(command_run, shell=True, text=True)
        
        print(f"Creating LP file: {LP_file} from \nModel : {output_model_file_preprocessed} \nDatafile: {output_txt_file_preprocessed}")

        cmd_lp_create= f"glpsol -m {output_model_file_preprocessed} -d {output_txt_file_preprocessed} --wlp {LP_file} --check"
        subprocess.run(cmd_lp_create, shell=True, text=True)
        
        # cmd_cbc_model_run= f"cbc {LP_file} solve -solu {data_sol_cbc_path}"
        # subprocess.run(cmd_cbc_model_run, shell=True, text=True)
        
    #### Solve the LP with GUROBI Solver
        print(f"Running Gurobi Solver with LP file: {LP_file} and the targeted ResultFile: {data_sol_path}")
        cmd_solve_model_gurobi= f"gurobi_cl ResultFile={data_sol_path} {LP_file}"
        subprocess.run(cmd_solve_model_gurobi, shell=True, text=True)
        
### Extract the CSV results from GUROBI Solution/Result datafile
        print(f"Initiating otoole to extract results from Gurobi Solver using Datafile : {output_txt_file} , config file: {otoole_yaml_file}")

        otoole_results_cmd= f"otoole results gurobi csv {data_sol_path} {otoole_results_dir} datafile {output_txt_file} {otoole_yaml_file}"
        print(otoole_results_cmd)
        subprocess.run(otoole_results_cmd, shell=True, text=True)
        
        command = f"cut -d' ' -f1-5 gurobi.log > {otoole_results_dir}/gurobi.log"
        # Run the command
        subprocess.run(command, shell=True, check=True)      
        print(f"Result extraction completed and saved to {otoole_results_dir}")
    # """
    
    return
    

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Run CLEWs paramater update script')
    
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
