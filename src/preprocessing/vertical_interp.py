import numpy as np
import xarray as xr

# The 15 target depths
TARGET_DEPTHS = [0, 5, 10, 20, 30, 50, 75, 100, 125, 150, 200, 300, 500, 700, 1000]

def extrapolate_surface_temp(glorys_ds: xr.Dataset, temp_var_name="thetao"):
    """
    GLORYS does not natively output a 0 m depth.
    Shallowest is ~0.494 m, second is ~1.541 m.
    Formula: T(0) = T(0.494) + (0 - 0.494) * [T(1.541) - T(0.494)] / [1.541 - 0.494]
    """
    # Assuming the first two depth indices correspond to ~0.494 and ~1.541
    # We select them by index to avoid strict float matching issues.
    t_0_494 = glorys_ds[temp_var_name].isel(depth=0)
    t_1_541 = glorys_ds[temp_var_name].isel(depth=1)
    
    # Check exact coordinates from GLORYS array if possible, otherwise use constants
    z1 = glorys_ds.depth.isel(depth=0).values # ~0.494
    z2 = glorys_ds.depth.isel(depth=1).values # ~1.541
    
    t_0 = t_0_494 + (0 - z1) * (t_1_541 - t_0_494) / (z2 - z1)
    
    t_0 = t_0.expand_dims(depth=[0.0])
    
    ds_0 = t_0.to_dataset(name=temp_var_name)
    # Concatenate along depth
    # Since glorys_ds might have other variables, we just extract temp_var_name
    glorys_ds_only = glorys_ds[[temp_var_name]]
    glorys_ds_extended = xr.concat([ds_0, glorys_ds_only], dim="depth")
    return glorys_ds_extended

def interpolate_to_target_depths(glorys_ds: xr.Dataset, temp_var_name="thetao"):
    """
    Interpolate 3D GLORYS temperature to the exact 15 target depths.
    """
    ds_extended = extrapolate_surface_temp(glorys_ds, temp_var_name)
    ds_interp = ds_extended.interp(depth=TARGET_DEPTHS, method="linear")
    return ds_interp

def create_ocean_mask(glorys_ds: xr.Dataset, temp_var_name="thetao"):
    """
    Constructs the 101x241 master ocean mask.
    Land will be set to NaN. Valid ocean regions will have a valid target value.
    We can define the mask where surface temperature is not NaN.
    """
    # Just take a single timestep surface slice to find NaNs
    mask = glorys_ds[temp_var_name].isel(time=0, depth=0).notnull()
    return mask

def apply_ocean_mask(ds: xr.Dataset, mask: xr.DataArray):
    """
    Applies the bounding mask to any dataset (Input variables).
    """
    return ds.where(mask)
