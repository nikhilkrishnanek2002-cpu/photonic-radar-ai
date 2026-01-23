"""
System Audit & Stability Test
============================

Strict verification of the entire Photonic Radar pipeline.
Checks for:
1. Import Errors
2. Runtime Crashes
3. Numerical Stability (NaN/Inf)
4. Edge Case Handling (Empty targets, Max noise)

Author: Principal Software Architect
"""

import sys
import os
import numpy as np
import traceback

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline import RadarPipeline
from src.simulation.photonic import PhotonicConfig
from src.simulation.environment import ChannelConfig, Target
from src.simulation.noise import NoiseConfig

def check_stability(data, name):
    if np.any(np.isnan(data)):
        print(f"❌ FAILURE: NaNs detected in {name}")
        return False
    if np.any(np.isinf(data)):
        print(f"❌ FAILURE: Infs detected in {name}")
        return False
    return True

def run_audit():
    print("🔹 Starting System Audit...")
    pipeline = RadarPipeline()
    
    # Standard Config
    p_cfg = PhotonicConfig()
    c_cfg = ChannelConfig()
    n_cfg = NoiseConfig()
    
    tests = [
        ("Normal Operation", [Target(100, 10, 0, "Test")]),
        ("Zero Targets", []),
        ("High Noise", [Target(100, 10, 0, "Test")], {"noise_level_db": 10.0}), # Extreme noise
        ("Silence (Low Noise)", [Target(100, 10, 0, "Test")], {"noise_level_db": -200.0}) # Underflow check
    ]
    
    all_passed = True
    
    for title, targets, *extra in tests:
        print(f"   Testing: {title}...", end=" ")
        
        # Apply overrides
        local_c = ChannelConfig()
        if extra:
            for k,v in extra[0].items():
                setattr(local_c, k, v)
                
        try:
            frame = pipeline.run(p_cfg, local_c, n_cfg, targets)
            
            # Checks
            checks = [
                check_stability(frame.rx_signal, "Rx Signal"),
                check_stability(frame.rd_map, "RD Map"),
                check_stability(frame.spectrogram, "Spectrogram")
            ]
            
            if all(checks):
                print("✅ PASSED")
            else:
                print("⚠️ STABILITY ISSUE")
                all_passed = False
                
        except Exception as e:
            print(f"❌ CRASH detected: {e}")
            traceback.print_exc()
            all_passed = False
            
    # Import Audit
    print("\n🔹 Checking Imports...")
    try:
        import src.ui.components
        import app
        print("✅ UI Modules Importable")
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        all_passed = False
        
    return all_passed

if __name__ == "__main__":
    if run_audit():
        print("\n🌟 SYSTEM AUDIT PASSED")
        sys.exit(0)
    else:
        print("\n💀 SYSTEM AUDIT FAILED")
        sys.exit(1)
