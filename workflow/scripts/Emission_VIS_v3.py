import os
import pandas as pd
import plotly.graph_objs as go
from plotly.offline import plot
import utilities as utils

def load_and_process_data(file_path, technologies):
    """Load CSV file and process data."""
    df = pd.read_csv(file_path)
    yearly_summed_values = {tech: [] for tech in technologies}
    all_years = sorted(set(df['YEAR']))
    for tech in technologies:
        filtered_df = df[df['TECHNOLOGY'].str.startswith(tech)]
        grouped = filtered_df.groupby('YEAR')['VALUE'].sum()
        yearly_summed_values[tech] = [grouped.get(year, 0) for year in all_years]
    return all_years, yearly_summed_values

def generate_line_plot(df, filename_mapping, plots_directory):
    """Generate and save line plot."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['YEAR'], y=df['VALUE'], mode='lines+markers', name='Emission', marker=dict(color='blue')))
    fig.update_layout(title=f'Yearly {filename_mapping} - REF Case', xaxis_title='Year', yaxis_title='Million Tonnes of CO2', showlegend=False, hovermode='closest', plot_bgcolor='rgba(0, 0, 0, 0)')
    html_filename = os.path.join(plots_directory, f"{filename_mapping}.html")
    fig.write_html(html_filename, include_plotlyjs='cdn')

def generate_stacked_bar_chart(technologies,all_years, yearly_summed_values, filename_mapping, custom_colors, legend_labels, plots_directory):
    """Generate and save stacked bar chart."""
    traces = []
    for tech in technologies:
        trace = go.Bar(x=all_years, y=yearly_summed_values[tech], name=legend_labels[tech], marker_color=custom_colors[tech])
        traces.append(trace)
    layout = go.Layout(title=f'Yearly {filename_mapping} - REF Case', xaxis=dict(title='Year'), yaxis=dict(title='Million Tonnes of CO2'), barmode='stack', legend=dict(x=1, y=0.5), plot_bgcolor='rgba(0, 0, 0, 0)', hovermode='closest')
    fig = go.Figure(data=traces, layout=layout)
    html_filename = os.path.join(plots_directory, f"{filename_mapping}.html")
    fig.write_html(html_filename, include_plotlyjs='cdn')

def generate_plots(model_results_directory, filenames, filenames_mapping, technologies, custom_colors, legend_labels, plots_directory):
    """Generate plots for each filename."""
    for filename in filenames:
        file_path = os.path.join(model_results_directory, filename)

        df_file = pd.read_csv(file_path)
        if "AnnualEmissions.csv" in filename:
            generate_line_plot(df_file, filenames_mapping[filename], plots_directory)
        else:
            all_years, yearly_summed_values = load_and_process_data(file_path, technologies)
            generate_stacked_bar_chart(technologies,all_years, yearly_summed_values, filenames_mapping[filename], custom_colors, legend_labels, plots_directory)
    print(f"Plots generated successfully and saved as HTML files to the output directory: {plots_directory}")

def main():
    visual_configs = utils.load_config('config_files/visualization_configs.yaml')
    model_results_directory = os.path.join(os.getcwd(), "results")
    plots_directory = os.path.join(os.getcwd(), "docs/Results_plots")
    os.makedirs(plots_directory, exist_ok=True)

    filenames = visual_configs['emission_plots']['filenames']
    filenames_mapping = visual_configs['emission_plots']['filenames_mapping']
    technologies = visual_configs['emission_plots']['technologies']
    custom_colors = visual_configs['emission_plots']['custom_colors']
    legend_labels = visual_configs['emission_plots']['legend_labels']

    generate_plots(model_results_directory, filenames, filenames_mapping, technologies, custom_colors, legend_labels, plots_directory)

if __name__ == "__main__":
    main()
