import os
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.offline import plot
import utilities as utils


visual_configs = utils.load_config('config_files/visualization_configs.yaml')
model_results_direc = os.path.join(os.getcwd(), "results")
plots_direc = os.path.join(os.getcwd(), "docs/Results_plots")
os.makedirs(plots_direc, exist_ok=True)
filenames = visual_configs['emission_plots']['filenames']
filenames_mapping = visual_configs['emission_plots']['filenames_mapping']
technologies = visual_configs['emission_plots']['technologies']
custom_colors = visual_configs['emission_plots']['custom_colors']
legend_labels = visual_configs['emission_plots']['legend_labels']

for filename in filenames:
    file = os.path.join(model_results_direc, filename)
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
        html_filename = f'{plots_direc}/{filenames_mapping[filename]}.html'
        fig.write_html(html_filename, include_plotlyjs='cdn')
        
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
        html_filename = f'{plots_direc}/{filenames_mapping[filename]}.html'
        # plot(fig, filename=html_filename, auto_open=False)
        fig.write_html(html_filename, include_plotlyjs='cdn')

print(f"Emission Plots generated successfully and saved as HTML files to the output directory: {plots_direc}")
