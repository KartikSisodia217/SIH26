# This script can be run in Kaggle directly if the repository is cloned, or converted to a Notebook.
import os
import subprocess

# 1. Install dependencies
# subprocess.run(["pip", "install", "copernicusmarine", "cdsapi", "xarray", "zarr", "netCDF4", "dask"])

# 2. Configure Credentials
# Ensure Kaggle Secrets contain:
# COPERNICUSMARINE_SERVICE_USERNAME
# COPERNICUSMARINE_SERVICE_PASSWORD
# CDSAPI_URL
# CDSAPI_KEY

# os.environ["COPERNICUSMARINE_SERVICE_USERNAME"] = "..."

# 3. Run Pipeline
from src.preprocessing.build_zarr import process_all_years

if __name__ == "__main__":
    raw_dir = "/kaggle/working/data/raw"
    processed_dir = "/kaggle/working/data/processed_zarr"
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    process_all_years(processed_dir, raw_dir)
