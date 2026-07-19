"""
CLEWs Model Runner Module

This module provides the core functionality for running Climate, Land, Energy, and Water Systems (CLEWs) 
optimization models within the BC Nexus framework. It handles the complete workflow from model preparation 
through execution to results extraction and visualization.

Key Components:
---------------
- RunModel: Main class that orchestrates the entire CLEWs model execution pipeline
  * Scenario configuration and data preprocessing
  * Model building with storage algorithms (Kotzur/Niet)
  * LP file generation using GLPK
  * Optimization solving with Gurobi or CBC solvers
  * Results extraction and CSV generation via otoole
  * Shadow price analysis and constraint reporting
  * Performance logging and memory tracking

Supported Storage Algorithms:
-----------------------------
- Kotzur: Storage representation based on Kotzur et al. methodology
- Niet: Storage representation based on Niet methodology

Supported Solvers:
-----------------
- Gurobi: Commercial optimization solver (default, recommended)
- CBC: Open-source solver (alternative)

Workflow:
---------
1. Initialize RunModel with scenario configuration
2. Process scenario data and update technology parameters
3. Generate preprocessed data and model files based on storage algorithm
4. Create LP file using GLPK
5. Solve optimization problem with selected solver
6. Extract results to CSV format
7. Generate reports, visualizations, and performance logs

Dependencies:
------------
- gurobipy: Gurobi optimizer Python interface
- pandas: Data manipulation and analysis
- psutil: System and process utilities
- yaml: YAML file parsing
- otoole: OSeMOSYS data management tool
- GLPK: GNU Linear Programming Kit (external)

Usage Example:
-------------
    runner = RunModel(
        run_scenario='Base_CNZ',
        storage_algorithm='Kotzur',
        scenario_config_path='config/scenarios_bcnexus.yaml'
    )
    runner.run(build=True, solver_name='gurobi', threads=32)

Notes:
------
- Requires proper installation of solvers (Gurobi or CBC) and GLPK
- Input data must follow OSeMOSYS format conventions
- Results are organized by scenario and timeslice configuration
- Memory and runtime are logged for performance analysis

Author: BC Nexus Development Team
License: See repository LICENSE file
"""

import argparse
import subprocess
import sys
import time
import warnings
from pathlib import Path
from typing import Optional

import gurobipy as gp
import pandas as pd
import psutil
import yaml

import bcnexus.plots as plotter
from bcnexus import utils

# local packages
from bcnexus.attributes_parser import AttributesParser
from bcnexus.clews import preprocess_data_Kotzur, preprocess_data_Niet, schema, solver
from bcnexus.clews.builder import BuildModel

warnings.filterwarnings("ignore")

class RunModel:
    """ 
    RunModel is a class that takes in the prepared folder of CSVs (SETs,Parameters) and do all the prerequisites to solve and extract the results.
    """
    def __init__(self,
                run_scenario:str,
                storage_algorithm:str=None,
                input_csvs:str|Path=None,
                scenario_config_path:str|Path=None,
                clustering_attributes:dict=None
               ):
        
        self.scenario_config_path:Path=Path(scenario_config_path) if scenario_config_path else Path('config/scenarios_bcnexus.yaml')
        self.aparser=AttributesParser(self.scenario_config_path)
        
        self.run_scenario=str(run_scenario)
        self.storage_algorithm=storage_algorithm if storage_algorithm else self.aparser.DEFAULT_STORAGE_ALGORITHM
        self.scenario_cfg:dict=self.aparser.scenario_dict.get('SCENARIOS').get(self.run_scenario)
        self.input_csvs=Path(input_csvs) if input_csvs else self.aparser.get_scenario_inputs_path(scenario=self.run_scenario,
                                                                                                  storage_algorithm=self.storage_algorithm)
        self.clustering_attributes = (
            clustering_attributes
            if clustering_attributes
            else utils.print_info("Using default clustering attributes: {'hour_grouping': 6, 'n_clusters': 2}")
                and dict(hour_grouping=6,
                         n_clusters=2)
        )

        utils.print_update(level=1,
                    message=f"Initiated CLEWs Model Runner for '{self.run_scenario}' scenario with '{self.storage_algorithm}' storage algorithm")
        utils.print_update(level=2,
                    message=f" Input CSVS set to: {self.input_csvs}")
        
        # The Attributes Parser handles all sorts of parsing from the User Config file and implements necessary checks, validation and sets suitable defaults if any field is missing.
        builder_args={
                'storage_algorithm': self.storage_algorithm,
                'run_scenario':self.run_scenario,
                'clustering_attributes':self.clustering_attributes
                }
            
        self.clewsBuilder=BuildModel(**builder_args)
        self.get_all_attributes()

  
        
    def get_all_attributes(self):
        self.otoole_yaml_file=self.aparser.get_otoole_yaml_file(self.storage_algorithm)
        self.clewsb_config:dict=self.aparser.clewsb_config #self.aparser.load_config(self.aparser.clews_builder_config_path)
        (self.start_year, self.last_year)=self.aparser.get_clews_snapshot()
        self.region=self.aparser.get_region()
        
        self.org_model_file=self.aparser.get_model_file_path(storage_algorithm=self.storage_algorithm)
        self.LP_file=self.input_csvs.parent/self.run_scenario/f'{self.run_scenario}.lp'
        self.scenario_results_root=self.aparser.get_scenario_results_path(scenario=self.run_scenario,
                                                                          storage_algorithm=self.storage_algorithm)
        # self.visual_config:dict=self.aparser.get_visual_configs()
        # self.plots_save_to:Path=self.aparser.get_plots_save_to()
        self.clewsBuilder.get_clustering_attributes()

    # ---------------------------------------------------------------- paths
    def run_dir(self) -> Path:
        """Deterministic output directory for this (scenario, algo, temporal) branch.

        Replaces the runtag-suffixed directory so an orchestrator (snakemake)
        can declare real file targets. One branch == one directory, re-entrant.
        Run history/versioning is DVC's job, not the filesystem's.
        """
        self.timeslices = len(pd.read_csv(self.input_csvs / 'TIMESLICE.csv'))
        d = self.scenario_results_root / f'{self.timeslices}ts'
        d.mkdir(parents=True, exist_ok=True)
        return d

    def process_scenario_data(self):
        utils.print_update(level=4,
                    message="Processing Scenario Data...")
        
        # Update TECHNOLOGY SET csv file
        TECHNOLOGY_df=pd.read_csv(self.input_csvs / 'TECHNOLOGY.csv')
        scenario_techs = list(self.scenario_cfg.get('TECHS').keys())
        tech_sets = list(TECHNOLOGY_df['VALUE'])

        for tech in scenario_techs:
            if tech not in tech_sets:
                tech_sets.append(tech)

        tech_sets_df = pd.DataFrame(tech_sets, columns=['VALUE'])
        tech_sets_df.to_csv(self.input_csvs / 'TECHNOLOGY.csv', index=False)
        utils.print_update(level=4,
                    message=f"File Updated: {self.input_csvs / 'TECHNOLOGY.csv'}")
        
        # Update TECHNOLOGY SET's info to clews_builder_config file.
        for tech_id, values in self.scenario_cfg.get('TECHS').items():
            for tech_type in self.clewsb_config['TECHNOLOGIES'].keys():
                if tech_id in self.clewsb_config['TECHNOLOGIES'][tech_type].keys():
                    self.clewsb_config['TECHNOLOGIES'][tech_type][tech_id].update(values)
                else:
                    pass
        # Save the updated YAML back to the same file
        with open(self.aparser.clews_builder_config_path, 'w') as file:
            yaml.dump(self.clewsb_config, file, default_flow_style=False)
        
        utils.print_update(level=4,
                    message=f"File Updated : {self.aparser.clews_builder_config_path}")
    
        # Define common args
        common_attr = {
            'scenario_cfg': self.scenario_cfg,
            'start_year': self.start_year,
            'last_year': self.last_year,
            'region': self.region,
            'delete_technologies_func': schema.delete_technologies,
            'add_technologies_func': schema.add_technologies,
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
                'pre_process': schema.pre_process_input_activity_ratio,
                'additional_columns': {'MODE_OF_OPERATION': 1},  # FUEL will be added dynamically
            },
        ]

        # Iterate over each attribute and apply the function
        for unique_attr in scenario_attributes:
            # Merge common params with unique params, giving precedence to unique params
            params = {**common_attr, **unique_attr}
            schema.process_scenario_attribute(**params)
        
        utils.print_update(level=4,
                    message="Scenario Data processing completed.Loading updated ClewsBuilder configuration...")
        self.clewsb_config=self.aparser.load_config(self.aparser.clews_builder_config_path)
        utils.print_update(level=4,
                    message=f"ClewsBuilder configuration reloaded from {self.aparser.clews_builder_config_path}")
    

    def get_input_datafile_from_csvs(self,
                                     input_csvs:str|Path=None,
                                     datafile_path:str=None)->Path:

        input_csvs = Path(input_csvs) if input_csvs else self.input_csvs
        datafile_path = datafile_path if datafile_path else utils.ensure_path(input_csvs.parent /self.run_scenario/ f'{self.run_scenario}_data.txt')

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
            storage_algorithm (Optional[str]): The storage algorithm to use ('Kotzur' or 'Niet').

        Returns:
            Tuple[Path, Path]: Paths to the processed data and model files.
        """
        data_infile=Path(data_infile) 
        print("DATA_INFILE:", data_infile, "IS_DIR?", Path(data_infile).is_dir())
        processed_datafile=data_infile.with_suffix('.txt').with_name(data_infile.stem + 'Processed.txt')
        processed_model=self.input_csvs.parent/self.run_scenario/f'{self.storage_algorithm}_Model_processed.txt'
        
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
        
        _data_file_=self.get_input_datafile_from_csvs(self.input_csvs)
        
        data_file, model_file = self.preprocess_data_model( data_infile=_data_file_,
                                                            model_file=self.org_model_file)
        
        return data_file,model_file
    
    def update_otoole_config(self):
        ### Updating otoole yaml file
        
        # Updating day split in yaml file
        schema.new_yaml_param(self.otoole_yaml_file, 'DaySplit', self.day_split)

        # schema.new_yaml_param(self.otoole_yaml_file, 'StorageMaxCapacity', self.StorageMaxCapacity)
        schema.new_yaml_param(self.otoole_yaml_file, 'ResidualStorageCapacity', self.ResidualStorageCapacity)
        
    def get_result_csvs(self,
                        solution_file:str|Path=None,
                        solver_name='gurobi',
                        debug_mode:Optional[bool]=False,
                        results_save_to:Optional[Path]=None)->Path:
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
        if results_save_to:
            self.otoole_results_dir=utils.ensure_path(results_save_to)
        else:
            # deterministic per-branch results dir (runtag removed; history is DVC's job)
            self.otoole_results_dir = utils.ensure_path(self.run_dir() / f'result_csvs_{solver_name}')
        
        if debug_mode:
            otoole_results_cmd= f"otoole -v results {solver_name} csv {self.solution_path} {self.otoole_results_dir} csv {self.input_csvs} {self.otoole_yaml_file}"
        else:
            otoole_results_cmd= f"otoole results {solver_name} csv {self.solution_path} {self.otoole_results_dir} csv {self.input_csvs} {self.otoole_yaml_file}"
        
        try:
            subprocess.run(otoole_results_cmd, shell=True, text=True)
            utils.print_update(level=3,
                message=f"Result extraction completed and saved to {self.otoole_results_dir}")
            return self.otoole_results_dir

        except Exception as e:
            utils.print_update(level=4,
                        message=f"An error occurred during otoole result extraction: {e} and ")
      

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
    
    # ---------------------------------------------------------------- stages
    # Each stage: file inputs -> file outputs, no reliance on state set by a
    # previous stage *in the same process*. run() composes them; snakemake
    # calls them one process each via bcnexus/stages.py.

    def stage_build(self, include_livestock: bool = True) -> Path:
        """#1-#3: CLEWs builder -> temporal profiles -> storage-case schema.

        Starts from a FRESH csv template (idempotent): re-running this stage on
        an already-built directory must not append duplicate rows (GLPK fails
        on e.g. 'OutputActivityRatio[...] already defined' otherwise).
        """
        utils.print_update(level=1,
            message=f'CLEWs Builder: SETs and Params for scenario: {self.run_scenario}')
        self.clewsBuilder.get_csv_template(force_replace=True)
        self.clewsBuilder.build(include_livestock=include_livestock,
                                update_clews_builder=True)
        self.clewsBuilder.update_temporal_profiles()
        utils.copy_csv_files(src_folder=self.clewsBuilder.clews_build_input_csv_dir,
                             dest_folder=self.clewsBuilder.storage_case_input_csvs,
                             all_files=True)
        self.clewsBuilder.update_storage_case_temporal_schema()
        return Path(self.clewsBuilder.storage_case_input_csvs)

    def stage_scenario(self) -> Path:
        """#4a: apply scenario overrides from scenarios config onto built CSVs."""
        utils.print_update(level=1,
            message=f'Loading scenario config @ {self.scenario_cfg}')
        self.process_scenario_data()
        return Path(self.input_csvs)

    def stage_datafile(self) -> tuple:
        """#4b: CSVs -> otoole datafile + model file selection."""
        utils.print_update(level=1, message='Preparing model and data files.')
        self.data_file, self.model_file = self.get_model_run_files()
        return Path(self.data_file), Path(self.model_file)

    def stage_lp(self) -> Path:
        """#5a: glpsol -> LP file. Re-derives datafile paths if not in memory."""
        if not hasattr(self, 'data_file'):
            self.stage_datafile()
        self.write_LP_file(self.model_file, self.data_file, self.LP_file)
        return Path(self.LP_file)

    def stage_solve(self, solver_name: str = 'gurobi', threads: int = 32):
        """#5b: solve LP -> .sol; gurobi path also writes duals, binding-constraint
        summary, and the ELCB02 shadow-price plot. Returns solution path or None."""
        out = self.run_dir()
        self.solution_path = out / f'{self.timeslices}ts_solution_{solver_name}.sol'
        self.solver_log_save_to = out / f'{solver_name}.log'

        utils.print_update(level=1,
            message=f'Solving the LP problem with {solver_name} solver')

        if solver_name == 'gurobi':
            self.solved_model = self.solve_model_gurobi(self.LP_file,
                                                        log_path=self.solver_log_save_to,
                                                        threads=threads)
            if not solver.get_solve_status(self.solved_model):
                utils.print_error(
                    f'X Model not solved, check logs @ {self.solver_log_save_to}')
                return None
            if self.solution_path.exists():
                self.solution_path.unlink()
            self.write_solution(self.solved_model, self.solution_path)

            # post-solve diagnostics (moved verbatim from run() tail)
            self.shadow_price_ELCB02 = self.get_shadow_price_ELCB02(
                self.solved_model,
                plot_save_to=out / f'shadowprice_ELC02_{self.timeslices}ts.png',
                show=False)
            self.duals_df, self.binding_constraints, self.non_binding_constraints = \
                self.get_constraints(self.solved_model)
            self.get_summary_report(self.binding_constraints,
                                    self.non_binding_constraints,
                                    out / 'constraints_summary.txt')
            self.duals_df.to_csv(out / 'EBa11_EnergyBalanceEachTS5_duals.csv')

        elif solver_name == 'cbc':
            self.solve_model_cbc(lp_path=self.LP_file,
                                 solution_path=self.solution_path,
                                 threads=threads)

        return self.solution_path if self.solution_path.exists() else None

    def stage_results(self, solver_name: str = 'gurobi'):
        """#6: .sol -> result CSVs via otoole. Re-derives solution path if needed."""
        if not hasattr(self, 'solution_path'):
            out = self.run_dir()
            self.solution_path = out / f'{self.timeslices}ts_solution_{solver_name}.sol'
        if not self.solution_path.exists():
            utils.print_update(level=1, message='X Solution file not found.')
            return None
        self.results_dir = self.get_result_csvs(solution_file=self.solution_path,
                                                solver_name=solver_name)
        return self.results_dir

    def run(self,
            input_csvs: str | Path=None,
            build:bool=False,
            save_individual_plots:bool=False,
            include_livestock:bool=False,
            solver_name='gurobi',
            threads:int=32,
            machine_id:str=None):
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
        # Measure runtime and memory usage
        start_time = time.time()
        process = psutil.Process()

    #1           
        if build:
            self.stage_build(include_livestock=include_livestock)
        else:
            utils.print_update(level=1,
                message=f'Skipping CLEWs builder; using SETs/Params from {input_csvs or self.input_csvs}')
            # temporal/storage schema still refresh, as before (#2-#3)
            self.clewsBuilder.update_temporal_profiles()
            utils.copy_csv_files(src_folder=self.clewsBuilder.clews_build_input_csv_dir,
                                 dest_folder=self.clewsBuilder.storage_case_input_csvs,
                                 all_files=True)
            self.clewsBuilder.update_storage_case_temporal_schema()

        self.stage_scenario()
        
        self.stage_datafile()
        self.stage_lp()
        sol = self.stage_solve(solver_name=solver_name, threads=threads)
        if sol is not None:
            self.stage_results(solver_name=solver_name)
        else:
            utils.print_update(level=1,
                message='X No solution available; skipping result extraction.')

        self.results_dir = self.stage_results(solver_name=solver_name)
        self.vis_dir = Path(str(self.results_dir).replace('results', 'vis', 1))
        
 

        plotter_args=dict(
            nexus_scenario=self.run_scenario,
            storage_algorithm=self.storage_algorithm,
            timeslices=self.timeslices,
            results_csvs=self.results_dir,
            save_individual=save_individual_plots,
            plots_save_to=self.vis_dir if save_individual_plots else 'vis/clews'
        )
        # plotter.main(**plotter_args)
        plotter.get_plots(**plotter_args)
        # Calculate runtime and memory usage
        memory_usage = process.memory_info().rss  # Resident Set Size (RSS) in bytes

        # Log runtime and memory usage
        # (was: Path(self.run_scenario/self.scenario_results_root/...) — str/Path
        #  TypeError waiting to happen; run_dir() is the deterministic branch dir)
        RunModel.log_runtime_and_memory(scenario=self.run_scenario, timeslices=self.timeslices, clustering_attributes=self.clustering_attributes, start_time=start_time, memory_usage=memory_usage, save_to=self.run_dir(), threads=threads, machine_id=machine_id)

    @staticmethod
    def log_runtime_and_memory(scenario:str, 
                               timeslices:int,
                               clustering_attributes:dict,
                               start_time:float, 
                               memory_usage:float, 
                               save_to:str|Path,
                               threads:int=None,
                               machine_id:Optional[str]=None):
        # Ensure the directory exists
        log_dir_path = Path(save_to)
        log_dir_path.mkdir(parents=True, exist_ok=True)
        log_path = log_dir_path / "runtime_memory_log.txt"
        runtime = time.time() - start_time

        # Get the number of CPU cores/threads used
        cpu_count = psutil.cpu_count(logical=True)

        with log_path.open("a") as log_file:
            log_file.write(f"Scenario: {scenario}\n")
            log_file.write(f"Timeslices: {timeslices}\n")
            
            hour_grouping = clustering_attributes.get('hour_grouping', 'Not specified')
            n_clusters = clustering_attributes.get('n_clusters', 'Not specified')
            log_file.write(f"Clustering Attributes - Hour Grouping: {hour_grouping} , No of Clusters: {n_clusters} \n")
            log_file.write(f"Runtime: {runtime:.2f} seconds ({runtime / 60:.2f} minutes)\n")
            log_file.write(f"Run Start Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}\n")
            log_file.write(f"Run End Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}\n")
            log_file.write(f"Memory Usage: {memory_usage / (1024 * 1024):.2f} MB\n")
            try:
                username = psutil.Process().username()
                log_file.write(f"Linux User: {username}\n")
            except AttributeError:
                log_file.write("User:---\n")
                
            if machine_id is None:
                try:
                    machine_id = subprocess.check_output("hostname", shell=True).decode().strip()
                except subprocess.CalledProcessError as e:
                    log_file.write(f"Machine ID: Error retrieving ({e})\n")
            else:
                log_file.write(f"Machine ID: {machine_id}\n")
            log_file.write(f" Total Cores/Threads in Machine {cpu_count}\n ; Used in simulation : {threads} | ")

            log_file.write("-" * 50 + "\n")
        
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
                    
   