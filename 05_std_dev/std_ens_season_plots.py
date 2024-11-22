#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
plt.rcParams.update({'font.size' : 18})
import pandas as pd
import numpy as np
import os


# List of sites
sites = ['FI-Hyy', 'FI-Sod', 'SE-Svb', 'CZ-BK1', 'DE-Obe', 'DE-RuW', 'IT-Lav', 
         'NL-Loo', 'ES-Cnd', 'FR-Pue', 'DE-Hai', 'DE-HoH', 'DK-Vng', 'BE-Bra']

legend_mapping = {
    'forcing': 'Perturbed atmospheric forcing',
    'soil': 'Perturbed soil parameters',
    'veg': 'Perturbed vegetation parameters',
    'combined': 'Combined perturbation'
}

xtick_labels = ['Forcing', 'Soil', 'Vegetation', 'Combined']

# Define custom colors
custom_colors = ['#3182bd', '#9ecae1', '#2ca25f', '#FF0000']

# Function to load data from CSV files
def load_data():
    filepaths = {
        'FI-Hyy': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/GPP/FI-Hyy.csv",
        'FI-Sod': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/GPP/FI-Sod.csv",
        'SE-Svb': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/GPP/SE-Svb.csv",
        'CZ-BK1': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/GPP/CZ-BK1.csv",
        'DE-Obe': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/GPP/DE-Obe.csv",
        'DE-RuW': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/GPP/DE-RuW.csv",
        'IT-Lav': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/GPP/IT-Lav.csv",
        'NL-Loo': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/GPP/NL-Loo.csv",
        'ES-Cnd': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/GPP/ES-Cnd.csv",
        'FR-Pue': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/GPP/FR-Pue.csv",
        'DE-Hai': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/GPP/DE-Hai.csv",
        'DE-HoH': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/GPP/DE-HoH.csv",
        'DK-Vng': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/GPP/DK-Vng.csv",
        'BE-Bra': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/GPP/BE-Bra.csv"
    }
    
    data = {}
    for site, filepath in filepaths.items():
        df = pd.read_csv(filepath, parse_dates=['datetime'])
        df['datetime'] = pd.to_datetime(df['datetime'], format='%Y-%m-%d')
        data[site] = df
    
    return data

# Function to assign seasons
def assign_season(month):
    if month in [12, 1, 2]:
        return 'Winter'
    elif month in [3, 4, 5]:
        return 'Spring'
    elif month in [6, 7, 8]:
        return 'Summer'
    elif month in [9, 10, 11]:
        return 'Fall'
    
# Load the data
data = load_data()

# Create directory for plots if it doesn't exist
plot_dir = "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/std_dev/GPP/season_plots"
if not os.path.exists(plot_dir):
    os.makedirs(plot_dir)

# Add season column and combine data from all sites
all_data = pd.DataFrame()

for site, df in data.items():
    df['season'] = df['datetime'].dt.month.apply(assign_season)
    df['site'] = site
    all_data = pd.concat([all_data, df], ignore_index=True)

# Ensure only numeric columns are selected for averaging
numeric_columns = ['forcing', 'soil', 'veg', 'combined']

# Calculate the average standard deviation across all sites grouped by perturbation groups and seasons
avg_std_devs = all_data.groupby(['season'])[numeric_columns].mean()

# Reorder the seasons to be in Spring, Summer, Fall, Winter order
season_order = ['Spring', 'Summer', 'Fall', 'Winter']
avg_std_devs = avg_std_devs.loc[season_order]

# Plot the average standard deviation across all sites grouped by perturbation groups and seasons
plt.figure(figsize=(12, 6))
avg_std_devs.plot(kind='bar', color=custom_colors, figsize=(12, 6), legend=False)
#plt.title('Average Standard Deviation by Season and Perturbation Groups Across All Sites')
plt.xlabel('Season')
plt.ylabel(r'Avg $\sigma$ (gC m$^{-2}$ d$^{-1}$)')
plt.xticks(rotation=0)
plt.grid(True)

# Save the average standard deviation plot
avg_plot_filepath = os.path.join(plot_dir, "all_sites_seasonal_avg_std_dev_plot.png")
plt.tight_layout()
plt.savefig(avg_plot_filepath, bbox_inches='tight', dpi=600)
plt.close()

# Plotting and saving box plots for each site grouped by perturbation groups and seasons
for site, df in data.items():
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Ensure the seasons are ordered
    season_order = ['Spring', 'Summer', 'Fall', 'Winter']
    
    # Prepare the data for boxplot
    box_data = []
    positions = []
    ticks = []
    for i, season in enumerate(season_order):
        for col in ['forcing', 'soil', 'veg', 'combined']:
            box_data.append(df[df['season'] == season][col].dropna())
        positions.extend([i * 5 + j for j in range(1, 5)])  # Separate groups visually
        ticks.append(i * 5 + 2.5)  # Position label in the middle of the group
    
    # Create box plot
    bp = ax.boxplot(box_data, positions=positions, patch_artist=True, notch=True, vert=True, widths=0.7)
    
    # Apply custom colors to the boxes based on the perturbation group
    for i, patch in enumerate(bp['boxes']):
        patch.set_facecolor(custom_colors[i % len(custom_colors)])
    
    # Customizing whiskers
    for whisker in bp['whiskers']:
        whisker.set(color='#8B008B', linewidth=1.5, linestyle=":")
    
    # Customizing caps
    for cap in bp['caps']:
        cap.set(color='#8B008B', linewidth=2)
    
    # Customizing medians
    for median in bp['medians']:
        median.set(color='black', linewidth=3)
    
    # Customizing fliers
    for flier in bp['fliers']:
        flier.set(marker='D', color='#e7298a', alpha=0.5)
    
    # Adjust y-axis limit to start from the minimum whisker value
    y_min = min([item.get_ydata()[1] for item in bp['whiskers']])
    ax.set_ylim(bottom=y_min)
    
    # Set title, labels, and ticks
    plt.title(f'{site}', loc='left')
    plt.xlabel('Season')
    plt.ylabel(r'$\sigma$ (gC m$^{-2}$ d$^{-1}$)')
    ax.set_xticks(ticks)
    ax.set_xticklabels(season_order, rotation=0)
    
    # Save plot
    plot_filename = f"{site}_seasonal_grouped_std_dev_boxplot.png"
    plot_filepath = os.path.join(plot_dir, plot_filename)
    plt.tight_layout()
    plt.savefig(plot_filepath, bbox_inches='tight', dpi=600)
    plt.close()
    
    print(f"Saved plot for {site}: {plot_filepath}")