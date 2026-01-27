import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import os
from ai_models.dataset_generator import RadarDatasetGenerator
from ai_models.architectures import get_hybrid_model # Updated import
import cv2

def create_pytorch_dataset(samples_per_class=50):
    # increased fs for better resolution in JEM/Micro-Doppler
    cfg = {"duration": 0.1, "fs": 5e5}
    generator = RadarDatasetGenerator(cfg)
    
    print("Generating simulated photonic radar dataset...")
    # Generate batch directly using the generator's optimized method
    batch = generator.generate_batch(samples_per_class=samples_per_class)
    
    # Batch dictionary contains: 'rd_maps', 'spectrograms', 'time_series', 'labels'
    return (
        batch['rd_maps'],
        batch['spectrograms'],
        batch['time_series'],
        batch['labels']
    )

def train_pytorch_model(epochs=5):
    # 1. Generate Data
    rd, spec, ts, y = create_pytorch_dataset(samples_per_class=20) # Small batch for demo/speed
    
    # 2. Create DataLoader
    dataset = TensorDataset(spec, ts, y) # Model takes (spectrogram, time_series)
    loader = DataLoader(dataset, batch_size=16, shuffle=True)

    # 3. Build Model
    # 5 classes: drone, aircraft, missile, bird, noise
    model = get_hybrid_model(num_classes=5)
    
    # device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # model.to(device)
    
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()

    print("Starting training...")
    model.train()
    
    for epoch in range(epochs):
        running_loss = 0.0
        for i, (b_spec, b_ts, b_y) in enumerate(loader):
            # b_spec, b_ts, b_y = b_spec.to(device), b_ts.to(device), b_y.to(device)
            
            optimizer.zero_grad()
            outputs, attn = model(b_spec, b_ts)
            loss = criterion(outputs, b_y)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
        
        print(f"Epoch {epoch+1}/{epochs}, Loss: {running_loss/len(loader):.4f}")

    # Save the model
    os.makedirs("results", exist_ok=True)
    torch.save(model.state_dict(), "results/radar_model_pytorch.pt")
    print("Model saved to results/radar_model_pytorch.pt")
    return model

if __name__ == "__main__":
    train_pytorch_model()
