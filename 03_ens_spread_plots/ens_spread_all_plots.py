import os
import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size' : 20})

# Function to load data from CSV files
def load_data(filepaths):
    data = {}
    for site, filepath in filepaths.items():
        df = pd.read_csv(filepath, parse_dates=['datetime'])
        df['datetime'] = pd.to_datetime(df['datetime'], format='%Y-%m-%d')
        data[site] = df
    return data 

# Define file paths
filepaths = {
    'FI-Hyy': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SMR/fi_hyy.csv",
    'FI-Sod': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SMR/fi_sod.csv",
    #'SE-Svb': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SMR/se_svb.csv",
    'CZ-BK1': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SMR/cz_bk1.csv",
    'DE-Obe': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SMR/de_obe.csv",
    'DE-RuW': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SMR/de_ruw.csv",
    'IT-Lav': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SMR/it_lav.csv",
    'NL-Loo': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SMR/nl_loo.csv",
    #'ES-Cnd': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SMR/es_cnd.csv",
    'FR-Pue': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SMR/fr_pue.csv",
    'DE-Hai': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SMR/de_hai.csv",
    'DE-HoH': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SMR/de_hoh.csv",
    'DK-Vng': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SMR/dk_vng.csv",
    'BE-Bra': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SMR/be_bra.csv"
}

# Output directory
output_dir = "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SMR/one_plot"
os.makedirs(output_dir, exist_ok=True)

# Function to load data from CSV files
def load_data(filepaths):
    data = {}
    for site, filepath in filepaths.items():
        df = pd.read_csv(filepath, parse_dates=['datetime'])
        df['datetime'] = pd.to_datetime(df['datetime'], format='%Y-%m-%d')
        data[site] = df
    return data

# Load the available data
data = load_data(filepaths)

# Define the y-axis limits based on the observation suffix
obs_suffix = 'SMR'
var   = 'SMR'
label = 'SMr'
unit = " (%)"

# Determine the appropriate y-axis limits dictionary
if obs_suffix == 'ET':
    ylimits = {
        'FI-Hyy': [-1.0, 8], 'FI-Sod': [-0.5, 8], 'SE-Svb': [-0.5, 8], 'CZ-BK1': [-0.5, 8], 
        'DE-Obe': [-0.5, 8], 'DE-RuW': [-0.7, 8], 'IT-Lav': [-0.5, 8], 'NL-Loo': [-0.5, 8], 
        'ES-Cnd': [-0.3, 8], 'FR-Pue': [0, 8], 'DE-Hai': [-0.5, 8], 'DE-HoH': [-0.5, 8], 
        'DK-Vng': [-0.5, 8], 'BE-Bra': [-0.5, 8]
    }
elif obs_suffix == 'NEE_VUT_REF':
    ylimits = {
        'FI-Hyy': [-12, 10], 'FI-Sod': [-12, 10], 'SE-Svb': [-12, 10], 'CZ-BK1': [-12, 10], 
        'DE-Obe': [-12, 10], 'DE-RuW': [-12, 10], 'IT-Lav': [-12, 10], 'NL-Loo': [-12, 10], 
        'ES-Cnd': [-12, 10], 'FR-Pue': [-12, 10], 'DE-Hai': [-12, 10], 'DE-HoH': [-12, 10], 
        'DK-Vng': [-12, 10], 'BE-Bra': [-12, 10]
    }
elif obs_suffix == 'H_F_MDS':
    ylimits = {
        'FI-Hyy': [-110, 200], 'FI-Sod': [-110, 200], 'SE-Svb': [-110, 200], 'CZ-BK1': [-110, 200], 
        'DE-Obe': [-110, 200], 'IT-Lav': [-110, 200], 'NL-Loo': [-110, 200], 'ES-Cnd': [-110, 200], 
        'FR-Pue': [-110, 200], 'DE-Hai': [-110, 200], 'DE-HoH': [-110, 200], 'DK-Vng': [-110, 200], 
        'BE-Bra': [-110, 200]
    }
elif obs_suffix == 'GPP_NT_VUT_REF':
    ylimits = {
        'FI-Hyy': [-0.5, 20], 'FI-Sod': [-0.5, 20], 'SE-Svb': [-0.5, 20], 'CZ-BK1': [-0.5, 20], 
        'DE-Obe': [-0.7, 20], 'DE-RuW': [-0.5, 20], 'IT-Lav': [-0.5, 20], 'NL-Loo': [-0.5, 20], 
        'FR-Pue': [-0.5, 20], 'DE-Hai': [-0.5, 20], 'DE-HoH': [-0.7, 20], 'BE-Bra': [-0.5, 20]
    }
elif obs_suffix == 'SM':
    ylimits = {
        'FI-Hyy': [8, 100], 'FI-Sod': [0, 100], 'CZ-BK1': [0, 100], 'DE-Obe': [0, 100], 
        'DE-RuW': [10, 100], 'IT-Lav': [0, 100], 'NL-Loo': [0, 100], 'FR-Pue': [0, 100], 
        'DE-Hai': [0, 100], 'DE-HoH': [0, 100], 'DK-Vng': [10, 100], 'BE-Bra': [0, 100]
    }
elif obs_suffix == 'SMR':
    ylimits = {
        'FI-Hyy': [0, 100], 'FI-Sod': [0, 100], 'CZ-BK1': [0, 100], 'DE-Obe': [0, 100], 
        'DE-RuW': [10, 100], 'IT-Lav': [0, 100], 'NL-Loo': [0, 100], 'FR-Pue': [0, 100], 
        'DE-Hai': [0, 100], 'DE-HoH': [0, 100], 'DK-Vng': [10, 100], 'BE-Bra': [0, 100]
    }
else:
    ylimits = {}

# Define the figure and axes
fig, axes = plt.subplots(12, 4, figsize=(30, 40), sharey=True, dpi=400)
fig.subplots_adjust(hspace=0.8, wspace=0.2)
perturb_group = ['forcing', 'soil', 'veg', 'combined']
plot_titles = ['Forcing', 'Soil', 'Vegetation', 'Combined']

def generate_label(index):
    """Generate subplot labels extending beyond single alphabet (a, b, ..., z, aa, ab, ...)"""
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    if index < len(alphabet):
        return alphabet[index]
    else:
        return generate_label(index // len(alphabet) - 1) + alphabet[index % len(alphabet)]


# Plotting data
plot_index = 0
for idx, (site, df) in enumerate(data.items()):
    for i, perturb in enumerate(perturb_group):
        ax = axes[idx, i]
        lower_bound = f'{perturb}_{site}_lb'
        upper_bound = f'{perturb}_{site}_ub'
        observation = f'{site}_{obs_suffix}'
        
        ax.fill_between(df['datetime'], df[lower_bound], df[upper_bound], color='#f03b20', alpha=0.3)
        ax.plot(df['datetime'], df[observation], marker='o', markersize=3, linestyle='--', color='black')
        
        if site in ylimits:
            ax.set_ylim(ylimits[site])
        
        ax.set_title(f'{site} - {plot_titles[i]}', fontsize=16, loc='left') #, fontweight='bold'
        
        # Add alphabet labels on the top-right side of each subplot
        ax.text(0.95, 0.95, f'({generate_label(plot_index)})', transform=ax.transAxes, fontsize=12, verticalalignment='top', horizontalalignment='right')
        plot_index += 1
        
        # Increase tick parameters for better visibility
        ax.tick_params(axis='x', labelsize=16, rotation=20)
        ax.tick_params(axis='y', labelsize=16)
        ax.grid(True)
        #ax.tick_params(axis='x', rotation=20)
        #ax.grid(True)
    
    # Add y-label for each panel
    axes[idx, 0].set_ylabel(label + unit, fontsize=16)


# Save the figure
output_path = os.path.join(output_dir, f'all_sites_{var}_plot.png')
fig.savefig(output_path, bbox_inches='tight')
plt.close(fig)
