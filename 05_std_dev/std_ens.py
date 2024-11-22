#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import os


def load_data():
    # Path to monthly Ens. data
    #filepath_fi_hyy = "/home/fernand/Documents/ensemble_analysis/ens_data/forcing/ens_128/SMR/FI-Hyy_aggregated.csv"
    #filepath_fi_sod = "/home/fernand/Documents/ensemble_analysis/ens_data/forcing/ens_128/SMR/FI-Sod_aggregated.csv"
    #filepath_cz_bk1 = "/home/fernand/Documents/ensemble_analysis/ens_data/forcing/ens_128/SMR/CZ-BK1_aggregated.csv"
    #filepath_de_obe = "/home/fernand/Documents/ensemble_analysis/ens_data/forcing/ens_128/SMR/DE-Obe_aggregated.csv"
    #filepath_de_ruw = "/home/fernand/Documents/ensemble_analysis/ens_data/forcing/ens_128/SMR/DE-RuW_aggregated.csv"
    #filepath_it_lav = "/home/fernand/Documents/ensemble_analysis/ens_data/forcing/ens_128/SMR/IT-Lav_aggregated.csv"
    #filepath_nl_loo = "/home/fernand/Documents/ensemble_analysis/ens_data/forcing/ens_128/SMR/NL-Loo_aggregated.csv"
    #filepath_es_cnd = "/home/fernand/Documents/ensemble_analysis/ens_data/forcing/ens_128/SMR/ES-Cnd_aggregated.csv"
    #filepath_fr_pue = "/home/fernand/Documents/ensemble_analysis/ens_data/forcing/ens_128/SMR/FR-Pue_aggregated.csv"
    #filepath_de_hai = "/home/fernand/Documents/ensemble_analysis/ens_data/forcing/ens_128/SMR/DE-Hai_aggregated.csv"
    #filepath_be_bra = "/home/fernand/Documents/ensemble_analysis/ens_data/forcing/ens_128/SMR/BE-Bra_aggregated.csv"
    #filepath_se_svb_test = "/home/fernand/Documents/ensemble_analysis/ens_data/forcing/ens_128/ET/test_SE-Svb_aggregated.csv"
    #filepath_se_svb_old  = "/home/fernand/Documents/ensemble_analysis/ens_data/forcing/ens_128/ET/old_SE-Svb_aggregated.csv"
    #filepath_de_hoh_test = "/home/fernand/Documents/ensemble_analysis/ens_data/forcing/ens_128/SMR/test_DE-HoH_aggregated.csv"
    #filepath_de_hoh_old  = "/home/fernand/Documents/ensemble_analysis/ens_data/forcing/ens_128/SMR/old_DE-HoH_aggregated.csv"
    filepath_dk_vng_test = "/home/fernand/Documents/ensemble_analysis/ens_data/forcing/ens_128/ET/test_DK-Vng_aggregated.csv"
    filepath_dk_vng_old  = "/home/fernand/Documents/ensemble_analysis/ens_data/forcing/ens_128/ET/old_DK-Vng_aggregated.csv"

    # Read CSV files and set time type
    #fi_hyy_df = pd.read_csv(filepath_fi_hyy, parse_dates=['datetime'])
    #fi_hyy_df['datetime'] = pd.to_datetime(fi_hyy_df['datetime'], format='%Y-%m-%d')
    #
    #fi_sod_df = pd.read_csv(filepath_fi_sod, parse_dates=['datetime'])
    #fi_sod_df['datetime'] = pd.to_datetime(fi_sod_df['datetime'], format='%Y-%m-%d')
#
    #cz_bk1_df = pd.read_csv(filepath_cz_bk1, parse_dates=['datetime'])
    #cz_bk1_df['datetime'] = pd.to_datetime(cz_bk1_df['datetime'], format='%Y-%m-%d')
    #
    #de_obe_df = pd.read_csv(filepath_de_obe, parse_dates=['datetime'])
    #de_obe_df['datetime'] = pd.to_datetime(de_obe_df['datetime'], format='%Y-%m-%d')
    #
    #de_ruw_df = pd.read_csv(filepath_de_ruw, parse_dates=['datetime'])
    #de_ruw_df['datetime'] = pd.to_datetime(de_ruw_df['datetime'], format='%Y-%m-%d')
    #
    #it_lav_df = pd.read_csv(filepath_it_lav, parse_dates=['datetime'])
    #it_lav_df['datetime'] = pd.to_datetime(it_lav_df['datetime'], format='%Y-%m-%d')
    #
    #nl_loo_df = pd.read_csv(filepath_nl_loo, parse_dates=['datetime'])
    #nl_loo_df['datetime'] = pd.to_datetime(nl_loo_df['datetime'], format='%Y-%m-%d')
    #
    #es_cnd_df = pd.read_csv(filepath_es_cnd, parse_dates=['datetime'])
    #es_cnd_df['datetime'] = pd.to_datetime(es_cnd_df['datetime'], format='%Y-%m-%d')
#
    #fr_pue_df = pd.read_csv(filepath_fr_pue, parse_dates=['datetime'])
    #fr_pue_df['datetime'] = pd.to_datetime(fr_pue_df['datetime'], format='%Y-%m-%d')
    #
    #de_hai_df = pd.read_csv(filepath_de_hai, parse_dates=['datetime'])
    #de_hai_df['datetime'] = pd.to_datetime(de_hai_df['datetime'], format='%Y-%m-%d')
#
    #be_bra_df = pd.read_csv(filepath_be_bra, parse_dates=['datetime'])
    #be_bra_df['datetime'] = pd.to_datetime(be_bra_df['datetime'], format='%Y-%m-%d')

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
    
    test_dk_vng_df = pd.read_csv(filepath_dk_vng_test, parse_dates=['datetime'])
    test_dk_vng_df['datetime'] = pd.to_datetime(test_dk_vng_df['datetime'], format='%Y-%m-%d')

    old_dk_vng_df = pd.read_csv(filepath_dk_vng_old, parse_dates=['datetime'])
    old_dk_vng_df['datetime'] = pd.to_datetime(old_dk_vng_df['datetime'], format='%Y-%m-%d')

    #return fi_hyy_df, fi_sod_df, cz_bk1_df, de_obe_df, de_ruw_df, it_lav_df, nl_loo_df, es_cnd_df, fr_pue_df, de_hai_df, be_bra_df
    #return test_se_svb_df, old_se_svb_df
    #return test_de_hoh_df, old_de_hoh_df
    return test_dk_vng_df, old_dk_vng_df


def create_monthly_dates(start_year, end_year):
    return pd.date_range(start=f'{start_year}-01-01', end=f'{end_year}-12-31', freq='MS')

def calculate_standard_deviation(ens_data):
    """
    Calculate the standard deviation of the ensemble members relative to the ensemble mean.
    Parameters:
        ens_data (pd.DataFrame): DataFrame containing ensemble data with time as index.
    Returns:
        pd.Series: Standard deviation of the ensemble members.
    """
    return np.std(ens_data.iloc[:, 1:], axis=1)

def create_and_save_std_dev_dataframe(time, ens_dfs, sites, var, site_i, output_dir):
    """
    Create a DataFrame with datetime and standard deviation values, and save it as a CSV file.
    Parameters:
        time (pd.DatetimeIndex): Datetime index for the DataFrame.
        std_deviation (pd.Series): Standard deviation values for each time step.
        site (str): Site name.
        var (str): Variable name.
        output_dir (str): Directory to save the CSV file.
    """
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create the DataFrame to store all standard deviations
    std_dev_df = pd.DataFrame({'datetime': time})

    # Calculate and store the standard deviation for each site
    for ens_data, site in zip(ens_dfs, sites):
        std_deviation = calculate_standard_deviation(ens_data)
        std_dev_df[f'{site}_std'] = std_deviation.values.round(2)

    # Save the DataFrame as a CSV file
    csv_filename = f"{var}_{site_i}_std_dev.csv"
    csv_filepath = os.path.join(output_dir, csv_filename)
    std_dev_df.to_csv(csv_filepath, index=False)
    print(f"Saved: {csv_filepath}")


def main():
    #fi_hyy_df, fi_sod_df, cz_bk1_df, de_obe_df, de_ruw_df, it_lav_df, nl_loo_df, es_cnd_df, fr_pue_df, de_hai_df, be_bra_df = load_data()
    #test_se_svb_df, old_se_svb_df = load_data()
    #test_de_hoh_df, old_de_hoh_df = load_data()
    test_dk_vng_df, old_dk_vng_df = load_data()

    # For reference
    #var    = ['ET', 'GPP', 'NEE', 'SH', 'SM', 'SMR']
    #dir    = ['perturbed_vegetation', 'perturbed_soil', 'perturbed_forcing', 'combined_perturbation']

    var     = 'ET'
    site_i  = 'dk_vng'      
    sub_dir = 'perturbed_forcing'
    dir     = 'ens_128'
    folder  = 'std_dev'


    # List of DataFrames and site codes
    #ens_dfs    = [fi_hyy_df, fi_sod_df, cz_bk1_df, de_obe_df, de_ruw_df, it_lav_df, nl_loo_df, es_cnd_df, fr_pue_df, de_hai_df, be_bra_df]
    # es_cnd_df 
    #ens_dfs = [test_se_svb_df, old_se_svb_df]
    #ens_dfs = [test_de_hoh_df, old_de_hoh_df]
    ens_dfs = [test_dk_vng_df, old_dk_vng_df]
    
    #sites      = ['FI-Hyy', 'FI-Sod', 'CZ-BK1', 'DE-Obe', 'DE-RuW', 'IT-Lav', 'NL-Loo', 'ES-Cnd', 'FR-Pue', 'DE-Hai', 'BE-Bra']
    # 'ES-Cnd',
    #sites   = ['SE-Svb', 'old_SE-Svb']
    #sites   = ['DE-HoH', 'old_DE-HoH']
    sites   = ['DK-Vng', 'old_DK-Vng']

    output_dir = f'/home/fernand/Documents/ensemble_analysis/ens_data/99_percent_ci/{dir}/{sub_dir}/{folder}'
    time = create_monthly_dates(2009, 2015)
    create_and_save_std_dev_dataframe(time, ens_dfs, sites, var, site_i, output_dir)


if __name__ == "__main__":
    main()