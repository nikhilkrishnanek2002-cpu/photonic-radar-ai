import time
import numpy as np
from simulation_engine.orchestrator import SimulationOrchestrator, TargetState
from photonic.signals import PhotonicConfig

def verify_scanning():
    print("🚀 Verifying Continuous Scanning Simulation...")
    
    # 1. Setup Config
    radar_config = {
        "fs": 1e6,
        "n_pulses": 32,
        "frame_dt": 0.05, # Fast simulation
        "rpm": 60.0,      # 1 Rotation per second (Very fast for testing)
        "beamwidth_deg": 45.0 # Wide beam
    }
    
    # 2. Setup Targets (One at 0 deg, one at 180 deg)
    targets = [
        TargetState(id=1, pos_x=1000, pos_y=0, vel_x=0, vel_y=0, type="drone"),      # Azimuth 0
        TargetState(id=2, pos_x=-1000, pos_y=0, vel_x=0, vel_y=0, type="aircraft"),  # Azimuth 180
    ]
    
    sim = SimulationOrchestrator(radar_config, targets)
    
    print("  - Running simulation loop...")
    detection_log = {1: [], 2: []}
    
    # Run for 2.2 seconds (2 full rotations + margin)
    for frame in sim.run_loop(max_frames=44):
        angle = frame["scan_angle"]
        illuminated = frame["illuminated_ids"]
        
        # Log which targets are seen at which angle
        for tid in illuminated:
            detection_log[tid].append(angle)
            
        # Optional: Print status every 10 frames
        if frame["frame"] % 10 == 0:
            print(f"    Frame {frame['frame']}: Angle {angle:.1f}°, Seen: {illuminated}")
    
    # 3. Analyze Results
    print("\n  - Analyzing Illumination Sectors:")
    
    # Target 1 (Az 0) should be seen when angle is near 0 or 360
    # Beamwidth 45 -> Seen between [-22.5, 22.5] -> [0, 22.5] and [337.5, 360]
    seen_angles_1 = detection_log[1]
    msg_1 = f"    TGT 1 (0°): Seen at angles {np.min(seen_angles_1):.1f} - {np.max(seen_angles_1):.1f}"
    print(msg_1)
    
    # Check if we saw it around 0
    has_zero_crossing = any(a < 25 or a > 335 for a in seen_angles_1)
    assert has_zero_crossing, "Target 1 should be seen near 0 degrees!"
    
    # Target 2 (Az 180) should be seen when angle is near 180
    # Beamwidth 45 -> Seen between [157.5, 202.5]
    seen_angles_2 = detection_log[2]
    min_2, max_2 = np.min(seen_angles_2), np.max(seen_angles_2)
    msg_2 = f"    TGT 2 (180°): Seen at angles {min_2:.1f} - {max_2:.1f}"
    print(msg_2)
    
    assert 150 < np.mean(seen_angles_2) < 210, "Target 2 should be centered around 180!"
    
    print("✅ Scanning mechanics verified.")

if __name__ == "__main__":
    verify_scanning()
