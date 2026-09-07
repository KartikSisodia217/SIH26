import os
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
import numpy as np
import random
import json
import argparse
import tempfile

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

def atomic_save(state, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp_path = path + f".tmp.{os.getpid()}"
    torch.save(state, temp_path)
    os.replace(temp_path, path)

def save_checkpoint(model, optimizer, scheduler, scaler, epoch, batch_idx, global_step, 
                    best_val_loss, train_history, val_history, path):
    state = {
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'scheduler_state_dict': scheduler.state_dict() if scheduler else None,
        'scaler_state_dict': scaler.state_dict() if scaler else None,
        'epoch': epoch,
        'batch_idx': batch_idx,
        'global_step': global_step,
        'best_val_loss': best_val_loss,
        'train_history': train_history,
        'val_history': val_history,
        'rng_states': {
            'python': random.getstate(),
            'numpy': np.random.get_state(),
            'torch': torch.get_rng_state(),
            'cuda': torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
        }
    }
    atomic_save(state, path)

def load_checkpoint(model, optimizer, scheduler, scaler, path):
    print(f"Resuming from checkpoint {path}")
    checkpoint = torch.load(path, map_location='cpu', weights_only=False)
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    if scheduler and checkpoint.get('scheduler_state_dict'):
        scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
    if scaler and checkpoint.get('scaler_state_dict'):
        scaler.load_state_dict(checkpoint['scaler_state_dict'])
        
    rng_states = checkpoint.get('rng_states')
    if rng_states:
        random.setstate(rng_states['python'])
        np.random.set_state(rng_states['numpy'])
        torch.set_rng_state(rng_states['torch'])
        if rng_states['cuda'] and torch.cuda.is_available():
            torch.cuda.set_rng_state_all(rng_states['cuda'])
            
    epoch = checkpoint.get('epoch', 0)
    batch_idx = checkpoint.get('batch_idx', -1)
    global_step = checkpoint.get('global_step', 0)
    best_val_loss = checkpoint.get('best_val_loss', float('inf'))
    train_history = checkpoint.get('train_history', [])
    val_history = checkpoint.get('val_history', [])
    
    return epoch, batch_idx, global_step, best_val_loss, train_history, val_history

def train(dummy_mode=False, resume_path=None, test_interval=None):
    cfg = Config()
    
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
    
    val_loader = DataLoader(val_dataset, batch_size=cfg.batch_size, shuffle=False, 
                            num_workers=cfg.num_workers, prefetch_factor=cfg.prefetch_factor)
                            
    print("Initializing model...")
    model = ConvFormer(in_channels=cfg.in_channels, out_channels=cfg.out_channels,
                       cnn_dim=cfg.cnn_dim, embed_dim=cfg.embed_dim,
                       transformer_layers=cfg.transformer_layers)
    model.to(device)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.learning_rate, weight_decay=cfg.weight_decay)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=3, factor=0.5)
    
    scaler = torch.cuda.amp.GradScaler() if getattr(cfg, 'mixed_precision', False) and device.type == 'cuda' else None
    
    start_epoch = 0
    start_batch_idx = -1
    global_step = 0
    best_val_loss = float('inf')
    train_history = []
    val_history = []
    epochs_no_improve = 0
    
    # Seed initialization
    set_seed(cfg.seed)
    
    if resume_path and os.path.exists(resume_path):
        start_epoch, start_batch_idx, global_step, best_val_loss, train_history, val_history = load_checkpoint(
            model, optimizer, scheduler, scaler, resume_path
        )
        if start_batch_idx == -1:
            # We finished the epoch in the checkpoint, advance to next epoch
            start_epoch += 1
            start_batch_idx = 0
        else:
            # We are resuming mid-epoch, so start_batch_idx is the next batch to run.
            start_batch_idx += 1
    else:
        start_batch_idx = 0

    max_epochs = 1 if dummy_mode else cfg.max_epochs
    print(f"Starting training for {max_epochs - start_epoch} epochs...")
    
    checkpoint_interval = test_interval if test_interval is not None else getattr(cfg, 'checkpoint_interval', 100)
    
    for epoch in range(start_epoch, max_epochs):
        # Deterministic shuffle per epoch
        g = torch.Generator()
        g.manual_seed(cfg.seed + epoch)
        train_loader = DataLoader(train_dataset, batch_size=cfg.batch_size, shuffle=True, 
                                  num_workers=cfg.num_workers, prefetch_factor=cfg.prefetch_factor,
                                  generator=g)
        
        # Train
        model.train()
        train_loss = 0.0
        batches_processed = 0
        
        for i, (inputs, targets) in enumerate(train_loader):
            if i < start_batch_idx:
                continue # Skip batches if resuming mid-epoch
                
            inputs, targets = inputs.to(device), targets.to(device)
            
            optimizer.zero_grad()
            
            if scaler:
                with torch.cuda.amp.autocast():
                    preds = model(inputs)
                    loss = masked_mse_loss(preds, targets)
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()
            else:
                preds = model(inputs)
                loss = masked_mse_loss(preds, targets)
                loss.backward()
                optimizer.step()
            
            loss_val = loss.item()
            train_loss += loss_val
            batches_processed += 1
            global_step += 1
            
            if (i + 1) % cfg.log_freq == 0:
                print(f"Epoch {epoch} | Step {i+1}/{len(train_loader)} | Train Loss: {loss_val:.4f}")
                
            # Periodic checkpoint
            if (i + 1) % checkpoint_interval == 0:
                latest_path = os.path.join(cfg.checkpoint_dir, "latest_batch.pt")
                print(f"Saving periodic checkpoint to {latest_path}")
                save_checkpoint(model, optimizer, scheduler, scaler, epoch, i, global_step,
                                best_val_loss, train_history, val_history, latest_path)
                if dummy_mode and test_interval is not None:
                    # In test mode, we want to stop after taking the checkpoint to test resuming
                    print("Test mode: stopping after periodic checkpoint.")
                    return

        # End of epoch
        start_batch_idx = 0 # reset for next epoch
        
        train_loss /= max(1, batches_processed)
        train_history.append(train_loss)
        
        # Eval
        model.eval()
        val_loss = 0.0
        val_metrics = {"mae": 0.0, "rmse": 0.0, "r2": 0.0}
        with torch.no_grad():
            for inputs, targets in val_loader:
                inputs, targets = inputs.to(device), targets.to(device)
                
                if scaler:
                    with torch.cuda.amp.autocast():
                        preds = model(inputs)
                        loss = masked_mse_loss(preds, targets)
                else:
                    preds = model(inputs)
                    loss = masked_mse_loss(preds, targets)
                    
                val_loss += loss.item()
                
                batch_metrics = get_metrics(preds, targets)
                for k in val_metrics:
                    val_metrics[k] += batch_metrics[k]
                    
        val_loss /= max(1, len(val_loader))
        for k in val_metrics:
            val_metrics[k] /= max(1, len(val_loader))
            
        val_history.append(val_loss)
            
        print(f"--- Epoch {epoch} Summary ---")
        print(f"Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}")
        print(f"Val MAE: {val_metrics['mae']:.4f} | Val RMSE: {val_metrics['rmse']:.4f} | Val R2: {val_metrics['r2']:.4f}")
        
        scheduler.step(val_loss)
        
        # Save End-of-Epoch
        epoch_path = os.path.join(cfg.checkpoint_dir, f"epoch_{epoch:03d}.pt")
        # Save as completed epoch by setting batch_idx to -1
        save_checkpoint(model, optimizer, scheduler, scaler, epoch, -1, global_step,
                        best_val_loss, train_history, val_history, epoch_path)
        
        # Update latest_batch.pt as well to reflect end of epoch
        latest_path = os.path.join(cfg.checkpoint_dir, "latest_batch.pt")
        save_checkpoint(model, optimizer, scheduler, scaler, epoch, -1, global_step,
                        best_val_loss, train_history, val_history, latest_path)
        
        # Save Best
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            epochs_no_improve = 0
            # Save final_model.pt for backend (just state_dict to avoid code dependencies)
            final_model_path = os.path.join(cfg.base_dir, "final_model.pt")
            torch.save(model.state_dict(), final_model_path)
            # Save full checkpoint as best.pt
            best_path = os.path.join(cfg.checkpoint_dir, "best.pt")
            save_checkpoint(model, optimizer, scheduler, scaler, epoch, -1, global_step,
                            best_val_loss, train_history, val_history, best_path)
            print("=> Saved new best model!")
        else:
            epochs_no_improve += 1
            print(f"No improvement for {epochs_no_improve} epochs.")
            if epochs_no_improve >= cfg.early_stopping_patience:
                print("Early stopping triggered!")
                break
                
    print("Training finished!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", type=str, default=None, help="Path to checkpoint to resume from")
    parser.add_argument("--dummy", action="store_true", help="Run in dummy mode")
    parser.add_argument("--test-interval", type=int, default=None, help="Override checkpoint interval for testing")
    args = parser.parse_args()
    
    train(dummy_mode=args.dummy, resume_path=args.resume, test_interval=args.test_interval)
