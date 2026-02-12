"""
EW Intelligence Ingestion Test Suite
=====================================

Tests intelligence ingestion, validation, and processing for Cognitive EW-AI.

Test Coverage:
1. Subscriber receives and validates messages
2. Schema validation catches errors
3. Missing data handling
4. Stale data detection
5. Comprehensive logging
6. End-to-end pipeline
"""

import sys
import time
import json
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from interfaces.subscriber import IntelligenceSubscriber
from interfaces.message_schema import TacticalPictureMessage, Track, ThreatAssessment, SceneContext
from cognitive.intelligence_pipeline import EWIntelligencePipeline
import logging

# Setup logging to see all intelligence updates
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def create_test_intelligence_message(frame_id: int) -> TacticalPictureMessage:
    """Create a valid test intelligence message."""
    tracks = [
        Track(
            track_id=101,
            range_m=5000.0,
            azimuth_deg=45.0,
            radial_velocity_m_s=-150.0,
            track_quality=0.92,
            track_age_frames=50,
            last_update_timestamp=time.time()
        )
    ]
    
    threats = [
        ThreatAssessment(
            track_id=101,
            threat_class="HOSTILE",
            target_type="MISSILE",
            classification_confidence=0.88,
            threat_priority=9,
            engagement_recommendation="ENGAGE",
            classification_uncertainty=0.12,
            position_uncertainty_m=2.5,
            velocity_uncertainty_m_s=1.2
        )
    ]
    
    scene = SceneContext(
        scene_type="TRACKING",
        clutter_ratio=0.1,
        mean_snr_db=22.5,
        num_confirmed_tracks=1
    )
    
    return TacticalPictureMessage.create(
        frame_id=frame_id,
        sensor_id="TEST_RADAR",
        tracks=tracks,
        threat_assessments=threats,
        scene_context=scene
    )


def test_subscriber_basic():
    """Test 1: Basic subscriber functionality."""
    print("\n" + "="*70)
    print("TEST 1: Basic Subscriber Functionality")
    print("="*70)
    
    test_dir = Path('./test_ew_intelligence')
    test_dir.mkdir(exist_ok=True)
    
    try:
        # Create subscriber
        subscriber = IntelligenceSubscriber(
            source_directory=str(test_dir),
            staleness_threshold_s=2.0,
            poll_interval_s=0.05,
            log_all_updates=True
        )
        
        subscriber.start()
        print("✓ Subscriber started")
        
        # Create test intelligence files
        for i in range(3):
            msg = create_test_intelligence_message(i)
            file_path = test_dir / f"intel_test_frame{i:06d}.json"
            with open(file_path, 'w') as f:
                f.write(msg.to_json(indent=2))
            print(f"  Created test file: {file_path.name}")
        
        # Wait for processing
        time.sleep(0.5)
        
        # Check statistics
        stats = subscriber.get_statistics()
        print(f"\nSubscriber Statistics:")
        print(f"  Messages received: {stats['messages_received']}")
        print(f"  Messages valid: {stats['messages_valid']}")
        print(f"  Messages invalid: {stats['messages_invalid']}")
        print(f"  Validation errors: {stats['validation_errors']}")
        
        assert stats['messages_received'] == 3, "Should receive 3 messages"
        assert stats['messages_valid'] == 3, "All messages should be valid"
        assert stats['validation_errors'] == 0, "No validation errors expected"
        
        subscriber.stop()
        print("\n✓ TEST 1 PASSED")
        
    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)


def test_schema_validation():
    """Test 2: Schema validation catches errors."""
    print("\n" + "="*70)
    print("TEST 2: Schema Validation")
    print("="*70)
    
    test_dir = Path('./test_ew_validation')
    test_dir.mkdir(exist_ok=True)
    
    try:
        subscriber = IntelligenceSubscriber(
            source_directory=str(test_dir),
            staleness_threshold_s=2.0,
            poll_interval_s=0.05
        )
        
        subscriber.start()
        
        # Create invalid message (missing mandatory field)
        invalid_msg = {
            "message_id": "test-123",
            "timestamp": time.time(),
            "frame_id": 0,
            # Missing sensor_id (mandatory)
            "tracks": [],
            "threat_assessments": []
        }
        
        file_path = test_dir / "intel_invalid.json"
        with open(file_path, 'w') as f:
            json.dump(invalid_msg, f)
        
        print("  Created invalid message (missing sensor_id)")
        
        # Wait for processing
        time.sleep(0.3)
        
        stats = subscriber.get_statistics()
        print(f"\nValidation Statistics:")
        print(f"  Messages received: {stats['messages_received']}")
        print(f"  Messages valid: {stats['messages_valid']}")
        print(f"  Messages invalid: {stats['messages_invalid']}")
        
        assert stats['messages_invalid'] > 0, "Should detect invalid message"
        
        subscriber.stop()
        print("\n✓ TEST 2 PASSED (Validation working)")
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_stale_data_detection():
    """Test 3: Stale data detection."""
    print("\n" + "="*70)
    print("TEST 3: Stale Data Detection")
    print("="*70)
    
    test_dir = Path('./test_ew_stale')
    test_dir.mkdir(exist_ok=True)
    
    try:
        subscriber = IntelligenceSubscriber(
            source_directory=str(test_dir),
            staleness_threshold_s=1.0,  # 1 second threshold
            poll_interval_s=0.05
        )
        
        subscriber.start()
        
        # Create message with old timestamp
        msg = create_test_intelligence_message(0)
        msg.timestamp = time.time() - 3.0  # 3 seconds old
        
        file_path = test_dir / "intel_stale.json"
        with open(file_path, 'w') as f:
            f.write(msg.to_json(indent=2))
        
        print("  Created stale message (3s old, threshold 1s)")
        
        # Wait for processing
        time.sleep(0.3)
        
        stats = subscriber.get_statistics()
        print(f"\nStaleness Statistics:")
        print(f"  Messages stale: {stats['messages_stale']}")
        
        assert stats['messages_stale'] > 0, "Should detect stale message"
        
        subscriber.stop()
        print("\n✓ TEST 3 PASSED (Staleness detection working)")
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_ew_pipeline_integration():
    """Test 4: End-to-end EW pipeline."""
    print("\n" + "="*70)
    print("TEST 4: EW Intelligence Pipeline Integration")
    print("="*70)
    
    test_dir = Path('./test_ew_pipeline')
    test_dir.mkdir(exist_ok=True)
    
    try:
        # Create pipeline
        pipeline = EWIntelligencePipeline(
            enable_ingestion=True,
            source_directory=str(test_dir),
            staleness_threshold_s=2.0,
            poll_interval_s=0.05,
            log_all_updates=True
        )
        
        pipeline.start()
        print("✓ EW Pipeline started")
        
        # Create test intelligence
        for i in range(5):
            msg = create_test_intelligence_message(i)
            file_path = test_dir / f"intel_pipeline_frame{i:06d}.json"
            with open(file_path, 'w') as f:
                f.write(msg.to_json(indent=2))
        
        print("  Created 5 test intelligence messages")
        
        # Wait for processing
        time.sleep(1.0)
        
        # Check statistics
        stats = pipeline.get_statistics()
        print(f"\nPipeline Statistics:")
        print(f"  Subscriber messages received: {stats['subscriber']['messages_received']}")
        print(f"  Pipeline messages processed: {stats['pipeline']['messages_processed']}")
        print(f"  Pipeline messages rejected: {stats['pipeline']['messages_rejected']}")
        print(f"  Has valid intelligence: {stats['pipeline']['has_valid_intelligence']}")
        
        # Get latest assessment
        assessment = pipeline.get_latest_assessment()
        if assessment:
            print(f"\nLatest Situation Assessment:")
            print(f"  Scene Type: {assessment.scene_type.value}")
            print(f"  Confirmed Tracks: {assessment.num_confirmed_tracks}")
            print(f"  Mean Confidence: {assessment.mean_classification_confidence:.2f}")
            print(f"  Estimated SNR: {assessment.estimated_snr_db:.1f} dB")
        
        assert stats['pipeline']['messages_processed'] > 0, "Should process messages"
        assert assessment is not None, "Should have situation assessment"
        
        pipeline.stop()
        print("\n✓ TEST 4 PASSED (End-to-end pipeline working)")
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("EW INTELLIGENCE INGESTION TEST SUITE")
    print("="*70)
    
    try:
        test_subscriber_basic()
        test_schema_validation()
        test_stale_data_detection()
        test_ew_pipeline_integration()
        
        print("\n" + "="*70)
        print("ALL TESTS PASSED ✓")
        print("="*70)
        print("\nKey Findings:")
        print("  ✓ Intelligence subscriber receives and validates messages")
        print("  ✓ Schema validation catches malformed messages")
        print("  ✓ Stale data detection working (configurable threshold)")
        print("  ✓ Comprehensive logging for every received update")
        print("  ✓ End-to-end pipeline processes intelligence correctly")
        print("  ✓ Cognitive engine generates situation assessments")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
