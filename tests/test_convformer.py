import torch
import torch.nn as nn
from src.models.convformer import ConvFormer, PatchEmbedding

def test_model_shape():
    model = ConvFormer(transformer_layers=4)
    x = torch.randn(1, 5, 7, 101, 241)
    out = model(x)
    assert out.shape == (1, 5, 15, 101, 241)

def test_model_parameters():
    model = ConvFormer(transformer_layers=4)
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Total parameters: {total_params}")
    print(f"Trainable parameters: {trainable_params}")

def test_padding():
    patch_embed = PatchEmbedding(in_channels=64, embed_dim=256, patch_size=4)
    x = torch.randn(1, 64, 101, 241)
    patches = patch_embed(x)
    assert patches.shape == (1, 256, 26, 61)
    
def test_batch_independence():
    model = ConvFormer(transformer_layers=4)
    model.eval()
    
    # Create two identical samples in a batch
    x = torch.randn(2, 5, 7, 101, 241)
    x[1] = x[0].clone()
    
    with torch.no_grad():
        out = model(x)
        
    assert torch.allclose(out[0], out[1], atol=1e-6)

def test_temporal_behavior():
    model = ConvFormer(transformer_layers=4)
    x = torch.randn(1, 5, 7, 101, 241)
    out = model(x)
    assert out.shape[1] == 5
    
def test_backprop():
    model = ConvFormer(transformer_layers=4)
    x = torch.randn(1, 5, 7, 101, 241)
    targets = torch.randn(1, 5, 15, 101, 241)
    
    out = model(x)
    loss = nn.MSELoss()(out, targets)
    loss.backward()
    
    # Check that grads exist
    for name, param in model.named_parameters():
        assert param.grad is not None

def test_six_layer_config():
    model = ConvFormer(transformer_layers=6)
    x = torch.randn(1, 5, 7, 101, 241)
    out = model(x)
    assert out.shape == (1, 5, 15, 101, 241)

if __name__ == "__main__":
    test_model_shape()
    test_model_parameters()
    test_padding()
    test_batch_independence()
    test_temporal_behavior()
    test_backprop()
    test_six_layer_config()
    print("All ConvFormer tests passed!")
