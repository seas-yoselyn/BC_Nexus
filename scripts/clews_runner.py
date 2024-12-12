import pandas as pd 
from pathlib import Path
from typing import Optional,List,Dict,Tuple 
import argparse
import yaml
from bc_combined_modelling import utils
from bc_combined_modelling import clews_builder
from pathlib import Path
from bc_combined_modelling.AttributesParser_cm import AttributesParserExtended
import subprocess
import argparse,yaml
import subprocess
from bc_combined_modelling import linking_utility as utils
from bc_combined_modelling import clews_builder
from bc_combined_modelling import clews_datapackage as clews_data_module
from pathlib import Path 
from bc_combined_modelling import solver
import gurobipy as gp

class build_model:
    def __init__(self, 
            clews_builder_config_path:str|Path,
            combined_model_config_path:str|Path):
        self.combined_model_config_path:Path=Path(combined_model_config_path)
        self.clews_builder_config_path:Path=Path(clews_builder_config_path)
        
    def build_skeleton_config(self):
        clews_builder.build_yaml_skeleton(self.clews_builder_config_path)

    def update_tech_schema(self):
        try:
            subprocess.run("bccm clews update_tech_schema", shell=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"CLI 'bccm' failed with exit code {e.returncode}")
            # try:
            #     subprocess.run(["python", "path_to_script.py"], check=True)
            # except subprocess.CalledProcessError as e:
            #     print(f"Script failed with exit code {e.returncode}")
    
    def update_yearly_params(self):
        
        try:
            subprocess.run("bccm clews update_yearly_params", shell=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"CLI 'bccm' failed with exit code {e.returncode}")
            # try:
            #     subprocess.run(["python", "path_to_script.py"], check=True)
            # except subprocess.CalledProcessError as e:
            #     print(f"Script failed with exit code {e.returncode}")
            #     ### Run the Prerequisites to update params
    
    def get_clustering_attributes(self):
        self.n_clusters = self.cm_config['clews']['CLUSTERING']['n_clusters']
        self.hour_grouping = self.cm_config['clews']['CLUSTERING']['hour_grouping']
        self.days_in_year = self.cm_config['clews']['CLUSTERING']['days_in_year']
        self.start_year = self.cm_config['clews']['GENERAL']['start_year']
        self.last_year = self.cm_config['clews']['GENERAL']['last_year']
    
    def get_profiling_param_attributes(self):
        
        # CLEWS Builder Config
        self.StorageMaxCapacity =  self.clewsb_config['STORAGE']['BATTERY']['storage_max_capacity']
        self.ResidualStorageCapacity =  self.clewsb_config['STORAGE']['BATTERY']['residual_storage_capacity']
        
        self.input_CF_wind_file = Path('data/processed_data/wind/existing/bc_ext_wind_ts.csv') # config['FILES']['DATA']['data_8760']['CF_wind']
        self.input_CF_solar_file =  Path('data/processed_data/solar/existing/bc_ext_solar_ts.csv') # config['FILES']['DATA']['data_8760']['CF_solar']
        self.input_SDP_file =  Path('data/downloaded_data/CODERS/data-pull/demand/BC_provincial_demand_profile.csv') #config['FILES']['DATA']['data_8760']['SDP']
        
        self.input_CF_csv_file =  Path('data/clews_data/inputs_csv_8760_2020/CapacityFactor.csv') #config['FILES']['capacity_factor_8760_file']
        self.input_CF_csv_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.input_SDP_csv_file =  Path('data/clews_data/inputs_csv_8760_2020/SpecifiedDemandProfile.csv') #config['FILES']['specified_demand_profile_8760_file']
        self.input_CF_csv_file.parent.mkdir(parents=True, exist_ok=True)
    
    def collect_profiling_param(self):

        self.get_profiling_param_attributes()
        self.get_temporal_clusters()
        
        try:
            subprocess.run("bccm clews update_profiling_params", shell=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"CLI 'bccm' failed with exit code {e.returncode}")
            # try:
            #     subprocess.run(["python", "path_to_script.py"], check=True)
            # except subprocess.CalledProcessError as e:
            #     print(f"Script failed with exit code {e.returncode}")
            #     ### Run the Prerequisites to update params
    
    def get_temporal_clusters(self):
        self.get_clustering_attributes()
        
        self.representative_days, self.chronological_sequence = clews_builder.cluster_data(self.input_CF_wind_file, 
                                                                                self.input_CF_solar_file, 
                                                                                self.input_SDP_file, 
                                                                                self.n_clusters)
        print(f"Representative days: {self.representative_days}")
        
        
        # Number of blocks per day based on the hour grouping
        self.blocks_per_day = 24 // self.hour_grouping
        # Total timeslices considering the representative days
        self.timeslices = len(self.representative_days) * self.blocks_per_day
        print(f">>> No. of Timeslices configured= {self.timeslices}")
        # Chronological timeslices is number of days in year * blocks per day. If hourly analysis, chronological timeslice is 8760
        self.chronological_timeslices = self.days_in_year * self.blocks_per_day
        self.daytypes = len(self.representative_days)
        self.year_split = 1 / self.timeslices
        self.day_split = self.hour_grouping / (24 * 365)
    
    def get_csv_template(self,
                        from_path:str|Path=None,
                        to_path:str|Path=None):

        ### Copying CSV Templates  >>> This should be done before other param update scripts, make it part of workflow
        self.input_csv_templates = Path(self.clewsb_config.get('clews_datapackage_template','models/BC_Nexus/csv_template'))
        self.input_csv_dir = Path(f'data/clews_data/inputs_csv')
        self.input_csv_dir.mkdir(parents=True,exist_ok=True)
        
        if from_path is None or to_path is None:
            clews_builder.copy_csv_files(self.input_csv_templates, self.input_csv_dir)
        else:
            clews_builder.copy_csv_files(from_path, to_path)
            
    def update_case_SETs(self):
        # Updating TIMESLICE
    
        self.case_timeslice_csv_file = self.case_input_csvs/'TIMESLICE.csv' #config['FILES']['timeslice_file']

        clews_builder.new_list(self.timeslices, self.case_timeslice_csv_file)

        # Updating daytype
        self.case_daytype_csv_file =  self.case_input_csvs/'DAYTYPE.csv' #config['FILES']['daytype_file']
        clews_builder.new_list(self.daytypes, self.case_daytype_csv_file)
    
        ### Updating YEARSPLIT
        self.case_yearsplit_csv_file =  self.case_input_csvs/'YearSplit.csv' #config['FILES']['yearsplit_file']
        
        clews_builder.yearsplit(self.timeslices, 
                                self.representative_days,  
                                self.chronological_sequence, 
                                self.days_in_year, 
                                self.start_year, 
                                self.case_yearsplit_csv_file)
        clews_builder.replication(self.case_yearsplit_csv_file, 
                                  self.start_year, 
                                  self.last_year)
        
        # Updating dayscro
        output_dayscro_csv_file = self.case_input_csvs/'DAYSCRO.csv'
        clews_builder.new_list(self.days_in_year, output_dayscro_csv_file)
        
        # Updating conversionld
        output_conversionld_csv_file =self. case_input_csvs/'Conversionld.csv' # case_info['input_otoole_csv']['conversionld']
        clews_builder.conversionld(self.timeslices, len(self.representative_days), output_conversionld_csv_file)

        # Updating conversionldc
        output_conversionldc_csv_file =  self.case_input_csvs/'Conversionldc.csv' # case_info['input_otoole_csv']['conversionldc']
        clews_builder.conversion(self.chronological_sequence, self.representative_days, self.days_in_year, output_conversionldc_csv_file)
    
    def get_case_profiling_Params(self):
        ### Update profiling Params (CF, Sepecific Demand Profile)
        self.case_CF_csv_file = self.case_input_csvs/'CapacityFactor.csv' # config['FILES']['capacity_factor_file']
        
        # Updating capacity factor (averaging the values)
        clews_builder.CFandSDP(self.input_CF_csv_file,
                                self.representative_days,
                                self.hour_grouping,
                                self.case_CF_csv_file,
                                operation='mean')

        # Data formatting
        clews_builder.replication(self.case_CF_csv_file,
                                    self.start_year,
                                    self.last_year,
                                    group_by='TECHNOLOGY')

        # Updating specified demand profile (summing the values)
        self.case_SDP_csv_file =  self.case_input_csvs/'SpecifiedDemandProfile.csv' #config['FILES']['specified_demand_profile_file']
        clews_builder.CFandSDP(self.input_SDP_csv_file, 
                            self.representative_days, 
                            self.hour_grouping, 
                            self.case_SDP_csv_file, 
                            operation='sum')
        
        clews_builder.replication(self.case_SDP_csv_file,
                                self.start_year, 
                                self.last_year, 
                                group_by='FUEL')
        
    def update_otoole_config(self,
                             case_name:str):
        ### Updating otoole yaml file
        
        # Updating day split in yaml file
        self.otoole_yaml_file = Path (f'models/BC_Nexus/Model_{case_name}/otoole_config_{case_name}.yaml') #case_info['otoole_config']
        clews_builder.new_yaml_param(self.otoole_yaml_file, 'DaySplit', self.day_split)

        clews_builder.new_yaml_param(self.otoole_yaml_file, 'StorageMaxCapacity', self.StorageMaxCapacity)
        clews_builder.new_yaml_param(self.otoole_yaml_file, 'ResidualStorageCapacity', self.ResidualStorageCapacity)

        # Creating txt from csv using otoole
        self.case_ip_data_file = Path(f'data/clews_data/Model_{case_name}/BCNexus_{case_name}.txt')

        print(f"Converting csv to txt with otoole for case: {case_name}")
    
    def get_model_run_files(self,
                        case_name:str):
        
        # Get the case_data.txt with otoole
        command_otoole = f"otoole convert csv datafile {self.case_input_csvs} {self.case_ip_data_file} {self.otoole_yaml_file}"
        subprocess.run(command_otoole, shell=True, text=True)
     
        # Preprocessing the case_data.txt and model.txt
        self.org_model_file = Path(f'models/BC_Nexus/Model_{case_name}/model_BCNexus_{case_name}.txt')
        otoole_preprocessing_script = Path(f'models/BC_Nexus/Model_{case_name}/preprocess_data_{case_name}.py')
        
        self.case_model_file_preprocessed = Path(f'data/clews_data/Model_{case_name}/model_BCNexus_{case_name}_preprocessed.txt')
        self.case_ip_data_file_preprocessed = Path(f'data/clews_data/Model_{case_name}/BCNexus_{case_name}_processed.txt')
             
        print(f"Preprocessing case: {case_name}")
        command_preprocess = f"python {otoole_preprocessing_script} {self.case_ip_data_file} {self.case_ip_data_file_preprocessed} {self.org_model_file} {self.case_model_file_preprocessed}"
        subprocess.run(command_preprocess, shell=True, text=True)
    
    def get_result_csvs(self):
        ### Extract the CSV results from GUROBI Solution/Result datafile
        print(f"Initiating otoole to extract results from Gurobi Solver using Datafile : {self.case_ip_data_file_preprocessed} , config file: {self.otoole_yaml_file}")

        otoole_results_cmd= f"otoole results gurobi csv {self.solution_path} {self.otoole_results_dir} datafile {self.case_ip_data_file_preprocessed} {self.otoole_yaml_file}"
        print(otoole_results_cmd)
        subprocess.run(otoole_results_cmd, shell=True, text=True)
        
        print(f"Result extraction completed and saved to {self.otoole_results_dir}")
    
    def write_LP_file(self):
        print(f"Creating LP file: {self.LP_file} from \nModel : {self.case_model_file_preprocessed} \nDatafile: {self.case_ip_data_file_preprocessed}")

        cmd_lp_create= f"glpsol -m {self.case_model_file_preprocessed} -d {self.case_ip_data_file_preprocessed} --wlp {self.LP_file} --check"
        subprocess.run(cmd_lp_create, shell=True, text=True)
  
    def collect_input_checker_report(self,
                                     case_datafiles:Path,
                                     case_name):
            # Create an instance of the class with the directory containing CSV files
            clews_data_checker:clews_data_module = clews_data_module.GetDataPackage(case_datafiles)

            # Get all DataFrames in the dictionary
            SETS_dfs,Params_dfs = clews_data_checker.load_data()

            checker=clews_data_module.Checker(SETS_dfs,Params_dfs)
            checker.get_summary_report(f'data/clews_data/Model_{case_name}/Input_checker_summary_report.txt')
    
    def run(self):
        if not Path(self.clews_builder_config_path).exists():
            self.build_skeleton_config()
        
        #clews builder config
        self.clewsb_config:dict=utils.load_config(self.clews_builder_config_path)
    
        # Combined Model Config
        self.cm_config:dict=utils.load_config(self.combined_model_config_path)

        # We keep the REF/BASE intact and apply the aggregation/updates on a cloned version inside 'data/clews/input_csvs'
        self.get_csv_template() # Ideally from BASE/REF case template to a temp and reproduceable folder i.e. 'data/clews/input_csvs'
        
        self.update_tech_schema() # Currently supports simplified power technology aggregation.
        self.collect_profiling_param() # Currently supports simplified temporal clustering.
        self.update_yearly_params() # Updates the associated parameters affected due to technology aggregation.
        
        # Set Attributes for storage algorithm cases
        self.storage_cases = ['Kotzur']

        for case_name in self.storage_cases:
            print(f"Updating case: {case_name}")
            
            # Get specific Attributes
            self.case_input_csvs=Path(f'data/clews_data/Model_{case_name}/inputs_csv')
            self.case_input_csvs.mkdir(parents=True,exist_ok=True)
                    
            #### Define results (csvs), solution (from solver), LP (from solver) file directories
            self.otoole_results_dir= Path(f'results/clews/Model_{case_name}_{self.timeslices}ts')
            self.otoole_results_dir.parent.mkdir(parents=True,exist_ok=True)
            self.solution_path = Path(f'data/clews_data/Model_{case_name}/{case_name}.sol')
            self.LP_file = Path(f'data/clews_data/Model_{case_name}/BCNexus_{case_name}.lp')
            
            # Apply Methods to modify template input files on set configs (currently supports: simplified temporal clustering, power technology aggreation)
            self.get_csv_template(from_path=self.input_csv_dir,
                                  to_path=self.case_input_csvs)
            
            self.get_case_profiling_Params()
            self.update_case_SETs()
            self.update_otoole_config(case_name)
            
            self.collect_input_checker_report(self.case_input_csvs,
                                              case_name)
            
            self.get_model_run_files(case_name)
            self.write_LP_file()
            log_save_to=f'results/clews/Model_{case_name}_shadowprice_ELC02_{self.timeslices}ts_gurobi.log'
            
            self.solved_model=solve_model(self.LP_file,
                             log_save_to)

            write_solution(self.solved_model,
                            self.solution_path)
            self.get_result_csvs()
            
            get_shadow_price_ELCB02(self.solved_model,
                                    plot_save_to=f'results/clews/Model_{case_name}_shadowprice_ELC02_{self.timeslices}ts.png',
                                    show=True)
            self.duals_df,self.binding_constraints,self.non_binding_constraints=get_constraints(self.solved_model)
            get_summary_report(self.binding_constraints,
                               self.non_binding_constraints,
                               f'results/clews/Model_{case_name}_{self.timeslices}ts_constraints_summary.txt')
            return self.solved_model

@staticmethod
def solve_model(LP_file:str,
                log_path:str):
    LP_file=str(LP_file)
    gurobi_model:gp.Model = solver.sol_gurobi(LP_file,
                                              log_path)
    return gurobi_model
    
@staticmethod
def write_solution(model:gp.Model,
                    solution_path:str):
    solution_path=str(solution_path) # gurobipy doesn't handle path objects
    solver.write_sol(model,
                        solution_path)

@staticmethod
def __get_duals__(model:gp.Model):
    # get duals df
    return solver.get_duals(model)

@staticmethod
def get_constraints(model:gp.Model):
    
    duals_df=__get_duals__(model)
    binding_constraints,non_binding_constraints=solver.get_constraints_type(duals_df)
    
    
    return duals_df,binding_constraints,non_binding_constraints
    
@staticmethod
def get_shadow_price_ELCB02(model:gp.Model,
                            plot_save_to:str,
                            show=True):
    duals_df=__get_duals__(model)
    binding_constraints,non_binding_constraints=solver.get_constraints_type(duals_df)
    constraint_df_ELC_aggr=solver.get_shadow_price_ELCB02(binding_constraints)
    solver.plot_shadow_price(constraint_df_ELC_aggr,
                             save_to=plot_save_to,
                             show=show)
    return constraint_df_ELC_aggr
    
@staticmethod
def get_summary_report(binding_constraints:pd.DataFrame,
                       non_binding_constraints:pd.DataFrame, 
                       summary_save_to: Path):
        """
        xxx
        """

        # # Prepare a list to store the summary of results
        summary :list= []
        
        print("Collecting constraints reports...")
        # Checking the validation methods and collect reports
        
        summary.append(f"{20*'='} Constraints {20*'='}\n")
        summary.append(f"Binding Constraints:\n".join(list(binding_constraints.constraint.unique())))


        print("Non-Binding Constraints:")
        print(non_binding_constraints.constraint.unique())
        summary.append(f"Non-Binding Constraints:\n".join(list(non_binding_constraints.constraint.unique())))

        # End of report
        summary.append(f"\n{100*'='}")
        
        print("Generating constraints summary report...")

    
        try:
            with open(summary_save_to, "w") as file:
                file.write("\n".join(summary))
            print(f"Summary saved to {summary_save_to}")
        except Exception as e:
            print(f"Error writing to file: {e}")

            
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
    clews_module=build_model(args.combined_model_config, args.clews_builder_config)
    clews_module.run()

            


            
           

           
