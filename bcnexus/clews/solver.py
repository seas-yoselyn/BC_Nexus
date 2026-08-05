import gurobipy as gp
from pathlib import Path
import pandas as pd
from typing import Optional
import matplotlib.pyplot as plt
from bcnexus.clews import model_structure as clews_const
import warnings
import subprocess
from bcnexus import utils

warnings.filterwarnings("ignore")
# Refactored by EL, 2024
# Source: https://github.com/KTH-dESA/OSeMBE_ECEMF/blob/main/run.py

def sol_gurobi(lp_path: str,
               log_path:Optional[str]='results/clews/gurobi.log',
               threads: int=16
   ):
    lp_path=str(lp_path)# gurobipy doesn't handle path objects
    log_path=str(log_path)
    threads=int(threads)
    
    try:
        utils.print_update(level=3,message="Gurobi update : \n")
        utils.print_update(level=3,message=f"{50*'-'}")
        m = gp.read(lp_path)
        m.Params.LogToConsole = 0  # don't send log to console
        m.Params.Method = 2  # 2 = barrier
        m.Params.Threads = threads  # limit solve to use max {threads}
        m.Params.NumericFocus = 2
        m.Params.ScaleFlag = 2  # aggressive scaling for wide coefficient ranges
        m.Params.BarHomogeneous = 1   # more robust barrier for numerically hard LPs
        m.Params.LogFile = log_path  # don't write log to file
        m.optimize()
        utils.print_update(level=3,message=f"{50*'-'}")
        utils.print_update(level=4,message="Model run completed. Please check the log for detailed report.")
        return m
    except gp.GurobiError as e:
        utils.print_update(level=4,message='Error code ' + str(e.errno) + ': ' + str(e))
    except AttributeError:
        utils.print_update(level=4,message='Encountered an attribute error')

def sol_cbc(lp_path: str,
            solution_path:str,
            threads:int=16):
    lp_path=str(lp_path)# cbc doesn't handle path objects
    solution_path=str(solution_path)# cbc doesn't handle path objects
    threads=int(threads)
    
    try:
        cmd_cbc=f"cbc {lp_path} solve threads {threads} -solu {solution_path}"
        subprocess.run(cmd_cbc, shell=True, text=True)
        """ 
        process = subprocess.Popen(cmd_cbc, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        for line in process.stdout:
            utils.print_update(message=line.strip())
            sys.stdout.flush()   # Force immediate print
        """
    except Exception as e:
        Warning(f" Error: {e}.\nCBC solution not generated !!")
        
def get_best_method(lp_path: str):
    m = gp.read(lp_path)
    
    # Solve the model with different values of Method
    bestTime = m.Params.TimeLimit
    bestMethod = -1
    
    for i in range(3):
        m.reset()
        m.Params.Method = i
        m.optimize()
        if m.Status == gp.GRB.OPTIMAL:
            bestTime = m.Runtime
            bestMethod = i
            # Reduce the TimeLimit parameter to save time with other methods
            m.Params.TimeLimit = bestTime

    # Report which method was fastest
    if bestMethod == -1:
        utils.print_update(level=4,message="Unable to solve this model")
    else:
        utils.print_update(level=4,message=f"Solved in {bestTime:g} seconds with Method {bestMethod}")

def get_duals(optimized_model:gp.Model):
    
    m=optimized_model
    start_year=clews_const.snapshot['start']
    current_year=2025
    try:
        # Retrieve dual values and constraints
        dual = m.Pi # Dual Values (shadow prices)
        constr = m.getConstrs()

        # Create DataFrame with constraint information and dual values
        df_dual = pd.DataFrame(data={'info': constr, 'value': dual})
        df_dual = df_dual.astype({'info': 'str'})

        # Extract meta-information from the constraint names
        meta = df_dual['info'].str.split('.', expand=True)
        meta = meta[1].str.split('(', expand=True)
        df_dual['constraint'] = meta[0]
        df_dual['sets'] = meta[1].str[:-2]
        df_dual = df_dual.drop(columns=['info'])
        
        discount_factor=0.04
        current_year=2025
        start_year=2020
        df_new = df_dual.copy()
        df_new['adjusted_value'] = df_new['value'] * ((1 + discount_factor) ** ((current_year - start_year) + 0.5))

        # df_dual['adjusted_value'] = df_dual.apply(
        #     lambda row: cal_discounted_value(row['value'], start_year=start_year, end_year=present_year), axis=1
        # )

        return df_new
    
    except Exception as e:
        utils.print_update(level=4,message=f"Error extracting duals: {e}")
        return {}
    
def cal_discounted_value(value: float, 
                         start_year: int, 
                         end_year: int, 
                         rate: float = 0.04) -> float:
    """
    Calculate the present value of a future amount using a discount rate.
    
    :param value: The future value to be discounted.
    :param start_year: The starting year (e.g., 2020).
    :param end_year: The ending year (e.g., 2025).
    :param rate: The annual discount rate (default is 4%).
    :return: The discounted value.
    """
    years = (end_year - start_year) + 0.5  # Optional half-year adjustment
    return value / ((1 + rate) ** years)


def get_solve_status(solved_model:gp.Model)->bool:
    if solved_model is not None:
        status = solved_model.status
        
        if status == gp.GRB.Status.OPTIMAL:
            ("Optimization successful. An optimal solution is available.")
            return True
        elif status == gp.GRB.Status.INFEASIBLE:
            utils.print_update(level=4,message="Model is infeasible. Computing IIS...")
            solved_model.computeIIS()
            solved_model.write("infeasible.ilp")
            return False
        elif status == gp.GRB.Status.UNBOUNDED:
            utils.print_update(level=4,message="Model is unbounded. Check the formulation.")
            return False
        elif status == gp.GRB.Status.INF_OR_UNBD:
            utils.print_update(level=4,message="Model is infeasible or unbounded. Re-running with DualReductions=0...")
            solved_model.setParam('DualReductions', 0)
            solved_model.optimize()
            return False
        elif status == gp.GRB.Status.TIME_LIMIT:
            utils.print_update(level=4,message="Optimization terminated due to time limit.")
            return False
        elif status == gp.GRB.Status.INTERRUPTED:
            utils.print_update(level=4,message="Optimization was interrupted by the user.")
            return False
        return False
    else:
        utils.print_update(level=4,message="Ambiguous solve status. Refer to Gurobi documentation for details.")
        

def write_sol(solved_model:gp.Model, 
              save_to: str):
    
    save_to = Path(save_to)
    save_to.parent.mkdir(parents=True, exist_ok=True)  # Ensure parent directories exist
    
    # As we handled the parent directory missing issue, now comnvert back to string !
    # save_to can't be a path object as gurobipy's write method doesn't handle pathobject,only string
    if get_solve_status(solved_model):
        solved_model.write(str(save_to)) 
    else:
        utils.print_update(level=4,message="Not a valid solution. Can not write to file")

def write_duals(dict_duals: dict,
                save_to:str)->None:
    
    save_to = Path(save_to)
    save_to.parent.mkdir(parents=True, exist_ok=True)  # Ensure parent directories exist

    # Write each constraint's dual value DataFrame to a separate CSV file
    for df in dict_duals:
        df_path = f'Dual_{df}.csv'  # Define the full file path
        dict_duals[df].to_csv(df_path, index=False)  # Save the DataFrame to CSV
    
    utils.print_update(level=4,message="Dual values saved to CSV successfully.")

def get_constraints_type(df_dual:pd.DataFrame)->tuple:
    
    # Identify binding and non-binding constraints
    df_dual['status'] = df_dual.apply(
        lambda row: 'Binding' if row['value'] != 0 else 'Non-Binding',
        axis=1
    )

    # Filter results
    binding_constraints = df_dual[df_dual['status'] == 'Binding']
    non_binding_constraints = df_dual[df_dual['status'] == 'Non-Binding']
    """ 
    print("Binding Constraints:")
    print(binding_constraints.constraint.unique())

    print("Non-Binding Constraints:")
    print(non_binding_constraints.constraint.unique())
    """
    
    return binding_constraints,non_binding_constraints

def get_shadow_price_ELCB02(all_binding_constraints:pd.DataFrame,
                            constraint:str='EBa11_EnergyBalanceEachTS5',
                            fuel:str='ELCB02',
                            datafield='adjusted_value'):
    
    """
    ### Conversion Factor:  3.6 * 1E-3 (m$/PJ to $/kWh)

    The conversion factor (3.6*1E-3 ) is used to convert million dollars per petajoule (m$/PJ) to dollars per kilowatt-hour ($/kWh).

    - Explanation:
    1. 1 PJ (petajoule)= 1E15 joules.
    2. 1 kWh = 3.6* 1E6 joules.

    """

    # Create a copy of the filtered DataFrame
    constraint_df = all_binding_constraints[all_binding_constraints['constraint'] == f'Constr {constraint}'].copy()

    # Extract components from 'sets' using .str.split
    constraint_df['fuel'] = constraint_df['sets'].str.split(',').str[2]
    constraint_df['year'] = constraint_df['sets'].str.split(',').str[3]
    constraint_df.sort_values(by='year')
    constraint_df['ts'] = constraint_df['sets'].str.split(',').str[1]

    # Use .loc to filter rows where 'technology' starts with 'ELC'
    constraint_df_ELC = constraint_df.loc[constraint_df['fuel'].str.startswith(fuel)]

    # Group by 'technology' and 'year', then calculate the mean of 'value'
    constraint_df_ELC_aggr = constraint_df_ELC.groupby(['fuel', 'year'], as_index=False)[datafield].median()
    
    # Conversion factor
    # conversion_factor=31.536/8760/1e6 # m$/PJ to $/kWh
    
    conversion_factor = 3.6E3 # 1 GWh= 3.6E-3 PJ
    constraint_df_ELC_aggr['$/kwh'] = constraint_df_ELC_aggr[datafield] * conversion_factor  # m$/PJ to $/MWh
    
    return constraint_df_ELC_aggr

def plot_shadow_price(constraint_df_ELC_aggr:pd.DataFrame,
                      constraint:str='EBa11_EnergyBalanceEachTS5',
                      fuel:str='ELCB02',
                      datafield:str='$/kwh',
                      save_to:Path='results/clews/shadow_price_ELCb02.png',
                      show:Optional[bool]=False):
        
    save_to = Path(save_to)
    save_to.parent.mkdir(parents=True, exist_ok=True)  # Ensure parent directories exist
    
    mask=constraint_df_ELC_aggr['fuel'] == fuel
    df_fuel = constraint_df_ELC_aggr[mask]
    
    # Convert 'year' to numeric type
    df_fuel['year'] = pd.to_numeric(df_fuel['year'])
    
    # Create the line chart
    plt.figure(figsize=(8, 6))
    plt.plot(df_fuel['year'], df_fuel[datafield], color='skyblue', label=fuel, linewidth=4)  # Use converted values
    plt.xlabel("Year")
    plt.ylabel("Shadow Price ($/kWh)")
    plt.grid(True, ls=":", color='grey', linewidth=.5)
    plt.title(f"Constraint: {constraint} for \n {fuel} : Electricity from transmission")
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Add a legend
    plt.legend()
    plt.savefig(save_to)
    # Show the plot
    if show:
        plt.show()
    else:
        pass


