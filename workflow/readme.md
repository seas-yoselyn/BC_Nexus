# How to run the workflow

## Set-up snakemake in your local machine:
You can try any of the following method
### METHOD 1
clone this [repository](https://github.com/DeltaE/BC-CLEWS-Model/tree/main/workflow) and then run the following cmd in WSL bash
```
conda env create -f .\envs\snakemake_environment.yml
```
```
conda activate snakemake
```
### METHOD 2
```
conda create -n snakemake python=3
```
```
conda activate snakemake
```
```
conda install -c bioconda -c conda-forge snakemake
```
You can check the version of your snakemake with this :
```
snakemake --version
```

## Run the Workflow
### Step 1:
```
cd <your/workflow/clonned/directory>
```

You can define the number of cores, or simply write "all" to utilize all available cores.
```
snakemake --cores all
```
### Step 2:
```
snakemake --cores 4 make_dag
```

*To remove the residual data and files*
```
snakemake --cores 4 clean
```
then type "y" in bash.

Optional File creation to get all the datafiles (.csv) inside same excel file by using otoole 
```
snakemake --cores 4 datafile_to_Excel
```
