"""
Synthetic Oceanographic Inference Engine for OceanEmbed Phase 1.
Generates physically realistic 15-depth subsurface temperature profiles and 2D grid slices
over the North Indian Ocean domain (5°N–30°N, 45°E–105°E).

This allows Member 4 (Frontend Lead) to immediately integrate and build the interactive
React/Leaflet dashboard before final PyTorch model weights are available.
"""

import math
from typing import List, Tuple, Optional, Dict, Any

# 15 target depth levels as specified by OceanEmbed architecture contract
TARGET_DEPTHS_M = [0.0, 5.0, 10.0, 20.0, 30.0, 50.0, 75.0, 100.0, 125.0, 150.0, 200.0, 300.0, 500.0, 700.0, 1000.0]

# Geographic Grid Specifications
LAT_MIN, LAT_MAX = 5.0, 30.0
LON_MIN, LON_MAX = 45.0, 105.0
NUM_LAT = 101
NUM_LON = 241


def is_land_coordinate(lat: float, lon: float) -> bool:
    """
    Simplified geographic land mask check for the North Indian Ocean bounding box.
    Identifies main landmasses (Indian subcontinent, Arabian Peninsula, Indochina/Myanmar).
    """
    # Indian Subcontinent approximation (triangular polygon extending down to ~8°N near Kanyakumari)
    if 8.0 <= lat <= 30.0 and 68.5 <= lon <= 89.0:
        # Approximate west coast boundary line (from 24°N,68°E to 8°N,77°E)
        west_bound = 68.5 + (77.5 - 68.5) * (24.0 - lat) / (24.0 - 8.0)
        # Approximate east coast boundary line (from 22°N,89°E to 8°N,77.5°E)
        east_bound = 89.0 - (89.0 - 77.5) * (22.0 - lat) / (22.0 - 8.0)
        if west_bound <= lon <= east_bound:
            return True

    # Arabian Peninsula (West of 60°E, North of 12°N)
    if lat >= 12.0 and lon <= 58.5:
        if lat >= 12.0 + (60.0 - lon) * 0.4:
            return True

    # Indochina & Myanmar (East of 98°E, North of 10°N)
    if lat >= 10.0 and lon >= 98.0:
        return True

    # Horn of Africa (South-West corner: lat < 12°N and lon < 51°E)
    if lat <= 12.0 and lon <= 51.0:
        if lat >= 5.0 + (lon - 45.0) * 0.8:
            return True

    return False


def calculate_d26(depths: List[float], temps: List[float]) -> Tuple[Optional[float], bool, str]:
    """
    Derives the D26 Isotherm Depth (depth where temperature drops to 26°C) using 1D linear interpolation.
    Formula from Spec Section 27:
      D26 = z1 + (26 - T1) * (z2 - z1) / (T2 - T1)
    
    Edge Cases:
    - If surface temp < 26°C -> D26 is None (No thermocline crossing).
    - If temp remains >= 26°C down to 1000m -> D26 > 1000m.
    """
    if not temps or len(depths) != len(temps):
        return None, False, "Invalid depth/temperature input."

    # Check if surface is below 26°C
    if temps[0] < 26.0:
        return None, False, f"Surface temperature ({temps[0]:.2f}°C) is below 26.0°C."

    # Scan profile from top down
    for i in range(len(temps) - 1):
        z1, z2 = depths[i], depths[i + 1]
        t1, t2 = temps[i], temps[i + 1]

        if t1 >= 26.0 and t2 < 26.0:
            # Linear interpolation formula
            d26 = z1 + (26.0 - t1) * (z2 - z1) / (t2 - t1)
            return round(d26, 2), True, f"D26 thermocline crossing interpolated between {z1}m ({t1:.2f}°C) and {z2}m ({t2:.2f}°C)."

    # If temp stays above 26°C all the way down
    if temps[-1] >= 26.0:
        return 1000.0, True, "Temperature remains >= 26.0°C down to maximum depth 1000m."

    return None, False, "Unable to determine D26 isotherm depth."


def generate_mock_profile(lat: float, lon: float) -> Dict[str, Any]:
    """
    Generates a physically realistic 15-depth vertical ocean temperature profile for (lat, lon).
    Models surface warming, mixed layer depth, thermocline decay, and deep ocean cooling.
    """
    is_land = is_land_coordinate(lat, lon)
    if is_land:
        return {
            "latitude": lat,
            "longitude": lon,
            "depths_m": TARGET_DEPTHS_M,
            "temperatures_c": [None] * len(TARGET_DEPTHS_M),
            "d26_depth_m": None,
            "surface_temp_c": None,
            "bottom_temp_c": None,
            "is_land": True,
            "units": "°C",
        }

    # Physical parameters based on latitude / location in North Indian Ocean
    # Warmer near equator (5-10°N), slightly cooler further north.
    base_sst = 28.5 - 0.1 * (lat - 5.0) + 0.5 * math.sin(math.radians(lon * 2))
    base_sst = max(25.5, min(30.5, base_sst))  # Clamp between 25.5°C and 30.5°C

    # Mixed layer depth ~30m - 60m
    mld = 40.0 + 15.0 * math.cos(math.radians(lat * 3 + lon))

    temperatures = []
    for z in TARGET_DEPTHS_M:
        if z <= mld:
            # Quasi-isothermal mixed layer
            temp = base_sst - 0.005 * z
        elif z <= 200.0:
            # Steep thermocline drop (from MLD down to 200m)
            mld_temp = base_sst - 0.005 * mld
            decay_factor = (z - mld) / (200.0 - mld)
            temp = mld_temp - (mld_temp - 13.0) * (decay_factor ** 0.8)
        else:
            # Deep ocean asymptotic decay down to ~4.5°C at 1000m
            temp = 13.0 - (13.0 - 4.5) * ((z - 200.0) / 800.0) ** 0.6

        temperatures.append(round(temp, 2))

    d26_depth, is_valid_d26, _ = calculate_d26(TARGET_DEPTHS_M, temperatures)

    return {
        "latitude": lat,
        "longitude": lon,
        "depths_m": TARGET_DEPTHS_M,
        "temperatures_c": temperatures,
        "d26_depth_m": d26_depth,
        "surface_temp_c": temperatures[0],
        "bottom_temp_c": temperatures[-1],
        "is_land": False,
        "units": "°C",
    }


def generate_mock_slice(depth_m: float) -> Dict[str, Any]:
    """
    Generates a 2D temperature grid (101 x 241) for a specific target depth level.
    """
    # Snap to closest target depth
    closest_depth = min(TARGET_DEPTHS_M, key=lambda d: abs(d - depth_m))

    lats = [round(LAT_MIN + i * (LAT_MAX - LAT_MIN) / (NUM_LAT - 1), 2) for i in range(NUM_LAT)]
    lons = [round(LON_MIN + j * (LON_MAX - LON_MIN) / (NUM_LON - 1), 2) for j in range(NUM_LON)]

    grid = []
    for i, lat in enumerate(lats):
        row = []
        for j, lon in enumerate(lons):
            prof = generate_mock_profile(lat, lon)
            if prof["is_land"]:
                row.append(None)
            else:
                idx = TARGET_DEPTHS_M.index(closest_depth)
                row.append(prof["temperatures_c"][idx])
        grid.append(row)

    return {
        "depth_m": closest_depth,
        "grid_shape": [NUM_LAT, NUM_LON],
        "latitudes": lats,
        "longitudes": lons,
        "temperatures_2d": grid,
        "units": "°C",
    }
