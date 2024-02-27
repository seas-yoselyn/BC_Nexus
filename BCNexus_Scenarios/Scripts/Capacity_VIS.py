import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Custom Script for Utilities and Functions
from tools import load_config

print("\033[1m**** Generating Plots for New and Total Installed Capacity - for all Cases...\033[0m\n")

config_file = r"/home/eliasinul/Visualizations/BCNexus_Scenarios/configs/configs.yaml"
cfg =load_config(config_file)

# Extract the SCENARIOS list from the config data
SCENARIOS = cfg["SCENARIOS"]

for scenario in SCENARIOS:
    # Set the output Directory path
    output_directory = os.path.join('scenario_files',scenario,cfg['output_directory'])

    # Input CSV files' Directory
    Nexus_results_directory = os.path.join('scenario_files',scenario,cfg['Nexus_results_directory'])


    # Input CSV for Plots
    filenames= ["NewCapacity.csv","TotalCapacityAnnual.csv"]
    filenames_mapping={
        'NewCapacity.csv':'NewCapacity',
        'TotalCapacityAnnual.csv':'TotalCapacityAnnual'
    }

    # Create the directory if it doesn't exist
    os.makedirs(output_directory, exist_ok=True)

    # Define the Lists
    technologies=cfg['technologies']
    #  Legend label dictionary
    legend_label_technologies=cfg['legend_label_technologies']
    #  Legend Color dictionary
    custom_color_technologies = cfg['custom_color_technologies']

    for filename in filenames:
        file= os.path.join(Nexus_results_directory, filename)
        df_file = pd.read_csv(file)

        # Create an empty dictionary for yearly summed values
        yearly_summed_values = {tech: [] for tech in technologies}

        # Calculate the yearly summed values for each technology
        all_years = sorted(set(df_file['y']))
        for tech in technologies:
            filtered_df = df_file[df_file['t'].str.startswith(tech)]
            grouped = filtered_df.groupby('y')[filenames_mapping[filename]].sum()
            yearly_summed_values[tech] = [grouped.get(year, 0) for year in all_years]

        # Generate a stacked bar chart
        x = np.array(all_years)
        bottom = np.zeros(len(x))

        for i, tech in enumerate(technologies):
            yearly_sum = yearly_summed_values[tech]
            if np.any(yearly_sum):
                plt.bar(x, yearly_sum, label=legend_label_technologies[tech], bottom=bottom, color=custom_color_technologies[tech])
                bottom += yearly_sum

        # Customize the plot
        plt.xlabel('Year')
        plt.ylabel('Gigawatts (GW)')
        plt.title(f'{filenames_mapping[filename]}')
        plt.grid(True)

        # Move the legend to the right side of the plot
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), ncol=1)
        
        # Adjust y-axis limits for extra space after the last value
        ylim_max = max(max(bottom), max(yearly_sum))  # Get the maximum value on the y-axis
        plt.ylim(0, ylim_max * 1.1)  # Add 10% extra space after the last value
        
        # Save the plot as an SVG file in the specified directory
        image_filename = f'{output_directory}/{filenames_mapping[filename]}_{scenario}.png'
        plt.savefig(image_filename, format='png', bbox_inches='tight')

    print(f"Plot created and saved for ------->> {scenario} Scenario")

print(f"\nCapacity Plots generated successfully\n")
