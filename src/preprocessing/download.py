import os
import subprocess
import calendar
import cdsapi

def get_last_day(year, month):
    return calendar.monthrange(year, month)[1]

def download_era5(year: int, month: int, output_dir: str):
    """
    Downloads ERA5 U10 and V10 variables for the given year and month.
    """
    c = cdsapi.Client()
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"era5_winds_{year}_{month:02d}.nc")
    if os.path.exists(output_path):
        print(f"Skipping ERA5 download, {output_path} exists.")
        return output_path
        
    last_day = get_last_day(year, month)
    days = [f"{d:02d}" for d in range(1, last_day + 1)]
    
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
            'day': days,
            'time': [
                '00:00', '06:00', '12:00', '18:00',
            ],
            'area': [
                30, 45, 5, 105,
            ],
        },
        output_path)
    return output_path

def download_glorys(year: int, month: int, output_dir: str):
    """
    Downloads GLORYS12V1 3D ocean temperature for the target.
    Product ID: cmems_mod_glo_phy_my_0.083deg_P1D-m
    """
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"glorys_{year}_{month:02d}.nc"
    if os.path.exists(os.path.join(output_dir, output_filename)):
        print(f"Skipping GLORYS download, {output_filename} exists.")
        return os.path.join(output_dir, output_filename)
        
    start_date = f"{year}-{month:02d}-01"
    last_day = get_last_day(year, month)
    end_date = f"{year}-{month:02d}-{last_day}"
    
    cmd = [
        "copernicusmarine", "subset",
        "-i", "cmems_mod_glo_phy_my_0.083deg_P1D-m",
        "-x", "45", "-X", "105", "-y", "5", "-Y", "30",
        "-z", "0.49", "-Z", "1000",
        "-t", start_date, "-T", end_date,
        "-v", "thetao",
        "-o", output_dir, "-f", output_filename,
        "--force-download"
    ]
    subprocess.run(cmd, check=True)
    return os.path.join(output_dir, output_filename)

def download_sst(year: int, month: int, output_dir: str):
    """
    Downloads SST (OSTIA).
    """
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"sst_{year}_{month:02d}.nc"
    if os.path.exists(os.path.join(output_dir, output_filename)):
        return os.path.join(output_dir, output_filename)
        
    start_date = f"{year}-{month:02d}-01"
    last_day = get_last_day(year, month)
    end_date = f"{year}-{month:02d}-{last_day}"
    
    cmd = [
        "copernicusmarine", "subset",
        "-i", "METOFFICE-GLO-SST-L4-REP-OBS-SST",
        "-x", "45", "-X", "105", "-y", "5", "-Y", "30",
        "-t", start_date, "-T", end_date,
        "-v", "analysed_sst",
        "-o", output_dir, "-f", output_filename,
        "--force-download"
    ]
    subprocess.run(cmd, check=True)
    return os.path.join(output_dir, output_filename)

def download_sss(year: int, month: int, output_dir: str):
    """
    Downloads SSS (Multi-Obs).
    """
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"sss_{year}_{month:02d}.nc"
    if os.path.exists(os.path.join(output_dir, output_filename)):
        return os.path.join(output_dir, output_filename)
        
    start_date = f"{year}-{month:02d}-01"
    last_day = get_last_day(year, month)
    end_date = f"{year}-{month:02d}-{last_day}"
    
    cmd = [
        "copernicusmarine", "subset",
        "-i", "cmems_obs-mob_glo_phy-sss_my_multi_P1D",
        "-x", "45", "-X", "105", "-y", "5", "-Y", "30",
        "-t", start_date, "-T", end_date,
        "-v", "sos",
        "-o", output_dir, "-f", output_filename,
        "--force-download"
    ]
    subprocess.run(cmd, check=True)
    return os.path.join(output_dir, output_filename)

def download_sla_currents(year: int, month: int, output_dir: str):
    """
    Downloads SLA, U, and V (SEALEVEL).
    """
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"sla_uv_{year}_{month:02d}.nc"
    if os.path.exists(os.path.join(output_dir, output_filename)):
        return os.path.join(output_dir, output_filename)
        
    start_date = f"{year}-{month:02d}-01"
    last_day = get_last_day(year, month)
    end_date = f"{year}-{month:02d}-{last_day}"
    
    cmd = [
        "copernicusmarine", "subset",
        "-i", "cmems_obs-sl_glo_phy-ssh_my_allsat-l4-duacs-0.125deg_P1D",
        "-x", "45", "-X", "105", "-y", "5", "-Y", "30",
        "-t", start_date, "-T", end_date,
        "-v", "sla", "-v", "ugos", "-v", "vgos",
        "-o", output_dir, "-f", output_filename,
        "--force-download"
    ]
    subprocess.run(cmd, check=True)
    return os.path.join(output_dir, output_filename)

if __name__ == "__main__":
    print("Starting 1-month local test download (Jan 1993)...")
    out = "./data/raw"
    download_era5(1993, 1, out)
    download_glorys(1993, 1, out)
    download_sst(1993, 1, out)
    download_sss(1993, 1, out)
    download_sla_currents(1993, 1, out)
    print("All downloads complete!")
