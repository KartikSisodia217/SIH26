import os
import xarray as xr
import sys

# Add src to python path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.preprocessing.regrid import get_target_grid

def test_era5_alignment():
    print("Loading ERA5 raw data...")
    ds = xr.open_dataset("./data/raw/era5_winds_1993_01.nc")
    
    # ERA5 raw data should have 'u10' and 'v10' and coordinates 'latitude' and 'longitude'
    print(f"Raw shape: {ds.dims}")
    
    print("Generating target 101x241 grid...")
    target_grid = get_target_grid()
    print(f"Target grid Lat bounds: {target_grid.lat.min().values} to {target_grid.lat.max().values} (Size: {target_grid.lat.size})")
    print(f"Target grid Lon bounds: {target_grid.lon.min().values} to {target_grid.lon.max().values} (Size: {target_grid.lon.size})")

    # Rename ERA5 coords to match our target grid ('lat', 'lon') if they are named 'latitude', 'longitude'
    if 'latitude' in ds.coords:
        ds = ds.rename({'latitude': 'lat', 'longitude': 'lon'})

    print("Regridding ERA5 to target grid...")
    ds_regridded = ds.interp(lat=target_grid.lat, lon=target_grid.lon, method="linear")
    
    print(f"Regridded shape: {ds_regridded.dims}")
    
    # Assertions to guarantee contract
    assert ds_regridded.lat.size == 101, "Latitude dimension is incorrect!"
    assert ds_regridded.lon.size == 241, "Longitude dimension is incorrect!"
    print("\n✅ SUCCESS: ERA5 data perfectly aligns with the (Time, 101, 241) spatial requirement!")

if __name__ == "__main__":
    test_era5_alignment()
