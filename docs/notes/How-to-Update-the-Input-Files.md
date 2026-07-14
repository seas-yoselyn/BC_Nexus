# Guideline to Update the Datafile: 
 
The workflow recognizes the "__datapackage__" directory as the raw data files for the workflow. But the Model run recognizes the "__workflow/data__" as the input data source.  The "__workflow/data__" directory will be updated with the files from  "__datapackage__" if you run the workflow. If you update the "__workflow/data__" files instead of "__datapackage__" , you file might be replaced by the data inside "__datapackage__" directory. Therefore, it is recommended to update the intended data with the .csv files inside "__datapackage__" directory only. 

Find the the following directory inside __BC-CLEWS-MODEL__ root:

 ```
 datapackage
  |__Params
  |__SETS
    |__ CLEWsy_outputs
    |__ ClusterDataSet
    |__ Sets-Not in use
  |__REF_datapackage_template
```
* `Params`: Includes the standard Parameters for the Model. __Currently you have to manually update these Parameters data fields. _Data pipeline and parameter update automation work in progress..._
* `SETS`:
  * `CLEWsy_outputs`: The SETS are being generated via [__clewsy v0.2.2__](https://pypi.org/project/clewsy/) tool. It generates the all SETS and InputActivityRatio.csv, OutputActivityRatio.csv files as defined by the Model Configuration file @ _config_/_BCNexus_CLEWsy.yaml_.
  * `ClusterDataSet`: Includes the land clusters related data and visuals. This dataset is not directly used inside the model but includes crucial base data that has been used in the land-use parameters of the model. 
  * `Sets- Not in use`: Sets that are currently not being used in the existing model. Planned work in progress...
* `REF_datapackage_template` : Backup files for all the sets and parameters (with sample values) required to run the Model. Saved it to restart a datafile (csv) in-case any datafile has been irreversibly manipulated to a non-functional stage.

## Workflow Rule:
The data-preparation rule will automatically recognize the changes you make and update the required directories prior to the model run. However, you can run specific rules of the workflow if you want to update the data now and run the model later. Run the following commands from __BC-CLEWS-MODEL__ root directory:

> Here <all> denotes the instruction to use all available cores in a CPU. If you want to use specific number of cores to test your model run hardware dependencies then you can use specific integer numbers instead of "all" in these following commands:

```console
snakemake -c all Model_Shell
```
> it generates the SETS and activity ratios .csv files.

```console
snakemake -c all prepare_input_data_CSV_files
```
> it collects the SETS, activity ratios and other parameter files and dumps to a single directory "workflow/data" that is recognized by the model as input dataset.

* You can also check you Reference Energy System (RES) diagram to cross check you intended system and links to technologies and fuels : 
```console
snakemake -c all make_RES
```
