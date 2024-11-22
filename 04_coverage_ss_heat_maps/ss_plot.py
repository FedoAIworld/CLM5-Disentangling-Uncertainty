import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
plt.rcParams.update({'font.size' : 16})

# Load the dataset from the specified directory
output_dir = "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/ss_ratio/all_periods/"
input_dir  = "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/ss_ratio/all_periods/"
file_path = os.path.join(input_dir, 'ss_combined.csv')
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
    (1.0, 0.4, 0.4),  # red for Underdispersed (<=0.5)
    (1.0, 0.8, 0.4),  # orange/yellow for Overdispersed (>1)
    (0.4, 0.8, 0.4)   # green for Calibrated (0.6 to 1)
])
# Normalize the data into categories to match the color range
def ss_category(val):
    if pd.isna(val):
        return 0  # Keep NaN as is (no category assigned, just NaN)
    elif  0.6 <= val <= 1:
        return 3  # Captures prediction uncertainty (Good capture)
    elif val > 1:
        return 2  # Spread larger than prediction error(overestimation)
    else:
        return 1  # Spread lower than prediction error (underestimation)

# Apply the coverage category function to the dataset
data_categorized = data_rounded.map(ss_category)

# Replace NaN values with "No Data" for annotations
annot_data = data_rounded.fillna("No Data")

# Create the heatmap without annotations and without a color bar
plt.figure(figsize=(10, 8))
ax = sns.heatmap(data_categorized, cmap=cmap, linewidths=0.8, annot=annot_data, fmt='', cbar=False) 
plt.title('Spread-Skill Ratio of the Combined Perturbation')

# Create the custom color bar on top
cbar = plt.colorbar(ax.collections[0], orientation="horizontal", pad=0.1, aspect=50)

# Set the color bar ticks and labels
cbar.set_ticks([0.375, 1.125, 1.875, 2.625]) # for forcings: 0.25, 0.75 
cbar.set_ticklabels(['No Data', 'Underdispersed', 'Overdispersed', 'Calibrated'])# , 'Overdispersed', 'Calibrated'

# Save the plot to the output directory
output_path = os.path.join(output_dir, 'combined_ss_heatmap.png')
plt.savefig(output_path, dpi=600)