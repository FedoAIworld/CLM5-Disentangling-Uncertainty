import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
plt.rcParams.update({'font.size' : 16})

# Load the dataset from the specified directory
output_dir = "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/coverage_plots/all_periods/"
input_dir  = "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/coverage_plots/all_periods/"
file_path = os.path.join(input_dir, 'combined_coverage_percentage.csv')
data = pd.read_csv(file_path)

# Ensure the output directory exists, and if not, create it
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Rename the column 'Smr' to 'SMr'
data = data.rename(columns={'Smr': 'SMr'})

# Round the values to 1 decimal place and set 'Site' as the index
data_rounded = data.set_index('Site').round(1)

# Define custom color map for different coverage levels
cmap = sns.color_palette([
    (0.9, 0.9, 0.9),  # light gray for NaN (missing data)
    (1.0, 0.4, 0.4),  # red for poor (0-50)
    (1.0, 0.8, 0.4),  # orange/yellow for moderate (60-90)
    (0.4, 0.8, 0.4)   # green for good (90-100)
])
# Normalize the data into categories to match the color range
def coverage_category(val):
    if pd.isna(val):
        return 0  # Keep NaN as is (no category assigned, just NaN)
    #elif val >= 90:
    #    return 3  # Good coverage (90-100)
    elif val >= 50:
        return 2  # Moderate coverage (60-90)
    else:
        return 1  # Poor coverage (0-50)

# Apply the coverage category function to the dataset
data_categorized = data_rounded.map(coverage_category)

# Replace NaN values with "No Data" for annotations
annot_data = data_rounded.fillna("No Data")

# Create the heatmap without annotations and without a color bar
plt.figure(figsize=(10, 8))
ax = sns.heatmap(data_categorized, cmap=cmap, linewidths=0.8, annot=annot_data, fmt='', cbar=False) 
plt.title('Coverage Percentages of the Combined Perturbation')

# Create the custom color bar on top
cbar = plt.colorbar(ax.collections[0], orientation="horizontal", pad=0.1, aspect=50)

# Set the color bar ticks and labels
cbar.set_ticks([0.375, 1.125, 1.875, 2.625])
cbar.set_ticklabels(['No Data', 'Poor', 'Moderate', 'Good'])

# Save the plot to the output directory
output_path = os.path.join(output_dir, 'combined_coverage_heatmap.png')
plt.savefig(output_path, dpi=600)

#plt.show()