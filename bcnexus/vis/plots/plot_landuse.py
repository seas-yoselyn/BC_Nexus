import os
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from bc_combined_modelling.vis import utilities as utils
# Load Visual Config File
visual_configs=utils.load_config('config/visualization_config.yaml')

# Input CSV files' Directory
model_results_direc=os.path.join(os.getcwd(),"results/clews/Model_Kotzur_Base/16ts_csvs_gurobi")

# Set the output Directory path
plots_direc = os.path.join(os.getcwd(), "docs/Results_plots")
os.makedirs(plots_direc, exist_ok=True)

filenames= visual_configs['landuse_plots']['filenames']
filenames_mapping=visual_configs['landuse_plots']['filenames_mapping']

# Define the technologies and colors from config file
technologies = visual_configs['landuse_plots']['technologies']
custom_colors = visual_configs['landuse_plots']['custom_colors']
legend_labels = visual_configs['landuse_plots']['legend_labels']

for filename in filenames:
    file = os.path.join(model_results_direc, filename)
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
    for i, tech in enumerate(technologies):
        yearly_sum = yearly_summed_values[tech]
        if np.any(yearly_sum):
            trace = go.Bar(
                x=all_years,
                y=yearly_sum,
                name=legend_labels[tech],
                marker=dict(color=custom_colors[tech]),
                textposition='auto',
                hoverinfo='y',
                hoverlabel=dict(bgcolor='white', bordercolor='gray'),
            )
            traces.append(trace)

    # Create the layout
    layout = go.Layout(
        title=f'Yearly {filenames_mapping[filename]} for Different Technologies - REF Case',
        xaxis=dict(title='Year'),
        yaxis=dict(title='Thousand Sq. Km per PJ'),
        barmode='stack',
        legend=dict(x=1, y=0.5),
        margin=dict(b=150),  # Add margin for legend
        hovermode='closest'
    )

    # Create the figure
    fig = go.Figure(data=traces, layout=layout)

    # Save the plot as an HTML file in the specified directory
    html_filename = f'{plots_direc}/{filenames_mapping[filename]}.html'
    fig.write_html(html_filename)

print(f"Landuse Plots generated successfully and saved as HTML files to the output directory: {plots_direc}")
