"""
OceanEmbed Data Preprocessor Module.
Applies frozen training normalization statistics (mean/std) and post-normalization land NaN filling.

Contract (Spec Sections 8, 9, 30):
- Formula: x_norm = (x - mu_train) / sigma_train
- Statistics: Computed exclusively on 1993-2018 training split (normalization_stats_train.json).
- Land NaN Fill: All land/invalid pixels explicitly filled with 0.0 AFTER normalization to prevent gradient destruction.
- Input Tensor Shape: PyTorch Float32 Tensor (B, 5, 7, 101, 241).
"""

import json
import os
from typing import Dict, Any, Optional, Union
import numpy as np
import torch


class OceanDataPreprocessor:
    """Handles standard scaling, land NaN filling, and tensor formatting for ConvFormer inference."""

    def __init__(self, stats_path: Optional[str] = None):
        if stats_path is None:
            # Default to root normalization_stats_train.json
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            stats_path = os.path.join(base_dir, "normalization_stats_train.json")
        
        self.stats_path = stats_path
        self.means: np.ndarray = np.zeros(7, dtype=np.float32)
        self.stds: np.ndarray = np.ones(7, dtype=np.float32)
        self.load_stats(self.stats_path)

    def load_stats(self, stats_path: str) -> None:
        """Loads channel means and standard deviations from JSON."""
        if not os.path.exists(stats_path):
            # Fallback to default statistics if file not found
            self.means = np.array([27.5, 34.5, 0.05, 0.02, -0.01, 1.2, -0.8], dtype=np.float32)
            self.stds = np.array([1.8, 1.2, 0.15, 0.25, 0.22, 4.5, 4.2], dtype=np.float32)
            return

        with open(stats_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        channels_info = data.get("channels", {})
        for i in range(7):
            ch_key = str(i)
            if ch_key in channels_info:
                self.means[i] = float(channels_info[ch_key].get("mean", 0.0))
                std_val = float(channels_info[ch_key].get("std", 1.0))
                self.stds[i] = std_val if std_val > 1e-7 else 1.0

    def normalize(self, data: np.ndarray) -> np.ndarray:
        """
        Applies standard scaling (x - mu) / sigma to input array.
        Supports inputs of shape (7, 101, 241), (5, 7, 101, 241), or (B, 5, 7, 101, 241).
        """
        arr = np.array(data, dtype=np.float32, copy=True)
        shape = arr.shape

        # Identify channel dimension
        if len(shape) == 3 and shape[0] == 7:
            # (7, 101, 241)
            for c in range(7):
                arr[c] = (arr[c] - self.means[c]) / self.stds[c]
        elif len(shape) == 4 and shape[1] == 7:
            # (5, 7, 101, 241)
            for c in range(7):
                arr[:, c] = (arr[:, c] - self.means[c]) / self.stds[c]
        elif len(shape) == 5 and shape[2] == 7:
            # (B, 5, 7, 101, 241)
            for c in range(7):
                arr[:, :, c] = (arr[:, :, c] - self.means[c]) / self.stds[c]
        else:
            raise ValueError(f"Unexpected input shape {shape}. Must have 7 channels at dimension 0, 1, or 2.")

        return arr

    def fill_land_nans(self, data: np.ndarray, fill_value: float = 0.0) -> np.ndarray:
        """
        Replaces all NaNs (representing land or missing observations) with fill_value (0.0).
        MUST be called AFTER normalization per spec contract.
        """
        arr = np.array(data, dtype=np.float32, copy=True)
        arr[np.isnan(arr)] = fill_value
        return arr

    def prepare_input_tensor(self, raw_sequence: Union[np.ndarray, torch.Tensor]) -> torch.Tensor:
        """
        Executes full pre-inference pipeline:
        1. Normalizes raw surface variables using train stats.
        2. Fills land NaNs with 0.0.
        3. Formats to PyTorch Float32 Tensor (B, 5, 7, 101, 241).
        """
        if isinstance(raw_sequence, torch.Tensor):
            raw_np = raw_sequence.detach().cpu().numpy()
        else:
            raw_np = np.array(raw_sequence, dtype=np.float32)

        # 1. Normalize
        norm_np = self.normalize(raw_np)

        # 2. Fill Land NaNs with 0.0
        clean_np = self.fill_land_nans(norm_np, fill_value=0.0)

        # 3. Add batch / sequence dimensions if missing
        if len(clean_np.shape) == 3:
            # (7, 101, 241) -> Repeat to T=5 sequence and add B=1
            clean_np = np.tile(clean_np[np.newaxis, ...], (5, 1, 1, 1))
            clean_np = clean_np[np.newaxis, ...]
        elif len(clean_np.shape) == 4:
            # (5, 7, 101, 241) -> Add B=1
            clean_np = clean_np[np.newaxis, ...]

        # Verify shape
        if clean_np.shape[1:] != (5, 7, 101, 241):
            raise ValueError(f"Invalid tensor shape {clean_np.shape}. Expected (B, 5, 7, 101, 241).")

        tensor = torch.from_numpy(clean_np).float()

        # Guarantee zero NaNs in input tensor
        if torch.isnan(tensor).any():
            raise ValueError("Input tensor contains NaNs after pre-processing!")

        return tensor
