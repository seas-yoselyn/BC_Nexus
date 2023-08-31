import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


# Custom Script for Utilities and Functions
import tools

config_file = r"/home/eliasinul/Visualizations/BCNexus_Scenarios/configs/configs.yaml"
cfg =tools.load_config(config_file)

# Set the output Directory path
output_directory = cfg['output_directory']

# Input CSV files' Directory
Nexus_results_directory = cfg['Nexus_results_directory']

# Input CSV for Plots
filenames= ["TotalTechnologyAnnualActivity.csv"]
filenames_mapping={
    'TotalTechnologyAnnualActivity.csv':'TotalTechnologyAnnualActivity',
}

# Create the directory if it doesn't exist
os.makedirs(output_directory, exist_ok=True)

# Define the Lists
technologies=cfg['technologies']
sectors=cfg['sectors']
consumption_fuels=cfg['consumption_fuels']

#  Legend label dictionary
legend_label_technologies=cfg['legend_label_technologies']
legend_label_sectors=cfg['legend_label_sectors']
legend_label_fuels=cfg['legend_label_fuels']

#  Legend Color dictionary
custom_color_technologies = cfg['custom_color_technologies']
custom_color_sectors=cfg['custom_color_sectors']
custom_color_fuels=cfg['custom_color_fuels']

for filename in filenames:
    file= os.path.join(Nexus_results_directory, filename)
    df_file = pd.read_csv(file)
    all_years = sorted(set(df_file['y']))
   
    ######## Energy Generation by Technologies ################################################################################################################

    # Create an empty dictionary for yearly summed values
    yearly_summed_values = {tech: [] for tech in technologies}

    # Calculate the yearly summed values for each technology

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
    plt.ylabel('Energy (PJ)')

    # Extract the file name without extension
    plt.title(f'Energy Generation-by Fuel')
    plt.grid(True)

    # Move the legend to the right side of the plot
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), ncol=1)

    # Adjust y-axis limits for extra space after the last value
    ylim_max = max(max(bottom), max(yearly_sum))  # Get the maximum value on the y-axis
    plt.ylim(0, ylim_max * 1.1)  # Add 10% extra space after the last value


    # Save the plot as a PNG file in the specified directory
    plt.savefig(f'{output_directory}/Energy Generation-by Fuel.png', bbox_inches='tight')
    
    
    # Create a new plot to avoid overlapping with previous plot
    plt.figure()

    ######## Energy Consumption by Sectors ################################################################################################################################
    
    # Create an empty dictionary for yearly summed values
    yearly_summed_values = {sector: [] for sector in sectors}

    for sector in sectors:
        filtered_df = df_file[df_file['t'].str.startswith(sector)]
        grouped = filtered_df.groupby('y')[filenames_mapping[filename]].sum()
        yearly_summed_values[sector] = [grouped.get(year, 0) for year in all_years]

    # Generate a stacked bar chart
    x = np.array(all_years)
    bottom = np.zeros(len(x))
    
    
    for s, sector in enumerate(sectors):
            yearly_sum = yearly_summed_values[sector]
            if np.any(yearly_sum):
                plt.bar(x, yearly_sum, label=legend_label_sectors[sector], bottom=bottom, color=custom_color_sectors[sector])
                bottom += yearly_sum

    # Customize the plot
    plt.xlabel('Year')
    plt.ylabel('Energy (PJ)')

    # Extract the file name without extension
    plt.title(f'Energy Consumption (PJ) - by Sector')
    plt.grid(True)

    # Move the legend to the right side of the plot
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), ncol=1)

    # Adjust y-axis limits for extra space after the last value
    ylim_max = max(max(bottom), max(yearly_sum))  # Get the maximum value on the y-axis
    plt.ylim(0, ylim_max * 1.1)  # Add 10% extra space after the last value

    # # Show the plot
    # plt.show()

    # Save the plot as a PNG file in the specified directory
    plt.savefig(f'{output_directory}/Energy Consumption (PJ) - by Sector.png', bbox_inches='tight')

    # Create a new plot to avoid overlapping with previous plot
    plt.figure()


######## Energy Consumption by consumption_fuels ################################################################################################################################
filenames2= ["UseByTechnologyAnnual.csv"]
filenames_mapping2={
    'UseByTechnologyAnnual.csv':'UseByTechnologyAnnual'
}
for filename in filenames2:
    file= os.path.join(Nexus_results_directory, filename)
    df_file = pd.read_csv(file)
    all_years = sorted(set(df_file['y']))    
    # Create an empty dictionary for yearly summed values
    yearly_summed_values = {fuel: [] for fuel in consumption_fuels}

    for fuel in consumption_fuels:
        filtered_df = df_file[df_file['f'].str.startswith(fuel)]
        grouped = filtered_df.groupby('y')[filenames_mapping2[filename]].sum()
        yearly_summed_values[fuel] = [grouped.get(year, 0) for year in all_years]

    # Generate a stacked bar chart
    x = np.array(all_years)
    bottom = np.zeros(len(x))


    for f, fuel in enumerate(consumption_fuels):
            yearly_sum = yearly_summed_values[fuel]
            if np.any(yearly_sum):
                plt.bar(x, yearly_sum, label=legend_label_fuels[fuel], bottom=bottom, color=custom_color_fuels[fuel])
                bottom += yearly_sum

    # Customize the plot
    plt.xlabel('Year')
    plt.ylabel('Energy (PJ)')

    # Extract the file name without extension
    plt.title(f'Energy Consumption (PJ) - by fuel')
    plt.grid(True)

    # Move the legend to the right side of the plot
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), ncol=1)

    # Adjust y-axis limits for extra space after the last value
    ylim_max = max(max(bottom), max(yearly_sum))  # Get the maximum value on the y-axis
    plt.ylim(0, ylim_max * 1.1)  # Add 10% extra space after the last value

    # # Show the plot
    # plt.show()

    # Save the plot as a PNG file in the specified directory
    plt.savefig(f'{output_directory}/Energy Consumption (PJ) - by fuel.png', bbox_inches='tight')


print(f"Energy Plots generated successfully and saved to output directory: {output_directory}")
