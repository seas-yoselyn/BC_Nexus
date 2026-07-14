**Step-by-Step guideline**  

This model file was originally named as [CLEWs model](https://github.com/OSeMOSYS/CLEWs); the code is written in GNU MathProg, a high-level mathematical programming language, yet straightforward enough to be understandable by all kinds of users, expert or not, in linear programming. There are four steps in running the model successfully:

**Workspace setup**

i. Initiate Linux/ WSL
[Install WSL on Windows OS](https://learn.microsoft.com/en-us/windows/wsl/install)

ii. Anaconda
[Steps to Install Anaconda on Windows Ubuntu Terminal](https://gist.github.com/kauffmanes/5e74916617f9993bc3479f401dfec7da)

Then follow the steps below:


* [__Step 1__](https://github.com/DeltaE/BC-CLEWS-Model/wiki/How-to-Run-the-Model/_edit#step-1-input-file): Prepare the input files based on the research questions and assumptions.
* [__Step 2__](https://github.com/DeltaE/BC-CLEWS-Model/wiki/How-to-Run-the-Model/_edit#step-2-model): Prepare the model script.
* [__Step 3__](https://github.com/DeltaE/BC-CLEWS-Model/wiki/How-to-Run-the-Model/_edit#step-2-model): Choose a solver.
* [__Step 4__](https://github.com/DeltaE/BC-CLEWS-Model/wiki/How-to-Run-the-Model/_edit#step-4-run-the-model):  Run the solver, feed the data and model script to solver.
* __Step 5__: Collect the results, and visualization.

![BC Nexus Workflow](https://github.com/DeltaE/BC-CLEWS-Model/blob/main/Graphical%20Resources/BC%20Nexus%20Workflow-Inouts2BCNexus.drawio.svg)
* __Model File__ : [model_BCNexus.txt](https://github.com/DeltaE/BC-CLEWS-Model/blob/main/model_BCNexus.txt) - located in the root folder of [BC-CLEWS-Model](https://github.com/DeltaE/BC-CLEWS-Model) repository.

These steps comprises two mode of run the model :
* [Osemosys Cloud](www.osemosys-cloud.com) Run (here [__Step 1__](https://github.com/DeltaE/BC-CLEWS-Model/wiki/How-to-Run-the-Model/_edit#step-1-input-file) + model file )
* Offline PC Run (follow all the steps)

### Create the SCENARIO folder
> Example: Clone this repository [data](https://github.com/DeltaE/BC-CLEWS-Model/tree/Datapackage_otoole/Data_otoole)

## Step 1: INPUT FILE
### Data preparation
> Find the subfolder 'data' from your cloned repository. Input Data CSV files from here. You should find **69 nos of Csv files** there.

![Input File Creating Workflow](https://github.com/DeltaE/BC-CLEWS-Model/blob/main/Graphical%20Resources/BC%20Nexus%20Input%20File%20Creation%20Workflow.svg)

> Land Clustering workflow [here](https://github.com/DeltaE/BC-CLEWS-Model/wiki/Land-System)  

## __Converting the CSV files to datafile__

The model code (.txt format) is written in GNU Mathprog, and the CSV data files are required to be formatted in a single data file (.txt) compatible with our model file. For that, we can use an [interfacing tool](http://www.osemosys.org/interfaces.html). For now, we are using [Otoole](https://otoole.readthedocs.io/en/latest/index.html) as the interfacing tool to process input data in the required format. But Otoole has **environment dependencies**, so the most time-saving solution is to use the CONDA environment to use Otoole. 

```
cd <directory of the SCENARIO folder> 
conda activate otoole
```

> We will use [otoole convert](https://otoole.readthedocs.io/en/latest/examples.html#otoole-convert) command. Check [examples](https://otoole.readthedocs.io/en/latest/examples.html) for a better idea. BC NEXUS Model's otoole configuration file "config_updated.yaml" [[download](https://github.com/DeltaE/BC-CLEWS-Model/tree/Datapackage_otoole/config_files)], model file "model_BCNexus.txt" [[download](https://github.com/DeltaE/BC-CLEWS-Model)]
```
otoole convert csv datafile data model_name.txt config_updated.yaml
```

If you completed the aforementioned steps correctly, you should get the **data.txt** file inside the <directory of the SCENARIO folder>. To learn more about the functionality of this syntax [Read this](https://otoole.readthedocs.io/en/latest/functionality.html#core-functionality).

This data file is good to run via [Osemosys-Cloud](www.osemosys-cloud.com). But it __needs to be processed further to run on your PC__. Inside the cloned repository, find the folder [***Scripts***](https://github.com/DeltaE/BC-CLEWS-Model/tree/main/workflow/Scripts) and the python script **"preprocess_data.py"** [[download](https://github.com/ClimateCompatibleGrowth/osemosys-cloud/tree/master/scripts)].

## Step 2: MODEL
### 2.1. Model Preparation
Our Model file [ [model_BCNexus.txt](https://github.com/DeltaE/BC-CLEWS-Model/blob/main/model_BCNexus.txt) - located in the root folder of [BC-CLEWS-Model](https://github.com/DeltaE/BC-CLEWS-Model repo)] needs a bit of processing with the script **preprocess_data.py**. 
>The script has four input arguments, i.e. input data file, Processed Input file name suggestion, model file, processed model  file name suggestion
>Open your CMD Terminal and write the following commands >>  
>> 'IP data file' = otoole generated .txt datafile.  
>> 'Processed data file name' = Write a name for your new datafile, this is one of your output files.  
>> 'processed model file name' = Write a name for your new model file, this is another output file.
	
```
cd <location of the model file>`  
python3 <directory of your SCENARIO folder> <IP data file> <Processed data file name> <model File name> <processed model file name>
```

> Now that we have the ready-to-run Input data file & the model file generated after step 3, we need a solver to generate the Linear Programming (LP) file and solve the problem to give an optimum solution.

## Step 3: SOLVER
We can solve our model with open-source solvers, e.g., GLP, CBC etc. or with commercial solvers, e.g., CPLEX or so on. Let's try the open-source solvers for now.
	
### 3.1. Install GLP solver 
Follow the instructions [here](http://www.osemosys.org/uploads/1/8/5/0/18504136/glpk_installation_guide_for_windows10_-_201702.pdf).

### 3.2. Create the Result folder & subfolders
As defined in our result processing script, our GLP solver shall create the results in CSV files inside certain defined directors. Hence, we need to create a folder and subfolders under the SCENARIO folder. A sub-folder named **“res”** and inside it another subfolder **‘csv’**.
	
> We are ready to RUN our model! 
	
## Step-4: Run the model 

### 4.1 With GLP solver
Run the Commands for Creating the Linear Programming (LP file) & solving the problem >>
>> 'model file name', 'data file name' are the outputs from step 2.1  
>> 'LP file name' = you have to suggest a name
	
```
glpsol -m <model file name> -d <data file name> --wlp <LP file name>
```
	
> We need the LP file to try on another solver. But you can drop the "--wlp <LP file name>" part if you don't have plans for using other solvers!

Now inside the SCENARIO folder, we got a Results sub-folder, “res” with all results files (CSV) inside the subfolder “csv”. You should get **21 nos. of CSV files.**

### 4.2 Alternate way of solving by using CBC solver
Install the __CBC solver__ ; instructions [here](https://calliope.readthedocs.io/en/stable/user/installation.html) **need to update this link
Open the Anaconda Powershell prompt, then enter the following commands >>

```
CD <directory of the model file>`  
conda activate <Your env>`  
cbc <LP file> solve -solu <Solution file name suggestion>
```

> The CBC solver shall give you a single solution file (.txt). If you need to generate csv files from this solution file, follow this <instruction resource>

## Step-5: Results & Visualization
Check [this](https://github.com/DeltaE/BC-CLEWS-Model/wiki/Results-&-Visualization)
