import os

# Specify the directories
results_directory = './res/csv/'
input_directory = './data'

# Get the list of file names in the results directory
results_file_names = os.listdir(results_directory)

# Get the list of file names in the input directory
input_file_names = os.listdir(input_directory)

# Specify the output file paths
results_output_file = 'Result_Files.txt'
input_output_file = 'Input_Files.txt'

# Open the results output file in write mode
with open(results_output_file, 'w') as f:
    # Write each result file name to the file
    for file_name in results_file_names:
        f.write(file_name + '\n')

# Open the input output file in write mode
with open(input_output_file, 'w') as f:
    # Write each input file name to the file
    for file_name in input_file_names:
        f.write(file_name + '\n')

print("File names have been saved to", results_output_file, "and", input_output_file)
