import os
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import utilities as utils

def generate_plot(scenario, filename_mapping, traces, plots_direc):
    layout = go.Layout(
    title=f'Yearly {filename_mapping} for Different Technologies - [{scenario}]',
    xaxis=dict(title='year'),
    yaxis=dict(title='Capacity (GW)'),
    barmode='stack',
    legend=dict(x=1.02, y=1),  # Adjust legend position
    margin=dict(b=150),  # Add margin for legend
    hovermode='closest'
    )

    fig = go.Figure(data=traces, layout=layout)
    html_filename = f'{plots_direc}/{filename_mapping}_{scenario}.html'
    fig.write_html(html_filename)

def generate_plots(scenario,model_results_direc, filenames, filenames_mapping, technologies, technology_column, year_column,custom_colors, legend_labels, plots_direc):
    for filename in filenames:
        file_path = os.path.join(model_results_direc, filename)
        all_years, yearly_summed_values = utils.load_and_process_data(file_path, technologies,technology_column, year_column)
        traces = utils.generate_traces(technologies, all_years,yearly_summed_values, custom_colors, legend_labels)
        generate_plot(scenario, filenames_mapping[filename], traces, plots_direc)
    # print(f"Capacity Plots generated successfully and saved as HTML files to the output directory: {plots_direc}")

def main():
    visual_configs = utils.load_config('config/visualization_config.yaml')
    SCENARIOS=visual_configs['SCENARIOS']
    technology_column='t'
    year_column='y'
    print(f"Generating Capacity Plots ...")
    for scenario in SCENARIOS:
        print(f"Creating Plots for SCENARIO: {scenario}")
        model_results_direc = os.path.join(os.getcwd(), f"scenario_files/{scenario}/results")

        plots_direc = os.path.join(os.getcwd(), f"scenario_plots/{scenario}")
        os.makedirs(plots_direc, exist_ok=True)

        filenames = visual_configs['capacity_plots']['filenames']
        filenames_mapping = visual_configs['capacity_plots']['filenames_mapping']
        technologies = visual_configs['capacity_plots']['technologies']
        custom_colors = visual_configs['capacity_plots']['custom_colors']
        legend_labels = visual_configs['capacity_plots']['legend_labels']
        generate_plots(scenario,model_results_direc, filenames, filenames_mapping, technologies,technology_column, year_column,custom_colors, legend_labels, plots_direc)
    print(f"Capacity Plots generated successfully.")

if __name__ == "__main__":
    main()
