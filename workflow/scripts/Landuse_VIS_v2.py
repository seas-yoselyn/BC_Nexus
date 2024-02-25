import os
import pandas as pd
import numpy as np
import plotly.graph_objs as go

# Set the output Directory path
output_directory = os.path.join(os.getcwd(), "docs/Results_plots")

# Input CSV files' Directory
directory_path = os.path.join(os.getcwd(), "results")
filename = "TotalAnnualTechnologyActivityByMode.csv"
file = os.path.join(directory_path, filename)

# Read the CSV file
df_file = pd.read_csv(file)

# List of selected technologies
selected_technologies = ['LNDAGRBC1C01', 'LNDAGRBC1C02', 'LNDAGRBC1C03', 'LNDAGRBC1C04', 'LNDAGRBC1C05', 'LNDAGRBC1C06', 'LNDAGRBC1C07']

# Filter technologies that start with 'LND' and are in the selected list
filtered_df = df_file[df_file['TECHNOLOGY'].str.startswith('LND') & df_file['TECHNOLOGY'].isin(selected_technologies)]

# Filter for MODE value of 54
filtered_df = filtered_df[filtered_df['MODE_OF_OPERATION'] == 54]

# Filter positive values
positive_technologies = filtered_df[filtered_df['VALUE'] > 0]

# Pivot the data to have years as columns
pivot_table = positive_technologies.pivot_table(index='YEAR', columns='TECHNOLOGY', values='VALUE', fill_value=0)

# Custom colors and legend labels
custom_colors = {
    'LNDAGRBC1C01': '#DDB3F9',
    'LNDAGRBC1C02': '#D27A78',
    'LNDAGRBC1C03': '#5BAB59',
    'LNDAGRBC1C04': '#86B4D8',
    'LNDAGRBC1C05': '#FEE566',
    'LNDAGRBC1C06': '#B067B3',
    'LNDAGRBC1C07': 'gray'
}

legend_labels = {
    'LNDAGRBC1C01': 'Land resource - Cluster 1',
    'LNDAGRBC1C02': 'Land resource - Cluster 2',
    'LNDAGRBC1C03': 'Land resource - Cluster 3',
    'LNDAGRBC1C04': 'Land resource - Cluster 4',
    'LNDAGRBC1C05': 'Land resource - Cluster 5',
    'LNDAGRBC1C06': 'Land resource - Cluster 6',
    'LNDAGRBC1C07': 'Land resource - Cluster 7'
}

# Create a list of traces for each technology
traces = []
for tech in selected_technologies:
    trace = go.Bar(
        x=pivot_table.index,
        y=pivot_table[tech],
        name=legend_labels[tech],
        marker=dict(color=custom_colors[tech])
    )
    traces.append(trace)

# Create the layout
layout = go.Layout(
    title='Landuse',
    xaxis=dict(title='Year'),
    yaxis=dict(title='Thousand Sq. Km per PJ'),
    barmode='stack',
    legend=dict(x=1, y=0.5),
    plot_bgcolor='rgba(0, 0, 0, 0)',
    showlegend=True
)

# Create the figure
fig = go.Figure(data=traces, layout=layout)

# Save the plot as an HTML file in the specified directory
html_filename = f'{output_directory}/Landuse.html'
fig.write_html(html_filename, include_plotlyjs='cdn')

print(f"Landuse Plot generated successfully and saved as HTML file to output directory: {output_directory}")
