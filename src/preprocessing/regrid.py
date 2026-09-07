import numpy as np
import xarray as xr

def get_target_grid():
    """
    Creates the target 101x241 grid:
    Latitude: 5 to 30 (0.25 deg resolution) -> (30-5)/0.25 = 100 intervals = 101 points
    Longitude: 45 to 105 (0.25 deg resolution) -> (105-45)/0.25 = 240 intervals = 241 points
    """
    lat = np.linspace(5, 30, 101)
    lon = np.linspace(45, 105, 241)
    
    target_grid = xr.Dataset({
        "lat": (["lat"], lat),
        "lon": (["lon"], lon),
    })
    return target_grid

def process_sst(sst_ds: xr.Dataset, sst_var_name="sst"):
    """
    Convert SST from Kelvin to Celsius and interpolate to exact grid.
    """
    target_grid = get_target_grid()
    
    # Check if max is likely Kelvin (> 100)
    if sst_ds[sst_var_name].max() > 100:
        sst_ds[sst_var_name] = sst_ds[sst_var_name] - 273.15
        
    # Interpolate
    sst_regridded = sst_ds.interp(lat=target_grid.lat, lon=target_grid.lon, method="linear")
    return sst_regridded

def process_sss(sss_ds: xr.Dataset, sss_var_name="sss"):
    """
    Squeeze redundant depth=1 axis from the SSS data and interpolate.
    """
    target_grid = get_target_grid()
    
    if "depth" in sss_ds.dims and sss_ds.sizes["depth"] == 1:
        sss_ds = sss_ds.squeeze(dim="depth", drop=True)
        
    sss_regridded = sss_ds.interp(lat=target_grid.lat, lon=target_grid.lon, method="linear")
    return sss_regridded

def process_currents_sla(ds: xr.Dataset):
    """
    Interpolate offset grids (SLA, Currents U/V) to target 0.25 deg grid.
    """
    target_grid = get_target_grid()
    regridded = ds.interp(lat=target_grid.lat, lon=target_grid.lon, method="linear")
    return regridded
