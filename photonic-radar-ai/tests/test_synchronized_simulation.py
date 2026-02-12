"""
Synchronized Simulation Test Suite
==================================

Tests for synchronized radar-EW closed-loop simulation.
"""

import sys
import logging
import numpy as np

sys.path.insert(0, '.')

from simulation_engine.synchronized_simulation import (
    SynchronizedRadarEWSimulation,
    create_test_scenario
)
from simulation_engine.physics import TargetState
from defense_core import reset_defense_bus

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_single_hostile_target():
    """Test with single hostile target."""
    print("\n" + "="*80)
    print("TEST: Single Hostile Target")
    print("="*80)
    
    reset_defense_bus()
    
    # Create target at multiple positions to ensure illumination
    radar_config, ew_config, _ = create_test_scenario('single_hostile')
    
    # Override with stationary target at beam center
    radar_config['rpm'] = 0  # Stop scanning
    radar_config['scan_angle_deg'] = 0  # Point at 0 degrees
    
    targets = [
        TargetState(
            id=1,
            pos_x=1000.0,  # 1000m at 0 degrees
            pos_y=0.0,
            vel_x=-50.0,   # Approaching
            vel_y=0.0,
            type="hostile"
        )
    ]
    
    sim = SynchronizedRadarEWSimulation(
        radar_config=radar_config,
        ew_config=ew_config,
        targets=targets,
        max_frames=30,
        enable_cycle_logging=True,
        log_every_n_frames=5
    )
    
    try:
        summary = sim.run(num_frames=30)
        
        print("\n" + "="*80)
        print("TEST RESULTS")
        print("="*80)
        print(f"Detections: {summary['cycle_stats']['total_detections']}")
        print(f"Tracks: {summary['cycle_stats']['total_tracks']}")
        print(f"Intel packets: {summary['cycle_stats']['total_intel_packets']}")
        print(f"Jam packets: {summary['cycle_stats']['total_jam_packets']}")
        print(f"Radar responses: {summary['cycle_stats']['total_radar_responses']}")
        print(f"RTF: {summary['real_time_factor']:.2f}x")
        print("="*80)
        
        # Verify
        assert summary['cycle_stats']['total_detections'] > 0, "Should detect target"
        assert summary['cycle_stats']['total_intel_packets'] > 0, "Should send intelligence"
        
        print("\n✓ Test passed")
        
    finally:
        sim.stop()
        reset_defense_bus()


def test_multiple_targets():
    """Test with multiple targets at different ranges."""
    print("\n" + "="*80)
    print("TEST: Multiple Targets")
    print("="*80)
    
    reset_defense_bus()
    
    radar_config, ew_config, _ = create_test_scenario('multiple_targets')
    
    # Stop scanning, point at 0 degrees
    radar_config['rpm'] = 0
    radar_config['scan_angle_deg'] = 0
    
    # Create targets all at 0 degrees azimuth
    targets = [
        TargetState(id=1, pos_x=1000.0, pos_y=0.0, vel_x=-50.0, vel_y=0.0, type="hostile"),
        TargetState(id=2, pos_x=1500.0, pos_y=0.0, vel_x=-30.0, vel_y=0.0, type="hostile"),
        TargetState(id=3, pos_x=800.0, pos_y=0.0, vel_x=-60.0, vel_y=0.0, type="civilian")
    ]
    
    sim = SynchronizedRadarEWSimulation(
        radar_config=radar_config,
        ew_config=ew_config,
        targets=targets,
        max_frames=30,
        enable_cycle_logging=True,
        log_every_n_frames=5
    )
    
    try:
        summary = sim.run(num_frames=30)
        
        print("\n" + "="*80)
        print("TEST RESULTS")
        print("="*80)
        print(f"Detections: {summary['cycle_stats']['total_detections']}")
        print(f"Tracks: {summary['cycle_stats']['total_tracks']}")
        print(f"Intel packets: {summary['cycle_stats']['total_intel_packets']}")
        print(f"Jam packets: {summary['cycle_stats']['total_jam_packets']}")
        print(f"Radar responses: {summary['cycle_stats']['total_radar_responses']}")
        print("="*80)
        
        # Verify
        assert summary['cycle_stats']['total_detections'] > 0, "Should detect targets"
        assert summary['cycle_stats']['total_tracks'] > 0, "Should track targets"
        
        print("\n✓ Test passed")
        
    finally:
        sim.stop()
        reset_defense_bus()


def test_deterministic_execution():
    """Test that simulation is deterministic."""
    print("\n" + "="*80)
    print("TEST: Deterministic Execution")
    print("="*80)
    
    def run_sim(seed):
        np.random.seed(seed)
        reset_defense_bus()
        
        radar_config, ew_config, _ = create_test_scenario('single_hostile')
        radar_config['rpm'] = 0
        
        targets = [
            TargetState(id=1, pos_x=1000.0, pos_y=0.0, vel_x=-50.0, vel_y=0.0, type="hostile")
        ]
        
        sim = SynchronizedRadarEWSimulation(
            radar_config=radar_config,
            ew_config=ew_config,
            targets=targets,
            max_frames=20,
            enable_cycle_logging=False
        )
        
        try:
            summary = sim.run(num_frames=20)
            return summary['cycle_stats']
        finally:
            sim.stop()
    
    # Run twice with same seed
    stats1 = run_sim(42)
    stats2 = run_sim(42)
    
    print("\nRun 1:", stats1)
    print("Run 2:", stats2)
    
    # Verify identical results
    assert stats1 == stats2, "Results should be identical with same seed"
    
    print("\n✓ Test passed - execution is deterministic")


def test_no_deadlocks():
    """Test that simulation doesn't deadlock."""
    print("\n" + "="*80)
    print("TEST: No Deadlocks")
    print("="*80)
    
    import time
    
    reset_defense_bus()
    
    radar_config, ew_config, targets = create_test_scenario('single_hostile')
    radar_config['rpm'] = 0
    
    targets = [
        TargetState(id=1, pos_x=1000.0, pos_y=0.0, vel_x=-50.0, vel_y=0.0, type="hostile")
    ]
    
    sim = SynchronizedRadarEWSimulation(
        radar_config=radar_config,
        ew_config=ew_config,
        targets=targets,
        max_frames=100,
        enable_cycle_logging=False
    )
    
    try:
        start_time = time.time()
        summary = sim.run(num_frames=100)
        elapsed = time.time() - start_time
        
        # Verify reasonable execution time (< 5 seconds for 100 frames)
        assert elapsed < 5.0, f"Simulation took too long: {elapsed:.2f}s (possible deadlock)"
        
        print(f"\n100 frames completed in {elapsed:.2f}s")
        print(f"Mean tick time: {summary['mean_tick_time_ms']:.2f}ms")
        print("\n✓ Test passed - no deadlocks")
        
    finally:
        sim.stop()
        reset_defense_bus()


if __name__ == '__main__':
    print("\n" + "="*80)
    print("SYNCHRONIZED SIMULATION TEST SUITE")
    print("="*80)
    
    tests = [
        ("Single Hostile Target", test_single_hostile_target),
        ("Multiple Targets", test_multiple_targets),
        ("Deterministic Execution", test_deterministic_execution),
        ("No Deadlocks", test_no_deadlocks)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            test_func()
            results[test_name] = "PASSED"
        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = "FAILED"
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, result in results.items():
        status = "✓" if result == "PASSED" else "✗"
        print(f"{status} {test_name}: {result}")
    
    passed = sum(1 for r in results.values() if r == "PASSED")
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED")
    else:
        print(f"\n✗ {total - passed} TEST(S) FAILED")
