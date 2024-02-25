import os
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.offline import plot

# Set the output Directory path
output_directory = os.path.join(os.getcwd(), "docs/Results_plots")

# Input CSV files' Directory
directory_path = os.path.join(os.getcwd(), "results")
# directory_path='/home/eliasinul/repositories/CLEWs_Kenya/workflow/results'

filenames = ["TotalTechnologyAnnualActivity.csv"]
filenames_mapping = {
    'TotalTechnologyAnnualActivity.csv': 'Generation'
}

# Create the directory if it doesn't exist
os.makedirs(output_directory, exist_ok=True)

# Define the technologies and colors
technologies = ['PWRBIO', 'PWRHYD', 'PWRNGS', 'PWRSOL', 'PWRWND', 'PWRGEO', 'PWRURN']
custom_colors = {
    'PWRWND': '#DDB3F9',
    'PWRNGS': '#D27A78',
    'PWRBIO': '#5BAB59',
    'PWRHYD': '#86B4D8',
    'PWRSOL': '#FEE566',
    'PWRGEO': '#B067B3',
    'PWRURN': 'gray'
}

# Legend label dictionary
legend_labels = {
    'PWRWND': 'Wind',
    'PWRNGS': 'Natural Gas',
    'PWRBIO': 'Biomass/Biofuel',
    'PWRHYD': 'Hydro',
    'PWRSOL': 'Solar',
    'PWRGEO': 'Geothermal',
    'PWRURN': 'Nuclear'
}

for filename in filenames:
    file = os.path.join(directory_path, filename)
    df_file = pd.read_csv(file)

    # Create an empty dictionary for yearly summed values
    yearly_summed_values = {tech: [] for tech in technologies}

    # Calculate the yearly summed values for each technology
    all_years = sorted(set(df_file['YEAR']))
    for tech in technologies:
        filtered_df = df_file[df_file['TECHNOLOGY'].str.startswith(tech)]
        grouped = filtered_df.groupby('YEAR')['VALUE'].sum()
        yearly_summed_values[tech] = [grouped.get(year, 0) for year in all_years]

    # Create a list to hold traces for the stacked bar chart
    traces = []

    # Generate traces for each technology
    for tech in technologies:
        trace = go.Bar(
            x=all_years,
            y=yearly_summed_values[tech],
            name=legend_labels[tech],
            marker=dict(color=custom_colors[tech])
        )
        traces.append(trace)

    # Create the layout
    layout = go.Layout(
        title=f'Yearly {filenames_mapping[filename]} for Different Technologies - REF Case',
        xaxis=dict(title='Year'),
        yaxis=dict(title='Generation (PJ)'),
        barmode='stack',
        legend=dict(x=1, y=0.5),
        plot_bgcolor='rgba(0, 0, 0, 0)'
    )

    # Create the figure
    fig = go.Figure(data=traces, layout=layout)

    # Save the plot as an HTML file in the specified directory
    html_filename = f'{output_directory}/{filenames_mapping[filename]}.html'
    fig.write_html(html_filename, include_plotlyjs='cdn')

print(f"Energy Plot generated successfully and saved as HTML files to the output directory: {output_directory}")
