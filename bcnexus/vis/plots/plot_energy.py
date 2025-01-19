import os
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from bcnexus import utils
from pathlib import Path

def generate_plot(scenario, 
                  filename_mapping, 
                  traces, 
                  plots_direc):
    layout = go.Layout(
    title=f'Yearly {filename_mapping} for Different Technologies [{scenario}]',
    xaxis=dict(title='y'),
    yaxis=dict(title='Generation (Pj)'),
    barmode='stack',
    legend=dict(x=1.02, y=1),  # Adjust legend position
    margin=dict(b=150),  # Add margin for legend
    hovermode='closest'
    )

    fig = go.Figure(data=traces, layout=layout)
    html_filename = f'{plots_direc}/{filename_mapping}_{scenario}.html'
    fig.write_html(html_filename)

def generate_plots(scenario,model_results_direc, filenames, filenames_mapping, technologies, technology_column,year_column,custom_colors, legend_labels, plots_direc):
    for filename in filenames:
        file_path = os.path.join(model_results_direc, filename)
        all_years, yearly_summed_values = utils.load_and_process_data(file_path, technologies,technology_column,year_column)
        traces = utils.generate_traces(technologies, all_years,yearly_summed_values, custom_colors, legend_labels)
        generate_plot(scenario, filenames_mapping[filename], traces, plots_direc)
    # print(f"Capacity Plots generated successfully and saved as HTML files to the output directory: {plots_direc}")

def create_plot(visual_configs:dict,
                model_results_direc:str|Path,
                plots_save_to:str|Path):
    
    plots_save_to = Path(plots_save_to)
    plots_save_to.mkdir(exist_ok=True,parents=True)


    filenames = visual_configs['energy_plots']['filenames']
    filenames_mapping = visual_configs['energy_plots']['filenames_mapping']
    technologies = visual_configs['energy_plots']['technologies']
    custom_colors = visual_configs['energy_plots']['custom_colors']
    legend_labels = visual_configs['energy_plots']['legend_labels']


    utils.print_update(level=2,
                    message="Creating emission plots...")
    generate_plots(model_results_direc, filenames, filenames_mapping, technologies, technology_column,year_column,custom_colors, legend_labels, plots_direc)


