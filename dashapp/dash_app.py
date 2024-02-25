from dash import Dash, html, dcc, callback, Output, Input, exceptions,clientside_callback
import plotly.graph_objs as go
import os

# List of HTML files for plots
result_plots = "Results_plots"

html_files = [f for f in os.listdir(result_plots) if f.endswith('.html')]

# Create Dash app
app = Dash(__name__)

# Define layout
app.layout = html.Div([
    html.H1(children='CLEWs Kenya (Preliminary Results)', style={'textAlign': 'center'}),
    dcc.Dropdown(options=[{'label': file, 'value': file} for file in html_files], value=html_files[0], id='dropdown-selection'),
    html.Iframe(id='plot-iframe', style={'width': '100%', 'height': '600px', 'border': 'none'})
])

# Define callback to update iframe content based on dropdown selection
@app.callback(
    Output('plot-iframe', 'srcDoc'),
    Input('dropdown-selection', 'value')
)
def update_iframe(selected_file):
    try:
        with open(selected_file, 'r') as f:
            plot_html = f.read()
        return plot_html
    except FileNotFoundError:
        return f"<h2>{selected_file} not found!</h2>"
    except exceptions.PreventUpdate:
        return None

if __name__ == '__main__':
    app.run_server(debug=True)
