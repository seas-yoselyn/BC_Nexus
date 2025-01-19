import os
from dash import Dash, html, dcc, Output, Input
import pandas as pd
from bcnexus.vis import vis_utils
from bcnexus import utils
import plotly.express as px
from bcnexus.vis.dashboard.dash_components import header, scenario_and_tabs
from pathlib import Path

# Load configurations
dash_configs: dict = utils.load_config('config/dashboard.yaml')

plot_files: dict = dash_configs['plot_files']
demand_data = dash_configs['demand_data']
units_mapping = dash_configs['units_mapping']
filenames_mapping = dash_configs['filenames_mapping']
selected_technologies = dash_configs['technologies']
custom_colors = dash_configs['custom_colors']
legend_labels = dash_configs['legend_labels']
result_type = dash_configs['result_type']
info_SCENARIOS = dash_configs['info_SCENARIOS']

# Define folders/sub-folders to access data
scenario_results_directory = Path('results/clews')
SCENARIOS = sorted([item.name for item in scenario_results_directory.iterdir() if item.is_dir()])

timeslices = 30
results_subfolder = f'{timeslices}ts_csvs_gurobi'
""" 
folder_names = []
for scenario in SCENARIOS:
    # Define the path to the directory
    directory_path = f'results/clews/{scenario}'  # Replace with your actual path
    if os.path.exists(directory_path):
        # List all subdirectories that end with 'ts'
        folder_names.extend([folder for folder in os.listdir(directory_path) 
                             if os.path.isdir(os.path.join(directory_path, folder)) and folder.endswith('ts')])

"""
# Initialize Dash app
app = Dash(__name__, external_stylesheets=['https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css'])
server = app.server

# Define layout
app.layout = html.Div([
    header(dash_configs['title']),
    scenario_and_tabs(SCENARIOS, plot_files),

    # Add the note at the top about timeslices styled as an alert
    html.Div(
        children=f"Displaying model results for {timeslices} timeslices",  # Dynamic message
        className="alert alert-info text-center",  # Bootstrap alert class for styling
        style={
            'fontSize': '0.9rem',  # Set the font size
            'color': '#333',  # Set text color for better readability
            'borderRadius': '5px',  # Rounded corners for the alert
            'padding': '10px',  # Padding for better spacing inside the alert
            'boxShadow': '0 2px 5px rgba(0, 0, 0, 0.1)',  # Subtle shadow for a modern touch
        }
    ),

    # Main contents
    html.Div(id='tab-content', className='mt-4')
], className='container')



# Callback to update scenario information
@app.callback(
    Output('scenario-info', 'children'),
    [Input('scenario-dropdown', 'value')]
)
def update_scenario_info(selected_scenario):
    info = info_SCENARIOS.get(selected_scenario, 'No information available for this scenario')
    return html.P(info, className='text-muted')

# Callback to update graph based on tab selection and dropdown value
@app.callback(
    Output('tab-content', 'children'),
    [Input('tabs', 'value'), 
     Input('scenario-dropdown', 'value')] + [Input({'type': 'plot_type-dropdown', 'index': tab_label}, 'value') for tab_label in plot_files]
)
def update_tab_content(selected_tab, selected_scenario, *selected_filenames):
    graphs = []
    plot_files_list = plot_files[selected_tab]
    selected_filenames = [filename for filename in selected_filenames if filename in plot_files_list]

    if selected_tab == 'demand':
        demand_file_paths = [Path(demand_data) / filename for filename in selected_filenames]
        for file_path, filename in zip(demand_file_paths, selected_filenames):
            if file_path.exists():
                df = pd.read_csv(file_path)
                if all(col in df.columns for col in ["year", "Commercial", "Industrial", "Residential", "Transportation"]):
                    fig = px.area(
                        df,
                        x="year",
                        y=["Commercial", "Industrial", "Residential", "Transportation"],
                        title="Sectoral Emissions (Canada Energy Future 2023)",
                        labels={"value": "Emissions (units)", "year": "Year"},
                        color_discrete_map={
                            "Commercial": "blue",
                            "Industrial": "green",
                            "Residential": "orange",
                            "Transportation": "red"
                        }
                    )
                    fig.update_layout(
                        barmode='stack',
                        xaxis_title="Year",
                        yaxis_title="Emissions (MteCO2)",
                        legend_title="Sector"
                    )
                    graphs.append(dcc.Graph(figure=fig))
    else:
        result_file_paths = [scenario_results_directory / selected_scenario / results_subfolder / filename for filename in selected_filenames]
        for file_path, filename in zip(result_file_paths, selected_filenames):
            if file_path.exists():
                df = pd.read_csv(file_path)
                if filename == "AnnualEmissions.csv":
                    fig = px.line(df, x='YEAR', y=df.columns[-1], title='Emission Trends', markers=False)
                    fig.update_xaxes(title_text='Year')
                    fig.update_yaxes(title_text=units_mapping[selected_tab])
                    graphs.append(dcc.Graph(figure=fig))
                elif filename == "AnnualTechnologyEmission.csv":
                    techs = selected_technologies[selected_tab]
                    years, df_processed = vis_utils.load_and_process_data(file_path, techs)
                    if all(col in df_processed.columns for col in ['YEAR', 'TECHNOLOGY']):
                        fig = px.area(df_processed, x=years, y=techs, title=filenames_mapping[filename], color_discrete_map=custom_colors)
                        fig.update_xaxes(title_text='Year')
                        fig.update_yaxes(title_text=units_mapping[selected_tab])
                        for tech, label in legend_labels.items():
                            fig.for_each_trace(lambda trace: trace.update(name=label) if trace.name == tech else ())
                        graphs.append(dcc.Graph(figure=fig))
                else:
                    techs = selected_technologies[selected_tab]
                    years, df_processed = vis_utils.load_and_process_data(file_path, techs)
                    fig = px.bar(df_processed, x=years, y=techs, title=filenames_mapping[filename], color_discrete_map=custom_colors)
                    fig.update_xaxes(title_text='Year')
                    fig.update_yaxes(title_text=units_mapping[selected_tab])
                    for tech, label in legend_labels.items():
                        fig.for_each_trace(lambda trace: trace.update(name=label) if trace.name == tech else ())
                    graphs.append(dcc.Graph(figure=fig))

    return graphs

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
