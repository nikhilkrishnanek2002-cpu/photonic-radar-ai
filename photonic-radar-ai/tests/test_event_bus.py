"""
Event-Driven Communication System - Test Suite
===============================================

Tests for dual-queue event bus.

Author: Defense Core Test Team
"""

import sys
import time
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from defense_core.event_bus import DefenseEventBus, get_defense_bus, reset_defense_bus
from defense_core import (
    RadarIntelligencePacket, ElectronicAttackPacket,
    Track, ThreatAssessment, SceneContext,
    Countermeasure, EngagementStatus
)


def test_non_blocking_reads():
    """Test non-blocking reads (no stalling)."""
    print("\n" + "="*70)
    print("TEST 1: Non-Blocking Reads")
    print("="*70)
    
    bus = DefenseEventBus()
    
    # Try to read from empty queue (should return None immediately)
    start = time.time()
    intel = bus.receive_intelligence(timeout=0.0)
    elapsed = time.time() - start
    
    assert intel is None, "Should return None for empty queue"
    assert elapsed < 0.01, f"Should be immediate, took {elapsed:.3f}s"
    print(f"✓ Non-blocking read from empty queue: {elapsed*1000:.1f}ms")
    
    # Try to read with short timeout
    start = time.time()
    intel = bus.receive_intelligence(timeout=0.1)
    elapsed = time.time() - start
    
    assert intel is None, "Should return None after timeout"
    assert 0.09 < elapsed < 0.15, f"Should timeout at ~0.1s, took {elapsed:.3f}s"
    print(f"✓ Timeout read: {elapsed*1000:.1f}ms")
    
    print("\n✓ TEST 1 PASSED\n")


def test_safe_writes():
    """Test safe writes (drop on full)."""
    print("\n" + "="*70)
    print("TEST 2: Safe Writes")
    print("="*70)
    
    # Create small queue
    bus = DefenseEventBus(radar_to_ew_maxsize=5)
    
    # Create test message
    track = Track(track_id=101, range_m=5000.0, azimuth_deg=45.0)
    threat = ThreatAssessment(
        track_id=101,
        threat_class='HOSTILE',
        target_type='MISSILE',
        classification_confidence=0.88
    )
    scene = SceneContext(
        scene_type='TRACKING',
        clutter_ratio=0.1,
        mean_snr_db=20.0,
        num_confirmed_tracks=1
    )
    
    # Fill queue
    for i in range(5):
        intel = RadarIntelligencePacket.create(
            frame_id=i,
            sensor_id='TEST',
            tracks=[track],
            threat_assessments=[threat],
            scene_context=scene
        )
        success = bus.publish_intelligence(intel)
        assert success, f"Message {i} should succeed"
    
    print(f"✓ Filled queue: 5/5 messages")
    
    # Try to write to full queue (should drop)
    intel = RadarIntelligencePacket.create(
        frame_id=99,
        sensor_id='TEST',
        tracks=[track],
        threat_assessments=[threat],
        scene_context=scene
    )
    success = bus.publish_intelligence(intel)
    assert not success, "Should drop message when queue full"
    print(f"✓ Dropped message on full queue")
    
    # Read one message
    msg = bus.receive_intelligence()
    assert msg is not None, "Should receive message"
    assert msg.frame_id == 0, "Should be first message"
    print(f"✓ Read message: frame={msg.frame_id}")
    
    # Now write should succeed
    success = bus.publish_intelligence(intel)
    assert success, "Should succeed after space available"
    print(f"✓ Write succeeded after space available")
    
    print("\n✓ TEST 2 PASSED\n")


def test_thread_safety():
    """Test thread-safe design."""
    print("\n" + "="*70)
    print("TEST 3: Thread Safety")
    print("="*70)
    
    bus = DefenseEventBus()
    messages_sent = []
    messages_received = []
    
    # Create test data
    track = Track(track_id=101, range_m=5000.0, azimuth_deg=45.0)
    threat = ThreatAssessment(
        track_id=101,
        threat_class='HOSTILE',
        target_type='MISSILE',
        classification_confidence=0.88
    )
    scene = SceneContext(
        scene_type='TRACKING',
        clutter_ratio=0.1,
        mean_snr_db=20.0,
        num_confirmed_tracks=1
    )
    
    def producer():
        """Producer thread (radar)."""
        for i in range(10):
            intel = RadarIntelligencePacket.create(
                frame_id=i,
                sensor_id='TEST',
                tracks=[track],
                threat_assessments=[threat],
                scene_context=scene
            )
            bus.publish_intelligence(intel)
            messages_sent.append(i)
            time.sleep(0.01)
    
    def consumer():
        """Consumer thread (EW)."""
        while len(messages_received) < 10:
            intel = bus.receive_intelligence(timeout=0.05)
            if intel:
                messages_received.append(intel.frame_id)
    
    # Start threads
    t1 = threading.Thread(target=producer)
    t2 = threading.Thread(target=consumer)
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()
    
    assert len(messages_sent) == 10, "Should send 10 messages"
    assert len(messages_received) == 10, "Should receive 10 messages"
    print(f"✓ Sent: {len(messages_sent)}, Received: {len(messages_received)}")
    
    print("\n✓ TEST 3 PASSED\n")


def test_no_stalling():
    """Test that radar never stalls if EW is slow."""
    print("\n" + "="*70)
    print("TEST 4: No Stalling (Radar Never Blocks)")
    print("="*70)
    
    bus = DefenseEventBus()
    
    # Create test data
    track = Track(track_id=101, range_m=5000.0, azimuth_deg=45.0)
    threat = ThreatAssessment(
        track_id=101,
        threat_class='HOSTILE',
        target_type='MISSILE',
        classification_confidence=0.88
    )
    scene = SceneContext(
        scene_type='TRACKING',
        clutter_ratio=0.1,
        mean_snr_db=20.0,
        num_confirmed_tracks=1
    )
    
    # Radar publishes 100 messages without EW reading
    start = time.time()
    for i in range(100):
        intel = RadarIntelligencePacket.create(
            frame_id=i,
            sensor_id='TEST',
            tracks=[track],
            threat_assessments=[threat],
            scene_context=scene
        )
        bus.publish_intelligence(intel)
    elapsed = time.time() - start
    
    # Should complete quickly (non-blocking)
    assert elapsed < 0.5, f"Should be fast, took {elapsed:.3f}s"
    print(f"✓ Published 100 messages in {elapsed*1000:.1f}ms (non-blocking)")
    
    # Check statistics
    stats = bus.get_statistics()
    print(f"✓ Radar→EW: sent={stats['radar_to_ew']['messages_sent']}, "
          f"dropped={stats['radar_to_ew']['messages_dropped']}")
    
    print("\n✓ TEST 4 PASSED\n")


def test_bidirectional_communication():
    """Test bidirectional radar↔EW communication."""
    print("\n" + "="*70)
    print("TEST 5: Bidirectional Communication")
    print("="*70)
    
    bus = DefenseEventBus()
    
    # Create test data
    track = Track(track_id=101, range_m=5000.0, azimuth_deg=45.0)
    threat = ThreatAssessment(
        track_id=101,
        threat_class='HOSTILE',
        target_type='MISSILE',
        classification_confidence=0.88
    )
    scene = SceneContext(
        scene_type='TRACKING',
        clutter_ratio=0.1,
        mean_snr_db=20.0,
        num_confirmed_tracks=1
    )
    
    # Radar → EW
    intel = RadarIntelligencePacket.create(
        frame_id=0,
        sensor_id='RADAR_01',
        tracks=[track],
        threat_assessments=[threat],
        scene_context=scene
    )
    bus.publish_intelligence(intel)
    print("✓ Radar published intelligence")
    
    # EW receives
    received_intel = bus.receive_intelligence()
    assert received_intel is not None, "EW should receive intelligence"
    assert received_intel.frame_id == 0, "Should be correct message"
    print(f"✓ EW received intelligence: frame={received_intel.frame_id}")
    
    # EW → Radar
    cm = Countermeasure(
        countermeasure_id=1,
        target_track_id=101,
        cm_type='NOISE_JAM',
        start_time=time.time(),
        power_level_dbm=40.0,
        effectiveness_score=0.8
    )
    eng = EngagementStatus(
        track_id=101,
        engagement_state='ENGAGING',
        kill_probability=0.75
    )
    feedback = ElectronicAttackPacket.create(
        effector_id='EW_01',
        countermeasures=[cm],
        engagements=[eng]
    )
    bus.publish_feedback(feedback)
    print("✓ EW published feedback")
    
    # Radar receives
    received_feedback = bus.receive_ew_feedback()
    assert received_feedback is not None, "Radar should receive feedback"
    assert len(received_feedback.active_countermeasures) == 1, "Should have 1 CM"
    print(f"✓ Radar received feedback: {len(received_feedback.active_countermeasures)} CMs")
    
    print("\n✓ TEST 5 PASSED\n")


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("EVENT-DRIVEN COMMUNICATION SYSTEM TEST SUITE")
    print("="*70)
    
    try:
        test_non_blocking_reads()
        test_safe_writes()
        test_thread_safety()
        test_no_stalling()
        test_bidirectional_communication()
        
        print("\n" + "="*70)
        print("ALL TESTS PASSED ✓")
        print("="*70)
        print("\nEvent-Driven Communication System:")
        print("  ✓ Non-blocking reads (no stalling)")
        print("  ✓ Safe writes (drop on full)")
        print("  ✓ Thread-safe design")
        print("  ✓ Radar never blocks")
        print("  ✓ Bidirectional communication")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
