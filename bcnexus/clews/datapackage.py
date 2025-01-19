import pandas as pd
from typing import List, Tuple
from pathlib import Path
from dataclasses import dataclass
from .. import utils


class GetDataPackage:
    def __init__(self, directory: str):
        """
        Initialize the class with the directory containing the CSV files.
        
        :param directory: Path to the directory containing CSV files.
        """
        self.directory = Path(directory)
        self.all_dfs_dict = {}
        
        # Load the CSV files into the dictionary
        self.csv_files = []
        self.load_csvs()

    def load_csvs(self) -> dict | None:
        """
        Load all CSV files from the specified directory into the dictionary.
        
        The dictionary key is the filename without the .csv extension, 
        and the value is the corresponding DataFrame.
        """

        # Convert generator to a list to avoid exhaustion
        self.csv_files = list(self.directory.glob('*.csv'))  # Convert to list

        if not self.csv_files:
            utils.print_update(level=2,message="No CSV files found in the directory.")
            self.all_dfs_dict = {}
            return {}

        self.all_dfs_dict = {}

        # Read all CSV files and store them in a dictionary
        self.all_dfs_dict = {}
        for file in self.csv_files:
            df = pd.read_csv(file)
            if not df.empty:
                self.all_dfs_dict[file.stem] = df
            else:
                pass
 
        return self.all_dfs_dict


    def get_dataframe(self, filename: str) -> pd.DataFrame:
        """
        Retrieve a specific DataFrame by filename (excluding .csv extension).
        
        :param filename: The name of the CSV file (without extension).
        :return: The DataFrame corresponding to the filename, or None if not found.
        """
        return self.all_dfs_dict.get(filename, None)

    def load_data(self) -> Tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame]]:
        """
        Return the entire dictionary of DataFrames.
        
        :return: Dictionary with filenames as keys and DataFrames as values.
        """
        dfs_list = list(self.all_dfs_dict.keys())
        
        # Create SETS list
        SETS = [item for item in dfs_list if item.isupper()]

        # Prepare Params list by excluding items in SETS from dfs_list
        Params = [item for item in dfs_list if item not in SETS]

        # Subset dictionary using keys in SETS
        SETS_dfs = {key: self.all_dfs_dict[key] for key in SETS if key in self.all_dfs_dict}

        # Subset dictionary using keys in Params
        Params_dfs = {key: self.all_dfs_dict[key] for key in Params if key in self.all_dfs_dict}
        utils.print_update(level=4, message=f"{len(SETS_dfs)} non-empty SETs loaded")
        utils.print_update(level=4, message=f"{len(Params_dfs)} non-empty Params loaded")
        
        return SETS_dfs, Params_dfs
    
    def get_params_args(self):
        _, Params_dfs = self.load_data()
        
        # Create a dictionary: key is the DataFrame name, value is the list of columns excluding "VALUE"
        Params_SETS_dict = {
            key: [col for col in df.columns if col != "VALUE"] for key, df in Params_dfs.items()
        }

        return Params_SETS_dict 
    
    def show(self) -> List:
        return list(self.all_dfs_dict.keys())

    
@dataclass
class Checker:
    SETs_dfs: dict[str, pd.DataFrame]
    Params_dfs: dict[str, pd.DataFrame]

    def check_sets(self):
        """
        Check if any SET item has None, empty, corrupted, whitespace-only entries, or non-string values.
        """
        utils.print_update(level=4,message="Checking if any SET item has None, empty, corrupted, whitespace-only entries, or non-string values.")
                
        # Prepare a list to store the summary of results
        sets_report :list= []
        empty_sets_report:list=[]   # List to store empty sets
        errors_report:list=[]        # List to store error in sets
        total_counts:dict = self.get_set_counts()
        
        # First, summarize the SETs info (values, unique counts, etc.)
        sets_report.append("SETs Summary:\n")
        
        for key, count in total_counts.items():
            if count!=0:
                sets_report.append(f"   {key}: {count}")
            else:
                empty_sets_report.append(f"{key}")  # Add the mismatch to the list
        
        # List all empty sets separately at the bottom
        if empty_sets_report:
            sets_report.append("  \nx Empty Sets:\n   " + "\n   ".join(empty_sets_report))
        
        for key, df in self.SETs_dfs.items():
            # Check if the 'VALUE' column exists
            if 'VALUE' not in df.columns:
                errors_report.append(f"  \n !!! Error: 'VALUE' column is missing in the SET: {key}")
            else:
                # Check if the 'VALUE' column has None, empty, corrupted, whitespace-only entries, or non-string values
                corrupted:list = df['VALUE'].apply(lambda x: pd.isna(x) or (isinstance(x, str) and (x == '' or x.isspace())))

                # If there are any errors, print the key
                if corrupted.any():
                    errors_report.append(f"  \n !!! >> Error found in key: {key}")
                else:
                    pass
        sets_report.append(" \nx Errors in Defined Sets:\n   " + "\n   ".join(errors_report))
        
        return sets_report

    def get_set_counts(self) -> dict[str, int]:
        """
        Get the unique count of 'VALUE' entries in each SET DataFrame.
        """
        sets_total_counts = {}
        
        # Iterate over the SETs_dfs dictionary
        for key, df in self.SETs_dfs.items():
            # Calculate the number of unique values for the 'VALUE' column
            count = df['VALUE'].nunique()  # Adjust the column to match your specific column in the DataFrame
            sets_total_counts[key] = count
        
        return sets_total_counts
    
    def check_demand_fuel_def(self)->list:
        # Extract unique values from each list
        accumulated_annual_demand_fuel = set(self.Params_dfs['AccumulatedAnnualDemand']['FUEL'].unique())
        specified_annual_demand_fuel = set(self.Params_dfs['SpecifiedAnnualDemand']['FUEL'].unique())
        specified_demand_profile_fuel = set(self.Params_dfs['SpecifiedDemandProfile']['FUEL'].unique())
        
        # Prepare a list to store the summary of results
        demand_fuel_def_report:list = []
            
        # Check for common items between the two lists
        multiple_def_fules: list = accumulated_annual_demand_fuel.intersection(specified_annual_demand_fuel)
        if multiple_def_fules:
            print(f"FUEL : {multiple_def_fules} It cannot be defined for a commodity if its SpecifiedAnnualDemand for the same year is already defined and vice versa."
                f"For more about model structure please check Demands in OSeMOPSYS/CLEWs (https://osemosys.readthedocs.io/en/latest/manual/Structure%20of%20OSeMOSYS.html#demands)")
            demand_fuel_def_report.append(" \n Duplicate definitions:\n")
            demand_fuel_def_report.append(f" \n  FUEL : {multiple_def_fules} \n  It cannot be defined for a commodity if its SpecifiedAnnualDemand for the same year is already defined and vice versa.")

        else:
            pass

        # Ensure items in 'SpecifiedDemandProfile' exist in one of the previous lists
        for fuel in specified_demand_profile_fuel:
            if fuel not in accumulated_annual_demand_fuel and fuel not in specified_annual_demand_fuel:
                utils.print_update(level=4,message=f"Item not found in any of the previous lists: {fuel}")
        if demand_fuel_def_report:
            pass
        else:
            demand_fuel_def_report=['  ✓ No error found.']
        return demand_fuel_def_report
    
    def check_params_sets_def(self):
        
        params_sets_def_report:list=[]
        empty_params_report:list=[]
        mismatches_report:list=[]
        
        total_counts:dict = self.get_set_counts()
        
        # Iterate over each parameter and its corresponding DataFrame in Params_dfs
        for param, df in self.Params_dfs.items():
            # Checking for empty DataFrame
            if df.empty:
                empty_params_report.append(param)  # Add empty DataFrame name to the list
                continue
            
            params_sets_def_report.append(f"'{param}': {list(df.columns)}\n")
            # Checking the unique values for each set
            for set_name, expected_count in total_counts.items():
                if set_name in df.columns:
                    unique_count = df[set_name].nunique()
                    params_sets_def_report.append(f"   {set_name}: {unique_count} unique values (SETs Defined : {expected_count})")
                    
                    if unique_count == expected_count:
                        params_sets_def_report.append("    ✓ Match!")
                    else:
                        mismatches_report.append(f"{param}[{set_name}]")  # Add the mismatch to the list
                        params_sets_def_report.append("    x Mismatch")
                else:
                    pass
            
            params_sets_def_report.append(f"{70*'_'}")
        
        # List all empty DataFrames at the bottom of the summary
        if empty_params_report:
            params_sets_def_report.append("Empty Params:")
            for empty_df in empty_params_report:
                params_sets_def_report.append(f"  - {empty_df}")
            params_sets_def_report.append(f"{70*'_'}")
        
        # List all mismatches separately at the bottom
        if mismatches_report:
            params_sets_def_report.append("Mismatches:\n  " + "\n  ".join(mismatches_report))
        
        return params_sets_def_report
    
    def get_supply_mines(self):
        supply_mins_report: list = []

        ipAR = set(self.Params_dfs['InputActivityRatio']['TECHNOLOGY'])
        techs = set(self.SETs_dfs['TECHNOLOGY']['VALUE'])
        sources_inputAR: list = list(techs.difference(ipAR))

        # Categorize technologies
        pwr_techs = [tech for tech in sources_inputAR if tech.startswith("PWR")]
        import_techs = [tech for tech in sources_inputAR if tech.startswith("IMP")]
        ground_water_supply_techs = [tech for tech in sources_inputAR if tech.startswith("MINPRC")]
    
        land_supply_techs = [tech for tech in sources_inputAR if tech.startswith("MINLND")]
        VRE_techs = [tech for tech in sources_inputAR if tech.startswith("RNW")]
        hydrobasin_inflow_tech = [tech for tech in sources_inputAR if tech.startswith("INFLOW")]
        public_water_demand_techs=[tech for tech in sources_inputAR if tech.startswith("DEMPUBGWT")]
        agr_water_demand_techs=[tech for tech in sources_inputAR if tech.startswith("DEMAGRGWT")]

        # Handle each category
        if pwr_techs:
            pwr_techs_text = "\n".join([f"  {tech}" for tech in pwr_techs])
            supply_mins_report.append(" x Error: Transport POWER Technologies not defined:")
            supply_mins_report.append(pwr_techs_text)
        
        if import_techs:
            import_techs_text = "\n".join([f"  {tech}" for tech in import_techs])
            supply_mins_report.append("\n FUEL-IMPORT Technologies:")
            supply_mins_report.append(import_techs_text)
            
        if ground_water_supply_techs:
            ground_water_text = "\n".join([f"  {tech}" for tech in ground_water_supply_techs])
            supply_mins_report.append("\n Ground Water Supply Technologies:")
            supply_mins_report.append(ground_water_text)

            
        if VRE_techs:
            vre_text = "\n".join([f"  {tech}" for tech in VRE_techs])
            supply_mins_report.append("\n Renewable Energy Supply Technologies:")
            supply_mins_report.append(vre_text)

            
        if hydrobasin_inflow_tech:
            reseroir_water_text = "\n".join([f"  {tech}" for tech in hydrobasin_inflow_tech])
            supply_mins_report.append("\n Hydrobasin Inflow Technologies:")
            supply_mins_report.append(reseroir_water_text)

        
        if public_water_demand_techs:
            public_water_demand_text = "\n".join([f"  {tech}" for tech in public_water_demand_techs])
            supply_mins_report.append("\n Public Water Demand:")
            supply_mins_report.append(public_water_demand_text)
    
        
        if agr_water_demand_techs:
            agr_water_demand_text = "\n".join([f"  {tech}" for tech in agr_water_demand_techs])
            supply_mins_report.append("\n Agricultural water demand Technologies:")
            supply_mins_report.append(agr_water_demand_text)

            
        if land_supply_techs:
            land_supply_text = "\n".join([f"  {tech}" for tech in land_supply_techs])
            supply_mins_report.append("\n Land Supply Technologies:")
            supply_mins_report.append(land_supply_text)

            
        # Handle other technologies
        other_techs = [tech for tech in sources_inputAR if tech not in (pwr_techs + 
                                                                        hydrobasin_inflow_tech+ 
                                                                        import_techs + 
                                                                        VRE_techs+
                                                                        ground_water_supply_techs + 
                                                                        public_water_demand_techs +
                                                                        agr_water_demand_techs+
                                                                        land_supply_techs)]
        if other_techs:
            other_techs_text = "\n".join([f"  {tech}" for tech in other_techs])
            supply_mins_report.append("\n Other Technologies:")
            supply_mins_report.append(other_techs_text)
            supply_mins_report.append("\n")

        return supply_mins_report


        
    
    def get_summary_report(self, summary_save_to: Path = "summary.txt"):
        """
        Check parameters in Params_dfs and summarize the results to a file.
        """
        
        # # Prepare a list to store the summary of results
        summary :list= []
        
        # Checking the validation methods and collect reports
        
        summary.append(f"{20*'='} SETS {20*'='}\n")
        summary.extend(self.check_sets())

        summary.append(f"\n{30*'='} Parameters {30*'='}\n")
        summary.extend(self.check_params_sets_def())
        
        summary.append(f"\n{30*'='} Other Validations {30*'='}")
        summary.append(f"\n{10*'>'} Fuel definition in SpecifiedDemandProfile, AccumulatedAnnualDemand and SpecifiedAnnualDemand\n")
        summary.extend(self.check_demand_fuel_def())
        
        summary.append(f"\n{10*'>'} List of SOURCE (mines) as per InputActivityRatio Definitions\n")
        summary.extend(self.get_supply_mines())
        
        # End of report
        summary.append(f"\n{100*'='}")

    
        try:
            with open(summary_save_to, "w") as file:
                file.write("\n".join(summary))
            utils.print_update(level=4, message=f"Summary saved to {summary_save_to}")
        except Exception as e:
           utils.print_update(level=4, message=f"Error writing to file: {e}")