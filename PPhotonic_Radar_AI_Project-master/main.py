import os
import sys

# --- MUST BE AT THE TOP TO PREVENT ERRORS ---
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Initialize config, logging and run startup checks before heavy imports
from src.config import get_config
from src.logger import init_logging, log_event
from src.startup_checks import run_startup_checks

cfg = get_config()
init_logging(cfg)
_startup = run_startup_checks()

import torch
# prefer CPU if startup checks show no GPU
use_cuda = _startup.get("gpu_available", False)
device = torch.device("cuda" if use_cuda else "cpu")
print(f"Using device: {device}")
log_event(f"Using device: {device}")

import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from src.feature_extractor import get_all_features
from src.signal_generator import generate_radar_signal
from src.model_pytorch import build_pytorch_model
from src.evaluate import evaluate_pytorch
import cv2

# ===============================
# CONFIG
# ===============================
os.makedirs("results", exist_ok=True)

LABELS = ["Drone", "Aircraft", "Bird", "Helicopter", "Missile", "Clutter"]
NUM_CLASSES = len(LABELS)
SAMPLES_PER_CLASS = 100
IMG_SIZE = 128

# ===============================
# DATASET GENERATION
# ===============================
rd_list, spec_list, meta_list, y_list = [], [], [], []

print("Generating Multi-Input Photonic Radar dataset... 📡")
for label_idx, label in enumerate(LABELS):
    for _ in range(SAMPLES_PER_CLASS):
        dist = np.random.uniform(50, 500)
        signal = generate_radar_signal(label.lower(), distance=dist)
        
        rd, spec, meta, _ = get_all_features(signal)
        
        # Resize to match model input
        rd = cv2.resize(rd, (IMG_SIZE, IMG_SIZE))
        spec = cv2.resize(spec, (IMG_SIZE, IMG_SIZE))
        
        # Normalize
        rd = (rd - np.mean(rd)) / (np.std(rd) + 1e-8)
        spec = (spec - np.mean(spec)) / (np.std(spec) + 1e-8)
        
        rd_list.append(rd)
        spec_list.append(spec)
        meta_list.append(meta)
        y_list.append(label_idx)

# Convert to PyTorch Tensors
rd_tensor = torch.tensor(np.array(rd_list), dtype=torch.float32)
spec_tensor = torch.tensor(np.array(spec_list), dtype=torch.float32)
# Standardize metadata too
meta_array = np.array(meta_list)
meta_mean = np.mean(meta_array, axis=0)
meta_std = np.std(meta_array, axis=0) + 1e-8
meta_array = (meta_array - meta_mean) / meta_std
meta_tensor = torch.tensor(meta_array, dtype=torch.float32)
y_tensor = torch.tensor(np.array(y_list), dtype=torch.long)

# Split into Train and Test
dataset = TensorDataset(rd_tensor, spec_tensor, meta_tensor, y_tensor)
train_size = int(0.8 * len(dataset))
test_size = len(dataset) - train_size
train_dataset, test_dataset = torch.utils.data.random_split(dataset, [train_size, test_size])

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

# ===============================
# MODEL
# ===============================
model = build_pytorch_model(num_classes=NUM_CLASSES).to(device)
optimizer = optim.Adam(model.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss()

# ===============================
# TRAIN
# ===============================
EPOCHS = 15 # Increased for better convergence with randomized data
print("Starting Training... 🚀")
model.train()
for epoch in range(EPOCHS):
    running_loss = 0.0
    for b_rd, b_spec, b_meta, b_y in train_loader:
        b_rd, b_spec, b_meta, b_y = b_rd.to(device), b_spec.to(device), b_meta.to(device), b_y.to(device)
        optimizer.zero_grad()
        outputs = model(b_rd, b_spec, b_meta)
        loss = criterion(outputs, b_y)
        loss.backward()
        optimizer.step()
        running_loss += loss.item()
    
    print(f"Epoch {epoch+1}/{EPOCHS}, Loss: {running_loss/len(train_loader):.4f}")

# ===============================
# EVALUATE
# ===============================
print("\nEvaluating Model... 📊")
evaluate_pytorch(model, test_loader, device=device)

# ===============================
# SAVE MODEL
# ===============================
model_path = "results/radar_model_pytorch.pt"
torch.save(model.state_dict(), model_path)
print(f"✅ PyTorch Model saved at {model_path}")
