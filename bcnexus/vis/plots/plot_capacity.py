import os
import numpy as np
import plotly.graph_objs as go
from . import vis_utils
from pathlib import Path
from bcnexus import utils

def _generate_traces(technologies: list[str], 
                    all_years: np.ndarray, 
                    yearly_summed_values: dict[str, np.ndarray],
                    custom_colors: dict[str, str], 
                    legend_labels: dict[str, str]) -> list[go.Bar]:
    traces = []
    for tech in technologies:
        yearly_sum = yearly_summed_values[tech]
        if np.any(yearly_sum):
            trace = go.Bar(
                x=all_years,
                y=yearly_sum,
                name=legend_labels[tech],
                marker=dict(color=custom_colors[tech]),
                textposition='auto',
                hoverinfo='y',
                hoverlabel=dict(bgcolor='white', bordercolor='gray')
            )
            traces.append(trace)
    return traces


def _generate_plot(
                  filename_mapping: str, 
                  traces: list[go.Bar], 
                  plots_direc: str) -> None:
    layout = go.Layout(
        title=f'Yearly {filename_mapping} for Different Technologies - REF Case',
        xaxis=dict(title='Year'),
        yaxis=dict(title='Capacity (GW)'),
        barmode='stack',
        legend=dict(x=1.02, y=1),  # Adjust legend position
        margin=dict(b=150),  # Add margin for legend
        hovermode='closest'
    )

    fig = go.Figure(data=traces, layout=layout)
    html_filename = f'{plots_direc}/{filename_mapping}.html'
    fig.write_html(html_filename)

def make_plots(model_results_direc: str | Path, 
               filenames: list[str], 
               filenames_mapping: dict[str, str], 
               technologies: list[str], 
               custom_colors: dict[str, str], 
               legend_labels: dict[str, str], 
               plots_direc: str | Path) -> None:
    
    for filename in filenames:
        
        file_path = os.path.join(model_results_direc, filename)
        
        all_years, yearly_summed_values = vis_utils.load_and_process_data(file_path, 
                                                                      technologies)
        
        traces = _generate_traces(technologies, 
                                 all_years,
                                 yearly_summed_values,
                                 custom_colors, 
                                 legend_labels)
        
        _generate_plot(filenames_mapping[filename], 
                      traces, 
                      plots_direc)
        
    utils.print_update(level=3,
                       message=f"Capacity Plots generated successfully and saved as HTML files to the output directory: {plots_direc}")

def create_plot(visual_configs:dict,
                          model_results_direc:str|Path,
                          plots_save_to:str|Path):
    
    # visual_configs = utils.load_config('config/visualization_config.yaml')
    # model_results_direc = os.path.join(os.getcwd(), "results/clews/Model_Kotzur_Base/16ts_csvs_gurobi")
    
    plots_save_to = Path(plots_save_to)
    plots_save_to.mkdir(exist_ok=True,parents=True)
    
    filenames = visual_configs['capacity_plots']['filenames']
    filenames_mapping = visual_configs['capacity_plots']['filenames_mapping']
    technologies = visual_configs['capacity_plots']['technologies']
    custom_colors = visual_configs['capacity_plots']['custom_colors']
    legend_labels = visual_configs['capacity_plots']['legend_labels']
            
    utils.print_update(level=2,
                       message="Creating capacity plots...")
    make_plots(model_results_direc, 
                   filenames, 
                   filenames_mapping, 
                   technologies, 
                   custom_colors, 
                   legend_labels, 
                   plots_save_to)
