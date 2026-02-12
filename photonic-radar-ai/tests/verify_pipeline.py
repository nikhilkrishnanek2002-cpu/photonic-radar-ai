
import sys
import os
import time
import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.generator import RadarGenerator, Target
from src.signal.features import get_all_features
from src.ai.inference import InferenceEngine

def test_pipeline():
    print("🔹 Starting System Verification...")
    
    # 1. Test Generator
    print("Testing RadarGenerator...")
    try:
        gen = RadarGenerator(fs=4096)
        targets = [Target(range_m=50, velocity_m_s=10, rcs_db=-10, category="Drone")]
        data = gen.simulate_scenario(targets, duration=0.1)
        signal = data['if_signal']
        print(f"✅ Generated Signal: {signal.shape} (Type: {signal.dtype})")
    except Exception as e:
        print(f"❌ Generator Failed: {e}")
        return False
        
    # 2. Test Signal Processing
    print("Testing Signal Processing...")
    try:
        rd_map, spec, metadata, params = get_all_features(signal, fs=gen.fs)
        print(f"✅ Range-Doppler Map: {rd_map.shape}")
        print(f"✅ Spectrogram: {spec.shape}")
        print(f"✅ Metadata: {metadata.shape}")
    except Exception as e:
        print(f"❌ Signal Processing Failed: {e}")
        return False
        
    # 3. Test AI Inference
    print("Testing AI Inference...")
    try:
        ai = InferenceEngine() # Model might not exist, should handle gracefully
        probs = ai.predict(rd_map, spec, metadata)
        print(f"✅ Inference Output: {probs} (Sum: {np.sum(probs):.2f})")
    except Exception as e:
        print(f"❌ AI Inference Failed: {e}")
        return False
        
    print("🌟 SYSTEM VERIFIED SUCCESSFULLY")
    return True

if __name__ == "__main__":
    success = test_pipeline()
    sys.exit(0 if success else 1)
