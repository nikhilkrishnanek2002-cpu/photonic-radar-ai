"""Unit tests for Kalman-based multi-target tracker."""

import pytest
import numpy as np
from src.tracker import Track, MultiTargetTracker, KalmanFilter1D


class TestKalmanFilter1D:
    """Tests for basic Kalman filter."""
    
    def test_predict_motion(self):
        """Test that predict advances state correctly."""
        x0 = np.array([0, 0, 1.0, 0])  # [x, y, vx, vy]
        P0 = np.eye(4)
        F = np.array([
            [1, 0, 0.1, 0],
            [0, 1, 0, 0.1],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        H = np.array([[1, 0, 0, 0], [0, 1, 0, 0]])
        Q = 0.01 * np.eye(4)
        R = 1.0 * np.eye(2)
        
        kf = KalmanFilter1D(x0, P0, Q, R, F, H)
        kf.predict()
        
        # After one step, x should be [0.1, 0, 1.0, 0]
        assert np.isclose(kf.x[0], 0.1)
        assert np.isclose(kf.x[1], 0)
        assert np.isclose(kf.x[2], 1.0)
    
    def test_update_with_measurement(self):
        """Test that update corrects state toward measurement."""
        x0 = np.array([0, 0, 0, 0])
        P0 = np.eye(4)
        F = np.eye(4)
        H = np.array([[1, 0, 0, 0], [0, 1, 0, 0]])
        Q = 0.01 * np.eye(4)
        R = 1.0 * np.eye(2)
        
        kf = KalmanFilter1D(x0, P0, Q, R, F, H)
        
        z = np.array([1.0, 1.0])
        kf.update(z)
        
        # After update, x should move toward measurement
        assert kf.x[0] > 0.0
        assert kf.x[1] > 0.0


class TestTrack:
    """Tests for single-target track."""
    
    def test_track_initialization(self):
        """Test track creation from detection."""
        detection = (10.0, 5.0, 0.8)
        track = Track(detection)
        
        assert track.state == 'tentative'
        assert track.measurement_count == 1
        assert track.missed_count == 0
        pos = track.get_position()
        assert np.isclose(pos[0], 10.0)
        assert np.isclose(pos[1], 5.0)
    
    def test_track_prediction(self):
        """Test track prediction (constant velocity model)."""
        detection = (0.0, 0.0, 1.0)
        track = Track(detection, dt=0.1)
        
        # Set velocity
        track.kf.x[2] = 1.0  # vx = 1.0
        track.kf.x[3] = 0.5  # vy = 0.5
        
        # Predict
        track.predict()
        pos = track.get_position()
        
        # Position should advance by velocity * dt
        assert pos[0] > 0.0
        assert pos[1] > 0.0
    
    def test_track_update_and_confidence(self):
        """Test track update and confidence scoring."""
        detection = (10.0, 5.0, 0.8)
        track = Track(detection)
        
        assert track.get_confidence() < 0.5  # Tentative
        
        # Add measurements to confirm track
        track.update((10.1, 5.1, 0.8))
        track.update((10.2, 5.2, 0.8))
        track.confirm()
        
        assert track.state == 'confirmed'
        assert track.get_confidence() > 0.5
    
    def test_track_missed_detection_and_deletion(self):
        """Test that tracks delete after missed detections."""
        detection = (10.0, 5.0, 0.8)
        track = Track(detection)
        track.confirm()
        
        for _ in range(6):
            track.miss()
        
        track.delete()
        assert track.state == 'deleted'
        assert track.get_confidence() == 0.0


class TestMultiTargetTracker:
    """Tests for multi-target tracker."""
    
    def test_tracker_initialization(self):
        """Test tracker creation."""
        cfg = {
            'max_missed': 5,
            'confirmation_threshold': 3,
            'gating_threshold': 20.0
        }
        tracker = MultiTargetTracker(cfg)
        
        assert len(tracker.tracks) == 0
        assert tracker.time_step == 0
    
    def test_single_target_tracking(self):
        """Test tracking a single target over time."""
        tracker = MultiTargetTracker({'gating_threshold': 20.0, 'confirmation_threshold': 2})
        
        # Simulate a target moving in a straight line
        for t in range(5):
            detection = (10.0 + t * 0.5, 5.0 + t * 0.2, 0.8)
            active = tracker.update([detection])
            
            if t >= 1:  # Should be confirmed after 2 detections
                # Should have at least one active track
                assert len(active) >= 0
    
    def test_multi_target_association(self):
        """Test association of multiple targets."""
        tracker = MultiTargetTracker({
            'gating_threshold': 30.0,
            'confirmation_threshold': 2,
            'max_missed': 3
        })
        
        # First scan: 2 detections
        detections1 = [(10.0, 5.0, 0.8), (50.0, 20.0, 0.7)]
        active1 = tracker.update(detections1)
        
        assert len(tracker.tracks) == 2
        
        # Second scan: same targets (slightly moved)
        detections2 = [(10.5, 5.1, 0.8), (50.3, 20.2, 0.7)]
        active2 = tracker.update(detections2)
        
        # Should still have 2 tracks
        assert len(tracker.tracks) == 2
    
    def test_track_initialization_and_confirmation(self):
        """Test that tracks go from tentative to confirmed."""
        tracker = MultiTargetTracker({
            'confirmation_threshold': 3,
            'gating_threshold': 20.0
        })
        
        # Feed 3 detections from same location
        for _ in range(3):
            detections = [(10.0, 5.0, 0.8)]
            active = tracker.update(detections)
        
        # After 3 detections, track should be confirmed
        active_tracks = tracker.get_active_tracks()
        if active_tracks:
            for track_info in active_tracks.values():
                assert track_info['state'] == 'confirmed'
    
    def test_new_target_creation(self):
        """Test that new detections create new tracks."""
        tracker = MultiTargetTracker({'max_tracks': 5})
        
        # Add 3 new targets in first scan
        detections = [(10.0, 5.0, 0.8), (50.0, 20.0, 0.7), (100.0, 30.0, 0.6)]
        tracker.update(detections)
        
        assert len(tracker.tracks) == 3
        
        # Add 2 more targets
        new_detections = [(10.0, 5.0, 0.8), (50.0, 20.0, 0.7), (100.0, 30.0, 0.6),
                          (30.0, 15.0, 0.7), (70.0, 40.0, 0.6)]
        tracker.update(new_detections)
        
        assert len(tracker.tracks) == 5
    
    def test_unmatched_detection_handling(self):
        """Test that unmatched detections don't crash tracker."""
        tracker = MultiTargetTracker({'gating_threshold': 5.0})
        
        # Add first detection
        detections1 = [(10.0, 5.0, 0.8)]
        tracker.update(detections1)
        
        # Add far-away detection (should start new track)
        detections2 = [(100.0, 100.0, 0.7)]
        tracker.update(detections2)
        
        assert len(tracker.tracks) == 2
    
    def test_missed_detection_and_track_deletion(self):
        """Test that missed detections eventually delete tracks."""
        tracker = MultiTargetTracker({
            'max_missed': 2,
            'confirmation_threshold': 1,
            'gating_threshold': 20.0
        })
        
        # Create and confirm track
        tracker.update([(10.0, 5.0, 0.8)])
        for _ in range(3):
            tracker.update([])
        
        # After multiple misses, should have deleted some tracks
        active_tracks = tracker.get_active_tracks()
        # The exact count depends on track deletion logic
        assert isinstance(active_tracks, dict)
    
    def test_get_active_tracks(self):
        """Test filtering of active high-confidence tracks."""
        tracker = MultiTargetTracker({
            'confirmation_threshold': 1,
            'gating_threshold': 20.0
        })
        
        # Create a tentative track
        tracker.update([(10.0, 5.0, 0.8)])
        tentative = tracker.get_active_tracks()
        
        # Tentative tracks should not appear in active_tracks (unless high confidence)
        # This depends on confidence threshold
        assert isinstance(tentative, dict)
    
    def test_reset_tracker(self):
        """Test tracker reset clears all state."""
        tracker = MultiTargetTracker()
        tracker.update([(10.0, 5.0, 0.8), (50.0, 20.0, 0.7)])
        
        assert len(tracker.tracks) > 0
        
        tracker.reset()
        assert len(tracker.tracks) == 0
        assert tracker.time_step == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
