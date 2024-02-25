import os
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.offline import plot

def combine_plots_for_dash(plots_html_directory, combined_plot_name):
    
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
    <title>CLEWs-BC results (case : REF)</title>
    <link rel="stylesheet" type="text/css" href="style.css">
    <style>
        /* Define styles for the headline */
        .headline {{
            font-size: 32px; /* Set the font size to 32 pixels */
            color: #00008B; /* Set the color to red (you can use any color code or name) */
        }}
    </style>
</head>
<body>
    <!-- Use the h1 tag for the headline and apply the "headline" class -->
    <h1 class="headline">CLEWs-BC results (case : REF)</h1>
"""

    for content in html_contents:
        combined_html += f"<div class='subplot'>{content}</div>"
    combined_html += "</body></html>"

    # Save the combined HTML content as a single HTML file
    with open(combined_plot_name, 'w') as file:
        file.write(combined_html)

def create_style_css(file_path):
    css_content = """
    /* Add borders to subplots */
.subplot {
    width: 45%; /* Adjust width as needed */
    height: auto;
    display: inline-block;
    margin: 2px;
    vertical-align: top;
    border: 1px solid #ccc; /* Add a solid border with a light gray color */
    padding: 10px; /* Add padding inside the subplot */
}

/* Add box shadows to subplots */
.subplot {
    width: 45%; /* Adjust width as needed */
    height: auto;
    display: inline-block;
    margin: 2px;
    vertical-align: top;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.1); /* Add a subtle box shadow */
    padding: 10px; /* Add padding inside the subplot */
}

/* Add grid lines to subplots */
.subplot {
    width: 45%; /* Adjust width as needed */
    height: auto;
    display: inline-block;
    margin: 2px;
    vertical-align: top;
    border: 1px solid #ccc; /* Add a solid border with a light gray color */
    padding: 10px; /* Add padding inside the subplot */
}

.subplot table {
    border-collapse: collapse; /* Collapse table borders */
}

.subplot th, .subplot td {
    border: 1px solid #ddd; /* Add borders to table cells */
    padding: 8px; /* Add padding to table cells */
}

    """
    with open(file_path, 'w') as file:
        file.write(css_content)

if __name__ == "__main__":
    plots_html_directory = "docs/Results_plots"
    index_html_directory='/home/eliasinul/repositories/BC-CLEWS-Model/index.html'
    combine_plots_for_dash(plots_html_directory, index_html_directory)
    style_css_directory='/home/eliasinul/repositories/BC-CLEWS-Model/style.css'
    create_style_css(style_css_directory)
    print(f"Interactive Dashboard Created and saved as index.html. \nstyle.css file created")
