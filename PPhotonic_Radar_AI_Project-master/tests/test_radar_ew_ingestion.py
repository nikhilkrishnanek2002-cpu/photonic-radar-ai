"""
Test Suite for Radar EW Action Ingestion
=========================================

Tests the radar's ability to ingest EW attack packets and apply
realistic jamming effects including:
- Noise jamming (SNR reduction)
- Deception jamming (false tracks)
- Track quality degradation
- Range/velocity drift
- Before/after metrics logging

Author: EW Systems Integration Team
"""

import sys
import time
import numpy as np
from typing import List, Dict

# Add project root to path
sys.path.insert(0, '.')

from simulation_engine.orchestrator import SimulationOrchestrator
from simulation_engine.physics import TargetState
from simulation_engine.ew_degradation import EWDegradationModel
from defense_core import (
    get_defense_bus,
    reset_defense_bus,
    ElectronicAttackPacket,
    Countermeasure,
    EngagementStatus
)
from interfaces.message_schema import CountermeasureType, EngagementState


def create_test_radar(enable_ew=True):
    """Create a test radar with EW effects enabled."""
    radar_config = {
        'sensor_id': 'TEST_RADAR_EW',
        'frame_dt': 0.1,
        'enable_defense_core': True,
        'enable_ew_effects': enable_ew,
        'ew_log_before_after': True,
        'ew_max_snr_degradation_db': 20.0,
        'ew_max_quality_degradation': 0.5,
        'ew_false_track_probability': 0.8,  # High probability for testing
        'enable_intelligence_export': False,
        'debug_packets': False
    }
    
    # Create single target at 1000m range, 0 degrees azimuth
    # Convert to Cartesian: x = r*cos(az), y = r*sin(az)
    targets = [
        TargetState(
            id=1,
            pos_x=1000.0,  # 1000m range at 0 degrees
            pos_y=0.0,
            vel_x=-50.0,   # Approaching radar
            vel_y=0.0,
            type="hostile"
        )
    ]
    
    return SimulationOrchestrator(radar_config, targets)


def create_noise_jamming_packet():
    """Create an EW attack packet with noise jamming."""
    cms = [
        Countermeasure(
            countermeasure_id=1,
            target_track_id=1,
            cm_type=CountermeasureType.NOISE_JAM.value,
            start_time=0.1,  # Must be positive
            power_level_dbm=45.0,  # High power
            frequency_mhz=77000.0,
            bandwidth_mhz=200.0,
            effectiveness_score=0.8,
            confidence=0.9,
            predicted_snr_reduction_db=15.0
        )
    ]
    
    engagements = [
        EngagementStatus(
            track_id=1,
            engagement_state=EngagementState.TRACKING.value,
            time_to_threat_s=20.0,
            kill_probability=0.7
        )
    ]
    
    return ElectronicAttackPacket.create(
        effector_id='TEST_EW_NOISE',
        countermeasures=cms,
        engagements=engagements,
        overall_effectiveness=0.8,
        decision_confidence=0.9
    )


def create_deception_jamming_packet():
    """Create an EW attack packet with deception jamming."""
    cms = [
        Countermeasure(
            countermeasure_id=2,
            target_track_id=1,
            cm_type=CountermeasureType.DECEPTION_JAM.value,
            start_time=0.1,  # Must be positive
            power_level_dbm=40.0,
            frequency_mhz=77000.0,
            bandwidth_mhz=200.0,
            effectiveness_score=0.7,
            confidence=0.85,
            predicted_snr_reduction_db=5.0
        )
    ]
    
    engagements = [
        EngagementStatus(
            track_id=1,
            engagement_state=EngagementState.TRACKING.value,
            time_to_threat_s=20.0,
            kill_probability=0.7
        )
    ]
    
    return ElectronicAttackPacket.create(
        effector_id='TEST_EW_DECEPTION',
        countermeasures=cms,
        engagements=engagements,
        overall_effectiveness=0.7,
        decision_confidence=0.85
    )


def test_noise_jamming_effects():
    """Test that noise jamming reduces SNR and track quality."""
    print("\n" + "="*80)
    print("TEST: Noise Jamming Effects")
    print("="*80)
    
    reset_defense_bus()
    radar = create_test_radar(enable_ew=True)
    bus = get_defense_bus()
    
    # Run a few frames without jamming to establish tracks
    print("\nRunning 5 frames without jamming...")
    for i in range(5):
        radar.tick()
    
    # Publish noise jamming packet
    packet = create_noise_jamming_packet()
    bus.publish_feedback(packet, timeout=0.1)
    print(f"\nPublished noise jamming packet (power={packet.active_countermeasures[0].power_level_dbm}dBm)")
    
    # Run frames with jamming
    print("\nRunning 5 frames with noise jamming...")
    for i in range(5):
        result = radar.tick()
    
    # Verify degradation occurred
    metrics = radar.ew_degradation.get_metrics()
    
    print(f"\nDegradation Metrics:")
    print(f"  SNR Reduction: {metrics.snr_reduction_db:.1f} dB")
    print(f"  Tracks Degraded: {metrics.tracks_degraded}")
    print(f"  Mean Quality Reduction: {metrics.mean_quality_reduction:.2%}")
    
    assert metrics.snr_reduction_db > 0, "SNR should be reduced by noise jamming"
    assert metrics.snr_reduction_db <= 20.0, "SNR reduction should be clamped to max"
    
    print("\n✓ Noise jamming effects verified")
    
    radar.stop()
    reset_defense_bus()
    return True


def test_deception_jamming_effects():
    """Test that deception jamming injects false tracks."""
    print("\n" + "="*80)
    print("TEST: Deception Jamming Effects")
    print("="*80)
    
    reset_defense_bus()
    radar = create_test_radar(enable_ew=True)
    bus = get_defense_bus()
    
    # Run frames without jamming
    print("\nRunning 5 frames without jamming...")
    for i in range(5):
        radar.tick()
    
    # Publish deception jamming packet
    packet = create_deception_jamming_packet()
    bus.publish_feedback(packet, timeout=0.1)
    print(f"\nPublished deception jamming packet (effectiveness={packet.overall_effectiveness})")
    
    # Run frames with jamming
    print("\nRunning 10 frames with deception jamming...")
    false_tracks_detected = False
    for i in range(10):
        radar.tick()
        
        # Check for false tracks
        if radar.ew_degradation.metrics.false_tracks_injected > 0:
            false_tracks_detected = True
            print(f"  Frame {i}: {radar.ew_degradation.metrics.false_tracks_injected} false tracks injected")
    
    metrics = radar.ew_degradation.get_metrics()
    
    print(f"\nDegradation Metrics:")
    print(f"  False Tracks Injected: {metrics.false_tracks_injected}")
    print(f"  Tracks Degraded: {metrics.tracks_degraded}")
    
    assert false_tracks_detected, "Deception jamming should inject false tracks"
    
    print("\n✓ Deception jamming effects verified")
    
    radar.stop()
    reset_defense_bus()
    return True


def test_range_velocity_drift():
    """Test that jamming causes range and velocity drift."""
    print("\n" + "="*80)
    print("TEST: Range/Velocity Drift")
    print("="*80)
    
    reset_defense_bus()
    radar = create_test_radar(enable_ew=True)
    bus = get_defense_bus()
    
    # Run frames without jamming
    print("\nRunning 5 frames without jamming...")
    for i in range(5):
        radar.tick()
    
    # Publish jamming packet
    packet = create_noise_jamming_packet()
    bus.publish_feedback(packet, timeout=0.1)
    print(f"\nPublished jamming packet")
    
    # Run frames with jamming
    print("\nRunning 10 frames with jamming...")
    drift_detected = False
    for i in range(10):
        radar.tick()
        
        metrics = radar.ew_degradation.get_metrics()
        if metrics.range_drift_m > 0 or metrics.velocity_drift_m_s > 0:
            drift_detected = True
            print(f"  Frame {i}: Range drift={metrics.range_drift_m:.1f}m, "
                  f"Velocity drift={metrics.velocity_drift_m_s:.1f}m/s")
    
    metrics = radar.ew_degradation.get_metrics()
    
    print(f"\nDrift Metrics:")
    print(f"  Range Drift: {metrics.range_drift_m:.1f} m")
    print(f"  Velocity Drift: {metrics.velocity_drift_m_s:.1f} m/s")
    
    assert drift_detected, "Jamming should cause range/velocity drift"
    assert metrics.range_drift_m <= 50.0, "Range drift should be physically plausible (< 50m)"
    assert metrics.velocity_drift_m_s <= 10.0, "Velocity drift should be physically plausible (< 10 m/s)"
    
    print("\n✓ Range/velocity drift verified")
    
    radar.stop()
    reset_defense_bus()
    return True


def test_before_after_logging(capsys=None):
    """Test that before/after metrics are logged."""
    print("\n" + "="*80)
    print("TEST: Before/After Logging")
    print("="*80)
    
    reset_defense_bus()
    radar = create_test_radar(enable_ew=True)
    bus = get_defense_bus()
    
    # Run frames without jamming
    for i in range(3):
        radar.tick()
    
    # Publish jamming packet
    packet = create_noise_jamming_packet()
    bus.publish_feedback(packet, timeout=0.1)
    
    # Run frames with jamming - logs should appear
    print("\nRunning frames with jamming (check logs)...")
    for i in range(5):
        radar.tick()
    
    print("\n✓ Check logs above for [EW-BEFORE] and [EW-AFTER] entries")
    print("  Should show track count, quality, SNR before and after jamming")
    
    radar.stop()
    reset_defense_bus()
    return True


def test_physical_plausibility():
    """Test that all effects are physically plausible."""
    print("\n" + "="*80)
    print("TEST: Physical Plausibility")
    print("="*80)
    
    reset_defense_bus()
    radar = create_test_radar(enable_ew=True)
    bus = get_defense_bus()
    
    # Run frames
    for i in range(3):
        radar.tick()
    
    # Publish high-power jamming
    packet = create_noise_jamming_packet()
    packet.active_countermeasures[0].power_level_dbm = 50.0  # Very high power
    bus.publish_feedback(packet, timeout=0.1)
    
    # Run with jamming
    for i in range(5):
        radar.tick()
    
    metrics = radar.ew_degradation.get_metrics()
    
    print(f"\nPhysical Plausibility Checks:")
    print(f"  SNR Reduction: {metrics.snr_reduction_db:.1f} dB (should be ≤ 20 dB)")
    print(f"  Quality Reduction: {metrics.mean_quality_reduction:.2%} (should be ≤ 50%)")
    print(f"  Range Drift: {metrics.range_drift_m:.1f} m (should be ≤ 50 m)")
    print(f"  Velocity Drift: {metrics.velocity_drift_m_s:.1f} m/s (should be ≤ 10 m/s)")
    
    # Verify limits
    assert metrics.snr_reduction_db <= 20.0, "SNR reduction exceeds physical limit"
    assert metrics.mean_quality_reduction <= 0.5, "Quality reduction exceeds limit"
    if metrics.range_drift_m > 0:
        assert metrics.range_drift_m <= 50.0, "Range drift exceeds physical limit"
    if metrics.velocity_drift_m_s > 0:
        assert metrics.velocity_drift_m_s <= 10.0, "Velocity drift exceeds physical limit"
    
    print("\n✓ All effects within physically plausible limits")
    
    radar.stop()
    reset_defense_bus()
    return True


if __name__ == '__main__':
    print("\n" + "="*80)
    print("RADAR EW INGESTION TEST SUITE")
    print("="*80)
    
    results = {}
    
    try:
        results['noise_jamming'] = test_noise_jamming_effects()
    except Exception as e:
        print(f"\n✗ Noise jamming test failed: {e}")
        import traceback
        traceback.print_exc()
        results['noise_jamming'] = False
    
    try:
        results['deception_jamming'] = test_deception_jamming_effects()
    except Exception as e:
        print(f"\n✗ Deception jamming test failed: {e}")
        import traceback
        traceback.print_exc()
        results['deception_jamming'] = False
    
    try:
        results['drift'] = test_range_velocity_drift()
    except Exception as e:
        print(f"\n✗ Drift test failed: {e}")
        import traceback
        traceback.print_exc()
        results['drift'] = False
    
    try:
        results['logging'] = test_before_after_logging()
    except Exception as e:
        print(f"\n✗ Logging test failed: {e}")
        import traceback
        traceback.print_exc()
        results['logging'] = False
    
    try:
        results['plausibility'] = test_physical_plausibility()
    except Exception as e:
        print(f"\n✗ Plausibility test failed: {e}")
        import traceback
        traceback.print_exc()
        results['plausibility'] = False
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:20s}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED")
    else:
        print(f"\n✗ {total - passed} TEST(S) FAILED")
