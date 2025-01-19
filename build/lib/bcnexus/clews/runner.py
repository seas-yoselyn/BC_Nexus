import pandas as pd 
from pathlib import Path
from typing import Optional
import argparse
import subprocess
import gurobipy as gp
import yaml
import sys

# local packages
from ..attributes_parser import AttributesParser
from .builder import BuildModel
from . import schema as clewsB
# from . import datapackage as clews_data_module
from . import solver
from . import preprocess_data_Kotzur
from . import preprocess_data_Niet
from .. import utils
from ..vis import plot_capacity,plot_emission#,plot_landuse,plot_energy


# Filetring the package reated warnings
import warnings
warnings.filterwarnings("ignore")


class RunModel:
    """ 
    RunModel is a class that takes in the prepared folder of CSVs (SETs,Parameters) and do all the prerequisites to solve and extract the results.
    """
    def __init__(self,
                scenario:str,
                storage_algorithm:str,
                input_csvs:str|Path=None,
                combined_model_config_path:str|Path=None,
                clustering_attributes:dict=None
               ):
        
        self.combined_model_config_path:Path=Path(combined_model_config_path) if combined_model_config_path else Path('config/config.yaml')
        self.scenario=scenario
        self.storage_algorithm=storage_algorithm
        self.input_csvs=Path(input_csvs) if input_csvs else Path(f'data/clews_data/Model_{self.storage_algorithm}/inputs_csv')
        self.clustering_attributes=clustering_attributes
        
        utils.print_update(level=1,
                    message=f"Initiated CLEWs Model Runner for '{self.scenario}' scenario with '{self.storage_algorithm}' storage algorithm")
        utils.print_update(level=2,
                    message=f" Input CSVS set to: {self.input_csvs}")
        
        # The Attributes Parser handles all sorts of parsing from the User Config file and implements necessary checks, validation and sets suitabel defaults if any field is missing.
        self.aparser=AttributesParser(self.combined_model_config_path)
        self.get_all_attributes()
  
        
    def get_all_attributes(self):
        self.otoole_yaml_file=self.aparser.get_otoole_yaml_file(self.storage_algorithm)
        self.scenario_cfg:dict=self.aparser.get_scenarios().get(self.scenario)
        
        self.clews_builder_config_path=self.aparser.clews_builder_config_path
        self.clewsb_config:dict=self.aparser.load_config(self.clews_builder_config_path)
        
        (self.start_year, self.last_year)=self.aparser.get_clews_snapshot()
        self.region=self.aparser.get_region()
        
        self.org_model_file=self.aparser.get_model_file_path(storage_algorithm=self.storage_algorithm)
        self.LP_file=self.input_csvs.parent/self.scenario/f'{self.scenario}.lp'
        self.scenario_results_root=self.aparser.get_scenario_results_path(scenario=self.scenario,
                                                                          storage_algorithm=self.storage_algorithm)
        
        # self.visual_config:dict=self.aparser.get_visual_configs()
        self.plots_save_to:Path=self.aparser.get_plots_save_to()
        
    def process_scenario_data(self):
        
        utils.print_update(level=2,
                    message="Processing Scenario Data")
        
        # Update TECHNOLOGY SET csv file
        TECHNOLOGY_df=pd.read_csv(self.input_csvs / 'TECHNOLOGY.csv')
        scenario_techs = list(self.scenario_cfg.get('TECHS').keys())
        tech_sets = list(TECHNOLOGY_df['VALUE'])

        for tech in scenario_techs:
            if tech not in tech_sets:
                tech_sets.append(tech)

        tech_sets_df = pd.DataFrame(tech_sets, columns=['VALUE'])
        tech_sets_df.to_csv(self.input_csvs / 'TECHNOLOGY.csv', index=False)
        utils.print_update(level=3,
                    message=f"File Updated: {self.input_csvs / 'TECHNOLOGY.csv'}")
        
        # Update TECHNOLOGY SET's info to clews_builder_config file.
        for tech_id, values in self.scenario_cfg.get('TECHS').items():
            for tech_type in self.clewsb_config['TECHNOLOGIES'].keys():
                if tech_id in self.clewsb_config['TECHNOLOGIES'][tech_type].keys():
                    self.clewsb_config['TECHNOLOGIES'][tech_type][tech_id].update(values)
                else:
                    pass
        # Save the updated YAML back to the same file
        with open(self.clews_builder_config_path, 'w') as file:
            yaml.dump(self.clewsb_config, file, default_flow_style=False)
        
        utils.print_update(level=3,
                    message=f"File Updated : {self.clews_builder_config_path}")
    
        # Define common args
        common_attr = {
            'scenario': self.scenario_cfg,
            'start_year': self.start_year,
            'last_year': self.last_year,
            'region': self.region,
            'delete_technologies_func': clewsB.delete_technologies,
            'add_technologies_func': clewsB.add_technologies,
        }

        # Define attributes with unique args
        scenario_attributes = [
            {'file_path': self.input_csvs / 'CapitalCost.csv', 
             'attribute_name': 'capital_cost', 
             'column_name': 'TECHNOLOGY'},
            
            {'file_path': self.input_csvs / 'OperationalLife.csv', 
             'attribute_name': 'operational_life', 
             'column_name': 'TECHNOLOGY', 
             'start_year': None, 
             'last_year': None},
            
            {'file_path': self.input_csvs / 'TotalAnnualMaxCapacityInvestment.csv', 
             'attribute_name': 'total_annual_max_capacity_investment', 
             'column_name': 'TECHNOLOGY'},
            
            {'file_path': self.input_csvs / 'TotalAnnualMaxCapacity.csv', 
             'attribute_name': 'total_annual_max_capacity', 
             'column_name': 'TECHNOLOGY'},
            
            {'file_path': self.input_csvs / 'TotalAnnualMinCapacity.csv', 
             'attribute_name': 'total_annual_min_capacity', 
             'column_name': 'TECHNOLOGY'},
            
            {'file_path': self.input_csvs / 'AccumulatedAnnualDemand.csv', 
             'attribute_name': 'accumulated_annual_demand', 
             'column_name': 'FUEL'},
            
            {'file_path': self.input_csvs / 'AnnualEmissionLimit.csv', 
             'attribute_name': 'annual_emission_limit', 
             'column_name': 'EMISSION'},
            
            {'file_path': self.input_csvs / 'EmissionsPenalty.csv', 
             'attribute_name': 'emission_penalty', 
             'column_name': 'EMISSION'},
            {
                'file_path': self.input_csvs / 'InputActivityRatio.csv',
                'attribute_name': 'input_activity_ratio',
                'column_name': 'TECHNOLOGY',
                'pre_process': clewsB.pre_process_input_activity_ratio,
                'additional_columns': {'MODE_OF_OPERATION': 1},  # FUEL will be added dynamically
            },
        ]

        # Iterate over each attribute and apply the function
        for unique_attr in scenario_attributes:
            # Merge common params with unique params, giving precedence to unique params
            params = {**common_attr, **unique_attr}
            clewsB.process_scenario_attribute(**params)
    

    def get_input_datafile_from_csvs(self,
                                     input_csvs:str|Path=None,
                                     datafile_path:str|Path=None)->Path:

        input_csvs = Path(input_csvs) if input_csvs else self.input_csvs
        datafile_path = Path(datafile_path) if datafile_path else input_csvs.parent /self.scenario/ 'data.txt'
        datafile_path.parent.mkdir(parents=True,exist_ok=True)
        """
        otoole_convert_args ={'config': otoole_config_file,
                            'from_format': 'csv',
                            'to_format': 'datafile',
                            'from_path': input_csvs,
                            'to_path': datafile_path,
                            'write_defaults' : True,
                            'keep_whitespace' : False}
        conversion_successful=otoole.convert(**otoole_convert_args)
        if conversion_successful:
            return datafile_path
        else:
            utils.print_update(message="Otoole conversion unsuccessful !!",
                               alert=True)
        """ 
        try:
            command_otoole = f"otoole convert csv datafile {input_csvs} {datafile_path} {self.otoole_yaml_file}"
            subprocess.run(command_otoole, shell=True, text=True)
            return datafile_path
        except Exception as e:
            Warning(f" Error: {e}.\nOtoole conversion not completed !!")
        
    
    def preprocess_data_model(
        self,
        data_infile: Optional[Path] = None,
        model_file: Optional[Path] = None,
    ):
        """
        Preprocess the case_data.txt and model.txt based on the specified storage algorithm.

        Parameters:
            ip_datafile (Optional[Path]): Path to the input data file.
            processed_datafile (Optional[Path]): Path to the processed data file.
            model_file (Optional[Path]): Path to the input model file.
            processed_model (Optional[Path]): Path to the processed model file.
            storage_algrithm (Optional[str]): The storage algorithm to use ('Kotzur' or 'Niet').

        Returns:
            Tuple[Path, Path]: Paths to the processed data and model files.
        """
        data_infile:Path=Path(data_infile)
        processed_datafile=data_infile.with_suffix('.txt').with_name(data_infile.stem + 'Processed.txt')
        processed_model=self.input_csvs.parent/self.scenario/'model_processed.txt'
        
        # Prepare arguments for the preprocessing module
        preprocessing_module_args = {
            'data_infile': data_infile,
            'data_outfile': processed_datafile,
            'model_file': model_file if model_file else self.org_model_file,
            'model_processed': processed_model,
        }
        utils.print_update(level=2,
                    message=f"Preprocessing data and model file for case: {self.storage_algorithm}")
        utils.print_update(level=3,
                    message=f"data file processed and saved as : {processed_datafile}")
        utils.print_update(level=3,
                    message=f"model file processed and saved as : {processed_model}")

        # Select the appropriate module to use based on the storage algorithm
        if self.storage_algorithm == "Kotzur":
            preprocess_data_Kotzur.main(**preprocessing_module_args)
        elif self.storage_algorithm == "Niet":
            preprocess_data_Niet.main(**preprocessing_module_args)
        else:
            raise ValueError(f"Unsupported storage algorithm: {self.storage_algorithm}")

        # Return the updated paths
        return (
            preprocessing_module_args['data_outfile'],
            preprocessing_module_args['model_processed'],
        )

    def get_model_run_files(self):
        
        _data_file_:Path=self.get_input_datafile_from_csvs(self.input_csvs)
        
        data_file, model_file = self.preprocess_data_model( data_infile=_data_file_,
                                                            model_file=self.org_model_file)
        
        return data_file,model_file
    
    def update_otoole_config(self):
        ### Updating otoole yaml file
        
        # Updating day split in yaml file
        clewsB.new_yaml_param(self.otoole_yaml_file, 'DaySplit', self.day_split)

        # clewsB.new_yaml_param(self.otoole_yaml_file, 'StorageMaxCapacity', self.StorageMaxCapacity)
        clewsB.new_yaml_param(self.otoole_yaml_file, 'ResidualStorageCapacity', self.ResidualStorageCapacity)
        
    def get_result_csvs(self,
                        solution_file:str|Path=None,
                        solver_name='gurobi',
                        debug_mode:Optional[bool]=False):
        """
        Args:
            solution_file (str | Path, optional): _description_. Defaults to None.
            solver (str, optional): _description_. Defaults to 'gurobi'. Supports 'cbc' also.
            debug_mode (Optional[bool], optional): _description_. Defaults to False.
        """
        
        solution_file=Path(solution_file) if solution_file else self.solution_path
        ### Extract the CSV results from GUROBI Solution/Result datafile
        utils.print_update(level=2,
                    message=f"Initiating otoole interface to extract results; input csvs : {self.input_csvs} , config file: {self.otoole_yaml_file}")
        self.otoole_results_dir = self.scenario_results_root / f'{self.timeslices}ts_csvs_{solver_name}'
        self.otoole_results_dir.mkdir(parents=True, exist_ok=True)
        
        if debug_mode:
            otoole_results_cmd= f"otoole -v results {solver_name} csv {self.solution_path} {self.otoole_results_dir} csv {self.input_csvs} {self.otoole_yaml_file}"
        else:
            otoole_results_cmd= f"otoole results {solver_name} csv {self.solution_path} {self.otoole_results_dir} csv {self.input_csvs} {self.otoole_yaml_file}"
        
        try:
            result = subprocess.run(otoole_results_cmd, shell=True, text=True)
            utils.print_update(result.check_returncode(),alert=True)
            utils.print_update(level=3,
                message=f"Result extraction completed and saved to {self.otoole_results_dir}")
            return self.otoole_results_dir

        except Exception as e:
            utils.print_update(level=4,
                        message=f"An error occurred during otoole result extraction: {e}")
      

    @staticmethod
    def write_LP_file(
        model_file: Optional[str | Path] = None,
        data_file: Optional[str | Path] = None,
        Lp_file: Optional[str | Path] = None
    ) -> Path:
        """
        Generate an LP file using GLPK's glpsol tool.

        Parameters:
            model_file (Optional[str | Path]): Path to the model file (.mod).
            data_file (Optional[str | Path]): Path to the data file (.dat).
            Lp_file (Optional[str | Path]): Path to save the generated LP file.

        Returns:
            Path: Path to the generated LP file.
        """
        utils.print_update(level=1,
            message='Preparing the LP file')
        utils.print_update(level=2,
                    message=f"Creating LP file: {Lp_file} from Model : {model_file}, Data : {data_file}")

        cmd = [
            "glpsol",
            "-m", model_file,
            "-d", data_file,
            "--wlp", Lp_file,
            "--check"
        ]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        for line in process.stdout:
            utils.print_update(message=line.strip())
            sys.stdout.flush()   # Force immediate print    
    @staticmethod
    def solve_model_gurobi(LP_file:str,
                    log_path:str,
                    threads:int=32):
        utils.print_update(level=2,message=f"Using {threads} threads to solve the model using Gurobi solver. If the solver fails to load/run due to memory issues, please use thread < your hardware limitation (cores)")
        LP_file=str(LP_file)
        gurobi_model:gp.Model = solver.sol_gurobi(LP_file,
                                                log_path,
                                                threads)
        return gurobi_model
    
    @staticmethod
    def solve_model_cbc(lp_path:str|Path,
                        solution_path:str|Path,
                        threads:int=32):
        utils.print_update(level=2,message=f"Using {threads} threads to solve the model using CBC solver. If the solver fails to load/run due to memory issues, please use thread < your hardware limitation (cores)")
        solver.sol_cbc(lp_path, 
                       solution_path,
                       threads)
        
    @staticmethod
    def write_solution(model:gp.Model,
                        solution_path:str):
        solution_path=str(solution_path) # gurobipy doesn't handle path objects

        solver.write_sol(model,solution_path)

    @staticmethod
    def get_constraints(model:gp.Model):
        
        duals_df=solver.get_duals(model)
        binding_constraints,non_binding_constraints=solver.get_constraints_type(duals_df)
        
        
        return duals_df,binding_constraints,non_binding_constraints
        
    @staticmethod
    def get_shadow_price_ELCB02(model:gp.Model,
                                plot_save_to:str,
                                show=True):
        duals_df=solver.get_duals(model)
        binding_constraints,non_binding_constraints=solver.get_constraints_type(duals_df)
        constraint_df_ELC_aggr=solver.get_shadow_price_ELCB02(binding_constraints)
        solver.plot_shadow_price(constraint_df_ELC_aggr,
                                save_to=plot_save_to,
                                show=show)
        return constraint_df_ELC_aggr
    
    @staticmethod      
    def get_visuals(model_results_direc:str|Path,
                    visual_configs:dict,
                    plots_save_to:str|Path):
        
        plot_capacity.create_plot(model_results_direc=model_results_direc,
                                            visual_configs=visual_configs,
                                            plots_save_to=plots_save_to)
        
        plot_emission.create_plot(model_results_direc=model_results_direc,
                                            visual_configs=visual_configs,
                                            plots_save_to=plots_save_to)   
        
    @staticmethod
    def get_summary_report(binding_constraints: pd.DataFrame,
                        non_binding_constraints: pd.DataFrame,
                        summary_save_to: Path):
        """
        Generate a summary report of binding and non-binding constraints and save it to a file.

        Args:
            binding_constraints (pd.DataFrame): DataFrame containing binding constraints.
            non_binding_constraints (pd.DataFrame): DataFrame containing non-binding constraints.
            summary_save_to (Path): File path to save the summary report.

        Returns:
            None
        """
        # Prepare a list to store the summary of results
        summary: list = []

        utils.print_update(level=3,message="Collecting constraints reports...")
        # Collect reports
        summary.append(f"{'=' * 20} Constraints {'=' * 20}\n")
        summary.append("Binding Constraints:\n")
        # Add space before each constraint
        summary.append("\n".join(f" {constraint}" for constraint in binding_constraints['constraint'].unique()))
        summary.append(f"\n{'.' * 50}")
        summary.append("Non-Binding Constraints:\n")
        # Add space before each constraint
        summary.append("\n".join(f" {constraint}" for constraint in non_binding_constraints['constraint'].unique()))

        # End of report
        summary.append(f"\n{'=' * 100}")

        try:
            # Ensure the parent directory exists
            summary_save_to = Path(summary_save_to)
            summary_save_to.parent.mkdir(parents=True, exist_ok=True)

            with open(summary_save_to, "w") as file:
                file.write("\n".join(summary))
            utils.print_update(level=3,message=f"Summary saved to {summary_save_to}")
        except Exception as e:
            utils.print_update(level=2,message=f"Error writing to file: {e}")
    
    def run(self,
            input_csvs: str | Path=None,
            build:bool=False,
            update_temporal_profiles=True,
            solver_name='gurobi',
            threads:int=32
            ):
        """
        Run the CLEWs model with the specified parameters.
        ## Args:
            input_csvs : str or Path, optional
                Directory of the CSVs with all SETs and Params. If not provided, uses self.input_csvs.
            build : bool, default=False
                If True, runs the ClewsBuilder module to update SETs and Params.
            solver : str, default='gurobi'
                The solver to use for optimization. Supports 'gurobi, cbc'
            threads : int, default=32
                Number of threads to use for the solver. Use according to your CPU hardware (core) limitation
            
        Returns: None
    
        Notes:
        ------
        - Loads the combined model configuration from the specified path.
        - If `build` is True, builds the model using the ClewsBuilder module.
        - Loads the scenario configuration and processes scenario data.
        - Prepares model and data files for the solver.
        - Solves the LP problem using the specified solver.
        - If the optimization is successful, writes the solution and generates summary reports.
        - Extracts results from the solution file and saves them to CSV.
        - If the model is not solved, logs an error message.
        input_csvs=Path(input_csvs) if input_csvs else self.input_csvs
        """

        
        if build or update_temporal_profiles:
    
            args={
                'combined_model_config_path': self.combined_model_config_path,
                'storage_algorithm': self.storage_algorithm,
                'scenario':self.scenario,
                'clustering_attributes':self.clustering_attributes
                }
            
            clewsBuild=BuildModel(**args)
            if build:
                clewsBuild.build(update_clews_builder=False)
            elif update_temporal_profiles:
                clewsBuild.update_temporal_profiles()
            
        else:
 
            utils.print_update(level=1,
                message=f'Skipping CLEWs builder and profile updates and using prepared SETs and Params from {input_csvs}')
            

    #1           
        # Should not assign loaded config from object, Loading the config from path is essential to recognize the changes in scenario data.
        utils.print_update(level=1,
                message=f' Loading config @ {self.combined_model_config_path}')
        self.cm_config=self.aparser.load_config(self.combined_model_config_path)
        
    #2        
        utils.print_update(level=1,
                message=f' Loading scenario config @ {self.combined_model_config_path}')
        self.scenario_cfg:dict=self.aparser.get_scenarios(self.cm_config['clews']).get(self.scenario)
        self.process_scenario_data()
        
        self.timeslices=len(pd.read_csv(self.input_csvs/'TIMESLICE.csv')) # We need this for directories
        utils.print_update(level=2,
                message=f'Timeslices: {self.timeslices}')
            
        self.solver_log_save_to=self.scenario_results_root/f'{self.timeslices}ts'/'gurobi.log'
        self.solver_log_save_to.parent.mkdir(parents=True,exist_ok=True)
         
        utils.print_update(level=1,
            message='Preparing model and data files. ')
        self.data_file,self.model_file=self.get_model_run_files()
    #3

        self.write_LP_file(self.model_file,
                           self.data_file,
                           self.LP_file)
        
        utils.print_update(level=1,
            message=f'Solving the LP problem with {solver} solver')
        
        #### solution (from solver), LP (from solver) file directories
        self.solution_path = self.scenario_results_root/f'{self.timeslices}ts'/f'{self.timeslices}ts_solution_{solver_name}.sol'
        

        if solver_name=='gurobi':
            self.solved_model=self.solve_model_gurobi(self.LP_file,
                                        log_path=self.solver_log_save_to,
                                        threads=threads)
                

            if self.solver_log_save_to.exists():
                self.solver_log_save_to.unlink()
            
            
            # save_to can't be a path object as gurobipy's write method doesn't handle pathobject,only string
            solved_successful:bool = solver.get_solve_status(self.solved_model)
        
            if solved_successful :
                utils.print_update(level=2,
                                message="Optimization successful. An optimal solution is available.")
                utils.print_update(level=1,
                        message=f'Writing the Solution to : {self.solution_path}')
                if self.solution_path.exists():
                        self.solution_path.unlink()
                    
                self.write_solution(self.solved_model,
                            self.solution_path)
                
                utils.print_update(level=1,
                    message='Extracting the shadow price of Electricity (ELCB02) from Electricity Balance Constraint')
                self.shadow_price_ELCB02=self.get_shadow_price_ELCB02(self.solved_model,
                                plot_save_to=self.scenario_results_root/f'{self.timeslices}ts'/f'shadowprice_ELC02_{self.timeslices}ts.png',
                                show=False)
                
                utils.print_update(level=1,
                    message='Preparing the summary reports for constraints, from solved model')
                self.duals_df,self.binding_constraints,self.non_binding_constraints=self.get_constraints(self.solved_model)
                self.get_summary_report(self.binding_constraints,
                        self.non_binding_constraints,
                        self.scenario_results_root/f'{self.timeslices}ts'/'constraints_summary.txt')
                
                duals_save_to=self.scenario_results_root/f'{self.timeslices}ts'/'EBa11_EnergyBalanceEachTS5_duals.csv'
                utils.print_update(level=2,
                    message=f'Duals extracted and saved to csv @ {duals_save_to} ')
                self.duals_df.to_csv(duals_save_to)
            
            else:
                utils.print_update(alert=True,
                message=f'X Model not solved, check the logs for more details @ {self.solver_log_save_to}')
            
        if solver_name=='cbc':
            self.solve_model_cbc(lp_path=self.LP_file,
                                 solution_path=self.solution_path,
                                 threads=threads)

        # Wait until the solution file exists
        if self.solution_path.exists():
                utils.print_update(level=1,
                message=f'Extracting results from Solution : {self.solution_path}')
                self.results_dir=self.get_result_csvs(solution_file=self.solution_path,
                                     solver_name=solver_name)
                
                utils.print_update(level=1, message="Creating the visuals...")  # handles the result folder creation
                if self.results_dir is not None:
                    """ 
                    self.get_visuals(model_results_direc=self.results_dir,
                                     visual_configs=self.visual_config,
                                     plots_save_to=self.plots_save_to)
                    """
                    utils.print_update(level=1, message="type bash command `bash dashboard.sh' from root directory for the interactive dashboard")  # handles the result folder creation

                else:
                    utils.print_update(level=2, message="Otoole Results files (.csvs) incomplete")  # handles the result folder creation
        
        else:
            utils.print_update(level=1, message="X The Solution file not found. Solution writing takes some time. Please wait until the file is written/exists.")  # handles the result folder creation
        

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Run CLEWs parameter update script')

    # Optional arguments with default values
    parser.add_argument('--combined_model_config', 
                        type=str, 
                        default=str(Path("config/config.yaml")), 
                        help="Path to the combined model configuration file (default: 'default_combined_model_config.yml')")
    
    parser.add_argument('--scenario', 
                        type=str, 
                        default=str('Base'), 
                        help="Scenario names that are already defined via config.yaml")


    parser.add_argument('--storage_algorithm', 
                        type=str, 
                        default=str('Kotzur'), 
                        help="Storage Algorithm name (supports Niet, Kotzur). Defaults to 'Kotzur'")

    parser.add_argument('--input_csvs', 
                        type=str or Path, 
                        help="Directory of the CSVs with all SETs, Params")
    """
    parser.add_argument('--solver', 
                        type=bool, 
                        default=False,
                        help="Currently supports 2 solvers: gurobi,cbc")
    """
    parser.add_argument('--build', 
                        type=bool, 
                        default=False,
                        help="If TRUE, runs the ClewsBuilder module. Recommended while SETs,Params needed updates e.g. clustering changes, snapshot changes etc.")
    
    # Parse the arguments
    args = parser.parse_args()

    clewsRunner = RunModel(args.combined_model_config,
                        args.scenario,
                        args.storage_algorithm,
                        args.input_csvs)
    
    clewsRunner.run(build=args.build)
                    
   