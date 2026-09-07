import os
import torch

class Config:
    # Model
    in_channels = 7
    out_channels = 15
    cnn_dim = 64
    embed_dim = 256
    transformer_layers = 4
    transformer_heads = 4
    
    # Dataset
    seq_len = 5
    grid_shape = (101, 241)
    batch_size = 1
    num_workers = 0  # 0 for local dummy, can be increased for Kaggle
    prefetch_factor = None
    
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    inputs_path = os.path.join(base_dir, "data", "processed_zarr", "inputs.zarr")
    targets_path = os.path.join(base_dir, "data", "processed_zarr", "targets.zarr")
    stats_file = os.path.join(base_dir, "normalization_stats_train.json")
    checkpoint_dir = os.path.join(base_dir, "checkpoints")
    model_config_path = os.path.join(base_dir, "model_config.json")
    best_model_path = os.path.join(checkpoint_dir, "best_model.pt")
    last_model_path = os.path.join(checkpoint_dir, "last_model.pt")
    training_state_path = os.path.join(checkpoint_dir, "training_state.pt")
    
    # Training
    seed = 42
    optimizer = "AdamW"
    learning_rate = 1e-3
    weight_decay = 1e-4
    scheduler = "ReduceLROnPlateau"
    early_stopping_patience = 8
    max_epochs = 50
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    mixed_precision = False
    log_freq = 1
