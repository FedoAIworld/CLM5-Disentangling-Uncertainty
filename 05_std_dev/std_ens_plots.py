#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
plt.rcParams.update({'font.size' : 16})
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
        'FI-Hyy': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/ET/FI-Hyy.csv",
        'FI-Sod': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/ET/FI-Sod.csv",
        'SE-Svb': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/ET/SE-Svb.csv",
        'CZ-BK1': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/ET/CZ-BK1.csv",
        'DE-Obe': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/ET/DE-Obe.csv",
        'DE-RuW': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/ET/DE-RuW.csv",
        'IT-Lav': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/ET/IT-Lav.csv",
        'NL-Loo': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/ET/NL-Loo.csv",
        'ES-Cnd': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/ET/ES-Cnd.csv",
        'FR-Pue': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/ET/FR-Pue.csv",
        'DE-Hai': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/ET/DE-Hai.csv",
        'DE-HoH': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/ET/DE-HoH.csv",
        'DK-Vng': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/ET/DK-Vng.csv",
        'BE-Bra': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/ET/BE-Bra.csv"
    }
    
    data = {}
    for site, filepath in filepaths.items():
        df = pd.read_csv(filepath, parse_dates=['datetime'])
        df['datetime'] = pd.to_datetime(df['datetime'], format='%Y-%m-%d')
        data[site] = df
    
    return data

# Load the data
data = load_data()

# Create directory for plots if it doesn't exist
plot_dir = "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_128/std_dev/ET/plots"
if not os.path.exists(plot_dir):
    os.makedirs(plot_dir)

# Calculate and plot the average standard deviation for each site
for site, df in data.items():
    # Calculate the average standard deviation for each perturbation group
    avg_std_devs = df[['forcing', 'soil', 'veg', 'combined']].mean()

    # Plot the average standard deviation
    plt.figure(figsize=(10, 6))
    avg_std_devs.plot(kind='bar', color=custom_colors)
    plt.title(f'Average Standard Deviation for {site}')
    plt.xlabel('Perturbation Groups')
    plt.ylabel(r'Avg $\sigma$ (mm d$^{-1}$)')
    plt.xticks(range(len(avg_std_devs)), xtick_labels, rotation=0)
    plt.grid(True)

    # Save the plot
    plot_filename = f"{site}_average_std_dev_plot.png"
    plot_filepath = os.path.join(plot_dir, plot_filename)
    plt.tight_layout()
    plt.savefig(plot_filepath, bbox_inches='tight')
    plt.close()

# Plotting and saving box plots for each site
for site, df in data.items():
    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(111)
    
    # Extract columns for box plot
    columns = [col for col in df.columns if col != 'datetime']
    box_data = [df[col].dropna() for col in columns]
    
    # Create box plot
    bp = ax.boxplot(box_data, patch_artist=True, notch=True, vert=True)
    
    # Apply custom colors to the boxes
    for patch, color in zip(bp['boxes'], custom_colors):
        patch.set_facecolor(color)
    
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
    
    # Set title, labels, and ticks
    plt.title(f'{site}', loc='left')
    plt.xlabel('Perturbation Groups')
    plt.ylabel(r'$\sigma$ (mm d$^{-1}$)')
    ax.set_xticklabels(['Forcing', 'Soil', 'Vegetation', 'Combined'])
    
    # Custom legend
    handles = [plt.Line2D([0], [0], color=color, lw=4) for color in custom_colors]
    labels = [legend_mapping.get(col, col) for col in columns]
    ax.legend(handles, labels, loc='upper left', bbox_to_anchor=(1, 1))
    
    # Save plot
    plot_filename = f"{site}_std_dev_boxplot.png"
    plot_filepath = os.path.join(plot_dir, plot_filename)
    plt.savefig(plot_filepath, bbox_inches='tight')
    plt.close()
    
    print(f"Saved plot for {site}: {plot_filepath}")