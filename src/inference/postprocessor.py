"""
OceanEmbed Data Postprocessor Module.
Converts ConvFormer model output tensors (B, 5, 15, 101, 241) into structured point profiles,
2D horizontal depth slices, and D26 isotherm depth metrics.

Contract (Spec Sections 18, 27, 30):
- Output Tensor: (B, T, 15, 101, 241) native Celsius temperature tensor.
- Depth Levels (15): 0, 5, 10, 20, 30, 50, 75, 100, 125, 150, 200, 300, 500, 700, 1000 m.
- Postprocessor handles D26 derivation downstream of the neural network.
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import torch
from src.inference.mock_engine import calculate_d26, is_land_coordinate, TARGET_DEPTHS_M


class OceanDataPostprocessor:
    """Post-processes PyTorch model temperature tensors into frontend-ready JSON structures."""

    def __init__(self):
        self.depths_m: List[float] = TARGET_DEPTHS_M
        self.lat_min, self.lat_max = 5.0, 30.0
        self.lon_min, self.lon_max = 45.0, 105.0
        self.num_lat = 101
        self.num_lon = 241

        # Precompute coordinate arrays
        self.lats = np.linspace(self.lat_min, self.lat_max, self.num_lat)
        self.lons = np.linspace(self.lon_min, self.lon_max, self.num_lon)

    def coord_to_index(self, lat: float, lon: float) -> Tuple[int, int]:
        """Converts lat/lon coordinate into nearest 2D grid index (i_lat, j_lon)."""
        lat_idx = int(np.clip(np.round((lat - self.lat_min) / (self.lat_max - self.lat_min) * (self.num_lat - 1)), 0, self.num_lat - 1))
        lon_idx = int(np.clip(np.round((lon - self.lon_min) / (self.lon_max - self.lon_min) * (self.num_lon - 1)), 0, self.num_lon - 1))
        return lat_idx, lon_idx

    def _to_numpy(self, tensor: Union[torch.Tensor, np.ndarray]) -> np.ndarray:
        """Helper to ensure input tensor is a float32 NumPy array."""
        if isinstance(tensor, torch.Tensor):
            return tensor.detach().cpu().numpy().astype(np.float32)
        return np.array(tensor, dtype=np.float32)

    def extract_point_profile(
        self,
        output_tensor: Union[torch.Tensor, np.ndarray],
        latitude: float,
        longitude: float,
        timestep_idx: int = -1
    ) -> Dict[str, Any]:
        """
        Extracts 15-depth vertical temperature profile at specified (latitude, longitude).
        Output tensor shape: (B, 5, 15, 101, 241) or (5, 15, 101, 241) or (15, 101, 241).
        """
        arr = self._to_numpy(output_tensor)
        
        # Squeeze batch dimension if present
        if len(arr.shape) == 5:
            arr = arr[0]  # (5, 15, 101, 241)
        if len(arr.shape) == 4:
            arr = arr[timestep_idx]  # (15, 101, 241)

        lat_idx, lon_idx = self.coord_to_index(latitude, longitude)
        is_land = is_land_coordinate(latitude, longitude)

        if is_land:
            return {
                "latitude": round(latitude, 4),
                "longitude": round(longitude, 4),
                "depths_m": self.depths_m,
                "temperatures_c": [None] * len(self.depths_m),
                "d26_depth_m": None,
                "surface_temp_c": None,
                "bottom_temp_c": None,
                "is_land": True,
                "units": "°C",
            }

        # Extract 15 depths temperature vector
        raw_profile = arr[:, lat_idx, lon_idx]  # (15,)
        temperatures = [round(float(t), 2) for t in raw_profile]

        d26_depth, _, _ = calculate_d26(self.depths_m, temperatures)

        return {
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "depths_m": self.depths_m,
            "temperatures_c": temperatures,
            "d26_depth_m": d26_depth,
            "surface_temp_c": temperatures[0],
            "bottom_temp_c": temperatures[-1],
            "is_land": False,
            "units": "°C",
        }

    def extract_depth_slice(
        self,
        output_tensor: Union[torch.Tensor, np.ndarray],
        depth_m: float,
        timestep_idx: int = -1
    ) -> Dict[str, Any]:
        """
        Extracts 2D grid (101 x 241) temperature slice at closest target depth level.
        Output tensor shape: (B, 5, 15, 101, 241) or (5, 15, 101, 241) or (15, 101, 241).
        """
        arr = self._to_numpy(output_tensor)
        if len(arr.shape) == 5:
            arr = arr[0]
        if len(arr.shape) == 4:
            arr = arr[timestep_idx]

        # Find closest depth index
        closest_depth = min(self.depths_m, key=lambda d: abs(d - depth_m))
        depth_idx = self.depths_m.index(closest_depth)

        raw_slice = arr[depth_idx]  # (101, 241)

        grid = []
        for i in range(self.num_lat):
            lat_val = float(self.lats[i])
            row = []
            for j in range(self.num_lon):
                lon_val = float(self.lons[j])
                if is_land_coordinate(lat_val, lon_val):
                    row.append(None)
                else:
                    row.append(round(float(raw_slice[i, j]), 2))
            grid.append(row)

        return {
            "depth_m": closest_depth,
            "grid_shape": [self.num_lat, self.num_lon],
            "latitudes": [round(float(lat), 2) for lat in self.lats],
            "longitudes": [round(float(lon), 2) for lon in self.lons],
            "temperatures_2d": grid,
            "units": "°C",
        }
