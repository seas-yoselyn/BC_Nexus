import os
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import utilities as utils

def load_and_process_data(file_path, technologies):
    df = pd.read_csv(file_path)
    yearly_summed_values = {tech: [] for tech in technologies}
    all_years = sorted(set(df['YEAR']))
    for tech in technologies:
        filtered_df = df[df['TECHNOLOGY'].str.startswith(tech)]
        grouped = filtered_df.groupby('YEAR')['VALUE'].sum()
        yearly_summed_values[tech] = [grouped.get(year, 0) for year in all_years]
    return all_years, yearly_summed_values

def generate_traces(technologies, all_years, yearly_summed_values, custom_colors, legend_labels):
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


def generate_plot(file_path, filename_mapping, all_years, traces, plots_direc):
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

def generate_plots(model_results_direc, filenames, filenames_mapping, technologies, custom_colors, legend_labels, plots_direc):
    for filename in filenames:
        file_path = os.path.join(model_results_direc, filename)
        all_years, yearly_summed_values = load_and_process_data(file_path, technologies)
        traces = generate_traces(technologies, all_years,yearly_summed_values, custom_colors, legend_labels)
        generate_plot(file_path, filenames_mapping[filename], all_years, traces, plots_direc)
    print(f"Capacity Plots generated successfully and saved as HTML files to the output directory: {plots_direc}")

def main():
    visual_configs = utils.load_config('config_files/visualization_configs.yaml')
    SCENARIOS=visual_configs['SCENARIOS']
    model_results_direc = os.path.join(os.getcwd(), "results")
    plots_direc = os.path.join(os.getcwd(), "docs/Results_plots")
    os.makedirs(plots_direc, exist_ok=True)
    filenames = visual_configs['capacity_plots']['filenames']
    filenames_mapping = visual_configs['capacity_plots']['filenames_mapping']
    technologies = visual_configs['capacity_plots']['technologies']
    custom_colors = visual_configs['capacity_plots']['custom_colors']
    legend_labels = visual_configs['capacity_plots']['legend_labels']
    generate_plots(model_results_direc, filenames, filenames_mapping, technologies, custom_colors, legend_labels, plots_direc)

if __name__ == "__main__":
    main()
