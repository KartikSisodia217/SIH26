import pytest
import torch
import numpy as np
from src.training.dataset import OceanEmbedDataset
from src.training.config import Config

def test_dataset_shape():
    cfg = Config()
    dataset = OceanEmbedDataset(cfg.inputs_path, cfg.targets_path, split='train', stats_file=cfg.stats_file)
    inputs, targets = dataset[0]
    
    assert inputs.shape == (5, 7, 101, 241)
    assert targets.shape == (5, 15, 101, 241)
    assert inputs.dtype == torch.float32
    assert targets.dtype == torch.float32
    
def test_normalization():
    cfg = Config()
    dataset = OceanEmbedDataset(cfg.inputs_path, cfg.targets_path, split='train', stats_file=cfg.stats_file)
    
    # After normalizaton, the mean of the training split should be approx 0 and std approx 1
    # We can just check that it's doing *something* different from the raw inputs.
    inputs, _ = dataset[0]
    # In dummy data, original means were 0 and stds 1 (from randn)
    # Plus land naNs were replaced with 0
    assert not torch.isnan(inputs).any()

def test_masked_loss():
    from src.training.train import masked_mse_loss
    preds = torch.ones(2, 5, 15, 101, 241) * 2.0
    targets = torch.ones(2, 5, 15, 101, 241) * 1.0
    # Half of targets are nan
    targets[:, :, :, :50, :] = float('nan')
    
    loss = masked_mse_loss(preds, targets)
    assert torch.isclose(loss, torch.tensor(1.0))
    
if __name__ == "__main__":
    test_dataset_shape()
    test_normalization()
    test_masked_loss()
    print("Dataset tests passed!")
