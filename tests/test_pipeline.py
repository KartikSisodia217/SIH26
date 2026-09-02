"""
Automated Pipeline Tests for Preprocessor, Normalization, Land NaN filling, and Postprocessor.
Verifies compliance with OceanEmbed Specification Sections 8, 9, 18, 27, and 30.
"""

import numpy as np
import torch
from src.inference.preprocessor import OceanDataPreprocessor
from src.inference.postprocessor import OceanDataPostprocessor


def test_preprocessor_stats_loading():
    """Verify preprocessor loads normalization statistics from normalization_stats_train.json."""
    preprocessor = OceanDataPreprocessor()
    assert len(preprocessor.means) == 7
    assert len(preprocessor.stds) == 7
    assert preprocessor.means[0] == 27.5  # SST mean
    assert preprocessor.stds[0] == 1.8    # SST std


def test_preprocessor_normalization_formula():
    """Verify standard scaling math: x_norm = (x - mu) / sigma."""
    preprocessor = OceanDataPreprocessor()
    raw = np.array([27.5, 34.5, 0.05, 0.02, -0.01, 1.2, -0.8], dtype=np.float32)
    raw_expanded = np.tile(raw[:, np.newaxis, np.newaxis], (1, 101, 241))
    
    norm = preprocessor.normalize(raw_expanded)
    # Since raw == means, norm should equal 0.0 across all channels
    assert np.allclose(norm, 0.0, atol=1e-5)


def test_preprocessor_land_nan_filling():
    """Verify land/invalid pixels are explicitly filled with 0.0 after normalization."""
    preprocessor = OceanDataPreprocessor()
    arr_with_nans = np.full((7, 101, 241), np.nan, dtype=np.float32)
    
    clean_arr = preprocessor.fill_land_nans(arr_with_nans, fill_value=0.0)
    assert not np.isnan(clean_arr).any()
    assert (clean_arr == 0.0).all()


def test_preprocessor_prepare_input_tensor_shape_and_nans():
    """Verify prepare_input_tensor outputs (1, 5, 7, 101, 241) Float32 Tensor with ZERO NaNs."""
    preprocessor = OceanDataPreprocessor()
    raw_sequence = np.random.randn(5, 7, 101, 241).astype(np.float32)
    raw_sequence[:, :, 10:20, 10:20] = np.nan  # Inject land NaNs
    
    tensor = preprocessor.prepare_input_tensor(raw_sequence)
    assert isinstance(tensor, torch.Tensor)
    assert tensor.dtype == torch.float32
    assert tensor.shape == (1, 5, 7, 101, 241)
    assert not torch.isnan(tensor).any()


def test_postprocessor_coord_to_index():
    """Verify lat/lon mapping to 101x241 grid indices."""
    postprocessor = OceanDataPostprocessor()
    
    # Bottom-Left Corner (5°N, 45°E) -> (0, 0)
    i0, j0 = postprocessor.coord_to_index(5.0, 45.0)
    assert i0 == 0 and j0 == 0

    # Top-Right Corner (30°N, 105°E) -> (100, 240)
    i1, j1 = postprocessor.coord_to_index(30.0, 105.0)
    assert i1 == 100 and j1 == 240

    # Center (17.5°N, 75°E) -> (50, 120)
    ic, jc = postprocessor.coord_to_index(17.5, 75.0)
    assert ic == 50 and jc == 120


def test_postprocessor_extract_point_profile():
    """Verify point profile extraction from (1, 5, 15, 101, 241) PyTorch tensor."""
    postprocessor = OceanDataPostprocessor()
    
    # Create realistic output tensor: surface=28°C dropping to 4°C at 1000m
    dummy_output = torch.zeros(1, 5, 15, 101, 241, dtype=torch.float32)
    depth_temps = [28.5, 28.5, 28.0, 27.5, 27.0, 25.0, 22.0, 18.0, 15.0, 13.0, 11.0, 8.0, 6.0, 5.0, 4.0]
    for d, temp in enumerate(depth_temps):
        dummy_output[0, :, d, :, :] = temp

    profile = postprocessor.extract_point_profile(dummy_output, latitude=15.0, longitude=65.0)
    assert profile["latitude"] == 15.0
    assert profile["longitude"] == 65.0
    assert profile["is_land"] is False
    assert len(profile["depths_m"]) == 15
    assert profile["surface_temp_c"] == 28.5
    assert profile["bottom_temp_c"] == 4.0
    assert profile["d26_depth_m"] is not None


def test_postprocessor_extract_depth_slice():
    """Verify 2D depth slice extraction from PyTorch output tensor."""
    postprocessor = OceanDataPostprocessor()
    dummy_output = torch.zeros(1, 5, 15, 101, 241, dtype=torch.float32)
    dummy_output[0, -1, 5, :, :] = 25.0  # Set depth_m=50m (idx=5) to 25°C

    slice_data = postprocessor.extract_depth_slice(dummy_output, depth_m=50.0)
    assert slice_data["depth_m"] == 50.0
    assert slice_data["grid_shape"] == [101, 241]
    assert len(slice_data["temperatures_2d"]) == 101
    assert len(slice_data["temperatures_2d"][0]) == 241
