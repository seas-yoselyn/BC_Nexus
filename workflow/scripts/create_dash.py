import os
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.offline import plot

def combine_plots_for_dash(plots_html_directory,combined_plot_name):
    
    html_files = [f for f in os.listdir(plots_html_directory) if f.endswith('.html')]

    # Read the content of each HTML plot file
    html_contents = []
    for file_name in html_files:
        file_path = os.path.join(plots_html_directory, file_name)
        with open(file_path, 'r') as file:
            html_contents.append(file.read())

    # Combine HTML content into a single HTML file with subplots
    combined_html = f"""
   <html>
<head>
    <title>CLEWs Kenya (preliminary results)</title>
    <link rel="stylesheet" type="text/css" href="style.css">
</head>
<body>
    <div class='title'>CLEWS Kenya (preliminary results)</div>
"""

    for content in html_contents:
        combined_html += f"<div class='subplot'>{content}</div>"
    combined_html += "</body></html>"

    # Save the combined HTML content as a single HTML file
    with open(combined_plot_name, 'w') as file:
        return file.write(combined_html)

def create_style_css(file_path):
    css_content = """
    .subplot {
        width: 45%; /* Adjust width as needed */
        display: inline-block;
        margin: 2px;
        vertical-align: top;
    }
    .title {
        font-weight: bold;
        font-size: 24px;
        text-align: center;
        margin-bottom: 0px;
    }
    """
    with open(file_path, 'w') as file:
        file.write(css_content)

if __name__ == "__main__":
    plots_html_directory = "docs/Results_plots"
    combine_plots_for_dash(plots_html_directory, 'index.html')
    create_style_css("style.css")
    print(f"Interactive Dashboard Created and saved as index.html. \nstyle.css file created")
