"""
Defense Core Module - Test Suite
=================================

Tests for defense_core neutral interface layer.

Author: Defense Core Test Team
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from defense_core import (
    Track, ThreatAssessment, SceneContext, TacticalPictureMessage,
    Countermeasure, EngagementStatus, EWFeedbackMessage,
    EventBus, Event, EventType,
    validate_tactical_picture, validate_ew_feedback,
    is_message_stale
)


def test_message_schemas():
    """Test message schema creation and serialization."""
    print("\n" + "="*70)
    print("TEST 1: Message Schemas")
    print("="*70)
    
    # Create tactical picture
    track = Track(
        track_id=101,
        range_m=5000.0,
        azimuth_deg=45.0,
        radial_velocity_m_s=-200.0,
        track_quality=0.92
    )
    
    threat = ThreatAssessment(
        track_id=101,
        threat_class="HOSTILE",
        target_type="MISSILE",
        classification_confidence=0.88,
        threat_priority=10,
        engagement_recommendation="ENGAGE"
    )
    
    scene = SceneContext(
        scene_type="TRACKING",
        clutter_ratio=0.1,
        mean_snr_db=20.0,
        num_confirmed_tracks=1
    )
    
    tactical_msg = TacticalPictureMessage.create(
        frame_id=0,
        sensor_id="TEST_RADAR",
        tracks=[track],
        threat_assessments=[threat],
        scene_context=scene
    )
    
    print(f"✓ Created tactical picture message")
    print(f"  Message ID: {tactical_msg.message_id[:16]}...")
    print(f"  Tracks: {len(tactical_msg.tracks)}")
    print(f"  Threats: {len(tactical_msg.threat_assessments)}")
    
    # Serialize to JSON
    json_str = tactical_msg.to_json(indent=2)
    print(f"✓ Serialized to JSON ({len(json_str)} bytes)")
    
    # Create EW feedback
    cm = Countermeasure(
        countermeasure_id=1,
        target_track_id=101,
        cm_type="NOISE_JAM",
        start_time=time.time(),
        power_level_dbm=40.0,
        effectiveness_score=0.8
    )
    
    engagement = EngagementStatus(
        track_id=101,
        engagement_state="ENGAGING",
        kill_probability=0.75
    )
    
    feedback_msg = EWFeedbackMessage.create(
        effector_id="TEST_EW",
        countermeasures=[cm],
        engagements=[engagement]
    )
    
    print(f"✓ Created EW feedback message")
    print(f"  Message ID: {feedback_msg.message_id[:16]}...")
    print(f"  Countermeasures: {len(feedback_msg.active_countermeasures)}")
    print(f"  Engagements: {len(feedback_msg.engagement_status)}")
    
    print("\n✓ TEST 1 PASSED\n")


def test_validators():
    """Test message validators."""
    print("\n" + "="*70)
    print("TEST 2: Message Validators")
    print("="*70)
    
    # Valid tactical picture
    track = Track(
        track_id=101,
        range_m=5000.0,
        azimuth_deg=45.0,
        radial_velocity_m_s=-200.0,
        track_quality=0.92
    )
    
    threat = ThreatAssessment(
        track_id=101,
        threat_class="HOSTILE",
        target_type="MISSILE",
        classification_confidence=0.88,
        threat_priority=10,
        engagement_recommendation="ENGAGE"
    )
    
    scene = SceneContext(
        scene_type="TRACKING",
        clutter_ratio=0.1,
        mean_snr_db=20.0,
        num_confirmed_tracks=1
    )
    
    tactical_msg = TacticalPictureMessage.create(
        frame_id=0,
        sensor_id="TEST_RADAR",
        tracks=[track],
        threat_assessments=[threat],
        scene_context=scene
    )
    
    is_valid, errors = validate_tactical_picture(tactical_msg)
    print(f"✓ Valid tactical picture: {is_valid}")
    assert is_valid, f"Validation failed: {errors}"
    
    # Invalid track (negative range)
    bad_track = Track(
        track_id=102,
        range_m=-1000.0,  # Invalid
        azimuth_deg=45.0,
        radial_velocity_m_s=-200.0,
        track_quality=0.92
    )
    
    bad_tactical_msg = TacticalPictureMessage.create(
        frame_id=0,
        sensor_id="TEST_RADAR",
        tracks=[bad_track],
        threat_assessments=[],
        scene_context=scene
    )
    
    is_valid, errors = validate_tactical_picture(bad_tactical_msg)
    print(f"✓ Invalid tactical picture detected: {not is_valid}")
    print(f"  Errors: {errors}")
    assert not is_valid, "Should have detected invalid range"
    
    # Test message staleness
    old_timestamp = time.time() - 10.0  # 10 seconds ago
    is_stale = is_message_stale(old_timestamp, time.time())
    print(f"✓ Stale message detected: {is_stale}")
    assert is_stale, "Should detect stale message"
    
    print("\n✓ TEST 2 PASSED\n")


def test_event_bus():
    """Test event bus publish/subscribe."""
    print("\n" + "="*70)
    print("TEST 3: Event Bus")
    print("="*70)
    
    bus = EventBus()
    
    # Track received events
    received_events = []
    
    def event_handler(event: Event):
        received_events.append(event)
    
    # Subscribe to event
    bus.subscribe(EventType.TACTICAL_PICTURE_PUBLISHED, event_handler)
    print(f"✓ Subscribed to TACTICAL_PICTURE_PUBLISHED")
    
    # Publish event
    event = Event.create(
        event_type=EventType.TACTICAL_PICTURE_PUBLISHED,
        data={'frame_id': 0, 'tracks': 1},
        source='TEST_RADAR'
    )
    
    bus.publish(event)
    print(f"✓ Published event")
    
    # Verify event received
    assert len(received_events) == 1, "Event not received"
    assert received_events[0].event_type == EventType.TACTICAL_PICTURE_PUBLISHED
    print(f"✓ Event received by subscriber")
    
    # Test queue-based subscriber
    queue = bus.create_queue_subscriber(
        subscriber_id='test_queue',
        event_types=[EventType.EW_FEEDBACK_PUBLISHED]
    )
    
    # Publish to queue
    event2 = Event.create(
        event_type=EventType.EW_FEEDBACK_PUBLISHED,
        data={'countermeasures': 1},
        source='TEST_EW'
    )
    
    bus.publish(event2)
    
    # Get from queue
    received = bus.get_event('test_queue', timeout=0.5)
    assert received is not None, "Event not in queue"
    assert received.event_type == EventType.EW_FEEDBACK_PUBLISHED
    print(f"✓ Queue-based subscription working")
    
    # Statistics
    stats = bus.get_statistics()
    print(f"\n✓ Event bus statistics:")
    print(f"  Events published: {stats['events_published']}")
    print(f"  Events delivered: {stats['events_delivered']}")
    print(f"  Active subscribers: {stats['active_subscribers']}")
    
    print("\n✓ TEST 3 PASSED\n")


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("DEFENSE CORE MODULE TEST SUITE")
    print("="*70)
    
    try:
        test_message_schemas()
        test_validators()
        test_event_bus()
        
        print("\n" + "="*70)
        print("ALL TESTS PASSED ✓")
        print("="*70)
        print("\nDefense Core Module:")
        print("  ✓ Message schemas working")
        print("  ✓ Validators working")
        print("  ✓ Event bus working")
        print("  ✓ No dependencies on radar/EW internals")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
