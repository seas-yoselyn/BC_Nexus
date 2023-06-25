import os
from pathlib import Path



#inside the YAML file >>>>>> otooleOutputDirectory: "./user_inputs/Sets/clewsy_output"


# rule all:
#     input:
#         SETS_file='Filelist/SETS_Files.txt',
#         clewsy_SET_files = os.listdir('./user_inputs/Sets/clewsy_output'),
#     output:
#         "unser_inputs/Sets/Status.txt"
#     run:
#         csv_files = os.listdir(directory(config['otooleOutputDirectory']))

configfile:'config_files/20221207_BC_CLEWS_Elias.yaml'
rule DATA_preparation:
    message:
        'Collecting the data files...'
    input:
        Input_files = 'user_inputs',
        CLEW_Config_file = 'config_files/20221207_BC_CLEWS_Elias.yaml'
    # params:
    #     output_directory=config['otooleOutputDirectory']
    output:
        directory(config['otooleOutputDirectory']),
        
    shell:
        '''
        # cd user_inputs/Sets
        clewsy build {input.CLEW_Config_file}
        [ -d {output} ]  && echo "BC NEXUS - SETS' files Created Successfully." || echo "Model Shell Creation failed !!!"
        # clewsy_SET_files = os.listdir('./user_inputs/Sets/clewsy_output')
        '''


rule clean:
    message:
        'Resetting to defaults and cleaning existing data...'
    params:
        directory(config['otooleOutputDirectory'])
    shell:
        '''
        if [ -d {params} ]; then
            rm -rf {params}
            echo "Resetting to defaults and cleaning existing data completed !"
        fi
        '''
