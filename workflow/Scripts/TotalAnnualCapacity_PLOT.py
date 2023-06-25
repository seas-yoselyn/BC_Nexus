import os
import pandas as pd
import matplotlib.pyplot as plt


directory_path = r"/home/eliasinul/BC-Nexus-Snakemake/res/csv"
filename= "TotalCapacityAnnual.csv"
file= os.path.join(directory_path, filename)
df = pd.read_csv(file)
# Define the technologies of interest
technologies = ['PWRBIO', 'PWRHYD', 'PWRSOL', 'PWRNGS', 'PWRGEO', 'PWRURN']

# Create an empty dictionary to store the yearly summed values for each technology
yearly_summed_values = {}

# Iterate over each technology
for technology in technologies:
    # Filter the dataframe based on technology
    filtered_df = df[df['t'].str.startswith(technology)]
    
    # Group the filtered dataframe by year and sum the capacity for each year
    yearly_sum = filtered_df.groupby('y')['TotalCapacityAnnual'].sum()
    
    # Store the yearly summed capacity in the dictionary
    yearly_summed_values[technology] = yearly_sum

# Generate a plot for the yearly summed values for each technology
for technology, yearly_sum in yearly_summed_values.items():
    plt.bar(yearly_sum.index, yearly_sum.values, label=technology)

# Add labels and title to the plot
plt.xlabel('Year')
plt.ylabel('Summed Capacity (GW)')
plt.title('Yearly Summed Capacity for Different Technologies')

# Add a legend
plt.legend()

# Set the output directory path
output_directory = "./docs/Results_plots"

# Create the directory if it doesn't exist
os.makedirs(output_directory, exist_ok=True)

# Save the plot as a PNG file in the specified directory
output_file = os.path.join(output_directory, "yearly_capacity.png")
plt.savefig(output_file)
# Show the plot
# plt.show()
