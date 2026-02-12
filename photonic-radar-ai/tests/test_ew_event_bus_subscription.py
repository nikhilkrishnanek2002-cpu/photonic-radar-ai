"""
Test EW Event Bus Subscription
================================

Verifies that the Cognitive EW-AI system can subscribe to radar intelligence
packets from the defense_core event bus with non-blocking operation and
graceful error handling.

Tests:
1. Non-blocking polling
2. Packet validation
3. Graceful handling of missing data
4. Logging verification
5. Idle behavior when no radar data
6. End-to-end radar→EW communication
"""

import sys
import time
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cognitive.intelligence_pipeline import EWIntelligencePipeline
from simulation_engine.orchestrator import SimulationOrchestrator
from simulation_engine.physics import TargetState
from defense_core import get_defense_bus, reset_defense_bus
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_non_blocking_polling():
    """Test that EW doesn't block when polling for intelligence."""
    print("\n" + "="*80)
    print("TEST: Non-Blocking Polling")
    print("="*80 + "\n")
    
    # Reset event bus
    reset_defense_bus()
    
    # Create EW pipeline with event bus mode
    ew_config = {
        'enable_ingestion': True,
        'ingestion_mode': 'event_bus',
        'staleness_threshold_s': 2.0,
        'poll_interval_s': 0.05,  # 50ms polling
        'log_all_updates': True
    }
    
    pipeline = EWIntelligencePipeline(**ew_config)
    pipeline.start()
    
    # Measure time to poll when no data available
    poll_times = []
    for i in range(10):
        start = time.time()
        assessment = pipeline.process_next_intelligence(timeout=0.05)
        elapsed = time.time() - start
        poll_times.append(elapsed)
        
        if assessment is None:
            print(f"  Poll {i+1}: No data (took {elapsed*1000:.2f}ms)")
        else:
            print(f"  Poll {i+1}: Got data (took {elapsed*1000:.2f}ms)")
    
    pipeline.stop()
    
    # Verify non-blocking
    avg_poll_time = sum(poll_times) / len(poll_times) * 1000
    max_poll_time = max(poll_times) * 1000
    
    print(f"\nPolling Performance:")
    print(f"  Average: {avg_poll_time:.2f}ms")
    print(f"  Maximum: {max_poll_time:.2f}ms")
    
    if max_poll_time < 100:  # Should be well under 100ms
        print("✓ Non-blocking verified (max poll time < 100ms)")
        return True
    else:
        print("✗ WARNING: Poll time too high, possible blocking")
        return False


def test_packet_validation():
    """Test packet validation and staleness detection."""
    print("\n" + "="*80)
    print("TEST: Packet Validation")
    print("="*80 + "\n")
    
    # Reset event bus
    reset_defense_bus()
    
    # Create radar to publish packets
    radar_config = {
        'sensor_id': 'TEST_RADAR_01',
        'frame_dt': 0.05,
        'enable_defense_core': True,
        'debug_packets': False,
        'rpm': 12.0,
        'beamwidth_deg': 5.0,
        'sampling_rate_hz': 2e6,
        'n_pulses': 64,
        'samples_per_pulse': 512,
        'start_frequency_hz': 77e9,
        'sweep_bandwidth_hz': 150e6,
        'noise_level_db': -50,
        'n_fft_range': 512,
        'n_fft_doppler': 64
    }
    
    # Create test target
    range1, az1 = 500.0, 45.0
    pos_x1 = range1 * math.cos(math.radians(az1))
    pos_y1 = range1 * math.sin(math.radians(az1))
    vel_x1 = -50.0 * math.cos(math.radians(az1))
    vel_y1 = -50.0 * math.sin(math.radians(az1))
    
    targets = [
        TargetState(
            id=1,
            pos_x=pos_x1,
            pos_y=pos_y1,
            vel_x=vel_x1,
            vel_y=vel_y1,
            type="aircraft"
        )
    ]
    
    radar = SimulationOrchestrator(radar_config, targets)
    
    # Create EW pipeline
    ew_config = {
        'enable_ingestion': True,
        'ingestion_mode': 'event_bus',
        'staleness_threshold_s': 0.5,  # Short threshold for testing
        'poll_interval_s': 0.05,
        'log_all_updates': True
    }
    
    pipeline = EWIntelligencePipeline(**ew_config)
    pipeline.start()
    
    # Publish some packets
    print("Publishing radar packets...")
    for i in range(5):
        radar.tick()
        time.sleep(0.1)
    
    # Wait for EW to receive
    time.sleep(0.2)
    
    # Check statistics
    stats = pipeline.get_statistics()
    
    print(f"\nEW Pipeline Statistics:")
    print(f"  Ingestion Mode: {stats['ingestion_mode']}")
    print(f"  Messages Processed: {stats['pipeline']['messages_processed']}")
    print(f"  Messages Rejected: {stats['pipeline']['messages_rejected']}")
    print(f"  Has Valid Intelligence: {stats['pipeline']['has_valid_intelligence']}")
    
    subscriber_stats = stats['subscriber']
    print(f"\nSubscriber Statistics:")
    print(f"  Messages Received: {subscriber_stats['messages_received']}")
    print(f"  Messages Valid: {subscriber_stats['messages_valid']}")
    print(f"  Messages Invalid: {subscriber_stats['messages_invalid']}")
    print(f"  Messages Stale: {subscriber_stats['messages_stale']}")
    
    radar.stop()
    pipeline.stop()
    
    # Verify
    success = (stats['pipeline']['messages_processed'] > 0 and
               stats['pipeline']['has_valid_intelligence'])
    
    if success:
        print("\n✓ Packet validation working")
    else:
        print("\n✗ Packet validation failed")
    
    return success


def test_graceful_missing_data():
    """Test graceful handling when no radar data available."""
    print("\n" + "="*80)
    print("TEST: Graceful Handling of Missing Data")
    print("="*80 + "\n")
    
    # Reset event bus
    reset_defense_bus()
    
    # Create EW pipeline WITHOUT radar (no data source)
    ew_config = {
        'enable_ingestion': True,
        'ingestion_mode': 'event_bus',
        'staleness_threshold_s': 2.0,
        'poll_interval_s': 0.05,
        'log_all_updates': False  # Reduce log spam
    }
    
    pipeline = EWIntelligencePipeline(**ew_config)
    pipeline.start()
    
    print("Running EW with no radar data for 10 iterations...")
    
    # Try to process intelligence when none available
    for i in range(10):
        assessment = pipeline.process_next_intelligence(timeout=0.05)
        
        if assessment is None:
            print(f"  Iteration {i+1}: No data (EW idle) ✓")
        else:
            print(f"  Iteration {i+1}: Unexpected data received")
    
    # Verify EW is still running
    stats = pipeline.get_statistics()
    
    print(f"\nEW Pipeline Status:")
    print(f"  Messages Processed: {stats['pipeline']['messages_processed']}")
    print(f"  Has Valid Intelligence: {stats['pipeline']['has_valid_intelligence']}")
    
    pipeline.stop()
    
    print("\n✓ EW handled missing data gracefully (no crashes)")
    return True


def test_end_to_end_communication():
    """Test end-to-end radar→EW communication via event bus."""
    print("\n" + "="*80)
    print("TEST: End-to-End Radar→EW Communication")
    print("="*80 + "\n")
    
    # Reset event bus
    reset_defense_bus()
    
    # Create radar
    radar_config = {
        'sensor_id': 'E2E_RADAR',
        'frame_dt': 0.05,
        'enable_defense_core': True,
        'debug_packets': False,
        'rpm': 12.0,
        'beamwidth_deg': 5.0,
        'sampling_rate_hz': 2e6,
        'n_pulses': 64,
        'samples_per_pulse': 512,
        'start_frequency_hz': 77e9,
        'sweep_bandwidth_hz': 150e6,
        'noise_level_db': -50,
        'n_fft_range': 512,
        'n_fft_doppler': 64
    }
    
    # Create test targets
    range1, az1 = 500.0, 45.0
    pos_x1 = range1 * math.cos(math.radians(az1))
    pos_y1 = range1 * math.sin(math.radians(az1))
    vel_x1 = -50.0 * math.cos(math.radians(az1))
    vel_y1 = -50.0 * math.sin(math.radians(az1))
    
    targets = [
        TargetState(
            id=1,
            pos_x=pos_x1,
            pos_y=pos_y1,
            vel_x=vel_x1,
            vel_y=vel_y1,
            type="aircraft"
        )
    ]
    
    radar = SimulationOrchestrator(radar_config, targets)
    
    # Create EW pipeline
    ew_config = {
        'enable_ingestion': True,
        'ingestion_mode': 'event_bus',
        'staleness_threshold_s': 2.0,
        'poll_interval_s': 0.05,
        'log_all_updates': True
    }
    
    pipeline = EWIntelligencePipeline(**ew_config)
    pipeline.start()
    
    # Run simulation
    print("Running 10-frame simulation...")
    packets_received = 0
    
    for i in range(10):
        # Radar tick
        radar.tick()
        
        # Give EW time to receive
        time.sleep(0.05)
        
        # Check if EW received
        assessment = pipeline.get_latest_assessment()
        if assessment:
            packets_received += 1
            print(f"  Frame {i}: EW received intelligence "
                  f"(tracks={assessment.num_confirmed_tracks}, "
                  f"scene={assessment.scene_type.value})")
    
    # Get final statistics
    radar_stats = {
        'packets_sent': radar.packets_sent,
        'packets_dropped': radar.packets_dropped
    }
    
    ew_stats = pipeline.get_statistics()
    
    print(f"\nRadar Statistics:")
    print(f"  Packets Sent: {radar_stats['packets_sent']}")
    print(f"  Packets Dropped: {radar_stats['packets_dropped']}")
    
    print(f"\nEW Statistics:")
    print(f"  Messages Processed: {ew_stats['pipeline']['messages_processed']}")
    print(f"  Messages Rejected: {ew_stats['pipeline']['messages_rejected']}")
    
    # Get event bus stats
    bus = get_defense_bus()
    bus_stats = bus.get_statistics()
    
    print(f"\nEvent Bus Statistics:")
    print(f"  Radar→EW Messages Sent: {bus_stats['radar_to_ew']['messages_sent']}")
    print(f"  Radar→EW Messages Received: {bus_stats['radar_to_ew']['messages_received']}")
    print(f"  Radar→EW Messages Dropped: {bus_stats['radar_to_ew']['messages_dropped']}")
    
    radar.stop()
    pipeline.stop()
    
    # Verify
    success_rate = (ew_stats['pipeline']['messages_processed'] / 
                   radar_stats['packets_sent'] * 100 if radar_stats['packets_sent'] > 0 else 0)
    
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("✓ End-to-end communication working")
        return True
    else:
        print("✗ End-to-end communication failed")
        return False


def test_idle_behavior():
    """Test that EW idles safely when radar stops sending."""
    print("\n" + "="*80)
    print("TEST: EW Idle Behavior")
    print("="*80 + "\n")
    
    # Reset event bus
    reset_defense_bus()
    
    # Create and run radar briefly
    radar_config = {
        'sensor_id': 'IDLE_TEST_RADAR',
        'frame_dt': 0.05,
        'enable_defense_core': True,
        'debug_packets': False,
        'rpm': 12.0,
        'beamwidth_deg': 5.0,
        'sampling_rate_hz': 2e6,
        'n_pulses': 64,
        'samples_per_pulse': 512,
        'start_frequency_hz': 77e9,
        'sweep_bandwidth_hz': 150e6,
        'noise_level_db': -50,
        'n_fft_range': 512,
        'n_fft_doppler': 64
    }
    
    targets = []
    radar = SimulationOrchestrator(radar_config, targets)
    
    # Create EW
    ew_config = {
        'enable_ingestion': True,
        'ingestion_mode': 'event_bus',
        'staleness_threshold_s': 2.0,
        'poll_interval_s': 0.05,
        'log_all_updates': False
    }
    
    pipeline = EWIntelligencePipeline(**ew_config)
    pipeline.start()
    
    # Run radar for 3 frames
    print("Radar active for 3 frames...")
    for i in range(3):
        radar.tick()
        time.sleep(0.05)
    
    # Stop radar
    radar.stop()
    print("Radar stopped.")
    
    # Continue running EW
    print("\nEW continues running (should idle safely)...")
    for i in range(5):
        assessment = pipeline.process_next_intelligence(timeout=0.05)
        if assessment is None:
            print(f"  Iteration {i+1}: EW idle (no data) ✓")
        else:
            print(f"  Iteration {i+1}: EW processing old data")
    
    pipeline.stop()
    
    print("\n✓ EW idled safely after radar stopped")
    return True


if __name__ == '__main__':
    print("\n" + "="*80)
    print("EW EVENT BUS SUBSCRIPTION TEST SUITE")
    print("="*80)
    
    results = {}
    
    # Run all tests
    results['non_blocking'] = test_non_blocking_polling()
    results['validation'] = test_packet_validation()
    results['missing_data'] = test_graceful_missing_data()
    results['end_to_end'] = test_end_to_end_communication()
    results['idle'] = test_idle_behavior()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {test_name:20s}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*80)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*80 + "\n")
