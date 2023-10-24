# How to run and visualize the workflow

<img src="https://github.com/DeltaE/BC-CLEWS-Model/blob/main/workflow/docs/BCNexus_workflow_dag.svg" width="30%" height="30%">

Snakemake has been used to design the workflow. It is popular open-source tool where workflows are described via a human readable, Python based language. Please check this [documentation on Snakemake](https://snakemake.readthedocs.io/en/stable/index.html)

###  !!! NOTE: This program runs on this program runs on Linux or Windows Subsystem for Linux (WSL).

## Step 1: Workspace setup
### 1.1 Initiate Linux/ WSL
>[Install WSL on Windows OS](https://learn.microsoft.com/en-us/windows/wsl/install)
### 1.2 Anaconda
[Install Anaconda on WSL/Linux](https://gist.github.com/kauffmanes/5e74916617f9993bc3479f401dfec7da)

## Step 2: Set-up snakemake

>### METHOD 1
clone this [repository](https://github.com/DeltaE/BC-CLEWS-Model/tree/main/workflow) and then run the following cmd in _WSL/Linux bash_
```
conda env create -f .\envs\snakemake_environment.yml
```
```
conda activate snakemake
```

* If you __already have snakemake__  please note that this workflow demands **minimum 6.0 version**. You can check the version of your snakemake with :
```
snakemake --version
```
>If needed please update snakemake version:
```
conda update -c bioconda snakemake
```

> ### METHOD 2 (alternate)
```
conda create -n snakemake python=3
```
```
conda activate snakemake
```
```
conda install -c bioconda -c conda-forge snakemake
```

## Step 3: Run the Workflow
### 3.1:
```
cd <your/workflow/clonned/directory>
```

> You can define the number of cores, or simply write "all" to utilize all available cores.
```
snakemake -c all
```

### 3.2:
```
snakemake -c 4 make_dag
```

* To remove the residual data and files*
```
snakemake -c 4 clean
```
> then type "y" in bash.

Optional File creation to get all the datafiles (.csv) inside same excel file by using otoole 
```
snakemake -c 4 datafile_to_Excel
```
> More Snakemake command line [here](https://snakemake.readthedocs.io/en/stable/executing/cli.html#visualization)

Now for better comprehension , please check the [DAG]((https://github.com/DeltaE/BC-CLEWS-Model/tree/main/workflow/docs), Rulegraph and Filegraph of the workflow to visualize the steps of the workflow.

> Filegraph of the workflow:

<img src="https://github.com/DeltaE/BC-CLEWS-Model/blob/main/workflow/docs/BCNexus_workflow_filegraph.svg" width="60%" height="auto">

<a rel="license" href="http://creativecommons.org/licenses/by/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by/4.0/88x31.png" /></a><br /><span xmlns:dct="http://purl.org/dc/terms/" href="http://purl.org/dc/dcmitype/Text" property="dct:title" rel="dct:type">BC-Nexus Model Workflow</span> by <a xmlns:cc="http://creativecommons.org/ns#" href="https://www.linkedin.com/in/eliasinul/" property="cc:attributionName" rel="cc:attributionURL">Md Eliasinul Islam</a> is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0 International License</a>.<br />Based on a work at <a xmlns:dct="http://purl.org/dc/terms/" href="https://github.com/DeltaE/BC-CLEWS-Model/tree/main/workflow" rel="dct:source">https://github.com/DeltaE/BC-CLEWS-Model/tree/main/workflow</a>.
