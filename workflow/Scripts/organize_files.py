import os
import shutil

def collect_files(source_dir, destination_dir):
    # Create the destination directory if it doesn't exist
    os.makedirs(destination_dir, exist_ok=True)

    # Define the folder names where CSV files should be collected
    target_folders = ['Constraints - Activity', 'Demand', 'Performance', 'Sets/Sets- Not in use', 'Sets/CLEWsy_outputs', 'Variables',
                      'Constraints - Capacity', 'Emissions', 'RE Gen Target', 'Storage',
                      'Constraints - Investment', 'Global Parameters', 'Reserve Margin', 'Technology Cost']

    # Iterate over the target folders
    for folder_name in target_folders:
        folder_path = os.path.join(source_dir, folder_name)

        if os.path.isdir(folder_path):
            # Collect CSV files from the target folder
            collect_csv_files(folder_path, destination_dir)

def collect_csv_files(source_dir, destination_dir):
    # Iterate over the files in the source directory
    for item in os.listdir(source_dir):
        item_path = os.path.join(source_dir, item)

        if os.path.isfile(item_path) and item.lower().endswith(".csv"):
            # Rename the specific CSV file if the path matches
            if item_path == "user_inputs/Sets/CLEWsy_outputs/COMMODITY.csv":
                destination_file = os.path.join(destination_dir, "FUEL.csv")
                shutil.copy(item_path, destination_file)
            else:
                # Copy the CSV file to the destination directory
                shutil.copy(item_path, destination_dir)

# Define the source directory and destination directory
source_directory = "user_inputs"
destination_directory = "data"

# Collect CSV files from specific folders in the source directory and copy them to the destination directory
collect_files(source_directory, destination_directory)
