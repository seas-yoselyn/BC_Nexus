import os
from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import utilities as utils

# Load configurations
dash_configs = utils.load_config('/home/eliasinul/repositories/BC-CLEWS-Model/config/dashboard.yaml')
SCENARIOS = dash_configs['SCENARIOS']
model_results_direc = '/home/eliasinul/repositories/BC-CLEWS-Model/results'
plots_direc = os.path.join(os.getcwd(), "docs/Results_plots")
os.makedirs(plots_direc, exist_ok=True)

result_files = dash_configs['result_files']
units_mapping = dash_configs['units_mapping']
filenames_mapping = dash_configs['filenames_mapping']
selected_technologies = dash_configs['technologies']
custom_colors = dash_configs['custom_colors']
legend_labels = dash_configs['legend_labels']

# Initialize Dash app
app = Dash(__name__)
server = app.server

# Define layout
app.layout = html.Div([
    html.H1(children=dash_configs['title'], style={'textAlign': 'center', 'fontSize': dash_configs['font_size'], 'color': dash_configs['font_color']}),
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

# Define callback to update graph based on tab selection and dropdown value
@app.callback(
    Output('tab-content', 'children'),
    [Input('tabs', 'value')] + [Input({'type': 'plot_type-dropdown', 'index': tab_label}, 'value') for tab_label in result_files]
)

def update_tab_content(selected_tab, *selected_filenames):

    # Initialize a list to store the graphs
    graphs = []

    # Get the plot files for the selected tab
    plot_files = result_files[selected_tab]

    # Filter the selected filenames based on the plot files for the selected tab
    selected_filenames_filtered = [filename for filename in selected_filenames if filename in plot_files]

    # Construct file paths for the filtered filenames
    result_file_paths_filtered = [os.path.join(model_results_direc, filename) for filename in selected_filenames_filtered]

    # Load and process data for each selected filename
    for file_path, filename in zip(result_file_paths_filtered, selected_filenames_filtered):

        if filename == "AnnualEmissions.csv":
            # Generate line chart for AnnualEmissions.csv
            df_emission = pd.read_csv(file_path)
            fig = px.line(df_emission, x='YEAR', y='VALUE', title=f'Emission Trends for {selected_tab}', 
                             markers=True)
            fig.update_xaxes(title_text='Year')
            units_title = units_mapping[selected_tab]
            fig.update_yaxes(title_text=units_title)
            graphs.append(dcc.Graph(figure=fig))

        else:
            # Load and process data for other file types
            techs = selected_technologies[selected_tab]
            years, df = utils.load_and_process_data(file_path, techs)
            fig = px.bar(df, x=years, y=techs, title=f'Stacked Bar Chart for {selected_tab}',
                         color_discrete_map=custom_colors)
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



# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
