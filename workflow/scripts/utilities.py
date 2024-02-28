import yaml
import pandas as pd

# Function to Load User Configuration File
def load_config(file_path):

    with open(file_path, 'r') as file:
        configs = yaml.safe_load(file)
    return configs

def load_and_process_data(file_path, technologies, year_column, technology_column):
    df = pd.read_csv(file_path)
    yearly_summed_values = {tech: [] for tech in technologies}
    all_years = sorted(set(df[year_column]))
    grouped_data = {}
    for tech in technologies:
        filtered_df = df[df[technology_column].str.startswith(tech)]
        last_column = filtered_df.iloc[:, -1]
        grouped = last_column.groupby(filtered_df[year_column]).sum()
        grouped_data[tech] = grouped.reindex(all_years, fill_value=0)
        yearly_summed_values[tech] = [grouped.get(year, 0) for year in all_years]
    result_df = pd.DataFrame(grouped_data)

    return all_years, result_df