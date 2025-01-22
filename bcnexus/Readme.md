# modules of _bcnexus_ package 
A brief description is given below:

## Attributes Parser
If you need to redefine the directories and include any new attributes via config. It is recommended to update the [Attributes Parser](https://github.com/DeltaE/BC_Nexus/blob/main/bcnexus/attributes_parser.py), to keep the attributes setup centralized, harmonized and flexible.

## clews
Contains all the modules to update,build and run bcnexus model.
- __builder__: updates parameters' data
- __datapackage__: simplified validation and reading sets/params.
- __model_structure__: replaced the legacy 'BCNexus_config.yaml' with a python script. It contains dictionary of the structural components of BCNexus. Required modification if new SETs and connections to be build.
- preprocess_data_<storage_algorithm_name>__: preprocessing script of data to handle sparse matrix parsing. 
   > [know that why this script is required](https://github.com/OSeMOSYS/osemosys-cloud/blob/bfa7f68a758a5558d384559805e6724c949b2c12/scripts/preprocess_data.py#L3C1-L29C90)
   > why do we have different scripts for storage alrogithms?
   > > storage algorithm requires some customized temporal paramters which are exclusive to these model codes. To keep them simple, we kept them as separate scripts. To be integrated in future to handle alrogithm params via single script.
- __runner__: The model run module to run any model from csvs/datafile. It's a standalone module. Has dependency on other modules only if the methods of _builder_ module (e.g. temporal clustering, parameter, sets upgrades) is used.
- __schema__: The module to handle technology aggregation and dynamically updating the SETs and Parameters associated to TECHNOLOGIES. It handles and dynamically updates the  [clews_builder.yaml](https://github.com/DeltaE/BC_Nexus/blob/main/config/clews_builder.yaml) file. Has dependency on _builder_ module.
 > Currently supports power, carbon capture, storage and hydro inflow technologies. 
- __sets_n_ratios__: replaced the legacy `clewsy` tool with this tailored version. The core methods are adopted from clewsy's scripts.
-__update_global_params__: Handles updating the global params for Technologies.
> work in progress.
- __update_yearly_params__: Handles the yearly parameter updates to harmonize _schema_ changes.
  > contains bugs that deletes and resets some unintended paramters. work in progress.

## Vis
Contains modules to support visuals and dashboard.

## cli

< work in progress >

---

🧢 __For more info and controbution, please connect with the developer : [Elias Islam](https://github.com/eliasinul)__
