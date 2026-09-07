import os
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
import numpy as np
import random
import json

from src.models.convformer import ConvFormer
from src.training.dataset import OceanEmbedDataset
from src.training.config import Config

def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def masked_mse_loss(preds, targets):
    valid_mask = ~torch.isnan(targets)
    if not valid_mask.any():
        return torch.tensor(0.0, device=preds.device, requires_grad=True)
    return F.mse_loss(preds[valid_mask], targets[valid_mask])

def get_metrics(preds, targets):
    valid_mask = ~torch.isnan(targets)
    if not valid_mask.any():
        return {"mae": 0.0, "rmse": 0.0, "r2": 0.0}
    
    valid_preds = preds[valid_mask]
    valid_targets = targets[valid_mask]
    
    mae = F.l1_loss(valid_preds, valid_targets).item()
    rmse = torch.sqrt(F.mse_loss(valid_preds, valid_targets)).item()
    
    target_mean = valid_targets.mean()
    ss_tot = torch.sum((valid_targets - target_mean) ** 2)
    ss_res = torch.sum((valid_targets - valid_preds) ** 2)
    r2 = (1 - ss_res / ss_tot).item() if ss_tot > 0 else 0.0
    
    return {"mae": mae, "rmse": rmse, "r2": r2}

def save_checkpoint(model, optimizer, scheduler, epoch, best_val_loss, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    state = {
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'scheduler_state_dict': scheduler.state_dict() if scheduler else None,
        'epoch': epoch,
        'best_val_loss': best_val_loss
    }
    torch.save(state, path)

def load_checkpoint(model, optimizer, scheduler, path):
    checkpoint = torch.load(path, map_location='cpu')
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    if scheduler and checkpoint['scheduler_state_dict']:
        scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
    return checkpoint['epoch'], checkpoint['best_val_loss']

def train(dummy_mode=False):
    cfg = Config()
    set_seed(cfg.seed)
    device = torch.device(cfg.device)
    print(f"Using device: {device}")
    
    # Write model config for backend
    model_config = {
        "model_name": "ConvFormer",
        "seq_len": cfg.seq_len,
        "in_channels": cfg.in_channels,
        "out_channels": cfg.out_channels,
        "grid_shape": cfg.grid_shape,
        "cnn_dim": cfg.cnn_dim,
        "embed_dim": cfg.embed_dim,
        "transformer_layers": cfg.transformer_layers
    }
    os.makedirs(os.path.dirname(cfg.model_config_path), exist_ok=True)
    with open(cfg.model_config_path, "w") as f:
        json.dump(model_config, f)
        
    print("Initializing datasets...")
    train_dataset = OceanEmbedDataset(cfg.inputs_path, cfg.targets_path, split='train', stats_file=cfg.stats_file)
    val_dataset = OceanEmbedDataset(cfg.inputs_path, cfg.targets_path, split='val', stats_file=cfg.stats_file)
    
    # DataLoader
    train_loader = DataLoader(train_dataset, batch_size=cfg.batch_size, shuffle=True, 
                              num_workers=cfg.num_workers, prefetch_factor=cfg.prefetch_factor)
    val_loader = DataLoader(val_dataset, batch_size=cfg.batch_size, shuffle=False, 
                            num_workers=cfg.num_workers, prefetch_factor=cfg.prefetch_factor)
                            
    print("Initializing model...")
    model = ConvFormer(in_channels=cfg.in_channels, out_channels=cfg.out_channels,
                       cnn_dim=cfg.cnn_dim, embed_dim=cfg.embed_dim,
                       transformer_layers=cfg.transformer_layers)
    model.to(device)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.learning_rate, weight_decay=cfg.weight_decay)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=3, factor=0.5)
    
    start_epoch = 0
    best_val_loss = float('inf')
    epochs_no_improve = 0
    
    if os.path.exists(cfg.training_state_path):
        print(f"Resuming from checkpoint {cfg.training_state_path}")
        start_epoch, best_val_loss = load_checkpoint(model, optimizer, scheduler, cfg.training_state_path)
        start_epoch += 1

    max_epochs = 1 if dummy_mode else cfg.max_epochs
    print(f"Starting training for {max_epochs - start_epoch} epochs...")
    
    for epoch in range(start_epoch, max_epochs):
        # Train
        model.train()
        train_loss = 0.0
        for i, (inputs, targets) in enumerate(train_loader):
            inputs, targets = inputs.to(device), targets.to(device)
            
            optimizer.zero_grad()
            preds = model(inputs)
            loss = masked_mse_loss(preds, targets)
            
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            
            if (i + 1) % cfg.log_freq == 0:
                print(f"Epoch {epoch} | Step {i+1}/{len(train_loader)} | Train Loss: {loss.item():.4f}")
                
        train_loss /= max(1, len(train_loader))
        
        # Eval
        model.eval()
        val_loss = 0.0
        val_metrics = {"mae": 0.0, "rmse": 0.0, "r2": 0.0}
        with torch.no_grad():
            for inputs, targets in val_loader:
                inputs, targets = inputs.to(device), targets.to(device)
                preds = model(inputs)
                loss = masked_mse_loss(preds, targets)
                val_loss += loss.item()
                
                batch_metrics = get_metrics(preds, targets)
                for k in val_metrics:
                    val_metrics[k] += batch_metrics[k]
                    
        val_loss /= max(1, len(val_loader))
        for k in val_metrics:
            val_metrics[k] /= max(1, len(val_loader))
            
        print(f"--- Epoch {epoch} Summary ---")
        print(f"Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}")
        print(f"Val MAE: {val_metrics['mae']:.4f} | Val RMSE: {val_metrics['rmse']:.4f} | Val R2: {val_metrics['r2']:.4f}")
        
        scheduler.step(val_loss)
        
        # Save Last
        save_checkpoint(model, optimizer, scheduler, epoch, best_val_loss, cfg.training_state_path)
        save_checkpoint(model, optimizer, scheduler, epoch, best_val_loss, cfg.last_model_path)
        
        # Save Best
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            epochs_no_improve = 0
            # Save final_model.pt for backend (just state_dict to avoid code dependencies)
            final_model_path = os.path.join(cfg.base_dir, "final_model.pt")
            torch.save(model.state_dict(), final_model_path)
            # Also save in checkpoints
            torch.save(model.state_dict(), cfg.best_model_path)
            print("=> Saved new best model!")
        else:
            epochs_no_improve += 1
            print(f"No improvement for {epochs_no_improve} epochs.")
            if epochs_no_improve >= cfg.early_stopping_patience:
                print("Early stopping triggered!")
                break
                
    print("Training finished!")

if __name__ == "__main__":
    train(dummy_mode=True)
