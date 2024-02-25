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

filenames = ["AnnualEmissions.csv", "AnnualTechnologyEmission.csv"]

filenames_mapping = {
    'AnnualTechnologyEmission.csv': 'Emission by Sector',
    'AnnualEmissions.csv': 'Emission'
}

# Define the technologies and colors
technologies = ['DEMAGR', 'DEMCOM', 'DEMIND', 'DEMRES', 'DEMTRA']
custom_colors = {
    'DEMAGR': '#C57F7B',
    'DEMCOM': '#65B465',
    'DEMIND': '#B3B3B3',
    'DEMRES': '#87B4D7',
    'DEMTRA': '#676767',
}

# Legend label dictionary
legend_labels = {
    'DEMRES': 'Residential',
    'DEMIND': 'Industrial',
    'DEMTRA': 'Transport',
    'DEMAGR': 'Agricultural',
    'DEMCOM': 'Commercial'
}

for filename in filenames:
    file = os.path.join(directory_path, filename)
    df_file = pd.read_csv(file)

    if filename == 'AnnualEmissions.csv':
        # Create the line chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_file['YEAR'], y=df_file['VALUE'], mode='lines+markers', name='Emission', marker=dict(color='blue')))
        
        # Customize the plot
        fig.update_layout(title=f'Yearly {filenames_mapping[filename]} - REF Case',
                          xaxis_title='Year',
                          yaxis_title='Million Tonnes of CO2',
                          showlegend=False,
                          hovermode='closest',
                          plot_bgcolor='rgba(0, 0, 0, 0)')

        # Save the plot as an HTML file in the specified directory
        html_filename = f'{output_directory}/{filenames_mapping[filename]}.html'
        plot(fig, filename=html_filename, auto_open=False)
        
    else:
        # Create a list to hold traces for the stacked bar chart
        traces = []

        # Generate traces for each technology
        for tech in technologies:
            filtered_df = df_file[df_file['TECHNOLOGY'].str.startswith(tech)]
            grouped = filtered_df.groupby('YEAR')['VALUE'].sum()
            trace = go.Bar(x=grouped.index, y=grouped.values, name=legend_labels[tech], marker_color=custom_colors[tech])
            traces.append(trace)

        # Create the layout
        layout = go.Layout(title=f'Yearly {filenames_mapping[filename]} - REF Case',
                           xaxis=dict(title='Year'),
                           yaxis=dict(title='Million Tonnes of CO2'),
                           barmode='stack',
                           legend=dict(x=1, y=0.5),
                           plot_bgcolor='rgba(0, 0, 0, 0)')

        # Create the figure
        fig = go.Figure(data=traces, layout=layout)

        # Save the plot as an HTML file in the specified directory
        html_filename = f'{output_directory}/{filenames_mapping[filename]}.html'
        # plot(fig, filename=html_filename, auto_open=False)
        fig.write_html(html_filename, include_plotlyjs='cdn')

print(f"Emission Plots generated successfully and saved as HTML files to the output directory: {output_directory}")
