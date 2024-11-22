#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import pandas as pd
import numpy as np

import xarray as xr



# preprocess variables of interest
def preprocess(ds, clm_vars):
    return ds[clm_vars]

# load ens data
def load_ens_sim(directory, clm_vars):
    sim_ds = {}
    file_list = os.listdir(directory)
    file_list.sort()  # Sort the file list in ascending order

    for filename in file_list:
        if filename.endswith('.nc'):
            file_path = os.path.join(directory, filename)
            parts = filename.split('.')
            ensemble_member = int(parts[1].split('_')[1])

            # Extract the year using regular expression
            match = re.search(r'\d{4}', filename)
            if match:
                year = int(match.group())
            else:
                continue

            clm_ds = xr.open_dataset(file_path, decode_times=True)
            clm_ds = preprocess(clm_ds, clm_vars)

            # Append the dataset to the corresponding ensemble member key
            if f'real_{ensemble_member}' not in sim_ds:
                sim_ds[f'real_{ensemble_member}'] = clm_ds
            else:
                sim_ds[f'real_{ensemble_member}'] = xr.concat([sim_ds[f'real_{ensemble_member}'], clm_ds], dim='time')

    return sim_ds

def modify_data_arrays_for_sites(data_arrays_list, sites, multiply_factor=100):
    modified_data_arrays = []

    for site_data, site_name in zip(data_arrays_list, sites):
        modified_site_data = {}
        
        for realization, data_array in site_data.items():
            if site_name == 'DK-Vng':
                # Special case for 'DK-Vng' with depths 2.5cm, 22.5cm, and 52.5cm
                depth_values = [5, 20, 50]
                variables = []
                
                for depth in depth_values:
                    levsoi_values = {
                        5:  [1],     # 2.5cm depth:  layer 2
                        20: [4],     # 22.5cm depth: layer 5
                        50: [6]      # 52.5cm depth: layer 7
                    }
                    
                    levsoi_indices = levsoi_values[depth]
                    levsoi_indices = [int(idx) for idx in levsoi_indices]  # Convert to integers
                    levsoi_avg = data_array.isel(levsoi=levsoi_indices).mean(dim='levsoi')
                    
                    # Create a separate DataArray for the 'depth' coordinate
                    depth_coord = xr.DataArray([depth], coords={'depth': [depth]}, dims=['depth'])
                    
                    # Concatenate the 'depth' coordinate with the averaged data
                    modified_data = xr.concat([levsoi_avg], dim='depth')
                    
                    # Multiply the data values by the specified factor (100 in this case)
                    modified_data *= multiply_factor

                    # Update the 'units' attribute to '%'
                    modified_data.attrs['units'] = '%'
                    
                    variables.append(modified_data)
                
                # Merge variables for different depths into a single dataset
                modified_data_array = xr.concat(variables, dim='depth')
                
            else:
                # For other sites, use the specified levsoi values for these depths
                depths = [5, 20, 50]
                variables = []

                for depth in depths:
                    levsoi_values = {
                        5:  [1],             # 5cm depth:  layer 2
                        20: [3],             # 20cm depth: layer 4
                        50: [6]              # 50cm depth: layer 7
                    }

                    levsoi_indices = levsoi_values[depth]
                    levsoi_indices = [int(idx) for idx in levsoi_indices]
                    modified_data = data_array.isel(levsoi=levsoi_indices)
                    
                    # Create a separate DataArray for the 'depth' coordinate
                    depth_coord = xr.DataArray([depth], coords={'depth': [depth]}, dims=['depth'])
                    
                    # Concatenate the 'depth' coordinate with the modified data
                    modified_data = xr.concat([modified_data], dim='depth')
                    
                    # Multiply the data values by the specified factor (100 in this case)
                    modified_data *= multiply_factor

                    # Update the 'units' attribute to '%'
                    modified_data.attrs['units'] = '%'
                    
                    variables.append(modified_data)
                
                # Merge variables for different depths into a single dataset
                modified_data_array = xr.concat(variables, dim='depth')

            modified_site_data[realization] = modified_data_array

        modified_data_arrays.append(modified_site_data)

    return modified_data_arrays

def combine_data_arrays_to_dataset(modify_data_arrays, sites, output_dir):
    """
    Combine data arrays from nested list of xarray datasets and save as CSV files.
    
    Parameters:
    modify_data_arrays (list): Nested list of xarray datasets for each site.
    sites (list): List of site names corresponding to the datasets.
    output_dir (str): Directory to save the output CSV files.
    
    Returns:
    dict: Dictionary with site names as keys and aggregated DataFrames as values.
    """
    aggregated_data = {}

    for i, site_data in enumerate(modify_data_arrays):
        site_name = sites[i]  # Get the site name using the index
        
        # Dictionary to store data for each depth level
        depth_level_data = {}

        for realization_name, data_array in site_data.items():
            depth_size = data_array.sizes['depth']
            for depth in range(depth_size):
                if depth not in depth_level_data:
                    depth_level_data[depth] = []

                time_values = data_array['time'].values
                depth_values = data_array['H2OSOI'].isel(depth=depth).values.squeeze()

                # Create a DataFrame for the current realization and depth
                df = pd.DataFrame({
                    'time': time_values,
                    realization_name: depth_values
                })
                
                depth_level_data[depth].append(df)

        # Aggregate data for each depth level and save as CSV
        site_aggregated_data = {}
        for depth, dfs in depth_level_data.items():
            aggregated_df = pd.concat(dfs, axis=1)
            
            # Remove duplicate 'time' columns
            aggregated_df = aggregated_df.loc[:, ~aggregated_df.columns.duplicated()]
            
            # Save to CSV
            csv_filename = f"{site_name}_depth_{depth}.csv"
            csv_filepath = os.path.join(output_dir, csv_filename)
            aggregated_df.to_csv(csv_filepath, index=False)
            print(f"Saved: {csv_filepath}")

            # Store the aggregated DataFrame in the site_aggregated_data dictionary
            site_aggregated_data[depth] = aggregated_df
        
        # Store the aggregated data for the site
        aggregated_data[site_name] = site_aggregated_data

    return aggregated_data
