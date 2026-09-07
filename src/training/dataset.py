import torch
from torch.utils.data import Dataset
import xarray as xr
import numpy as np
import os
import json

class OceanEmbedDataset(Dataset):
    def __init__(self, inputs_path, targets_path, seq_len=5, split='train', stats_file=None):
        """
        Args:
            inputs_path (str): Path to the inputs Zarr store.
            targets_path (str): Path to the targets Zarr store.
            seq_len (int): Sequence length, default is 5.
            split (str): 'train', 'val', or 'test'.
            stats_file (str): Path to normalization stats JSON file.
        """
        # We use zarr backend in xarray to load lazily
        self.inputs_ds = xr.open_zarr(inputs_path)
        self.targets_ds = xr.open_zarr(targets_path)
        
        self.seq_len = seq_len
        self.split = split
        self.stats_file = stats_file
        
        # Determine temporal bounds
        # Total times available:
        self.total_time = len(self.inputs_ds.time)
        
        # Splitting logic based on dates? 
        # The spec says:
        # Train: 1993-2018
        # Val: 2019-2020
        # Test: 2021-2023
        
        # In dummy data, time is just integers 0..time_steps-1. We'll fallback to ratios if actual dates aren't there.
        # But we can check if times are datetime64.
        times = self.inputs_ds.time.values
        if np.issubdtype(times.dtype, np.datetime64):
            years = times.astype('datetime64[Y]').astype(int) + 1970
            if split == 'train':
                self.indices = np.where((years >= 1993) & (years <= 2018))[0]
            elif split == 'val':
                self.indices = np.where((years >= 2019) & (years <= 2020))[0]
            elif split == 'test':
                self.indices = np.where((years >= 2021) & (years <= 2023))[0]
            else:
                self.indices = np.arange(self.total_time)
        else:
            # Fallback for dummy data
            if split == 'train':
                self.indices = np.arange(0, int(self.total_time * 0.7))
            elif split == 'val':
                self.indices = np.arange(int(self.total_time * 0.7), int(self.total_time * 0.85))
            elif split == 'test':
                self.indices = np.arange(int(self.total_time * 0.85), self.total_time)
            else:
                self.indices = np.arange(self.total_time)
                
        # To get sequence of length seq_len, we can only start from index such that index + seq_len <= len(self.indices)
        # Actually, consecutive days! So we need indices[i] + seq_len - 1 to be in indices.
        # Since they are chronologically ordered, we just limit the valid start indices.
        if len(self.indices) >= self.seq_len:
            self.valid_starts = self.indices[:-self.seq_len + 1]
        else:
            self.valid_starts = []
            
        # Load or compute normalization stats
        self.mean = None
        self.std = None
        if self.split == 'train' and stats_file is not None and not os.path.exists(stats_file):
            self._compute_and_save_stats()
        elif stats_file is not None and os.path.exists(stats_file):
            self._load_stats()
            
    def _compute_and_save_stats(self):
        print("Computing normalization stats on training split... This may take a while.")
        
        train_ds = self.inputs_ds.isel(time=self.indices)
        input_var = list(self.inputs_ds.data_vars.keys())[0]
        mean = train_ds[input_var].mean(dim=['time', 'lat', 'lon'], skipna=True).values
        std = train_ds[input_var].std(dim=['time', 'lat', 'lon'], skipna=True).values
        
        std[std == 0] = 1.0
        
        self.mean = mean.astype(np.float32)
        self.std = std.astype(np.float32)
        
        # Match backend expected format
        stats_dict = {
            "dataset": "OceanEmbed Training Baseline (1993-2018)",
            "num_channels": 7,
            "channels": {}
        }
        
        channel_names = ["SST", "SSS", "SLA", "u", "v", "u10", "v10"]
        channel_full_names = [
            "Sea Surface Temperature", "Sea Surface Salinity", "Sea Level Anomaly",
            "Zonal Surface Current", "Meridional Surface Current", 
            "ERA5 Zonal Wind", "ERA5 Meridional Wind"
        ]
        channel_units = ["°C", "psu", "m", "m/s", "m/s", "m/s", "m/s"]
        
        for i in range(7):
            stats_dict["channels"][str(i)] = {
                "name": channel_names[i],
                "full_name": channel_full_names[i],
                "unit": channel_units[i],
                "mean": float(self.mean[i]),
                "std": float(self.std[i])
            }
            
        with open(self.stats_file, 'w') as f:
            json.dump(stats_dict, f, indent=2)
            
        print(f"Saved normalization stats to {self.stats_file}")
        
    def _load_stats(self):
        with open(self.stats_file, 'r') as f:
            stats = json.load(f)
            
        self.mean = np.zeros(7, dtype=np.float32)
        self.std = np.ones(7, dtype=np.float32)
        
        channels_info = stats.get("channels", {})
        for i in range(7):
            ch_key = str(i)
            if ch_key in channels_info:
                self.mean[i] = float(channels_info[ch_key].get("mean", 0.0))
                std_val = float(channels_info[ch_key].get("std", 1.0))
                self.std[i] = std_val if std_val > 1e-7 else 1.0
        
    def __len__(self):
        return len(self.valid_starts)
        
    def __getitem__(self, idx):
        start_idx = self.valid_starts[idx]
        
        # Read seq_len slices using dynamic variable names
        input_var = list(self.inputs_ds.data_vars.keys())[0]
        target_var = list(self.targets_ds.data_vars.keys())[0]
        
        input_slice = self.inputs_ds[input_var].isel(time=slice(start_idx, start_idx + self.seq_len)).values
        target_slice = self.targets_ds[target_var].isel(time=slice(start_idx, start_idx + self.seq_len)).values
        
        # input_slice: (5, 7, 101, 241), target_slice: (5, 15, 101, 241)
        # Convert to tensor
        input_tensor = torch.from_numpy(input_slice).float()
        target_tensor = torch.from_numpy(target_slice).float()
        
        # Normalize
        if self.mean is not None and self.std is not None:
            # Reshape mean and std to broadcast (1, 7, 1, 1)
            m = torch.from_numpy(self.mean).view(1, -1, 1, 1)
            s = torch.from_numpy(self.std).view(1, -1, 1, 1)
            input_tensor = (input_tensor - m) / s
            
        # NaN Handling for Inputs: Convert NaNs to 0.0 after normalization
        input_tensor = torch.nan_to_num(input_tensor, nan=0.0)
        
        # Target NaNs are preserved
        
        return input_tensor, target_tensor
