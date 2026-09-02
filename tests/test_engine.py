"""
Automated Unit Tests for ConvFormer PyTorch Inference Engine and Fallback Mechanism.
"""

import os
import tempfile
import torch
import torch.nn as nn
from src.inference.engine import ConvFormerInferenceEngine, reset_inference_engine


def test_engine_fallback_when_model_missing():
    """Verify engine operates in mock fallback mode when final_model.pt does not exist."""
    engine = reset_inference_engine(model_path="non_existent_file.pt")
    assert engine.is_real_model is False
    assert engine.mode == "mock_fallback"

    # Test predict execution in fallback mode
    input_tensor = torch.randn(1, 5, 7, 101, 241, dtype=torch.float32)
    output_tensor = engine.predict(input_tensor)
    
    assert isinstance(output_tensor, torch.Tensor)
    assert output_tensor.shape == (1, 5, 15, 101, 241)


class DummyModel(nn.Module):
    """Simple PyTorch dummy module mapping (B, 5, 7, 101, 241) -> (B, 5, 15, 101, 241)."""
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv2d(7, 15, kernel_size=1)

    def forward(self, x):
        # x shape: (B, 5, 7, 101, 241)
        B, T, C, H, W = x.shape
        x_reshaped = x.view(B * T, C, H, W)
        out_reshaped = self.conv(x_reshaped)
        return out_reshaped.view(B, T, 15, H, W)


def test_engine_loading_real_pytorch_model():
    """Verify engine successfully loads and executes PyTorch nn.Module checkpoint."""
    dummy_model = DummyModel()
    
    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as tmp:
        tmp_path = tmp.name
        torch.save(dummy_model, tmp_path)

    try:
        engine = reset_inference_engine(model_path=tmp_path)
        assert engine.is_real_model is True
        assert engine.mode == "real_pytorch"

        input_tensor = torch.randn(1, 5, 7, 101, 241, dtype=torch.float32)
        output_tensor = engine.predict(input_tensor)

        assert isinstance(output_tensor, torch.Tensor)
        assert output_tensor.shape == (1, 5, 15, 101, 241)
        assert not torch.isnan(output_tensor).any()

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        # Reset engine back to default
        reset_inference_engine()
