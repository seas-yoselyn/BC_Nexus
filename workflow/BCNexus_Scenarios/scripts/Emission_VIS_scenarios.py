import os
import pandas as pd
import plotly.graph_objs as go
from plotly.offline import plot
import utilities as utils


def generate_line_plot(scenario,df, filename_mapping, plots_directory):
    """Generate and save line plot."""
    parameter=df.columns[-1]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['y'], y=df[parameter], mode='lines+markers', name='Emission', marker=dict(color='blue')))
    fig.update_layout(title=f'yly {filename_mapping} - [{scenario}]', xaxis_title='y', yaxis_title='Million Tonnes of CO2', showlegend=False, hovermode='closest', plot_bgcolor='rgba(0, 0, 0, 0)')
    html_filename = os.path.join(plots_directory, f"{filename_mapping}_{scenario}.html")
    fig.write_html(html_filename, include_plotlyjs='cdn')

def generate_stacked_bar_chart(scenario,technologies,all_ys, yly_summed_values, filename_mapping, custom_colors, legend_labels, plots_directory):
    """Generate and save stacked bar chart."""
    traces = []
    for tech in technologies:
        trace = go.Bar(x=all_ys, y=yly_summed_values[tech], name=legend_labels[tech], marker_color=custom_colors[tech])
        traces.append(trace)
    layout = go.Layout(title=f'yly {filename_mapping} - [{scenario}]', xaxis=dict(title='y'), yaxis=dict(title='Million Tonnes of CO2'), barmode='stack', legend=dict(x=1, y=0.5), plot_bgcolor='rgba(0, 0, 0, 0)', hovermode='closest')
    fig = go.Figure(data=traces, layout=layout)
    html_filename = os.path.join(plots_directory, f"{filename_mapping}_{scenario}.html")
    fig.write_html(html_filename, include_plotlyjs='cdn')

def generate_plots(scenario,model_results_directory, filenames, filenames_mapping, technologies, technology_column,year_column, custom_colors, legend_labels, plots_directory):
    """Generate plots for each filename."""
    for filename in filenames:
        file_path = os.path.join(model_results_directory, filename)

        df_file = pd.read_csv(file_path)
        if "AnnualEmissions.csv" in filename:
            generate_line_plot(scenario,df_file, filenames_mapping[filename], plots_directory)
        else:
            all_ys, yly_summed_values = utils.load_and_process_data(file_path, technologies, technology_column,year_column)
            generate_stacked_bar_chart(scenario,technologies,all_ys, yly_summed_values, filenames_mapping[filename], custom_colors, legend_labels, plots_directory)
    # print(f"Plots generated successfully and saved as HTML files to the output directory: {plots_directory}")

def main():
    visual_configs = utils.load_config('config/visualization_config.yaml')
    SCENARIOS=visual_configs['SCENARIOS']
    technology_column='t'
    year_column='y'
    print(f"Generating Emission Plots ...")

    for scenario in SCENARIOS:
        print(f"Creating Plots for SCENARIO: {scenario}")
        model_results_direc = os.path.join(os.getcwd(), f"scenario_files/{scenario}/results")

        plots_direc = os.path.join(os.getcwd(), f"scenario_plots/{scenario}")
        os.makedirs(plots_direc, exist_ok=True)

        filenames = visual_configs['emission_plots']['filenames']
        filenames_mapping = visual_configs['emission_plots']['filenames_mapping']
        technologies = visual_configs['emission_plots']['technologies']
        custom_colors = visual_configs['emission_plots']['custom_colors']
        legend_labels = visual_configs['emission_plots']['legend_labels']

        generate_plots(scenario,model_results_direc, filenames, filenames_mapping, technologies, technology_column,year_column,custom_colors, legend_labels, plots_direc)
    print(f"Emission Plots generated successfully.")

if __name__ == "__main__":
    main()
