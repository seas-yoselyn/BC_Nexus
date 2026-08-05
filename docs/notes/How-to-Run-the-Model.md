This setup is a __lightweight__ and __standalone__ installation of the packages required to run BCNexus model only. All of the required primary data is already given temporarily in this repo to make the modelling results repeatable. 
> __The data will be removed during public release.__

---

<img src="https://github.com/DeltaE/BC_Nexus/blob/main/docs/BCNexus_2025.png" width="90%"> 

---

## Instructions to Set-up Modelling

### __1__ : This installation setup assumes you have the following Softwares are already installed in your machine:

> - Linux/ WSL (if on windows machine) ,[Install WSL on Windows OS](https://learn.microsoft.com/en-us/windows/wsl/install) 
> - Anaconda (on your WSL/Linux), [Steps to Install Anaconda on Windows Ubuntu Terminal](https://gist.github.com/kauffmanes/5e74916617f9993bc3479f401dfec7da)

clone the repo:
`git clone https://github.com/DeltaE/BC_Nexus`

change the directory to cloned repository
`cd BC_Nexus`

### __2__ : Create the conda environment 

`conda env create --file env/environment.yaml`
> this will create an environment named `bcnexus`

activate the environment : 
 
`conda activate bcnexus`

### __3__ : install the local package _bcnexus_:

`bash install_bcnexus.sh`

**or** run the following bash cmd from root

`pip install .`

### __4__ : All of the required data is temporarily uploaded at [data](https://github.com/DeltaE/BC_Nexus/tree/main/data)
> We will replace this with combined model data-pipeline workflow. This is one time task for data collection. Not required to be applied frequently.

### __5__ : Test the sample results and dashboard connection:

`bash dashboard.sh`
----

<img src="https://github.com/DeltaE/BC_Nexus/blob/main/docs/Graphical%20Resources/DASH_DEMO.gif" width="auto"> 

---
- How to get out of the dash render from terminal?

: press `ctrl+z` or `ctrl+c`

# How should I start ?

## 3 simple steps:
### __A__. Find the script that runs the model [BCNexus.py](https://github.com/DeltaE/BC_Nexus/blob/main/BCNexus.py) @ repository root.
 > What does this script do ?
 >> In the BCNexus workflow illustration above, follow the 2nd block of the workflow i.e. starting from _Update scenario data from config.yaml_ block.

### __B__. Try different configurations.
- __temporal clustering__ (timeslices) via the script __BCNexus.py__ 
- __scenario__ configs via __config.yaml__

__What, where and how to change ?__
> Can modify the __scenario__ and __temporal clsutering__ via `args` of  [BCNexus.py](https://github.com/DeltaE/BC_Nexus/blob/main/BCNexus.py). 
> example configuration in script: 
> > ```python
>  > args={
>  >     'storage_algorithm': 'Kotzur', # Lets do all the run with Kotzur for now.
>  >     'scenario':'Base',
>  >     'clustering_attributes': {
>  >         'hour_grouping': 4,
>  >         'n_clusters': 5
>  >         }
>  > ```
>  > > The temporal arguments provides 30 timeslices  ( 24 hrs / 4 hours in a group * 5 clusters)

> The `scenario` name you defined above should be harmonized with the scenario configuration at __config.yaml__. A template and some sample scenarios are given at scenario [config](https://github.com/DeltaE/BC_Nexus/blob/611ab95fc48bb9d0c5df9b4796d93d00666c2acc/config/config.yaml#L12C4-L22C63).

__What are these arguments for _.run()_ method ?__

> Here is an instance of run using a __32 core machine__.
> > ```python
> > clewsRun.run(update_temporal_profiles=True,
> >              solver_name='gurobi',
> >              threads=32)
> > ```
> > > The thread depends on the hardware limitations of your machine. If you have 4 core CPU, use Thread <=4. 
> >  > > For Linux/WSL use this __bash cmd__ to check your machine's number of cores: `nproc`

#### __How to run the script?__
> Can run the script from bash with `python BCNexus.py` 

__or__

> open the file and run in interactive window to get jupyter notebook features (e.g. analysing interim data, object attributes, applying several methods to extract interim data etc.)

### __C__. __Check results__ 
__How to check results and visuals__?

from dash run cmd 
`bash dashboard.sh`
>__When you run this bash cmd, a pop-up will likely appear to you for selection of the dashboard rendering. You can select "open-on browser"__
> - The plots are dynamically produced from the data residing at [results/clews/Model_Kotzur_Base](https://github.com/DeltaE/BC_Nexus/tree/main/results/clews/Model_Kotzur_Base)
>> the timeslice data folder it will access is hardcoded [here](https://github.com/DeltaE/BC_Nexus/blob/75cd2b4614861d9a8df323ac05cf23c2f850229c/bcnexus/vis/dashboard/app.py#L27). Consider modifying this if want to showcase different ts results. Make Sure this data exists to expect plots.
> - __When you run this bash cmd, a pop-up will likely appear to you for selection of the dashboard rendering. You can select "open-on browser"__
---
# Known Issues and how to resolve 🔢 

- ### Solvers doesn't install properly and/or installed version and licensed version conflict
> Check about the version for which you acquired license, you might have to install a specific version to harmonize license and version e.g. if you have v12.0 license then :
> > ```
> > conda install -c gurobi gurobi==12.0
> > ```

- ### Gurobi License doesn't work after restarting PC/WSL terminal
> This is a reported issue with WSL setup only. The temporary fix is you have request a license every time you restart the terminal. After the license retrieval in your gurobi web-profile, copy your license key and use bash cmd from repository root:
> `grbgetkey <your license key>`
> >  replace  <your license key> with the key obtained. 

- ### I just can't set-up gurobi as I don't have academic email id to get the free license.
> We have free solver cbc setup to solve the model. The setup can be done via `args` of  [BCNexus.py](https://github.com/DeltaE/BC_Nexus/blob/main/BCNexus.py).
> > ```python
> > clewsRun.run(update_temporal_profiles=True,
> >              solver_name='cbc',
> >              threads=32)
> > ```

- ### Environment can't be set-up properly.
> The solution is case by case basis resolve based on the machine related issues. 