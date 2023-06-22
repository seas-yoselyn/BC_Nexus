import os

# # Get the current working directory
# current_directory = os.getcwd()



# Specify the directories
results_directory = './res/csv/'
input_directory = './data'
SETS_directory='./user_inputs/Sets/clewsy_output'
datapackage_list='./user_inputs'

# Get the list of file names in the results directory
results_file_names = os.listdir(results_directory)

# Get the list of file names in the input directory
input_file_names = os.listdir(input_directory)


# Get the list of file names in the SETS directory
SETS_file_names = os.listdir(SETS_directory)


# Get the list of file names in the SETS directory
datapackage_folder_names = os.listdir(datapackage_list)

# Change the directory
new_directory = "./FileList"
os.chdir(new_directory)


# Specify the output file paths
results_output_file = 'Result_Files.txt'
input_output_file = 'Input_Files.txt'
SETS_output_file = 'SETS_Files.txt'
datapackage_list_output_file='datapackage_folders.txt'

# Open the results output file in write mode
with open(results_output_file, 'w') as f:
    # Write each result file name to the file
    for file_name in results_file_names:
        f.write(file_name + '\n')

# Open the input file in write mode
with open(input_output_file, 'w') as f:
    # Write each input file name to the file
    for file_name in input_file_names:
        f.write(file_name + '\n')

# Open the SETS file in write mode
with open(SETS_output_file, 'w') as f:
    # Write each input file name to the file
    for file_name in SETS_file_names:
        f.write(file_name + '\n')


# Open the files list output file in write mode
with open(datapackage_list_output_file, 'w') as f:
    # Write each input file name to the file
    for file_name in datapackage_list_output_file:
        f.write(file_name + '\n')
        
print("File names have been saved to", results_output_file, "and", input_output_file,"and", SETS_output_file, "and", datapackage_list_output_file)
