#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import numpy as np
import pandas as pd

from sklearn.metrics import mean_squared_error, r2_score
from scipy.stats import pearsonr

import matplotlib.pyplot as plt



def calculate_site_percentiles(dataframes, sites):
    '''
    Function to calculate the 0.5 and 99.5 percentiles of a row without interpolation
    - Sort the values of the row (excluding the datetime column)
    - 0.5 percentile corresponds to the 5th position (index 4)
    - 99.5 percentile corresponds to the 995th position (index 994)
    '''
    
    def calculate_percentiles(row):
        sorted_row = np.sort(row[1:])  
        value_0_5 = sorted_row[0]     
        value_99_5 = sorted_row[127]   
        return value_0_5, value_99_5
    
    # Initialize the final DataFrame
    final_df = pd.DataFrame()
    
    # Process each DataFrame
    for df, site in zip(dataframes, sites):
        # Apply the function to each row of the DataFrame
        percentiles = df.apply(calculate_percentiles, axis=1)
        percentiles_df = pd.DataFrame(percentiles.tolist(), columns=[f'{site}_lb', f'{site}_ub'])
        percentiles_df.insert(0, 'datetime', df['datetime'])
        
        # Merge with the final DataFrame
        if final_df.empty:
            final_df = percentiles_df
        else:
            final_df = final_df.merge(percentiles_df, on='datetime', how='outer')
    
    return final_df


def plot_ensemble_spread(merged_df, pert_factor, var, label, unit, save_dir, sites, site_full, var_title, et_plot_ylimit, nee_plot_ylimit, sh_plot_ylimit, gpp_plot_ylimit, ssm_plot_ylimit, smr_plot_ylimit):
    os.makedirs(save_dir, exist_ok=True)
    
    # Determine the appropriate y-axis limits dictionary
    if var == 'ET':
        ylimits = et_plot_ylimit
    elif var == 'NEE_VUT_REF':
        ylimits = nee_plot_ylimit
    elif var == 'H_F_MDS':
        ylimits = sh_plot_ylimit
    elif var == 'GPP_NT_VUT_REF':
        ylimits = gpp_plot_ylimit
    elif var == 'SM':
        ylimits = ssm_plot_ylimit
    elif var == 'SMR':
        ylimits = smr_plot_ylimit
    else:
        ylimits = {}

    for site, full_site in zip(sites, site_full):
        plt.figure(figsize=(15, 12))

        # Filter the result_df based on the observed time range for the current site
        #site_result_df = merged_df[merged_df['datetime'].isin(observed_time_ranges[site])]

        plt.fill_between(merged_df['datetime'], merged_df[f'{site}_lb'], merged_df[f'{site}_ub'], color='#f03b20', alpha=0.3, label='Ens. Spread (min-max)')
        plt.plot(merged_df['datetime'], merged_df[f'{site}_{var}'], marker='o', markersize=5, linestyle='--', label='Observation', color='black')

        plt.xlabel('Date')
        plt.ylabel(f'{label} {unit}')
        plt.title(f'{pert_factor} at {full_site}', y=1.02)
        plt.xticks(rotation=20, ha='center')
        plt.grid(True)
        plt.legend(loc='upper left')
        plt.tight_layout()

        # Set y-axis limits if specified for the site
        if site in ylimits:
            plt.ylim(ylimits[site])

        plot_subdir = os.path.join(save_dir, f'{site.lower()}')
        if not os.path.exists(plot_subdir):
            os.makedirs(plot_subdir)

        plot_filename = os.path.join(plot_subdir, f'{site.lower()}_{var_title}.png')
        plt.savefig(plot_filename)

        plt.close()


def percent_coverage(merged_df, observed_time_ranges, var, sites, save_cover):
    # Directory to save coverage files
    coverage_dir = os.path.join(save_cover, 'coverage_others')
    if not os.path.exists(coverage_dir):
        os.makedirs(coverage_dir)

    # Helper function to filter data for the months from April to October
    def is_april_to_october(date):
        return date.month in range(4, 11)

    # Function to calculate coverage
    def calculate_coverage(filter_func=None):
        available_data = {}
        coverage_percentages = {}
        
        for site in sites:
            obs_values = merged_df[f'{site}_{var}']
            valid_indices = merged_df['datetime'].isin(observed_time_ranges[site])
            
            if filter_func:
                valid_indices &= merged_df['datetime'].apply(filter_func)

            obs_values = obs_values[valid_indices]
            available_data[site] = np.sum(~np.isnan(obs_values))

            lb_values = merged_df[f'{site}_lb'][valid_indices]
            ub_values = merged_df[f'{site}_ub'][valid_indices]
            obs_values = obs_values[valid_indices]

            within_range = np.logical_and(obs_values >= lb_values, obs_values <= ub_values)
            coverage_percentages[site] = np.sum(within_range) / available_data[site] * 100 if available_data[site] > 0 else np.nan

        return available_data, coverage_percentages

    # Calculate coverage for the entire period
    available_data_all, coverage_percentages_all = calculate_coverage()

    # Calculate coverage for the period from April to October
    available_data_apr_oct, coverage_percentages_apr_oct = calculate_coverage(is_april_to_october)

    # Create DataFrames for coverage percentages
    coverage_df_all = pd.DataFrame(coverage_percentages_all.items(), columns=['Site', 'CoveragePercentage'])
    coverage_df_all['Obs_Count'] = coverage_df_all['Site'].map(available_data_all)

    coverage_df_apr_oct = pd.DataFrame(coverage_percentages_apr_oct.items(), columns=['Site', 'CoveragePercentage'])
    coverage_df_apr_oct['Obs_Count'] = coverage_df_apr_oct['Site'].map(available_data_apr_oct)

    # Save the coverage percentages to CSV files
    coverage_csv_path_all = os.path.join(coverage_dir, 'coverage_all_periods.csv')
    coverage_df_all.round(2).to_csv(coverage_csv_path_all, index=False)

    coverage_csv_path_apr_oct = os.path.join(coverage_dir, 'coverage_april_october.csv')
    coverage_df_apr_oct.round(2).to_csv(coverage_csv_path_apr_oct, index=False)

    return coverage_df_all, coverage_df_apr_oct


def calculate_ubrmse(observed, predicted):
    # Calculate the means of observed and predicted values
    mean_observed = np.mean(observed)
    mean_predicted = np.mean(predicted)
    
    # Calculate the deviations from means
    deviation_observed = observed - mean_observed
    deviation_predicted = predicted - mean_predicted
    
    # Calculate the squared differences of deviations
    squared_diff = (deviation_predicted - deviation_observed) ** 2
    
    # Calculate the mean of the squared differences
    mean_squared_diff = np.mean(squared_diff)
    
    # Calculate the unbiased RMSE
    ubrmse = np.sqrt(mean_squared_diff)
    
    return ubrmse

def calculate_performance_metrics(observed, predicted, ensemble_members):
    rmse = np.sqrt(mean_squared_error(observed, predicted))
    r_squared = r2_score(observed, predicted)
    mean_bias = np.mean(predicted - observed)
    pbias = 100 * (np.sum(predicted - observed) / np.sum(observed))
    # ubrmse = np.sqrt((rmse**2)-(bias**2))
    ubrmse = calculate_ubrmse(observed, predicted)
    pearson_corr, _ = pearsonr(observed, predicted)

    # Calculate the standard deviation of the ensemble members relative to the ensemble mean
    std_deviation = np.std(ensemble_members, axis=1)
    
    # Calculate the mean standard deviation
    mean_std_dev = np.mean(std_deviation)

    # Calculate the median standard deviation
    median_std_dev = np.median(std_deviation)

    # Calculate SS
    ss = mean_std_dev / ubrmse if ubrmse != 0 else np.nan
    
    return rmse, r_squared, mean_bias, pbias, ubrmse, pearson_corr, ss, mean_std_dev, median_std_dev

def process_and_save_metrics(ens_dfs, sites, observed_df, observed_time_ranges, var, save_dir):
    # Directory to save metrics files
    metrics_dir = os.path.join(save_dir, 'metrics_others')
    if not os.path.exists(metrics_dir):
        os.makedirs(metrics_dir)

    # Helper function to filter data for the months from April to October
    def is_april_to_october(date):
        return date.month in range(4, 11)

    def calculate_and_save_metrics(filter_func, file_suffix):
        metrics_list = []

        for df, site in zip(ens_dfs, sites):
            # Calculate ensemble mean
            ensemble_columns = [col for col in df.columns if 'real_' in col]
            df['ensemble_mean'] = df[ensemble_columns].mean(axis=1)

            # Filter the ensemble data based on the observed time range for the current site
            valid_indices = df['datetime'].isin(observed_time_ranges[site])
            if filter_func:
                valid_indices &= df['datetime'].apply(filter_func)
            
            site_ens_df = df[valid_indices]
            ens_mean = site_ens_df['ensemble_mean']

            # Filter the observed data based on the observed time range for the current site
            site_observed_df = observed_df[observed_df['datetime'].isin(observed_time_ranges[site])]
            if filter_func:
                site_observed_df = site_observed_df[site_observed_df['datetime'].apply(filter_func)]

            observed_values = site_observed_df[f'{site}_{var}']

            # Get the ensemble members for the same time range
            ensemble_members = site_ens_df[ensemble_columns].values

            # Calculate performance metrics
            rmse, r_squared, mean_bias, pbias, ubrmse, pearson_corr, ss, mean_std_dev, median_std_dev = calculate_performance_metrics(observed_values, ens_mean, ensemble_members)
            
            # Append the results
            metrics_list.append({
                'Site': site,
                'RMSE': rmse,
                'R2': r_squared,
                'MBE': mean_bias,
                'PBIAS': pbias,
                'ubRMSE': ubrmse,
                'R': pearson_corr,
                'SS': ss,
                'Avg_Std_Dev': mean_std_dev,
                'Median_Std_Dev': median_std_dev
            })
        
        # Create a DataFrame for metrics
        metrics_df = pd.DataFrame(metrics_list)

        # Save the metrics to a CSV file
        metrics_csv_path = os.path.join(metrics_dir, f'metrics_{file_suffix}.csv')
        metrics_df.to_csv(metrics_csv_path, index=False)

        return metrics_df

    # Calculate and save metrics for the entire period
    metrics_df_all = calculate_and_save_metrics(None, 'all_periods')

    # Calculate and save metrics for the period from April to October
    metrics_df_apr_oct = calculate_and_save_metrics(is_april_to_october, 'april_october')

    return metrics_df_all, metrics_df_apr_oct


def calculate_variance_stats(ens_dfs, sites, save_variance):
    # Directory to save variance files
    variance_dir = os.path.join(save_variance, 'variance')
    if not os.path.exists(variance_dir):
        os.makedirs(variance_dir)

    # Function to calculate sample variance for each row
    def calculate_sample_variance(row):
        return np.var(row[1:], ddof=1)

    # Initialize the list to store variance statistics for each site
    variance_stats = []

    # Process each DataFrame
    for df, site in zip(ens_dfs, sites):
        # Apply the function to each row of the DataFrame to calculate variances
        variances = df.apply(calculate_sample_variance, axis=1)
        
        # Calculate mean and median variances for the site
        mean_variance = np.mean(variances).round(2)
        median_variance = np.median(variances).round(2)
        
        # Append the results to the variance_stats list
        variance_stats.append({
            'site': site,
            'mean_variance': mean_variance,
            'median_variance': median_variance
        })

    # Create a DataFrame for the variance statistics
    variance_stats_df = pd.DataFrame(variance_stats)

    # Save the variance statistics DataFrame as a CSV file
    variance_csv_path = os.path.join(variance_dir, 'variance_statistics.csv')
    variance_stats_df.to_csv(variance_csv_path, index=False)

    return variance_stats_df

# Function to calculate the rank of the observation within the ensemble
def calculate_ranks(ensemble_forecasts):
    return np.argsort(np.argsort(ensemble_forecasts, axis=1), axis=1)

#def calculate_observed_rank(ensemble_forecasts, observation):
#    return np.sum(ensemble_forecasts < observation, axis=1)

def calculate_observed_rank(ensemble_forecasts, observation):
    # Ensure no NaN values in ensemble forecasts or observation
    valid_mask = ~np.isnan(ensemble_forecasts)
    valid_ensemble_forecasts = ensemble_forecasts[valid_mask]
    
    if np.isnan(observation):
        return np.nan
    
    # Perform the comparison only on valid data
    return np.sum(valid_ensemble_forecasts < observation)

def plot_rank_histogram(observed_ranks, site, timestep, output_dir):
    # Create the plot
    plt.hist(observed_ranks, bins=np.arange(len(observed_ranks) + 2) - 0.5, edgecolor='black')
    plt.title(f'Rank Histogram for {site} at Timestep {timestep}')
    plt.xlabel('Rank')
    plt.ylabel('Frequency')
    plt.grid(True)
    
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save the plot
    plot_filename = os.path.join(output_dir, f'hist_{site}_{timestep}.png')
    plt.savefig(plot_filename)
    plt.close()
    
    plt.close()

def calculate_site_spreads(dataframes, sites):
    """
    Function to calculate the mean, lower bound (mean - std), and upper bound (mean + std) for each row.
    """
    def calculate_spread(row):
        mean_value = np.mean(row[1:])
        std_value = np.std(row[1:])
        lb = mean_value - (std_value)
        ub = mean_value + (std_value)
        return lb, ub
    
    # Initialize the final DataFrame
    final_df = pd.DataFrame()
    
    # Process each DataFrame
    for df, site in zip(dataframes, sites):
        # Apply the function to each row of the DataFrame
        spreads = df.apply(calculate_spread, axis=1)
        spreads_df = pd.DataFrame(spreads.tolist(), columns=[f'{site}_lb', f'{site}_ub'])
        spreads_df.insert(0, 'datetime', df['datetime'])
        
        # Merge with the final DataFrame
        if final_df.empty:
            final_df = spreads_df
        else:
            final_df = final_df.merge(spreads_df, on='datetime', how='outer')
    
    return final_df

def plot_ensemble_spread_std(merged_df, pert_factor, var, label, unit, save_dir, sites, site_full, var_title, et_plot_ylimit, nee_plot_ylimit, sh_plot_ylimit, gpp_plot_ylimit):
    os.makedirs(save_dir, exist_ok=True)

    # Determine the appropriate y-axis limits dictionary
    if var == 'ET':
        ylimits = et_plot_ylimit
    elif var == 'NEE_VUT_REF':
        ylimits = nee_plot_ylimit
    elif var == 'H_F_MDS':
        ylimits = sh_plot_ylimit
    elif var == 'GPP_NT_VUT_REF':
        ylimits = gpp_plot_ylimit
    else:
        ylimits = {}

    for site, full_site in zip(sites, site_full):
        plt.figure(figsize=(15, 12))

        plt.fill_between(merged_df['datetime'], merged_df[f'{site}_lb'], merged_df[f'{site}_ub'], color='#f03b20', alpha=0.3, label='Ens. Spread (mean ± std)')
        plt.plot(merged_df['datetime'], merged_df[f'{site}_{var}'], marker='o', markersize=5, linestyle='--', label='Observation', color='black')

        plt.xlabel('Date')
        plt.ylabel(f'{label} {unit}')
        plt.title(f'{pert_factor} at {full_site}', y=1.02)
        plt.xticks(rotation=20, ha='center')
        plt.grid(True)
        plt.legend(loc='upper left')
        plt.tight_layout()

        # Set y-axis limits if specified for the site
        if site in ylimits:
            plt.ylim(ylimits[site])

        plot_subdir = os.path.join(save_dir, f'{site.lower()}')
        if not os.path.exists(plot_subdir):
            os.makedirs(plot_subdir)

        plot_filename = os.path.join(plot_subdir, f'{site.lower()}_{var_title}.png')
        plt.savefig(plot_filename)

        plt.close()

def percent_coverage_std(merged_df, observed_time_ranges, var, sites, save_cover):
    # Directory to save coverage files
    coverage_dir = os.path.join(save_cover, 'coverage')
    if not os.path.exists(coverage_dir):
        os.makedirs(coverage_dir)

    # Calculate available data counts for each site
    available_data = {}
    for site in sites:
        obs_values = merged_df[f'{site}_{var}']
        valid_indices = merged_df['datetime'].isin(observed_time_ranges[site])
        obs_values = obs_values[valid_indices]
        available_data[site] = np.sum(~np.isnan(obs_values))

    # Calculate percent coverage excluding NaN values
    coverage_percentages = {}
    for site in sites:
        obs_values = merged_df[f'{site}_{var}']
        lb_values = merged_df[f'{site}_lb']
        ub_values = merged_df[f'{site}_ub']

        # Filter ensemble spread data to match the observed data time range
        valid_indices = merged_df['datetime'].isin(observed_time_ranges[site])
        lb_values = lb_values[valid_indices]
        ub_values = ub_values[valid_indices]

        # Align arrays using the same index
        obs_values = obs_values[valid_indices]

        # Calculate coverage percent
        within_range = np.logical_and(obs_values >= lb_values, obs_values <= ub_values)
        coverage_percentages[site] = np.sum(within_range) / available_data[site] * 100

    # Create a DataFrame for coverage percentages
    coverage_df = pd.DataFrame(coverage_percentages.items(), columns=['Site', 'CoveragePercentage'])

    # Add the available obs data to the DataFrame
    coverage_df['Obs_Count'] = coverage_df['Site'].map(available_data)

    # Save the coverage percentages to a CSV file
    coverage_csv_path = os.path.join(coverage_dir, 'coverage.csv')
    coverage_df.round(2).to_csv(coverage_csv_path, index=False)

    return coverage_df