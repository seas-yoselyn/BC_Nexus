import os
from jinja2 import Template

# Function to list HTML files in a directory
def list_html_files(directory):
    html_files = []
    for file in os.listdir(directory):
        if file.endswith(".html"):
            html_files.append(file)
    return html_files

# Function to read HTML content from file
def read_html_file(file_path):
    with open(file_path, "r") as file:
        return file.read()

# Function to generate combined HTML file
def generate_combined_html(directory):
    html_files = list_html_files(directory)
    html_content = {}
    for file_name in html_files:
        file_path = os.path.join(directory, file_name)
        html_content[file_name] = read_html_file(file_path)

    with open("combined.html", "w") as combined_file:
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Combined HTML</title>
            <style>
                #html_content {
                    width: 100%;
                    height: 500px;
                    overflow-y: auto;
                    border: 1px solid #ccc;
                    padding: 10px;
                }
                .hidden {
                    display: none;
                }
            </style>
        </head>
        <body>
            <label for="html_files">Select HTML file:</label>
            <select id="html_files" onchange="loadHtmlFile()">
                <option value="">Select a file</option>
                {% for file_name, content in html_content.items() %}
                    <option value="{{ file_name }}">{{ file_name }}</option>
                    <div id="{{ file_name|replace('.html', '_content') }}" class="hidden">
                        {{ content }}
                    </div>
                {% endfor %}
            </select>
            <div id="html_content">
                <!-- HTML content will be loaded here -->
            </div>

            <script>
            function loadHtmlFile() {
                var selectElement = document.getElementById("html_files");
                var selectedFile = selectElement.options[selectElement.selectedIndex].value;
                var selectedFileContent = document.getElementById(selectedFile.replace('.html', '_content'));
                var htmlContent = selectedFileContent ? selectedFileContent.innerHTML : "";
                document.getElementById("html_content").innerHTML = htmlContent;
            }
            </script>
        </body>
        </html>
        """)
        combined_file.write(template.render(html_content=html_content))



# Directory containing HTML files
html_directory = "scenario_plots"

# Generate combined HTML file
generate_combined_html(html_directory)
