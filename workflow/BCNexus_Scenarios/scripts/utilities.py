import yaml
import pandas as pd
import numpy as np
import plotly.graph_objs as go

# Function to Load User Configuration File
def load_config(file_path):

    with open(file_path, 'r') as file:
        configs = yaml.safe_load(file)
    return configs

def load_and_process_data(file_path, technologies,technology_column,year_column):
    df = pd.read_csv(file_path)
    parameter=df.columns[-1]
    yearly_summed_values = {tech: [] for tech in technologies}
    all_years = sorted(set(df[year_column]))
    for tech in technologies:
        filtered_df = df[df[technology_column].str.startswith(tech)]
        grouped = filtered_df.groupby(year_column)[parameter].sum()
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