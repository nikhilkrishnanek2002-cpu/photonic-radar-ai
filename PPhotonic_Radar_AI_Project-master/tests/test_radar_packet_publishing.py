"""
Test Radar Intelligence Packet Publishing
==========================================

Verifies that the radar orchestrator publishes RadarIntelligencePacket
at every tracking update via the defense_core event bus.

Tests:
1. Packets are published at every tick
2. Non-blocking behavior (radar doesn't stall)
3. Packet contents match track data
4. Statistics tracking works
5. Debug mode output works
"""

import sys
import time
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from simulation_engine.orchestrator import SimulationOrchestrator
from simulation_engine.physics import TargetState
from defense_core import get_defense_bus, reset_defense_bus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_packet_publishing():
    """Test that packets are published at every tracking update."""
    print("\n" + "="*80)
    print("TEST: Radar Intelligence Packet Publishing")
    print("="*80 + "\n")
    
    # Reset event bus
    reset_defense_bus()
    
    # Create test configuration
    radar_config = {
        'sensor_id': 'TEST_RADAR_01',
        'frame_dt': 0.05,  # 20 Hz
        'enable_defense_core': True,
        'debug_packets': True,  # Enable debug output
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
    
    # Create test targets (using Cartesian coordinates)
    # Target 1: 500m range at 45°, approaching at 50 m/s
    import math
    range1, az1 = 500.0, 45.0
    pos_x1 = range1 * math.cos(math.radians(az1))
    pos_y1 = range1 * math.sin(math.radians(az1))
    vel_x1 = -50.0 * math.cos(math.radians(az1))  # Approaching
    vel_y1 = -50.0 * math.sin(math.radians(az1))
    
    # Target 2: 1000m range at 90°, receding at 100 m/s
    range2, az2 = 1000.0, 90.0
    pos_x2 = range2 * math.cos(math.radians(az2))
    pos_y2 = range2 * math.sin(math.radians(az2))
    vel_x2 = 100.0 * math.cos(math.radians(az2))  # Receding
    vel_y2 = 100.0 * math.sin(math.radians(az2))
    
    targets = [
        TargetState(
            id=1,
            pos_x=pos_x1,
            pos_y=pos_y1,
            vel_x=vel_x1,
            vel_y=vel_y1,
            type="aircraft"
        ),
        TargetState(
            id=2,
            pos_x=pos_x2,
            pos_y=pos_y2,
            vel_x=vel_x2,
            vel_y=vel_y2,
            type="missile"
        )
    ]
    
    # Create orchestrator
    print("Initializing radar orchestrator...")
    orchestrator = SimulationOrchestrator(radar_config, targets)
    
    # Get event bus
    event_bus = get_defense_bus()
    
    # Run simulation for 10 frames
    num_frames = 10
    print(f"\nRunning {num_frames} frames...\n")
    
    packets_received = []
    frame_times = []
    
    for i in range(num_frames):
        frame_start = time.time()
        
        # Execute radar tick
        result = orchestrator.tick()
        
        # Try to receive packet from event bus
        packet = event_bus.receive_intelligence(timeout=0.1)
        if packet:
            packets_received.append(packet)
            print(f"✓ Frame {i}: Received packet (frame_id={packet.frame_id}, "
                  f"tracks={len(packet.tracks)}, threats={len(packet.threat_assessments)})")
        else:
            print(f"✗ Frame {i}: No packet received")
        
        frame_time = time.time() - frame_start
        frame_times.append(frame_time)
    
    # Stop orchestrator
    orchestrator.stop()
    
    # Print results
    print("\n" + "="*80)
    print("TEST RESULTS")
    print("="*80)
    
    print(f"\nPackets Published: {orchestrator.packets_sent}")
    print(f"Packets Dropped: {orchestrator.packets_dropped}")
    print(f"Packets Received: {len(packets_received)}")
    
    success_rate = len(packets_received) / num_frames * 100
    print(f"Success Rate: {success_rate:.1f}%")
    
    avg_frame_time = sum(frame_times) / len(frame_times) * 1000
    max_frame_time = max(frame_times) * 1000
    print(f"\nFrame Time (avg): {avg_frame_time:.2f}ms")
    print(f"Frame Time (max): {max_frame_time:.2f}ms")
    
    # Verify non-blocking behavior
    if max_frame_time < 100:  # Should be well under 100ms
        print("✓ Non-blocking verified (max frame time < 100ms)")
    else:
        print("✗ WARNING: Frame time too high, possible blocking")
    
    # Verify packet contents
    if packets_received:
        sample_packet = packets_received[0]
        print(f"\nSample Packet Contents:")
        print(f"  Message ID: {sample_packet.message_id}")
        print(f"  Sensor ID: {sample_packet.sensor_id}")
        print(f"  Frame ID: {sample_packet.frame_id}")
        print(f"  Timestamp: {sample_packet.timestamp:.3f}")
        print(f"  Tracks: {len(sample_packet.tracks)}")
        print(f"  Threats: {len(sample_packet.threat_assessments)}")
        print(f"  Overall Confidence: {sample_packet.overall_confidence:.2f}")
        print(f"  Data Quality: {sample_packet.data_quality:.2f}")
        
        if sample_packet.tracks:
            track = sample_packet.tracks[0]
            print(f"\n  Sample Track:")
            print(f"    Track ID: {track.track_id}")
            print(f"    Range: {track.range_m:.1f}m")
            print(f"    Velocity: {track.radial_velocity_m_s:.1f}m/s")
            print(f"    Quality: {track.track_quality:.2f}")
        
        if sample_packet.threat_assessments:
            threat = sample_packet.threat_assessments[0]
            print(f"\n  Sample Threat:")
            print(f"    Track ID: {threat.track_id}")
            print(f"    Class: {threat.threat_class}")
            print(f"    Type: {threat.target_type}")
            print(f"    Confidence: {threat.classification_confidence:.2f}")
            print(f"    Priority: {threat.threat_priority}")
    
    # Get event bus statistics
    bus_stats = event_bus.get_statistics()
    print(f"\nEvent Bus Statistics:")
    print(f"  Backend: {bus_stats['backend_type']}")
    print(f"  Radar→EW Messages Sent: {bus_stats['radar_to_ew']['messages_sent']}")
    print(f"  Radar→EW Messages Received: {bus_stats['radar_to_ew']['messages_received']}")
    print(f"  Radar→EW Messages Dropped: {bus_stats['radar_to_ew']['messages_dropped']}")
    print(f"  Radar→EW Queue Size: {bus_stats['radar_to_ew']['queue_size']}")
    
    # Final verdict
    print("\n" + "="*80)
    if success_rate >= 90 and max_frame_time < 100:
        print("✓ TEST PASSED")
    else:
        print("✗ TEST FAILED")
    print("="*80 + "\n")


def test_debug_mode():
    """Test debug mode packet printing."""
    print("\n" + "="*80)
    print("TEST: Debug Mode Packet Printing")
    print("="*80 + "\n")
    
    # Reset event bus
    reset_defense_bus()
    
    # Create configuration with debug enabled
    radar_config = {
        'sensor_id': 'DEBUG_RADAR_01',
        'frame_dt': 0.05,
        'enable_defense_core': True,
        'debug_packets': True,  # Enable debug output
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
    
    # Create test target (using Cartesian coordinates)
    import math
    range1, az1 = 500.0, 45.0
    pos_x1 = range1 * math.cos(math.radians(az1))
    pos_y1 = range1 * math.sin(math.radians(az1))
    vel_x1 = -50.0 * math.cos(math.radians(az1))  # Approaching
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
    
    # Create orchestrator
    orchestrator = SimulationOrchestrator(radar_config, targets)
    
    # Run 3 frames to see debug output
    print("Running 3 frames with debug mode enabled...\n")
    for i in range(3):
        orchestrator.tick()
        time.sleep(0.1)
    
    orchestrator.stop()
    
    print("\n✓ Debug mode test complete (check output above)")


if __name__ == '__main__':
    test_packet_publishing()
    test_debug_mode()
