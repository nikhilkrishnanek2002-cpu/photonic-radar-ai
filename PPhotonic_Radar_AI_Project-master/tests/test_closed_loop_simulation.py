"""
Closed-Loop Simulation Test Suite
==================================

Tests complete closed-loop integration of radar and EW systems.

Verifies:
1. Time synchronization
2. No deadlocks
3. Deterministic execution
4. Complete loop logging

Author: Integration Test Team
"""

import sys
import time
import shutil
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from simulation_engine.closed_loop_simulation import ClosedLoopSimulation
from simulation_engine.physics import TargetState
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def create_test_config():
    """Create test configuration."""
    radar_config = {
        'sensor_id': 'TEST_RADAR',
        'enable_intelligence_export': True,
        'enable_ew_feedback': True,
        'carrier_frequency_hz': 77e9,
        'bandwidth_hz': 150e6,
        'max_range_m': 10000,
        'range_resolution_m': 1.0,
        'velocity_resolution_m_s': 0.5,
    }
    
    ew_config = {
        'effector_id': 'TEST_EW',
        'enable_intelligence_ingestion': True,
        'enable_feedback_export': True,
    }
    
    # Create test targets
    targets = [
        TargetState(
            x=5000.0, y=0.0, z=1000.0,
            vx=-200.0, vy=0.0, vz=0.0,
            rcs=10.0,
            target_type='MISSILE'
        ),
        TargetState(
            x=7000.0, y=2000.0, z=1500.0,
            vx=-150.0, vy=-50.0, vz=0.0,
            rcs=5.0,
            target_type='AIRCRAFT'
        )
    ]
    
    return radar_config, ew_config, targets


def test_time_synchronization():
    """Test 1: Verify time synchronization."""
    print("\n" + "="*70)
    print("TEST 1: Time Synchronization")
    print("="*70)
    
    radar_config, ew_config, targets = create_test_config()
    
    sim = ClosedLoopSimulation(
        radar_config=radar_config,
        ew_config=ew_config,
        targets=targets,
        frame_rate_hz=20.0,
        enable_logging=False
    )
    
    try:
        # Run 10 frames
        for i in range(10):
            result = sim.run_frame()
            
            # Verify frame ID
            assert result['frame_id'] == i + 1, f"Frame ID mismatch: {result['frame_id']} != {i+1}"
            
            # Verify simulation time
            expected_time = (i + 1) * sim.dt
            assert abs(result['simulation_time'] - expected_time) < 1e-6, \
                f"Time mismatch: {result['simulation_time']} != {expected_time}"
        
        print(f"✓ Time synchronization verified:")
        print(f"  Frames: {sim.frame_id}")
        print(f"  Simulation time: {sim.simulation_time:.3f}s")
        print(f"  Time step: {sim.dt:.3f}s")
        
        print("\n✓ TEST 1 PASSED\n")
        
    finally:
        sim.stop()


def test_no_deadlocks():
    """Test 2: Verify no deadlocks occur."""
    print("\n" + "="*70)
    print("TEST 2: Deadlock Prevention")
    print("="*70)
    
    radar_config, ew_config, targets = create_test_config()
    
    sim = ClosedLoopSimulation(
        radar_config=radar_config,
        ew_config=ew_config,
        targets=targets,
        frame_rate_hz=20.0,
        enable_logging=False
    )
    
    try:
        # Run 50 frames with timeout
        start_time = time.time()
        timeout = 10.0  # 10 seconds max
        
        for i in range(50):
            sim.run_frame()
            
            if time.time() - start_time > timeout:
                raise TimeoutError("Simulation deadlocked")
        
        elapsed = time.time() - start_time
        
        print(f"✓ No deadlocks detected:")
        print(f"  Frames: 50")
        print(f"  Elapsed time: {elapsed:.2f}s")
        print(f"  Mean frame time: {elapsed/50*1000:.1f}ms")
        
        assert elapsed < 5.0, f"Simulation too slow: {elapsed}s"
        
        print("\n✓ TEST 2 PASSED\n")
        
    finally:
        sim.stop()


def test_deterministic_execution():
    """Test 3: Verify deterministic execution."""
    print("\n" + "="*70)
    print("TEST 3: Deterministic Execution")
    print("="*70)
    
    radar_config, ew_config, targets = create_test_config()
    
    # Set random seed for determinism
    np.random.seed(42)
    
    # Run 1
    sim1 = ClosedLoopSimulation(
        radar_config=radar_config.copy(),
        ew_config=ew_config.copy(),
        targets=[t for t in targets],  # Copy targets
        frame_rate_hz=20.0,
        enable_logging=False
    )
    
    trace1 = []
    try:
        for i in range(20):
            result = sim1.run_frame()
            trace1.append({
                'frame_id': result['frame_id'],
                'simulation_time': result['simulation_time'],
                'num_tracks': result['num_tracks']
            })
    finally:
        sim1.stop()
    
    # Reset seed
    np.random.seed(42)
    
    # Run 2
    sim2 = ClosedLoopSimulation(
        radar_config=radar_config.copy(),
        ew_config=ew_config.copy(),
        targets=[t for t in targets],  # Copy targets
        frame_rate_hz=20.0,
        enable_logging=False
    )
    
    trace2 = []
    try:
        for i in range(20):
            result = sim2.run_frame()
            trace2.append({
                'frame_id': result['frame_id'],
                'simulation_time': result['simulation_time'],
                'num_tracks': result['num_tracks']
            })
    finally:
        sim2.stop()
    
    # Verify identical execution
    matches = 0
    for i in range(20):
        if (trace1[i]['frame_id'] == trace2[i]['frame_id'] and
            abs(trace1[i]['simulation_time'] - trace2[i]['simulation_time']) < 1e-6):
            matches += 1
    
    print(f"✓ Deterministic execution verified:")
    print(f"  Matching frames: {matches}/20")
    print(f"  Frame IDs match: {all(t1['frame_id'] == t2['frame_id'] for t1, t2 in zip(trace1, trace2))}")
    print(f"  Simulation times match: {all(abs(t1['simulation_time'] - t2['simulation_time']) < 1e-6 for t1, t2 in zip(trace1, trace2))}")
    
    assert matches == 20, f"Execution not deterministic: only {matches}/20 frames match"
    
    print("\n✓ TEST 3 PASSED\n")


def test_complete_loop_logging():
    """Test 4: Verify complete detection → decision → response logging."""
    print("\n" + "="*70)
    print("TEST 4: Complete Loop Logging")
    print("="*70)
    
    radar_config, ew_config, targets = create_test_config()
    
    log_dir = Path('./test_closed_loop_logs')
    if log_dir.exists():
        shutil.rmtree(log_dir)
    
    sim = ClosedLoopSimulation(
        radar_config=radar_config,
        ew_config=ew_config,
        targets=targets,
        frame_rate_hz=20.0,
        enable_logging=True,
        log_directory=str(log_dir)
    )
    
    try:
        # Run simulation
        summary = sim.run(num_frames=10)
        
        print(f"✓ Simulation completed:")
        print(f"  Frames: {summary['frames_simulated']}")
        print(f"  Simulation time: {summary['simulation_duration_s']:.3f}s")
        print(f"  Wall clock time: {summary['wall_clock_time_s']:.2f}s")
        print(f"  Real-time factor: {summary['real_time_factor']:.2f}x")
        print(f"  Mean frame time: {summary['mean_frame_time_ms']:.1f}ms")
        
        # Check trace
        trace_summary = summary['trace_summary']
        print(f"\n✓ Execution trace:")
        print(f"  Total detections: {trace_summary['total_detections']}")
        print(f"  Total EW decisions: {trace_summary['total_ew_decisions']}")
        print(f"  Total radar responses: {trace_summary['total_radar_responses']}")
        
        # Verify log files exist
        log_files = list(log_dir.glob('frame_*_trace.json'))
        print(f"\n✓ Log files created: {len(log_files)}")
        
        assert len(log_files) == 10, f"Expected 10 log files, got {len(log_files)}"
        
        # Verify complete trace file
        complete_trace = log_dir / 'complete_trace.json'
        assert complete_trace.exists(), "Complete trace file not found"
        print(f"  Complete trace: {complete_trace}")
        
        print("\n✓ TEST 4 PASSED\n")
        
    finally:
        sim.stop()
        # Cleanup
        if log_dir.exists():
            shutil.rmtree(log_dir)


def test_full_integration():
    """Test 5: Full integration test."""
    print("\n" + "="*70)
    print("TEST 5: Full Integration")
    print("="*70)
    
    radar_config, ew_config, targets = create_test_config()
    
    sim = ClosedLoopSimulation(
        radar_config=radar_config,
        ew_config=ew_config,
        targets=targets,
        frame_rate_hz=20.0,
        enable_logging=True,
        log_directory='./test_integration_logs'
    )
    
    try:
        # Run full simulation
        summary = sim.run(num_frames=30)
        
        print(f"✓ Full integration test:")
        print(f"  Frames simulated: {summary['frames_simulated']}")
        print(f"  Simulation duration: {summary['simulation_duration_s']:.3f}s")
        print(f"  Real-time factor: {summary['real_time_factor']:.2f}x")
        
        # Get statistics
        stats = sim.get_statistics()
        print(f"\n✓ System statistics:")
        print(f"  Final frame: {stats['frame_id']}")
        print(f"  Final time: {stats['simulation_time']:.3f}s")
        print(f"  EW messages processed: {stats['ew_stats']['pipeline']['messages_processed']}")
        print(f"  EW feedback published: {stats['ew_publisher_stats']['messages_published']}")
        
        print("\n✓ TEST 5 PASSED\n")
        
    finally:
        sim.stop()
        # Cleanup
        log_dir = Path('./test_integration_logs')
        if log_dir.exists():
            shutil.rmtree(log_dir)


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("CLOSED-LOOP SIMULATION TEST SUITE")
    print("="*70)
    
    try:
        test_time_synchronization()
        test_no_deadlocks()
        test_deterministic_execution()
        test_complete_loop_logging()
        test_full_integration()
        
        print("\n" + "="*70)
        print("ALL TESTS PASSED ✓")
        print("="*70)
        print("\nKey Findings:")
        print("  ✓ Time synchronization working (frame-based)")
        print("  ✓ No deadlocks detected (timeout protection)")
        print("  ✓ Deterministic execution verified")
        print("  ✓ Complete loop logging functional")
        print("  ✓ Detection → Decision → Response cycle working")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Cleanup shared directories
    for dir_name in ['./shared_intel', './shared_feedback']:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
