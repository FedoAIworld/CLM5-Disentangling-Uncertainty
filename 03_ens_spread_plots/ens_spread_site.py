import os
import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size' : 16})



# Function to load data from CSV files

filepaths = {
    'FI-Hyy': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SH/fi_hyy.csv",
    'FI-Sod': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SH/fi_sod.csv",
    'SE-Svb': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SH/se_svb.csv",
    'CZ-BK1': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SH/cz_bk1.csv",
    'DE-Obe': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SH/de_obe.csv",
    #'DE-RuW': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SH/de_ruw.csv",
    'IT-Lav': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SH/it_lav.csv",
    'NL-Loo': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SH/nl_loo.csv",
    'ES-Cnd': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SH/es_cnd.csv",
    'FR-Pue': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SH/fr_pue.csv",
    'DE-Hai': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SH/de_hai.csv",
    'DE-HoH': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SH/de_hoh.csv",
    'DK-Vng': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SH/dk_vng.csv",
    'BE-Bra': "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SH/be_bra.csv"
}

# Output directory
output_dir = "/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/ens_first_manuscript/main_effects/SH/plots"
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

#labels         = ['Evapotranspiration', 'GPP', 'NEE', 'H', r'$\theta$', r'Root zone $\theta$']
#units          = [" (mm d$^{-1}$)", " (gC m$^{-2}$ d$^{-1}$)", " (gC m$^{-2}$ d$^{-1}$)", " (Wm$^{-2}$)", " (%)"]
#obs_var_suffix = ['ET', 'GPP_NT_VUT_REF','NEE_VUT_REF','H_F_MDS', 'SM', 'SMR']

obs_suffix = 'H_F_MDS'
var        = 'H'
label      = 'H'
unit       = " (Wm$^{-2}$)"

# Determine the appropriate y-axis limits dictionary
if obs_suffix == 'ET':
    ylimits = {
        'FI-Hyy': [-1.0, 6], 'FI-Sod': [-0.5, 4], 'SE-Svb': [-0.5, 5], 'CZ-BK1': [-0.5, 5], 
        'DE-Obe': [-0.5, 4], 'DE-RuW': [-0.7, 5], 'IT-Lav': [-0.5, 5], 'NL-Loo': [-0.5, 4], 
        'ES-Cnd': [-0.3, 5], 'FR-Pue': [0, 6], 'DE-Hai': [-0.5, 6], 'DE-HoH': [-0.5, 5], 
        'DK-Vng': [-0.5, 5], 'BE-Bra': [-0.5, 5]
    }
elif obs_suffix == 'NEE_VUT_REF':
    ylimits = {
        'FI-Hyy': [-10, 8], 'FI-Sod': [-10.5, 6], 'SE-Svb': [-10, 10], 'CZ-BK1': [-7, 5], 
        'DE-Obe': [-6, 4], 'DE-RuW': [-8, 6], 'IT-Lav': [-12, 6], 'NL-Loo': [-8, 8], 
        'ES-Cnd': [-8, 6], 'FR-Pue': [-10, 8], 'DE-Hai': [-12, 8], 'DE-HoH': [-12, 8], 
        'DK-Vng': [-10.5, 4.5], 'BE-Bra': [-7, 4]
    }
elif obs_suffix == 'H_F_MDS':
    ylimits = {
        'FI-Hyy': [-70, 100], 'FI-Sod': [-110, 120], 'SE-Svb': [-60, 120], 'CZ-BK1': [-70, 110], 
        'DE-Obe': [-70, 125], 'DE-RuW': [-80, 125], 'IT-Lav': [-60, 150], 'NL-Loo': [-70, 125], 
        'ES-Cnd': [-60, 200], 'FR-Pue': [-70, 150], 'DE-Hai': [-80, 125], 'DE-HoH': [-55, 150], 
        'DK-Vng': [-50, 70], 'BE-Bra': [-76, 120]
    }
elif obs_suffix == 'GPP_NT_VUT_REF':
    ylimits = {
        'FI-Hyy': [-0.5, 20], 'FI-Sod': [-0.5, 20], 'SE-Svb': [-0.5, 20], 'CZ-BK1': [-0.5, 15], 
        'DE-Obe': [-0.7, 13], 'DE-RuW': [-0.5, 15], 'IT-Lav': [-0.5, 15], 'NL-Loo': [-0.5, 14], 
        'FR-Pue': [-0.5, 20], 'DE-Hai': [-0.5, 20], 'DE-HoH': [-0.7, 19], 'BE-Bra': [-0.5, 14]
    }
elif obs_suffix == 'SM':
    ylimits = {
        'FI-Hyy': [8, 100], 'FI-Sod': [0, 100], 'CZ-BK1': [0, 80], 'DE-Obe': [0, 75], 
        'DE-RuW': [10, 85], 'IT-Lav': [0, 80], 'NL-Loo': [0, 70], 'FR-Pue': [0, 80], 
        'DE-Hai': [0, 80], 'DE-HoH': [0, 70], 'DK-Vng': [10, 70], 'BE-Bra': [0, 80]
    }
elif obs_suffix == 'SMR':
    ylimits = {
        'FI-Hyy': [0, 60], 'FI-Sod': [0, 80], 'CZ-BK1': [0, 50], 'DE-Obe': [0, 40], 
        'DE-RuW': [10, 60], 'IT-Lav': [0, 50], 'NL-Loo': [0, 50], 'FR-Pue': [0, 60], 
        'DE-Hai': [0, 60], 'DE-HoH': [0, 60], 'DK-Vng': [10, 60], 'BE-Bra': [0, 60]
    }
else:
    ylimits = {}



# Plot the ensemble spread against observation for each site
for site, df in data.items():
    fig, axes = plt.subplots(2, 2, figsize=(15, 12), sharey=True)
    perturb_group = ['forcing', 'soil', 'veg', 'combined']
    plot_titles = ['Perturbed Atmospheric Forcings', 'Perturbed Soil Parameters', 'Perturbed Vegetation Parameters', 'Combined Perturbation']
    
    for i, perturb in enumerate(perturb_group):
        ax = axes[i // 2, i % 2]
        lower_bound = f'{perturb}_{site}_lb'
        upper_bound = f'{perturb}_{site}_ub'
        observation = f'{site}_{obs_suffix}'
        
        ax.fill_between(df['datetime'], df[lower_bound], df[upper_bound], color='#f03b20', alpha=0.3, label='Ens. Spread (min-max)')
        ax.plot(df['datetime'], df[observation], marker='o', markersize=5, linestyle='--', label='Observation', color='black')
        
        # Set y-axis limits if specified for the site
        if site in ylimits:
            ax.set_ylim(ylimits[site])

        ax.set_title(plot_titles[i])
        ax.tick_params(axis='x', rotation=20)
        ax.grid(True)

    # Set common labels
    fig.supxlabel('Date')
    fig.supylabel(label + unit)

    fig.suptitle(f'Ensemble Spread vs Observation for {site}')
    fig.tight_layout(rect=[0, 0, 0.85, 1])
    
    # Add the legend
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper left', bbox_to_anchor=(1, 1))
    
    # Save the figure
    output_path = os.path.join(output_dir, f'{site.lower()}_{var}_plot.png')
    fig.savefig(output_path, bbox_inches='tight', dpi=600)
    plt.close(fig)

