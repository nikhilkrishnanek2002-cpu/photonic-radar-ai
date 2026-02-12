"""
Integration Ticker Demo with Synchronized Simulation
====================================================

Demonstrates real-time integration ticker with actual radar-EW simulation.

Shows: RADAR → INTEL → EW → JAM → EFFECT

Updates every tick with live data.
"""

import sys
import time
import numpy as np

sys.path.insert(0, '.')

from simulation_engine.synchronized_simulation import SynchronizedRadarEWSimulation
from simulation_engine.physics import TargetState
from ui.integration_ticker import IntegrationTicker
from defense_core import reset_defense_bus


def run_ticker_demo():
    """Run integration ticker demo with real simulation."""
    print("\n" + "="*80)
    print("REAL-TIME INTEGRATION TICKER DEMO")
    print("="*80)
    print("\nShowing: RADAR → INTEL → EW → JAM → EFFECT")
    print("Updates every simulation tick\n")
    print("Legend:")
    print("  ○ = Idle    ● = Active    ✓ = Success    ✗ = Failed    ⋯ = Waiting")
    print("  [Stage:Count] = Stage name with metric count")
    print("\n" + "="*80 + "\n")
    
    time.sleep(2)
    
    # Reset event bus
    reset_defense_bus()
    
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Create scenario with multiple targets
    radar_config = {
        'sensor_id': 'RADAR_01',
        'frame_dt': 0.1,
        'rpm': 60,
        'scan_angle_deg': 120,
        'enable_defense_core': True,
        'enable_ew_effects': True,
        'ew_log_before_after': False,
        'debug_packets': False
    }
    
    ew_config = {
        'effector_id': 'EW_JAMMER_01',
        'enable_ingestion': True,
        'ingestion_mode': 'event_bus',
        'log_all_updates': False
    }
    
    # Create targets
    targets = [
        TargetState(
            id=1,
            pos_x=1000.0,
            pos_y=500.0,
            vel_x=-30.0,
            vel_y=-10.0,
            type="hostile"
        ),
        TargetState(
            id=2,
            pos_x=1500.0,
            pos_y=-300.0,
            vel_x=-40.0,
            vel_y=5.0,
            type="civilian"
        ),
        TargetState(
            id=3,
            pos_x=800.0,
            pos_y=200.0,
            vel_x=-25.0,
            vel_y=-15.0,
            type="hostile"
        )
    ]
    
    # Create simulation
    sim = SynchronizedRadarEWSimulation(
        radar_config=radar_config,
        ew_config=ew_config,
        targets=targets,
        max_frames=50,
        enable_cycle_logging=False
    )
    
    # Create ticker
    ticker = IntegrationTicker()
    
    try:
        # Run simulation with ticker
        for frame in range(50):
            ticker.start_cycle(frame)
            
            # Run simulation tick
            result = sim.tick()
            
            # Update ticker stages
            
            # 1. RADAR stage
            num_detections = result.get('num_detections', 0)
            num_tracks = result.get('num_tracks', 0)
            ticker.update_radar(num_detections, num_tracks)
            
            # 2. INTEL stage
            num_threats = len([t for t in result.get('tracks', []) 
                              if t.get('threat_class') == 'HOSTILE'])
            intel_sent = result.get('intelligence_exported', False)
            ticker.update_intel(num_threats, intel_sent)
            
            # 3. EW stage (simplified - check if threats exist)
            ew_processed = num_threats > 0
            num_decisions = num_threats  # Assume 1 decision per threat
            ticker.update_ew(num_decisions, ew_processed)
            
            # 4. JAM stage (check if EW effects are being applied)
            num_cms = 1 if result.get('ew_effects_applied', False) else 0
            jam_active = num_cms > 0
            ticker.update_jam(num_cms, jam_active)
            
            # 5. EFFECT stage
            num_effects = 1 if result.get('ew_effects_applied', False) else 0
            effect_applied = num_effects > 0
            ticker.update_effect(num_effects, effect_applied)
            
            ticker.end_cycle()
            ticker.print_ticker()
            
            time.sleep(0.1)  # Slow down for visibility
    
    finally:
        sim.stop()
    
    print("\n" + "="*80)
    print("DEMO COMPLETE")
    print("="*80)
    print(f"\nFinal State:")
    final_state = ticker.get_state_dict()
    print(f"  Total frames: {final_state['frame_id']}")
    print(f"  Average latency: {final_state['cycle_latency_ms']:.1f}ms")
    print(f"  Final stages:")
    for stage_name, stage_data in final_state['stages'].items():
        print(f"    {stage_data['label']}: {stage_data['status']} ({stage_data['metric']} items)")
    print("="*80 + "\n")


if __name__ == '__main__':
    run_ticker_demo()
