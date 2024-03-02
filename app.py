import os
# import sys
# sys.path.append('workflow/scripts')
from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
from  workflow.scripts import utilities as utils
import plotly.io as pio

# Load configurations
dash_configs = utils.load_config('config/dashboard.yaml')
# SCENARIOS = dash_configs['SCENARIOS']
# List all files and directories in the specified directory
scenario_results_directory='workflow/BCNexus_Scenarios/scenario_files'
contents = os.listdir(scenario_results_directory)
# Filter out directories
SCENARIOS = sorted([item for item in contents if os.path.isdir(os.path.join(scenario_results_directory, item))])

model_results_direc = 'results'
scenario_results_direc='workflow/BCNexus_Scenarios/scenario_files'
plots_direc = os.path.join(os.getcwd(), "docs/Results_plots")
os.makedirs(plots_direc, exist_ok=True)

result_files = dash_configs['result_files']
units_mapping = dash_configs['units_mapping']
filenames_mapping = dash_configs['filenames_mapping']
selected_technologies = dash_configs['technologies']
custom_colors = dash_configs['custom_colors']
legend_labels = dash_configs['legend_labels']
result_type=dash_configs['result_type']
info_SCENARIOS=dash_configs['info_SCENARIOS']

# Initialize Dash app
app = Dash(__name__)

server = app.server

# Define layout
app.layout = html.Div([
    html.H1(children=dash_configs['title'], style={'textAlign': 'center', 'fontSize': dash_configs['font_size'], 'color': dash_configs['font_color'],'margin-bottom': '1px'}),
    html.Div(
        children=[
            html.A("more about BC-CLEWS-Model", href="https://github.com/DeltaE/BC-CLEWS-Model/wiki", target="_blank"),
        ],
        style={'textAlign': 'center', 'margin-bottom': '2px'}
    ),
    html.Div([
        html.Label('Select Scenario ', style={'font-weight': 'bold', 'color': 'brown', 'display': 'inline-block', 'margin-right': '10px'}),
        dcc.Dropdown(
            id='scenario-dropdown',
            options=[{'label': scenario, 'value': scenario} for scenario in SCENARIOS],
            value=SCENARIOS[0],
            style={'width': '50%', 'margin': 'auto', 'display': 'inline-block'}
        ),
        html.Br(),
        html.Div(id='scenario-info')
    ]),
    dcc.Tabs(id='tabs', value=list(result_files.keys())[0], children=[
        dcc.Tab(label=tab_label, value=tab_label, children=[
            html.Div([
                dcc.Dropdown(
                    id={'type': 'plot_type-dropdown', 'index': tab_label},
                    options=[{'label': filenames_mapping[filename], 'value': filename} for filename in plot_files],
                    value=plot_files[0] if plot_files else None
                )
            ])
        ]) for tab_label, plot_files in result_files.items()
    ]),
    html.Div(id='tab-content')
])


# Callback to update scenario information
@app.callback(
    Output('scenario-info', 'children'),
    [Input('scenario-dropdown', 'value')]
)
def update_scenario_info(selected_scenario):
    info = info_SCENARIOS.get(selected_scenario, 'No information available for this scenario')
    return html.P(info)


# Define callback to update graph based on tab selection and dropdown value
@app.callback(
    Output('tab-content', 'children'),
    [Input('tabs', 'value'), Input('scenario-dropdown', 'value')] + [Input({'type': 'plot_type-dropdown', 'index': tab_label}, 'value') for tab_label in result_files]
)
def update_tab_content(selected_tab, selected_scenario, *selected_filenames):

    # Initialize a list to store the graphs
    graphs = []

    # Get the plot files for the selected tab
    plot_files = result_files[selected_tab]

    # Filter the selected filenames based on the plot files for the selected tab
    selected_filenames_filtered = [filename for filename in selected_filenames if filename in plot_files]

    # Construct file paths for the filtered filenames
    result_file_paths_filtered = [os.path.join(scenario_results_direc, selected_scenario, 'results', filename) for filename in selected_filenames_filtered]
    year_col='YEAR'
    technology_col='TECHNOLOGY'
    # Load and process data for each selected filename
    for file_path, filename in zip(result_file_paths_filtered, selected_filenames_filtered):

        if filename == "AnnualEmissions.csv":
            # Generate line chart for AnnualEmissions.csv
            df_emission = pd.read_csv(file_path)    
            if 'YEAR'  not in df_emission.columns:
                year_col='y'
            fig = px.line(df_emission, x=year_col, y=df_emission.columns[-1], title=f'Emission Trends', markers=True)
            fig.update_xaxes(title_text='Year')
            units_title = units_mapping[selected_tab]
            fig.update_yaxes(title_text=units_title)
            graphs.append(dcc.Graph(figure=fig))

        else:
            # Load and process data for other file types
            techs = selected_technologies[selected_tab]
            years, df = utils.load_and_process_data(file_path, techs)
            if 'YEAR' or 'TECHNOLOGY' not in df.columns:
                year_col='y'
                technology_col='t'
            fig = px.bar(df, x=years, y=techs, title=f'{filenames_mapping[filename]}', color_discrete_map=custom_colors)
            fig.update_xaxes(title_text='Year')
            units_title = units_mapping[selected_tab]
            fig.update_yaxes(title_text=units_title)

            for tech, label in legend_labels.items():
                fig.for_each_trace(lambda trace: trace.update(name=label) if trace.name == tech else (), row=None, col=None)

            graphs.append(dcc.Graph(figure=fig))

    print("Selected tab:", selected_tab)
    print("Selected filenames:", selected_filenames)
    print("Filtered filenames:", selected_filenames_filtered)
    return graphs

# Define a route to serve the exported HTML
@app.server.route('/export')
def serve_export():
    pio.write_html(app, 'dash_export.html')
    return app.index()

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
