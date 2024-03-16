import os
import plotly.graph_objects as go
from dash import Dash, html, dcc, callback, Output, Input
import pandas as pd




app = Dash(__name__)

server = app.server

app.layout = html.Div([
    html.H1('Timeslice Dashboard'),
    # Add a container for the dashboard content
    html.Div(id='dashboard-content')
])

@app.callback(
    Output('dashboard-content', 'children'),
    []
)


def create_timeseries_plots(site_type,cluster_ts,save_to):
    sites=cluster_ts.keys()
    # Extract dates, values, and labels
    dates = cluster_ts.index
    for site in sites:
        values = cluster_ts[site]
        labels = cluster_ts['season_daytime']

        timeslice_name_mapping = {
            'Fall_D': 'SEA2D',
            'Fall_N': 'SEA2N',
            'Out_of_Season': 'NA',
            'Spring_D': 'SEA3D',
            'Spring_N': 'SEA3N',
            'Summer_D': 'SEA4D',
            'Summer_N': 'SEA4N',
            'Winter1_D': 'SEA1D',
            'Winter1_N': 'SEA1N',
            'Winter2_D': 'SEA1D',
            'Winter2_N': 'SEA1N'
        }

        color_mapping = {
            'SEA1D': 'deepskyblue',  # darkblue
            'SEA1N': 'lightblue',  # darkgreen
            'SEA2D': 'orange',  # darkred
            'SEA2N': 'palegoldenrod',  # darkorange
            'SEA3D': 'plum',  # darkviolet
            'SEA3N': 'thistle',  # darkcyan
            'SEA4D': 'steelblue',  # darkmagenta
            'SEA4N': 'lightgreen',  # darkyellow
            'NA': 'lightgrey'  # darkgray
        }

        # Create a list of colors corresponding to each label
        colors = [color_mapping[timeslice_name_mapping[label]] for label in labels]

        # Create a Plotly figure
        fig = go.Figure()

        # Add a trace for the data
        fig.add_trace(go.Scatter(x=dates, y=values, mode='markers', name='Squamish-Lillooet_1', text=labels,
                                marker=dict(color=colors)))  # Set the color of the markers

        # Add separate traces for each color category with custom legend entries
        for key, color in color_mapping.items():
            fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', marker=dict(color=color), name=key))

        # Customize the layout
        fig.update_layout(title='Solar',
                        xaxis_title='Date',
                        yaxis_title='Value',
                        hovermode='x',  # Enable hover for x-values only
                        xaxis=dict(type='date', rangeslider=dict(visible=True)),  # Enable interactive zooming
                        )
        fig.write_html(f"{save_to}/{site_type}_time_series_plot_{site}.html")

    return print(f'{site_type} - Cluster timeseries plots generated and saved to {save_to}')

cluster_ts=pd.read_pickle('solar_ts.pkl')

def update_dashboard(_):
    # Load the data
    cluster_ts = pd.read_pickle('solar_ts.pkl')
    
    # Define the directory to save HTML files
    save_to = 'vis'
    
    # Call the create_timeseries_plots function
    create_timeseries_plots('Solar', cluster_ts, save_to)
    
    # Get the list of HTML files in the directory
    html_files = [f for f in os.listdir(save_to) if f.endswith('.html')]
    
    # Create Dash components for each HTML file
    dashboard_components = [html.Iframe(src=f'/{save_to}/{file}', width='100%', height='600') for file in html_files]
    
    return dashboard_components
@app.server.route('/vis')
def serve_timeseries_plots():
    # Add code to serve the exported HTML files
    # You may need to modify this part based on how you're storing and serving the HTML files
    return app.index()

if __name__ == '__main__':
    app.run_server(debug=True)
