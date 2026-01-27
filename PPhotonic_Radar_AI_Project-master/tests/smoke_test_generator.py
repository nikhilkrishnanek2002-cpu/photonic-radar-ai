import torch
from ai_models.dataset_generator import RadarDatasetGenerator

def test_generator_fidelity():
    print("🚀 Verifying Dataset Generator Fidelity...")
    cfg = {"duration": 0.1, "fs": 1e6}
    gen = RadarDatasetGenerator(cfg)
    
    # Test individual classes
    for cls in ["drone", "aircraft", "missile", "noise"]:
        sample = gen.generate_sample(cls)
        print(f"  - Class: {cls}")
        print(f"    - RD Map: {sample['rd_map'].shape}")
        print(f"    - Spectrogram: {sample['spectrogram'].shape}")
        print(f"    - Time-Series: {sample['time_series'].shape}")
        print(f"    - Metadata Kinematics: {sample['metadata']['kinematics']}")
        
        assert sample['rd_map'].shape == (128, 128), "RD Map shape mismatch" # Fixed 128x128 FFT output
        assert sample['time_series'].shape == (2, 512), "Time-series shape mismatch"
        
    print("✅ Generator fidelity verified.")

def test_batch_integration():
    print("\n🚀 Verifying ML Integration (Batching)...")
    cfg = {"duration": 0.05, "fs": 1e5}
    gen = RadarDatasetGenerator(cfg)
    batch = gen.generate_batch(samples_per_class=2)
    
    print(f"  - Batch Labels: {batch['labels']}")
    print(f"  - Spectrograms Shape: {batch['spectrograms'].shape}")
    print(f"  - Time Series Shape: {batch['time_series'].shape}")
    
    assert batch['spectrograms'].ndim == 4, "Batch spectrograms should stay 4D (N, C, H, W)"
    assert batch['labels'].shape[0] == 10, "Target classes count mismatch (5 classes * 2 samples)" # drone, aircraft, missile, bird, noise
    
    print("✅ ML integration batching verified.")

if __name__ == "__main__":
    test_generator_fidelity()
    test_batch_integration()
