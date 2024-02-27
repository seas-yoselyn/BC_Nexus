import os
import utilities as utils

def combine_plots_for_dash(plots_html_directory, combined_plot_name,title,font_size,font_color):
    # Ensure the plots HTML directory exists
    if not os.path.exists(plots_html_directory):
        print(f"Error: {plots_html_directory} does not exist.")
        return

    plot_html_files = [f for f in os.listdir(plots_html_directory) if f.endswith('.html')]
    if not plot_html_files:
        print("Error: No HTML plot files found in the specified directory.")
        return

    # Read the content of each HTML plot file
    html_contents = []
    for file_name in plot_html_files:
        file_path = os.path.join(plots_html_directory, file_name)
        with open(file_path, 'r') as file:
            html_contents.append(file.read())

    # Combine HTML content into a single HTML file with subplots

    combined_html = f"""
    <html>
    <head>
        <title>{title}</title>
        <link rel="stylesheet" type="text/css" href="style.css">
        <style>
            /* Define styles for the headline */
            .headline {{
                font-size: {font_size}; /* Set the font size */
                color: {font_color}; /* Set the color */
            }}
        </style>
    </head>
    <body>
        <!-- Use the h1 tag for the headline and apply the "headline" class -->
        <h1 class="headline">{title}</h1>
    """

    for content in html_contents:
        combined_html += f"<div class='subplot'>{content}</div>"
    combined_html += "</body></html>"

    # Save the combined HTML content as a single HTML file
    with open(combined_plot_name, 'w') as file:
        file.write(combined_html)
    print(f"Interactive Dashboard Created and saved as {combined_plot_name}.")

def create_style_css(file_path, width, height):
    # Define common style for subplot
    css_content = f"""
    .subplot {{
        width: {width};
        height: {height};
        display: inline-block;
        margin: 5px 8px;
        vertical-align: top;
        padding: 10px;
        border: 1px solid #ccc;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }}

    /* Add grid lines to subplots */
    .subplot table {{
        border-collapse: collapse;
    }}

    .subplot th, .subplot td {{
        border: 1px solid #ddd;
        padding: 8px;
    }}
    """

    with open(file_path, 'w') as file:
        file.write(css_content)
    print(f"Style CSS file created at {file_path}.")

if __name__ == "__main__":
    visual_configs = utils.load_config('config/visualization_config.yaml')
    title=visual_configs['interactive_dashboard']['title']
    font_size=visual_configs['interactive_dashboard']['font_size']
    font_color=visual_configs['interactive_dashboard']['font_color']
    width=visual_configs['interactive_dashboard']['plot_width']
    height=visual_configs['interactive_dashboard']['plot_height']

    plots_html_directory = "docs/Results_plots"
    index_html_directory = visual_configs['interactive_dashboard']['index_html_directory']
    style_css_directory = visual_configs['interactive_dashboard']['style_css_directory']

    combine_plots_for_dash(plots_html_directory, index_html_directory,title,font_size,font_color)
    create_style_css(style_css_directory,width, height)
