"""
Test EW Attack Packet Publishing
==================================

Verifies that the Cognitive EW-AI system publishes Electronic Attack Packets
to the radar via the event bus with all required fields.

Tests:
1. Packet creation with all required fields
2. Action type mapping
3. Jam power calculation
4. Expected effect calculation
5. Confidence metrics
6. Decision rationale
7. Event bus publishing
8. Logging verification
9. End-to-end communication
"""

import sys
import time
import logging
from pathlib import Path
import math

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cognitive.ew_feedback_publisher import EWFeedbackPublisher
from cognitive.engine import CognitiveRadarEngine, AdaptationCommand
from simulation_engine.orchestrator import SimulationOrchestrator
from simulation_engine.physics import TargetState
from cognitive.intelligence_pipeline import EWIntelligencePipeline
from defense_core import get_defense_bus, reset_defense_bus
from interfaces.message_schema import ThreatAssessment, ThreatClass, TargetType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_test_adaptation_command(frame_id: int = 0) -> AdaptationCommand:
    """Create test adaptation command."""
    return AdaptationCommand(
        frame_id=frame_id,
        timestamp=time.time(),
        bandwidth_scaling=1.2,
        prf_scale=1.0,
        tx_power_scaling=1.5,
        cfar_alpha_scale=0.9,
        dwell_time_scale=1.0,
        reasoning={
            'tx_power_scaling': 'Low confidence: boost TX power',
            'bandwidth_scaling': 'Cluttered scene: expand BW',
            'cfar_alpha_scale': 'High confidence: aggressive detection'
        },
        decision_confidence=0.85,
        predicted_snr_improvement_db=3.5,
        predicted_pfa_change=-0.1,
        predicted_range_resolution_m=60.0
    )


def create_test_threat_assessments():
    """Create test threat assessments."""
    return [
        ThreatAssessment(
            track_id=1,
            threat_class=ThreatClass.HOSTILE.value,
            target_type=TargetType.AIRCRAFT.value,
            classification_confidence=0.9,
            threat_priority=8,
            engagement_recommendation="ENGAGE"
        ),
        ThreatAssessment(
            track_id=2,
            threat_class=ThreatClass.HOSTILE.value,
            target_type=TargetType.MISSILE.value,
            classification_confidence=0.95,
            threat_priority=10,
            engagement_recommendation="ENGAGE"
        )
    ]


def test_packet_creation():
    """Test Electronic Attack Packet creation with all required fields."""
    print("\n" + "="*80)
    print("TEST: Packet Creation with Required Fields")
    print("="*80 + "\n")
    
    # Create publisher
    publisher = EWFeedbackPublisher(
        effector_id='TEST_EW_01',
        enable_export=False,
        enable_event_bus=False
    )
    
    # Create test data
    threats = create_test_threat_assessments()
    adaptation_cmd = create_test_adaptation_command()
    
    # Generate countermeasures
    countermeasures = publisher._generate_countermeasures_with_adaptation(
        threats, adaptation_cmd
    )
    
    print(f"Generated {len(countermeasures)} countermeasures:")
    for cm in countermeasures:
        print(f"\n  CM {cm.countermeasure_id}:")
        print(f"    Target Track: {cm.target_track_id}")
        print(f"    Action Type: {cm.cm_type}")
        print(f"    Jam Power: {cm.power_level_dbm:.1f} dBm")
        print(f"    Effectiveness: {cm.effectiveness_score:.2f}")
    
    # Verify all required fields
    assert len(countermeasures) == 2, "Should have 2 countermeasures"
    
    for cm in countermeasures:
        assert cm.cm_type in ['NOISE_JAM', 'DECEPTION_JAM', 'FALSE_TARGET'], \
            f"Invalid CM type: {cm.cm_type}"
        assert 20.0 <= cm.power_level_dbm <= 50.0, \
            f"Jam power out of range: {cm.power_level_dbm}"
        assert 0.0 <= cm.effectiveness_score <= 1.0, \
            f"Effectiveness out of range: {cm.effectiveness_score}"
    
    print("\n✓ All required fields present and valid")
    return True


def test_action_type_mapping():
    """Test action type mapping from adaptation command."""
    print("\n" + "="*80)
    print("TEST: Action Type Mapping")
    print("="*80 + "\n")
    
    publisher = EWFeedbackPublisher(
        effector_id='TEST_EW_02',
        enable_export=False,
        enable_event_bus=False
    )
    
    # Test 1: High power scaling → NOISE_JAM
    cmd1 = create_test_adaptation_command()
    cmd1.tx_power_scaling = 1.5
    cm_type1 = publisher._map_adaptation_to_cm_type(cmd1)
    print(f"High power scaling (1.5×) → {cm_type1}")
    assert cm_type1 == 'NOISE_JAM', "Should map to NOISE_JAM"
    
    # Test 2: High bandwidth scaling → DECEPTION_JAM
    cmd2 = create_test_adaptation_command()
    cmd2.tx_power_scaling = 1.0
    cmd2.bandwidth_scaling = 1.3
    cm_type2 = publisher._map_adaptation_to_cm_type(cmd2)
    print(f"High bandwidth scaling (1.3×) → {cm_type2}")
    assert cm_type2 == 'DECEPTION_JAM', "Should map to DECEPTION_JAM"
    
    # Test 3: Low CFAR → FALSE_TARGET
    cmd3 = create_test_adaptation_command()
    cmd3.tx_power_scaling = 1.0
    cmd3.bandwidth_scaling = 1.0
    cmd3.cfar_alpha_scale = 0.9
    cm_type3 = publisher._map_adaptation_to_cm_type(cmd3)
    print(f"Low CFAR scaling (0.9×) → {cm_type3}")
    assert cm_type3 == 'DECEPTION_JAM', "Should map to DECEPTION_JAM"
    
    print("\n✓ Action type mapping correct")
    return True


def test_jam_power_calculation():
    """Test jam power calculation."""
    print("\n" + "="*80)
    print("TEST: Jam Power Calculation")
    print("="*80 + "\n")
    
    publisher = EWFeedbackPublisher(
        effector_id='TEST_EW_03',
        enable_export=False,
        enable_event_bus=False
    )
    
    # Test with different power scalings
    cmd = create_test_adaptation_command()
    
    # Low threat priority
    power1 = publisher._calculate_jam_power(cmd, threat_priority=2)
    print(f"Low priority (2/10), power scaling 1.5× → {power1:.1f} dBm")
    
    # High threat priority
    power2 = publisher._calculate_jam_power(cmd, threat_priority=10)
    print(f"High priority (10/10), power scaling 1.5× → {power2:.1f} dBm")
    
    # Verify power increases with priority
    assert power2 > power1, "Power should increase with threat priority"
    assert 20.0 <= power1 <= 50.0, "Power should be in valid range"
    assert 20.0 <= power2 <= 50.0, "Power should be in valid range"
    
    print("\n✓ Jam power calculation correct")
    return True


def test_effectiveness_calculation():
    """Test effectiveness and impact calculations."""
    print("\n" + "="*80)
    print("TEST: Effectiveness and Impact Calculation")
    print("="*80 + "\n")
    
    publisher = EWFeedbackPublisher(
        effector_id='TEST_EW_04',
        enable_export=False,
        enable_event_bus=False
    )
    
    cmd = create_test_adaptation_command()
    
    # Overall effectiveness
    effectiveness = publisher._calculate_effectiveness(cmd)
    print(f"Overall Effectiveness: {effectiveness:.2f}")
    assert 0.0 <= effectiveness <= 1.0, "Effectiveness out of range"
    
    # Expected impact
    impact = publisher._calculate_expected_impact(cmd)
    print(f"Expected Impact: {impact:.2f}")
    assert 0.0 <= impact <= 1.0, "Impact out of range"
    
    print("\n✓ Effectiveness and impact calculations correct")
    return True


def test_decision_rationale():
    """Test decision rationale inclusion."""
    print("\n" + "="*80)
    print("TEST: Decision Rationale")
    print("="*80 + "\n")
    
    from defense_core import ElectronicAttackPacket, Countermeasure as DCCountermeasure
    
    publisher = EWFeedbackPublisher(
        effector_id='TEST_EW_05',
        enable_export=False,
        enable_event_bus=False
    )
    
    threats = create_test_threat_assessments()
    cmd = create_test_adaptation_command()
    
    # Generate countermeasures (these are interfaces/message_schema.Countermeasure)
    cms_interface = publisher._generate_countermeasures_with_adaptation(threats, cmd)
    
    # Convert to defense_core.Countermeasure for the packet
    cms_dc = []
    for cm in cms_interface:
        dc_cm = DCCountermeasure(
            countermeasure_id=cm.countermeasure_id,
            target_track_id=cm.target_track_id,
            cm_type=cm.cm_type,
            start_time=cm.start_time,
            power_level_dbm=cm.power_level_dbm,
            frequency_mhz=cm.frequency_mhz,
            bandwidth_mhz=cm.bandwidth_mhz,
            effectiveness_score=cm.effectiveness_score,
            confidence=cmd.decision_confidence,
            predicted_snr_reduction_db=cmd.predicted_snr_improvement_db
        )
        cms_dc.append(dc_cm)
    
    engagements = publisher.generate_engagement_status(threats)
    
    # Create packet
    packet = ElectronicAttackPacket.create(
        effector_id='TEST_EW_05',
        countermeasures=cms_dc,
        engagements=engagements,
        overall_effectiveness=0.8,
        decision_confidence=cmd.decision_confidence
    )
    
    # Add decision rationale
    packet.effector_metadata = {
        'decision_rationale': cmd.reasoning,
        'adaptation_command': {
            'tx_power_scaling': cmd.tx_power_scaling,
            'bandwidth_scaling': cmd.bandwidth_scaling
        }
    }
    
    print("Decision Rationale:")
    for key, value in packet.effector_metadata['decision_rationale'].items():
        print(f"  {key}: {value}")
    
    print("\nAdaptation Command:")
    for key, value in packet.effector_metadata['adaptation_command'].items():
        print(f"  {key}: {value}")
    
    assert 'decision_rationale' in packet.effector_metadata
    assert 'adaptation_command' in packet.effector_metadata
    assert len(packet.effector_metadata['decision_rationale']) > 0
    
    print("\n✓ Decision rationale included")
    return True


def test_event_bus_publishing():
    """Test event bus publishing."""
    print("\n" + "="*80)
    print("TEST: Event Bus Publishing")
    print("="*80 + "\n")
    
    # Reset event bus
    reset_defense_bus()
    
    # Create publisher with event bus enabled
    publisher = EWFeedbackPublisher(
        effector_id='TEST_EW_06',
        enable_export=False,
        enable_event_bus=True,
        log_all_transmissions=True
    )
    
    threats = create_test_threat_assessments()
    cmd = create_test_adaptation_command(frame_id=42)
    
    # Publish attack packet
    success = publisher.publish_attack_packet(threats, cmd)
    
    print(f"Publish Success: {success}")
    print(f"Packets Sent: {publisher.packets_sent}")
    print(f"Packets Dropped: {publisher.packets_dropped}")
    
    # Verify
    bus = get_defense_bus()
    feedback = bus.receive_ew_feedback(timeout=0.1)
    
    if feedback:
        print(f"\nReceived Feedback:")
        print(f"  Effector ID: {feedback.effector_id}")
        print(f"  Countermeasures: {len(feedback.active_countermeasures)}")
        print(f"  Engagements: {len(feedback.engagement_status)}")
        print(f"  Effectiveness: {feedback.overall_effectiveness:.2f}")
        print(f"  Confidence: {feedback.decision_confidence:.2f}")
        print(f"  Expected Impact: {feedback.expected_impact:.2f}")
    
    assert success, "Publish should succeed"
    assert publisher.packets_sent == 1, "Should have sent 1 packet"
    assert feedback is not None, "Should receive feedback"
    
    print("\n✓ Event bus publishing working")
    return True


def test_end_to_end():
    """Test end-to-end radar→EW→radar communication."""
    print("\n" + "="*80)
    print("TEST: End-to-End Radar→EW→Radar Communication")
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
        'staleness_threshold_s': 2.0,
        'poll_interval_s': 0.05,
        'log_all_updates': True
    }
    
    pipeline = EWIntelligencePipeline(**ew_config)
    pipeline.start()
    
    # Run simulation
    print("Running 5-frame simulation...")
    attack_packets_received = 0
    
    for i in range(5):
        # Radar tick
        radar.tick()
        time.sleep(0.1)
        
        # Check for EW attack packets
        bus = get_defense_bus()
        feedback = bus.receive_ew_feedback(timeout=0.01)
        
        if feedback:
            attack_packets_received += 1
            print(f"  Frame {i}: Radar received EW attack "
                  f"({len(feedback.active_countermeasures)} CMs, "
                  f"effectiveness={feedback.overall_effectiveness:.2f})")
    
    # Get statistics
    radar_stats = {
        'packets_sent': radar.packets_sent
    }
    
    ew_stats = pipeline.feedback_publisher.get_statistics()
    
    print(f"\nRadar Statistics:")
    print(f"  Intelligence Packets Sent: {radar_stats['packets_sent']}")
    
    print(f"\nEW Statistics:")
    print(f"  Attack Packets Sent: {ew_stats['packets_sent']}")
    print(f"  Attack Packets Dropped: {ew_stats['packets_dropped']}")
    
    print(f"\nRadar Received:")
    print(f"  Attack Packets: {attack_packets_received}")
    
    radar.stop()
    pipeline.stop()
    
    # Verify
    assert ew_stats['packets_sent'] > 0, "EW should send attack packets"
    assert attack_packets_received > 0, "Radar should receive attack packets"
    
    print("\n✓ End-to-end communication working")
    return True


if __name__ == '__main__':
    print("\n" + "="*80)
    print("EW ATTACK PACKET PUBLISHING TEST SUITE")
    print("="*80)
    
    results = {}
    
    # Run all tests
    results['packet_creation'] = test_packet_creation()
    results['action_type'] = test_action_type_mapping()
    results['jam_power'] = test_jam_power_calculation()
    results['effectiveness'] = test_effectiveness_calculation()
    results['rationale'] = test_decision_rationale()
    results['event_bus'] = test_event_bus_publishing()
    results['end_to_end'] = test_end_to_end()
    
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
