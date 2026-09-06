import os
import cdsapi
# Note: Ensure you have copernicusmarine installed and configured as well
# pip install copernicusmarine

def download_era5(year: int, month: int, output_dir: str):
    """
    Downloads ERA5 U10 and V10 variables for the given year and month.
    """
    c = cdsapi.Client()
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"era5_winds_{year}_{month:02d}.nc")
    
    # Area: North=30, West=45, South=5, East=105
    c.retrieve(
        'reanalysis-era5-single-levels',
        {
            'product_type': 'reanalysis',
            'format': 'netcdf',
            'variable': [
                '10m_u_component_of_wind', '10m_v_component_of_wind',
            ],
            'year': str(year),
            'month': f"{month:02d}",
            'day': [f"{d:02d}" for d in range(1, 32)],
            'time': [
                '00:00', '06:00', '12:00', '18:00',
            ],
            'area': [
                30, 45, 5, 105,
            ],
        },
        output_path)
    return output_path

import subprocess

def download_glorys(year: int, month: int, output_dir: str):
    """
    Downloads GLORYS12V1 3D ocean temperature for the target.
    Product ID: cmems_mod_glo_phy_my_0.083_P1D-m
    """
    os.makedirs(output_dir, exist_ok=True)
    # Define time bounds for the month
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-31" # Copernicus subset gracefully handles invalid end days like Feb 31
    
    output_filename = f"glorys_{year}_{month:02d}.nc"
    
    print(f"Downloading GLORYS12V1 for {start_date} to {output_filename}...")
    cmd = [
        "copernicusmarine", "subset",
        "-i", "cmems_mod_glo_phy_my_0.083deg_P1D-m",
        "-x", "45", "-X", "105", # Longitude
        "-y", "5", "-Y", "30",   # Latitude
        "-z", "0.49", "-Z", "1000", # Depth (GLORYS starts at ~0.494m)
        "-t", start_date, "-T", end_date,
        "-v", "thetao",          # Temperature variable
        "-o", output_dir,
        "-f", output_filename,
        "--force-download"
    ]
    subprocess.run(cmd, check=True)
    print("GLORYS download complete!")

def download_satellite_data(year: int, month: int, output_dir: str):
    """
    Downloads SST (OSTIA) and SLA (CMEMS).
    """
    os.makedirs(output_dir, exist_ok=True)
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-31"
    
    print(f"Downloading OSTIA SST for {start_date}...")
    subprocess.run([
        "copernicusmarine", "subset",
        "-i", "METOFFICE-GLO-SST-L4-REP-OBS-SST",
        "-x", "45", "-X", "105", "-y", "5", "-Y", "30",
        "-t", start_date, "-T", end_date,
        "-v", "analysed_sst",
        "-o", output_dir, "-f", f"sst_{year}_{month:02d}.nc", "--force-download"
    ], check=True)

if __name__ == "__main__":
    print("Starting 1-month local test download (Jan 1993)...")
    # ERA5 is already downloaded from our previous test
    # download_era5(1993, 1, "./data/raw/")
    download_glorys(1993, 1, "./data/raw/")
    download_satellite_data(1993, 1, "./data/raw/")
    print("All downloads complete!")
