#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size' : 30})

from analysis_funcs import *

#all_surface_swc_mm.csv
#all_sm_root_mm.csv
#all_obs_data.csv

def load_data():
    # Read monthly obs data
    filepath_obs = "/home/fernand/Documents/ensemble_analysis/obs_data/all_obs_data.csv"
    obs_data = pd.read_csv(filepath_obs, parse_dates=['time'])
    obs_data['time'] = pd.to_datetime(obs_data['time'], format='%Y%m')

    # Path to monthly Ens. data
    filepath_fi_hyy = "/home/fernand/Documents/ensemble_analysis/ens_data/combined/ens_128/ET/FI-Hyy_aggregated.csv"
    filepath_fi_sod = "/home/fernand/Documents/ensemble_analysis/ens_data/combined/ens_128/ET/FI-Sod_aggregated.csv"
    filepath_cz_bk1 = "/home/fernand/Documents/ensemble_analysis/ens_data/combined/ens_128/ET/CZ-BK1_aggregated.csv"
    filepath_de_obe = "/home/fernand/Documents/ensemble_analysis/ens_data/combined/ens_128/ET/DE-Obe_aggregated.csv"
    filepath_de_ruw = "/home/fernand/Documents/ensemble_analysis/ens_data/combined/ens_128/ET/DE-RuW_aggregated.csv"
    filepath_it_lav = "/home/fernand/Documents/ensemble_analysis/ens_data/combined/ens_128/ET/IT-Lav_aggregated.csv"
    filepath_nl_loo = "/home/fernand/Documents/ensemble_analysis/ens_data/combined/ens_128/ET/NL-Loo_aggregated.csv"
    filepath_es_cnd = "/home/fernand/Documents/ensemble_analysis/ens_data/combined/ens_128/ET/ES-Cnd_aggregated.csv"
    filepath_fr_pue = "/home/fernand/Documents/ensemble_analysis/ens_data/combined/ens_128/ET/FR-Pue_aggregated.csv"
    filepath_de_hai = "/home/fernand/Documents/ensemble_analysis/ens_data/combined/ens_128/ET/DE-Hai_aggregated.csv"
    filepath_be_bra = "/home/fernand/Documents/ensemble_analysis/ens_data/combined/ens_128/ET/BE-Bra_aggregated.csv"
    #filepath_se_svb_test = "/home/fernand/Documents/ensemble_analysis/ens_data/combined/ens_128/SH/test_SE-Svb_aggregated.csv"
    #filepath_se_svb_old = "/home/fernand/Documents/ensemble_analysis/ens_data/combined/ens_128/SH/old_SE-Svb_aggregated.csv"
    #filepath_de_hoh_test = "/home/fernand/Documents/ensemble_analysis/ens_data/combined/ens_128/SMR/test_DE-HoH_aggregated.csv"
    #filepath_de_hoh_old  = "/home/fernand/Documents/ensemble_analysis/ens_data/combined/ens_128/SMR/old_DE-HoH_aggregated.csv"
    #filepath_dk_vng_test = "/home/fernand/Documents/ensemble_analysis/ens_data/forcing_soil/ens_128/SMR/test_DK-Vng_aggregated.csv"
    #filepath_dk_vng_old = "/home/fernand/Documents/ensemble_analysis/ens_data/forcing_soil/ens_128/SMR/old_DK-Vng_aggregated.csv"

    # Read CSV files and set time type
    fi_hyy_df = pd.read_csv(filepath_fi_hyy, parse_dates=['datetime'])
    fi_hyy_df['datetime'] = pd.to_datetime(fi_hyy_df['datetime'], format='%Y-%m-%d')
    
    fi_sod_df = pd.read_csv(filepath_fi_sod, parse_dates=['datetime'])
    fi_sod_df['datetime'] = pd.to_datetime(fi_sod_df['datetime'], format='%Y-%m-%d')

    cz_bk1_df = pd.read_csv(filepath_cz_bk1, parse_dates=['datetime'])
    cz_bk1_df['datetime'] = pd.to_datetime(cz_bk1_df['datetime'], format='%Y-%m-%d')
    
    de_obe_df = pd.read_csv(filepath_de_obe, parse_dates=['datetime'])
    de_obe_df['datetime'] = pd.to_datetime(de_obe_df['datetime'], format='%Y-%m-%d')
    
    de_ruw_df = pd.read_csv(filepath_de_ruw, parse_dates=['datetime'])
    de_ruw_df['datetime'] = pd.to_datetime(de_ruw_df['datetime'], format='%Y-%m-%d')
    
    it_lav_df = pd.read_csv(filepath_it_lav, parse_dates=['datetime'])
    it_lav_df['datetime'] = pd.to_datetime(it_lav_df['datetime'], format='%Y-%m-%d')
    
    nl_loo_df = pd.read_csv(filepath_nl_loo, parse_dates=['datetime'])
    nl_loo_df['datetime'] = pd.to_datetime(nl_loo_df['datetime'], format='%Y-%m-%d')
    
    es_cnd_df = pd.read_csv(filepath_es_cnd, parse_dates=['datetime'])
    es_cnd_df['datetime'] = pd.to_datetime(es_cnd_df['datetime'], format='%Y-%m-%d')

    fr_pue_df = pd.read_csv(filepath_fr_pue, parse_dates=['datetime'])
    fr_pue_df['datetime'] = pd.to_datetime(fr_pue_df['datetime'], format='%Y-%m-%d')
    
    de_hai_df = pd.read_csv(filepath_de_hai, parse_dates=['datetime'])
    de_hai_df['datetime'] = pd.to_datetime(de_hai_df['datetime'], format='%Y-%m-%d')

    be_bra_df = pd.read_csv(filepath_be_bra, parse_dates=['datetime'])
    be_bra_df['datetime'] = pd.to_datetime(be_bra_df['datetime'], format='%Y-%m-%d')

    #test_se_svb_df = pd.read_csv(filepath_se_svb_test, parse_dates=['datetime'])
    #test_se_svb_df['datetime'] = pd.to_datetime(test_se_svb_df['datetime'], format='%Y-%m-%d')
#
    #old_se_svb_df = pd.read_csv(filepath_se_svb_old, parse_dates=['datetime'])
    #old_se_svb_df['datetime'] = pd.to_datetime(old_se_svb_df['datetime'], format='%Y-%m-%d')

    #test_de_hoh_df = pd.read_csv(filepath_de_hoh_test, parse_dates=['datetime'])
    #test_de_hoh_df['datetime'] = pd.to_datetime(test_de_hoh_df['datetime'], format='%Y-%m-%d')
#
    #old_de_hoh_df = pd.read_csv(filepath_de_hoh_old, parse_dates=['datetime'])
    #old_de_hoh_df['datetime'] = pd.to_datetime(old_de_hoh_df['datetime'], format='%Y-%m-%d')
    
    #test_dk_vng_df = pd.read_csv(filepath_dk_vng_test, parse_dates=['datetime'])
    #test_dk_vng_df['datetime'] = pd.to_datetime(test_dk_vng_df['datetime'], format='%Y-%m-%d')
#
    #old_dk_vng_df = pd.read_csv(filepath_dk_vng_old, parse_dates=['datetime'])
    #old_dk_vng_df['datetime'] = pd.to_datetime(old_dk_vng_df['datetime'], format='%Y-%m-%d')

    return obs_data, fi_hyy_df, fi_sod_df, cz_bk1_df, de_obe_df, de_ruw_df, it_lav_df, nl_loo_df, es_cnd_df, fr_pue_df, de_hai_df, be_bra_df
    #return obs_data, test_se_svb_df, old_se_svb_df
    #return obs_data, test_de_hoh_df, old_de_hoh_df
    #return obs_data, test_dk_vng_df, old_dk_vng_df
    #es_cnd_df, 



def main():
    obs_data, fi_hyy_df, fi_sod_df, cz_bk1_df, de_obe_df, de_ruw_df, it_lav_df, nl_loo_df, es_cnd_df, fr_pue_df, de_hai_df, be_bra_df = load_data()
    #obs_data, test_se_svb_df, old_se_svb_df = load_data()
    #obs_data, test_de_hoh_df, old_de_hoh_df = load_data()
    #obs_data, test_dk_vng_df, old_dk_vng_df = load_data()

    # For reference
    #sim_vars       = ['QFLX_EVAP_TOT', 'GPP', 'NEE', 'FSH']
    #obs_var_suffix = ['ET', 'GPP_NT_VUT_REF','NEE_VUT_REF','H_F_MDS', 'SM', 'SMR']
    #labels         = ['Evapotranspiration', 'GPP', 'NEE', 'H', r'$\theta$', r'Root zone $\theta$']
    #units          = [" (mm d$^{-1}$)", " (gC m$^{-2}$ d$^{-1}$)", " (gC/m$^{2}$/day)", " (Wm$^{-2}$)", " (%)"]
    #dir            = ['perturbed_vegetation', 'perturbed_soil', 'perturbed_forcing', 'combined_perturbation']

    var            = 'ET'     
    var_title      = 'Evapotranspiration'
    label          = 'Evapotranspiration'
    unit           = " (mm d$^{-1}$)"
    dir            = 'combined_perturbation'
    pert_factor    = 'Combined perturbation'
    folder         = 'ET'
    percentile     = '99_percent_ci'

    # Observed data
    observed_data = {
        'datetime': obs_data['time'],
        'FI-Hyy_'f'{var}': obs_data['FI-Hyy_'f'{var}'],
        'FI-Sod_'f'{var}': obs_data['FI-Sod_'f'{var}'],
        'CZ-BK1_'f'{var}': obs_data['CZ-BK1_'f'{var}'],
        'DE-Obe_'f'{var}': obs_data['DE-Obe_'f'{var}'],
        'DE-RuW_'f'{var}': obs_data['DE-RuW_'f'{var}'],
        'IT-Lav_'f'{var}': obs_data['IT-Lav_'f'{var}'],
        'NL-Loo_'f'{var}': obs_data['NL-Loo_'f'{var}'],
        'ES-Cnd_'f'{var}': obs_data['ES-Cnd_'f'{var}'],
        'FR-Pue_'f'{var}': obs_data['FR-Pue_'f'{var}'],
        'DE-Hai_'f'{var}': obs_data['DE-Hai_'f'{var}'],
        'BE-Bra_'f'{var}': obs_data['BE-Bra_'f'{var}'],
        #'test_SE-Svb_'f'{var}': obs_data['test_SE-Svb_'f'{var}'],
        #'old_SE-Svb_'f'{var}': obs_data['old_SE-Svb_'f'{var}'],
        #'test_DE-HoH_'f'{var}': obs_data['test_DE-HoH_'f'{var}'][72:],
        #'old_DE-HoH_'f'{var}': obs_data['old_DE-HoH_'f'{var}'][72:],
        #'test_DK-Vng_'f'{var}': obs_data['test_DK-Vng_'f'{var}'][53:84],
        #'old_DK-Vng_'f'{var}': obs_data['old_DK-Vng_'f'{var}'][53:84],
    }

    # List of DataFrames and site codes
    ens_dfs    = [fi_hyy_df, fi_sod_df, cz_bk1_df, de_obe_df, de_ruw_df, it_lav_df, nl_loo_df, es_cnd_df, fr_pue_df, de_hai_df, be_bra_df]
    # es_cnd_df, dk_vng_df, se_svb_df,
    #ens_dfs = [test_se_svb_df, old_se_svb_df]
    #ens_dfs = [test_de_hoh_df, old_de_hoh_df]
    #ens_dfs = [test_dk_vng_df, old_dk_vng_df]

    sites      = ['FI-Hyy', 'FI-Sod', 'CZ-BK1', 'DE-Obe', 'DE-RuW', 'IT-Lav', 'NL-Loo', 'ES-Cnd', 'FR-Pue', 'DE-Hai', 'BE-Bra']
    # 'ES-Cnd', 'DK-Vng', 'SE-Svb', 
    #sites   = ['test_SE-Svb', 'old_SE-Svb']
    #sites   = ['test_DE-HoH', 'old_DE-HoH']
    #sites   = ['test_DK-Vng', 'old_DK-Vng']

    site_full  = ['FI-Hyytiälä','FI-Sodankylä', 'CZ-Bily Kriz', 'DE-Oberbärenburg', 'DE-Wüstebach', 'IT-Lavarone', 'NL-Loobos', 'ES-Conde', 'FR-Puechabon', 'DE-Hainich', 'BE-Brasschaat']
    # 'ES-Conde', 'DK-Voulund', 'SE-Svartberget',
    #site_full  = ['SE-Svartberget', 'SE-Svartberget']
    #site_full  = ['DE-Hohes Holz', 'DE-Hohes Holz']
    #site_full  = ['DK-Voulund', 'DK-Voulund']

    #ens_spread_df = calculate_site_spreads(ens_dfs, sites)
    ens_spread_df = calculate_site_percentiles(ens_dfs, sites)
    observed_df   = pd.DataFrame(observed_data)
    merged_df     = ens_spread_df.merge(observed_df, on='datetime')
    #merged_df_rounded = merged_df.round(2)

    # Save the rounded DataFrame as a CSV file
    output_csv_path = f"/home/fernand/Documents/ensemble_analysis/ens_data/{percentile}/ens_128/{dir}/{folder}/merged_df_others.csv"
    #merged_df_rounded.to_csv(output_csv_path, index=False)
    merged_df.to_csv(output_csv_path, index=False)

    # Initialize a dictionary to store the observed time ranges for each site
    observed_time_ranges = {}
    for site in sites:
        observed_time_ranges[site] = observed_df[observed_df[f'{site}_{var}'].notnull()]['datetime']
    

    et_plot_ylimit = {'FI-Hyy':[-1.0, 6], 'FI-Sod':[-0.5, 4], 'CZ-BK1':[-0.5, 5], 'DE-Obe':[-0.5, 4], 'DE-RuW':[-0.7,5], 
                      'IT-Lav':[-0.5, 5], 'NL-Loo':[-0.5, 4], 'ES-Cnd':[-0.3, 5], 'FR-Pue':[0, 6], 'DE-Hai':[-0.5, 6], 'BE-Bra':[-0.5, 5]}
    #et_plot_ylimit = {'test_SE-Svb':[-0.5, 5], 'old_SE-Svb':[-0.5, 5]}
    #et_plot_ylimit = {'test_DE-HoH':[-0.5, 5],    'old_DE-HoH':[-0.5, 5]}
    #et_plot_ylimit = {'test_DK-Vng':[-0.5, 5], 'old_DK-Vng':[-0.5, 5]}
    
    nee_plot_ylimit = {'FI-Hyy':[-10, 8], 'FI-Sod':[-10.5, 6], 'CZ-BK1':[-7, 5], 'DE-Obe':[-6, 4], 'DE-RuW':[-8, 6], 
                       'IT-Lav':[-12, 6],  'NL-Loo':[-8, 8],   'ES-Cnd':[-8, 6], 'FR-Pue':[-10, 8], 'DE-Hai':[-12, 8], 'BE-Bra':[-7, 4]}
    #nee_plot_ylimit = {'test_SE-Svb':[-10, 10],   'old_SE-Svb':[-10, 10]}
    #nee_plot_ylimit = {'test_DE-HoH':[-10, 6],    'old_DE-HoH':[-10, 6]}
    #nee_plot_ylimit = {'test_DK-Vng':[-10.5, 4.5], 'old_DK-Vng':[-10.5, 4.5]}
    
    sh_plot_ylimit = {'FI-Hyy':[-70, 100], 'FI-Sod':[-110, 120], 'CZ-BK1':[-60, 110], 'DE-Obe':[-60, 125], 'DE-RuW':[-80, 125], 
                      'IT-Lav':[-60, 150], 'NL-Loo':[-70, 125], 'ES-Cnd':[-60, 200], 'FR-Pue':[-60, 200], 'DE-Hai':[-75, 125], 'BE-Bra':[-76, 120]}
    #sh_plot_ylimit = {'test_SE-Svb':[-60, 120],  'old_SE-Svb':[-60, 120]}
    #sh_plot_ylimit = {'test_DE-HoH':[-105, 150], 'old_DE-HoH':[-105, 150]}
    #sh_plot_ylimit = {'test_DK-Vng':[-40, 70],   'old_DK-Vng':[-40, 70]}
    
    gpp_plot_ylimit = {'FI-Hyy':[-0.5, 17], 'FI-Sod':[-0.5, 20], 'CZ-BK1':[-0.5, 15], 'DE-Obe':[-0.7, 12],   'DE-RuW':[0, 15], 
                       'IT-Lav':[-0.5, 15], 'NL-Loo':[-0.5, 14], 'FR-Pue':[-0.5, 20], 'DE-Hai':[-0.5, 17.5], 'BE-Bra':[-0.5, 12]}
    #gpp_plot_ylimit = {'test_SE-Svb':[-0.5, 19], 'old_SE-Svb':[-0.5, 19]}
    #gpp_plot_ylimit = {'test_DE-HoH':[-0.7, 18], 'old_DE-HoH':[-0.7, 18]}
    

    ssm_plot_ylimit = {'FI-Hyy':[10, 80], 'FI-Sod':[0, 100], 'CZ-BK1':[0, 80], 'DE-Obe':[0, 75], 'DE-RuW':[10, 85], 'IT-Lav':[0, 80],
                       'NL-Loo':[0, 70],  'FR-Pue':[0, 65],  'DE-Hai':[0, 80], 'BE-Bra':[0, 80]}
    #ssm_plot_ylimit = {'test_DE-HoH':[0, 70], 'old_DE-HoH':[0, 70]}
    #ssm_plot_ylimit = {'test_DK-Vng':[10, 70], 'old_DK-Vng':[10, 70]}

    smr_plot_ylimit = {'FI-Hyy':[0, 60], 'FI-Sod':[0, 60], 'CZ-BK1':[0, 50], 'DE-Obe':[0, 40], 'DE-RuW':[10, 60], 'IT-Lav':[0, 50],
                       'NL-Loo':[0, 50], 'FR-Pue':[0, 60], 'DE-Hai':[0, 60], 'BE-Bra':[0, 50]}
    #smr_plot_ylimit = {'test_DE-HoH':[0, 60], 'old_DE-HoH':[0, 60]}
    #smr_plot_ylimit = {'test_DK-Vng':[10, 60], 'old_DK-Vng':[10, 60]}

    save_dir = f"/home/fernand/Documents/ensemble_analysis/ens_data/{percentile}/ens_128/{dir}/{folder}"
    #metrics_dir = f"/home/fernand/Documents/ensemble_analysis/ens_data/{percentile}/{dir}/test/{folder}"
    #save_variance = f"/home/fernand/Documents/ensemble_analysis/ens_data/{dir}/{folder}"
    plot_ensemble_spread(merged_df, pert_factor, var, label, unit, save_dir, sites, site_full, var_title, et_plot_ylimit, nee_plot_ylimit, sh_plot_ylimit, gpp_plot_ylimit, ssm_plot_ylimit, smr_plot_ylimit)
    percent_coverage(merged_df, observed_time_ranges, var, sites, save_dir)
    #plot_ensemble_spread_std(merged_df_rounded, pert_factor, var, label, unit, save_dir, sites, site_full, var_title, et_plot_ylimit, nee_plot_ylimit, sh_plot_ylimit, gpp_plot_ylimit)
    #percent_coverage_std(merged_df_rounded, observed_time_ranges, var, sites, save_dir)
    metrics_df_all, metrics_df_apr_oct = process_and_save_metrics(ens_dfs, sites, observed_df, observed_time_ranges, var, save_dir)
    # calculate_variance_stats(ens_dfs, sites, save_dir)

if __name__ == "__main__":
    main()