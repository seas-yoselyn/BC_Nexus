import os
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import glob

# Initialize Dash app
app = dash.Dash(__name__)

# Define function to get HTML files in directory
def get_html_files(directory):
    html_files = glob.glob(os.path.join(directory, '*.html'))
    return html_files

# Get HTML files in 'vis' directory
html_files = get_html_files('vis')

# Create tabs dynamically based on HTML files
tabs = html.Div([
    dcc.Tabs(id='tabs', value=html_files[0], children=[
        dcc.Tab(label=os.path.basename(file).split('-')[0]+ ' - Sample Site', value=file) for file in html_files
    ]),
    html.Div(id='tab-content')
])

# Define callback to update tab content
@app.callback(Output('tab-content', 'children'),
              [Input('tabs', 'value')])
def update_tab_content(selected_tab):
    if selected_tab is not None:
        with open(selected_tab, 'r') as f:
            html_content = f.read()
            return html.Iframe(srcDoc=html_content, style={'width': '100%', 'height': '90vh'})
    else:
        return "No tab selected"

# Define app layout
app.layout = html.Div([
    html.H1("Timeseries Dashboard"),
    tabs
])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
