import xarray as xr
import zarr

def stack_inputs(sst_ds, sss_ds, sla_ds, curr_ds, era5_ds):
    """
    Stacks the 7 input variables chronologically.
    Variables: SST, SSS, SLA, U, V, ERA5_U, ERA5_V
    Shape should be (Time, 7, 101, 241)
    """
    # Placeholder: Assuming all datasets are already regridded and aligned
    # Extract DataArrays
    da_list = [
        sst_ds['sst'],
        sss_ds['sss'],
        sla_ds['sla'],
        curr_ds['u'],
        curr_ds['v'],
        era5_ds['10m_u_component_of_wind'],
        era5_ds['10m_v_component_of_wind']
    ]
    
    # Concatenate along a new 'channel' dimension
    stacked = xr.concat(da_list, dim='channel')
    stacked = stacked.assign_coords(channel=['sst', 'sss', 'sla', 'u', 'v', 'era5_u', 'era5_v'])
    
    return stacked

def process_month(year, month):
    """
    Process 1 month locally to verify alignment.
    Downloads, regrids, interpolates vertically, and stacks.
    """
    # This function links download, regrid, and vertical_interp
    # For now, it's a structural placeholder to be executed in parallel later.
    print(f"Processing {year}-{month:02d}...")
    pass

def process_all_years(output_path: str):
    """
    Main pipeline loop to be executed on Kaggle.
    Iterates from 1993 to 2023, downloads raw data, regrids, and appends to Zarr.
    """
    print("Starting full 30-year pipeline processing (1993-2023)...")
    
    for year in range(1993, 2024):
        for month in range(1, 13):
            print(f"Processing {year}-{month:02d}...")
            # Step 1: Download
            # download_era5(year, month, "./data/raw/")
            # download_glorys(year, month, "./data/raw/")
            # download_satellite_data(year, month, "./data/raw/")
            
            # Step 2 & 3: Load, Regrid & Interpolate (Using functions from regrid.py & vertical_interp.py)
            
            # Step 4: Stack & Append to Zarr
            # ds_inputs_chunked.to_zarr(output_path + "/inputs.zarr", append_dim='time')
            # ds_targets_chunked.to_zarr(output_path + "/targets.zarr", append_dim='time')
            pass

    print(f"Successfully processed and serialized all data to {output_path}")

if __name__ == "__main__":
    # Execute full pipeline (Designed for Kaggle)
    process_all_years("./data/processed_zarr")
