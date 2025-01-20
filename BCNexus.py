# 1 Load Clews runner Module
    # From `clews.runner` module, load the `RunModel` Object as `clewsRun` instance
from bcnexus.clews.runner import RunModel

# 1(A) Define the Arguments
args={
    'storage_algorithm': 'Kotzur', # Lets do all the run with Kotzur for now.
    'scenario':'LIMITED_CO2_PLTY',
    'clustering_attributes': {
        'hour_grouping': 4,
        'n_clusters': 5
        }
    }

# 1(B) Load the instance of `RunModel` object
clewsRun = RunModel(**args)

# 1(C) Apply the .run() method
clewsRun.run(update_temporal_profiles=True,
             solver_name='gurobi',
             threads=32) # The thread depends on the hardware limitations of your machine. If you have 4 core CPU, use Thread <=4 )

# Result extraction is included in .run() method.