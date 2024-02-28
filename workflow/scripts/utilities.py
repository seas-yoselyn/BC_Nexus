import yaml
import pandas as pd

# Function to Load User Configuration File
def load_config(file_path):

    with open(file_path, 'r') as file:
        configs = yaml.safe_load(file)
    return configs

def load_and_process_data(file_path, technologies):

    # if "AnnualEmissions.csv" in file_path:
    #     # Load data for emissions
    #     print("Loading data for AnnualEmissions.csv")  # Add a print statement to check if data is being loaded
    #     result_df = pd.read_csv(file_path)
    #     all_years=sorted(set(result_df['YEAR']))
    #     # return years, result_df
    # else:
    df = pd.read_csv(file_path)
    yearly_summed_values = {tech: [] for tech in technologies}
    all_years = sorted(set(df['YEAR']))
    grouped_data = {}
    for tech in technologies:
        filtered_df = df[df['TECHNOLOGY'].str.startswith(tech)]
        grouped = filtered_df.groupby('YEAR')['VALUE'].sum()
        grouped_data[tech] = grouped.reindex(all_years, fill_value=0)
        yearly_summed_values[tech] = [grouped.get(year, 0) for year in all_years]
    result_df = pd.DataFrame(grouped_data)

    return all_years, result_df