# Creating the Datafiles

Adapted from clewsy-[Readme](https://github.com/OSeMOSYS/clewsy/blob/main/README.rst)  

## CLEWsy ##
A set of tools for building CLEWs models,it is a Python package which provides a command-line interface for building CLEWs models using OSeMOSYS.

## Input Requirements ##
* Configuration file [[Structure explanation](https://github.com/DeltaE/BC-CLEWS-Model/tree/main/Create%20the%20Input%20Datafiles) , [download](https://github.com/DeltaE/BC-CLEWS-Model/blob/main/Create%20the%20Input%20Datafiles/ReadMe_CofigurationFileForCLEWsy.md)]
* Clustering data files [[download](https://github.com/DeltaE/BC-CLEWS-Model/tree/main/Create%20the%20Input%20Datafiles)]

## Dependencies ##
CLEWsy requires a number of dependencies, but these should be installed automatically when installing clewsy.

## Installation ##
Install clewsy using pip:

**`pip install clewsy`**

To upgrade clewsy using pip:

**`pip install clewsy --upgrade`**

## Usage ##
For instructions of the use of the tool, run the command line

**`clewsy --help`**

![Sets creation workflow](https://github.com/DeltaE/BC-CLEWS-Model/blob/main/Graphical%20Resources/CLEWsy%20workflow.svg)

## Step-by-step example ##
1. Lets create a Folder "*CLEWsy*"

2. Clone the "[clusterDataSet](https://github.com/DeltaE/BC-CLEWS-Model/tree/main/Create%20the%20Input%20Datafiles/ClusterDataSet)" folder and paste it inside your "*CLEWsy*" folder

3. Download the yaml file from [here](https://github.com/DeltaE/BC-CLEWS-Model/blob/main/Create%20the%20Input%20Datafiles/2023%2003%2002%20BC%20Nexus_CLEWsy.yaml)
>* **Line-16** of the yaml file denotes the output directory name, which will be created after the script run.
>>otooleOutputDirectory: CLEWsy_outputs
>* **Line-71** denotes the directory of the land clustering data sources, which we did in step 2 here.
>>DataDirectoryName: "./ClusterDataSet"

4. Change the directory to "CLEWsy" folder  
**`cd <path to CLEWsy folder>`**  

5. Run the clewsy tool cmd :  
**`clewsy build <yaml File Path>`**

>It will create a folder  "CLEWsy_outputs" which contains all the set. The folder will be created on the directory in which the command is being executed i.e. here inside '*CLEWsy*' folder.
