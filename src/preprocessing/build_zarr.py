import os
import gc
import json
import numpy as np
import xarray as xr
from datetime import datetime

from src.preprocessing.download import (
    download_era5, download_glorys, download_sst, download_sss, download_sla_currents
)
from src.preprocessing.regrid import (
    get_target_grid, process_sst, process_sss, process_currents_sla
)
from src.preprocessing.vertical_interp import (
    interpolate_to_target_depths, create_ocean_mask, apply_ocean_mask
)

def fix_lon(ds, lon_name='longitude'):
    """Normalize longitude to -180 to 180 if needed, or 0 to 360 to match 45 to 105."""
    # Our target is 45 to 105. Both 0-360 and -180-180 are fine for this, 
    # but we need to ensure the coordinate is named 'lon'.
    if lon_name in ds.coords and lon_name != 'lon':
        ds = ds.rename({lon_name: 'lon'})
    if 'latitude' in ds.coords:
        ds = ds.rename({'latitude': 'lat'})
    return ds

def process_era5(era5_path):
    ds = xr.open_dataset(era5_path)
    ds = fix_lon(ds)
    if 'valid_time' in ds.coords:
        ds = ds.rename({'valid_time': 'time'})
    if 'time' not in ds.coords and 'time' in ds.dims:
        pass
    
    # ERA5 is 6-hourly. Take daily mean.
    ds_daily = ds.resample(time="1D").mean()
    target_grid = get_target_grid()
    ds_regridded = ds_daily.interp(lat=target_grid.lat, lon=target_grid.lon, method="linear")
    
    # Ensure standard names are mapped
    if 'u10' in ds_regridded and '10m_u_component_of_wind' not in ds_regridded:
        ds_regridded = ds_regridded.rename({'u10': '10m_u_component_of_wind', 'v10': '10m_v_component_of_wind'})
        
    return ds_regridded

def process_month(year, month, raw_dir, processed_dir):
    """
    Process 1 month end-to-end.
    Downloads, regrids, interpolates vertically, and stacks.
    Returns (inputs_chunk, targets_chunk) datasets.
    """
    print(f"Processing {year}-{month:02d}...")
    
    # 1. Download
    era5_path = download_era5(year, month, raw_dir)
    glorys_path = download_glorys(year, month, raw_dir)
    sst_path = download_sst(year, month, raw_dir)
    sss_path = download_sss(year, month, raw_dir)
    sla_path = download_sla_currents(year, month, raw_dir)
    
    # 2. Load and preprocess each dataset
    
    # GLORYS (Target)
    glorys_ds = xr.open_dataset(glorys_path)
    glorys_ds = fix_lon(glorys_ds)
    # Target depth interpolation
    targets_ds = interpolate_to_target_depths(glorys_ds, "thetao")
    # Regrid targets to target grid (GLORYS is 0.083, we want 0.25)
    target_grid = get_target_grid()
    targets_ds = targets_ds.interp(lat=target_grid.lat, lon=target_grid.lon, method="linear")
    
    # Create mask from GLORYS surface before regridding or after?
    # After regridding makes the mask exactly 101x241
    mask = create_ocean_mask(targets_ds, "thetao")
    
    # SST
    sst_ds = xr.open_dataset(sst_path)
    sst_ds = fix_lon(sst_ds)
    sst_ds = process_sst(sst_ds, "analysed_sst")
    
    # SSS
    sss_ds = xr.open_dataset(sss_path)
    sss_ds = fix_lon(sss_ds)
    sss_ds = process_sss(sss_ds, "sos")
    
    # SLA / Currents
    sla_ds = xr.open_dataset(sla_path)
    sla_ds = fix_lon(sla_ds)
    sla_ds = process_currents_sla(sla_ds)
    
    # ERA5
    era5_ds = process_era5(era5_path)
    
    # 3. Align Time
    # Normalizing time coordinates to exactly YYYY-MM-DD 00:00:00 or similar
    def normalize_time(ds):
        # Floors time to day to easily match. 
        ds['time'] = ds.indexes['time'].normalize()
        return ds
        
    targets_ds = normalize_time(targets_ds)
    sst_ds = normalize_time(sst_ds)
    sss_ds = normalize_time(sss_ds)
    sla_ds = normalize_time(sla_ds)
    era5_ds = normalize_time(era5_ds)
    
    # Find common times
    common_time = (
        targets_ds.indexes['time']
        .intersection(sst_ds.indexes['time'])
        .intersection(sss_ds.indexes['time'])
        .intersection(sla_ds.indexes['time'])
        .intersection(era5_ds.indexes['time'])
    )
    
    if len(common_time) == 0:
        raise ValueError(f"No common timestamps found for {year}-{month:02d}!")
        
    print(f"Aligned {len(common_time)} days.")
    
    targets_ds = targets_ds.sel(time=common_time)
    sst_ds = sst_ds.sel(time=common_time)
    sss_ds = sss_ds.sel(time=common_time)
    sla_ds = sla_ds.sel(time=common_time)
    era5_ds = era5_ds.sel(time=common_time)
    
    # 4. Stack Inputs
    da_list = [
        sst_ds['analysed_sst'].rename('sst'),
        sss_ds['sos'].rename('sss'),
        sla_ds['sla'].rename('sla'),
        sla_ds['ugos'].rename('u'),
        sla_ds['vgos'].rename('v'),
        era5_ds['10m_u_component_of_wind'].rename('era5_u'),
        era5_ds['10m_v_component_of_wind'].rename('era5_v')
    ]
    
    stacked = xr.concat(da_list, dim='channel')
    stacked = stacked.assign_coords(channel=['sst', 'sss', 'sla', 'u', 'v', 'era5_u', 'era5_v'])
    
    # Create final datasets
    inputs_final = xr.Dataset({'inputs': stacked.transpose('time', 'channel', 'lat', 'lon')})
    targets_final = xr.Dataset({'thetao': targets_ds['thetao'].transpose('time', 'depth', 'lat', 'lon')})
    
    # 5. Apply Mask (Only to targets? Or to inputs?)
    # "Land pixels should become NaN. Input land pixels may eventually be filled with zero after normalization by the training Dataset."
    # We apply mask to inputs so land is NaN.
    # Targets should already be NaN where mask is False because the mask is derived from targets.
    inputs_final = inputs_final.where(mask)
    targets_final = targets_final.where(mask)
    
    # Cast to float32
    inputs_final = inputs_final.astype(np.float32)
    targets_final = targets_final.astype(np.float32)
    
    # Set chunking
    # Time chunks = maybe 5 to match sequence length? Or larger?
    # Kaggle allows around 21GB, so 30 days is fine to hold in memory.
    chunking_inputs = {'time': 10, 'channel': 7, 'lat': 101, 'lon': 241}
    chunking_targets = {'time': 10, 'depth': 15, 'lat': 101, 'lon': 241}
    
    inputs_final = inputs_final.chunk(chunking_inputs)
    targets_final = targets_final.chunk(chunking_targets)
    
    return inputs_final, targets_final, mask

def write_zarr(ds, path):
    if not os.path.exists(path):
        ds.to_zarr(path, mode='w', consolidated=True)
    else:
        # Append
        # Ensure we drop encoding that might conflict with appending
        for var in ds.variables:
            ds[var].encoding.pop('chunks', None)
        ds.to_zarr(path, mode='a', append_dim='time', consolidated=True, align_chunks=True)

def process_all_years(output_path: str, raw_dir: str):
    """
    Main pipeline loop to be executed on Kaggle.
    """
    print("Starting full 30-year pipeline processing (1993-2023)...")
    
    inputs_path = os.path.join(output_path, "inputs.zarr")
    targets_path = os.path.join(output_path, "targets.zarr")
    progress_file = os.path.join(output_path, "progress.json")
    
    processed_months = []
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            processed_months = json.load(f)
            
    for year in range(1993, 2024):
        for month in range(1, 13):
            month_str = f"{year}-{month:02d}"
            if month_str in processed_months:
                print(f"Skipping {month_str}, already processed.")
                continue
                
            try:
                inputs_ds, targets_ds, _ = process_month(year, month, raw_dir, output_path)
                
                # Write to Zarr
                write_zarr(inputs_ds, inputs_path)
                write_zarr(targets_ds, targets_path)
                
                # Cleanup raw
                for f in os.listdir(raw_dir):
                    if f.endswith('.nc'):
                        os.remove(os.path.join(raw_dir, f))
                        
                processed_months.append(month_str)
                with open(progress_file, 'w') as f:
                    json.dump(processed_months, f)
                    
                print(f"Successfully appended {month_str} to Zarr.")
                
            except Exception as e:
                print(f"Error processing {month_str}: {e}")
                raise
            
            # Force GC
            gc.collect()

    print(f"Successfully processed and serialized all data to {output_path}")

def run_qa(inputs_path, targets_path):
    print("\n--- Running QA ---")
    inputs_ds = xr.open_zarr(inputs_path)
    targets_ds = xr.open_zarr(targets_path)
    
    print("Inputs shape:", inputs_ds['inputs'].shape)
    print("Targets shape:", targets_ds['thetao'].shape)
    
    assert inputs_ds['inputs'].shape[1:] == (7, 101, 241)
    assert targets_ds['thetao'].shape[1:] == (15, 101, 241)
    assert list(inputs_ds['channel'].values) == ['sst', 'sss', 'sla', 'u', 'v', 'era5_u', 'era5_v']
    
    times = inputs_ds.time.values
    print("Time range:", times[0], "to", times[-1])
    
    # Check NaN counts
    inputs_na = np.isnan(inputs_ds['inputs'].isel(time=0).values).sum()
    targets_na = np.isnan(targets_ds['thetao'].isel(time=0).values).sum()
    print("NaNs in Inputs (first timestep):", inputs_na)
    print("NaNs in Targets (first timestep):", targets_na)
    print("Valid values mean inputs:", np.nanmean(inputs_ds['inputs'].values))
    print("Valid values mean targets:", np.nanmean(targets_ds['thetao'].values))
    print("QA passed!")

if __name__ == "__main__":
    # Test Jan 1993 only
    raw_dir = "./data/raw"
    processed_dir = "./data/processed_zarr"
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    
    # For Jan 1993, just run process_month directly
    # inputs_ds, targets_ds, mask = process_month(1993, 1, raw_dir, processed_dir)
    # write_zarr(inputs_ds, os.path.join(processed_dir, "inputs.zarr"))
    # write_zarr(targets_ds, os.path.join(processed_dir, "targets.zarr"))
    # run_qa(os.path.join(processed_dir, "inputs.zarr"), os.path.join(processed_dir, "targets.zarr"))
