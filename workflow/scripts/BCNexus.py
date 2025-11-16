# %%
from bcnexus.clews.runner import RunModel

# %%
scenarios = [
    # 'Base_CNZ',
    'Base_CNZ_noCCS',
    # 'CNZ_LIMITED_CO2_PTY'
    # 'CNZ_LIMITED_CO2',
    # 'NUC_standard_2028',
    # 'NUC_standard_2028_2xCost',
    # 'NUC_standard_2030',
    # 'NUC_standard_2030_2xCost',
    # 'NUC_standard_2035',
    # 'NUC_standard_2035_2xCost',
    # 'NUC_standard_2035_4xCost',
    # 'IMP_USA_100'
    # 'HYDROGEN', # contains bugs
]


# %%
def run_model(scenario: str):
    # 1(A) Define the Arguments
    args = {
        'storage_algorithm': 'Kotzur',  # Lets do all the run with Kotzur for now.
        'scenario': scenario,
        'clustering_attributes': {  # (24 hrs in a day / 6 hour group) * 4 clusters = 16 timeslices
            'hour_grouping': 4,
            'n_clusters': 4
        }
    }

    # 1(B) Load the instance of `RunModel` object
    clewsRun = RunModel(**args)

    # 1(C) Apply the .run() method
    clewsRun.run(
        build=False,  # Should be true for the very first run
        include_livestock=False,
        solver_name='gurobi',
        threads=32 ,# The thread depends on the hardware limitations of your machine. If you have 4 core CPU, use Thread <=4
        machine_id='srye-deltae-07' # for hardware tracking
    )

# %%
for scenario in scenarios:
    run_model(scenario)
