import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Custom Script for Utilities and Functions
import tools

print("\033[1m**** Generating Plots for LAND USE - for all Cases...\033[0m\n")


config_file = r"/home/eliasinul/Visualizations/BCNexus_Scenarios/configs/configs.yaml"
cfg =tools.load_config(config_file)

# Extract the SCENARIOS list from the config data
SCENARIOS = cfg["SCENARIOS"]



for scenario in SCENARIOS:
    # Set the output Directory path
    output_directory = os.path.join('scenario_files',scenario,cfg['output_directory'])

    # Input CSV files' Directory
    Nexus_results_directory = os.path.join('scenario_files',scenario,cfg['Nexus_results_directory'])

    # Input CSV for Plots
    filename = "TotalAnnualTechnologyActivityByMode.csv"

    file = os.path.join(Nexus_results_directory, filename)

    # Read the CSV file
    df_file = pd.read_csv(file)

    # List of selected technologies
    # selected_technologies = ['LNDAGRBC1C01', 'LNDAGRBC1C02', 'LNDAGRBC1C03', 'LNDAGRBC1C04', 'LNDAGRBC1C05', 'LNDAGRBC1C06', 'LNDAGRBC1C07']
    selected_technologies=cfg['landuse_technolgies']

    # Filter technologies that start with 'LND' and are in the selected list
    filtered_df = df_file[df_file['t'].str.startswith('LND') & df_file['t'].isin(selected_technologies)]

    # Filter for MODE value of 54
    filtered_df = filtered_df[filtered_df['m'] == 54]

    # Filter positive values
    positive_technologies = filtered_df[filtered_df['TotalAnnualTechnologyActivityByMode'] > 0]

    # Pivot the data to have years as columns
    pivot_table = positive_technologies.pivot_table(index='y', columns='t', values='m', fill_value=0)

    # Create a stacked bar plot for yearly data
    ax = pivot_table.plot(kind='bar', stacked=True, figsize=(10, 6))

    # Customize the plot
    plt.xlabel('Year')
    plt.ylabel('Thousand Sq. Km per PJ')
    plt.title('Landuse of BC')
    plt.xticks(rotation=45, ha='right')

    # Custom colors and legend labels
    custom_colors=cfg['custom_colors_landuse']
    legend_labels=cfg['legend_labels_landuse']

    # Add legend
    handles = [plt.Rectangle((0, 0), 1, 1, color=custom_colors[tech]) for tech in selected_technologies]
    # Move the legend to the right side of the plot
    plt.legend(handles, [legend_labels[tech] for tech in selected_technologies], loc='center left', bbox_to_anchor=(1, 0.5), ncol=1)

    # Calculate the sum of values in 2050
    total_land_use_2050 = pivot_table.loc[2050].sum()
    plt.grid(True)

    # Add total value text above the legend
    plt.text(1.02, 0.8, f'Total Land use in 2050 = {total_land_use_2050:.2f} Th. sq. km', transform=ax.transAxes,
            va='center', ha='left', fontsize=10, color='black', bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.4'))

    # Save the plot as an SVG file in the specified directory
    image_filename = f'{output_directory}/{filename}_{scenario}.png'
    plt.savefig(image_filename, format='png', bbox_inches='tight')

    print(f"Plot created and saved for ------->> {scenario} Scenario")

print(f"\nLanduse Plot generated successfully\n")
