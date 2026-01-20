"""
Kalman-based Multi-Target Tracker for Photonic Radar.

Handles:
- Track initiation, confirmation, deletion
- Unique persistent target IDs
- Missed detection handling
- Track confidence scoring
- Data association via Hungarian algorithm
"""

import numpy as np
from scipy.optimize import linear_sum_assignment
from collections import defaultdict
import uuid
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple


@dataclass
class KalmanState:
    """Single Kalman filter state for a target."""
    x: np.ndarray  # [x, y, vx, vy] in range-Doppler space
    P: np.ndarray  # Covariance (4x4)
    F: np.ndarray  # State transition (4x4)
    H: np.ndarray  # Measurement matrix (2x4): [x, y] observed
    Q: np.ndarray  # Process noise (4x4)
    R: np.ndarray  # Measurement noise (2x2)


class KalmanFilter1D:
    """Simple Kalman filter for 1D state estimation."""
    
    def __init__(self, x0, P0, Q, R, F, H):
        self.x = x0
        self.P = P0
        self.Q = Q
        self.R = R
        self.F = F
        self.H = H
    
    def predict(self):
        """Predict next state."""
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
    
    def update(self, z):
        """Update with measurement."""
        y = z - self.H @ self.x  # Innovation
        S = self.H @ self.P @ self.H.T + self.R  # Innovation covariance
        K = self.P @ self.H.T @ np.linalg.inv(S)  # Kalman gain
        self.x = self.x + K @ y
        self.P = (np.eye(len(self.x)) - K @ self.H) @ self.P
        return np.linalg.norm(y) ** 2 / np.linalg.norm(S)  # Mahalanobis distance squared


class Track:
    """Single target track with Kalman filter."""
    
    def __init__(self, detection: Tuple[float, float, float], 
                 process_noise: float = 0.1, 
                 measurement_noise: float = 1.0,
                 dt: float = 0.1):
        """
        Initialize a track from a detection.
        
        Args:
            detection: (range_idx, doppler_idx, value)
            process_noise: std of process noise
            measurement_noise: std of measurement noise
            dt: time step
        """
        self.id = str(uuid.uuid4())[:8]
        self.creation_time = 0
        self.measurement_count = 1  # started with 1 detection
        self.missed_count = 0
        self.state = 'tentative'  # 'tentative', 'confirmed', or 'deleted'
        
        # State: [x, y, vx, vy]
        x0 = np.array([detection[0], detection[1], 0.0, 0.0])
        P0 = np.diag([1.0, 1.0, 1.0, 1.0])
        
        # Transition matrix (constant velocity model)
        F = np.array([
            [1, 0, dt, 0],
            [0, 1, 0, dt],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        
        # Measurement matrix (observe position only)
        H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ])
        
        # Process noise
        Q = (process_noise ** 2) * np.diag([0.1, 0.1, 1.0, 1.0])
        
        # Measurement noise
        R = (measurement_noise ** 2) * np.eye(2)
        
        self.kf = KalmanFilter1D(x0, P0, Q, R, F, H)
        self.last_measurement = np.array([detection[0], detection[1]])
        self.detection_value = detection[2]
    
    def predict(self):
        """Predict track to next time step."""
        self.kf.predict()
    
    def update(self, detection: Tuple[float, float, float]):
        """Update track with a measurement."""
        z = np.array([detection[0], detection[1]])
        self.kf.update(z)
        self.last_measurement = z
        self.detection_value = detection[2]
        self.measurement_count += 1
        self.missed_count = 0
    
    def miss(self):
        """Increment missed detection counter."""
        self.missed_count += 1
    
    def get_state(self) -> Tuple[float, float, float, float]:
        """Return current state [x, y, vx, vy]."""
        return tuple(self.kf.x)
    
    def get_position(self) -> Tuple[float, float]:
        """Return current position [x, y]."""
        return (float(self.kf.x[0]), float(self.kf.x[1]))
    
    def get_confidence(self) -> float:
        """Compute track confidence score [0, 1]."""
        if self.state == 'deleted':
            return 0.0
        if self.state == 'tentative':
            # Confidence grows with measurements
            return min(self.measurement_count / 3.0, 0.5)
        # Confirmed tracks
        base = 0.7 + 0.2 * min(self.measurement_count / 10.0, 1.0)
        penalty = 0.05 * self.missed_count
        return np.clip(base - penalty, 0.5, 1.0)
    
    def confirm(self):
        """Promote tentative track to confirmed."""
        if self.state == 'tentative':
            self.state = 'confirmed'
    
    def delete(self):
        """Mark track as deleted."""
        self.state = 'deleted'


class MultiTargetTracker:
    """Multi-target tracker using Kalman filters and data association."""
    
    def __init__(self, config: Dict = None):
        """
        Initialize tracker.
        
        Args:
            config: dict with keys:
                - 'max_missed': max missed detections before deletion (default 5)
                - 'confirmation_threshold': measurements to confirm (default 3)
                - 'gating_threshold': Mahalanobis dist for association (default 9.0)
                - 'process_noise': Kalman Q parameter (default 0.1)
                - 'measurement_noise': Kalman R parameter (default 1.0)
                - 'max_tracks': maximum simultaneous tracks (default 100)
        """
        self.config = config or {}
        self.max_missed = self.config.get('max_missed', 5)
        self.confirmation_threshold = self.config.get('confirmation_threshold', 3)
        self.gating_threshold = self.config.get('gating_threshold', 9.0)
        self.process_noise = self.config.get('process_noise', 0.1)
        self.measurement_noise = self.config.get('measurement_noise', 1.0)
        self.max_tracks = self.config.get('max_tracks', 100)
        
        self.tracks: Dict[str, Track] = {}  # id -> Track
        self.time_step = 0
    
    def predict_all(self):
        """Predict all tracks to next time step."""
        for track in self.tracks.values():
            if track.state != 'deleted':
                track.predict()
    
    def associate_detections(self, detections: List[Tuple[float, float, float]]) -> Dict[str, Optional[int]]:
        """
        Associate detections to tracks using Hungarian algorithm.
        
        Args:
            detections: list of (range_idx, doppler_idx, value)
        
        Returns:
            dict: track_id -> detection_index or None (unmatched)
        """
        if not detections or not self.tracks:
            return {tid: None for tid in self.tracks}
        
        active_tracks = [t for t in self.tracks.values() if t.state in ('tentative', 'confirmed')]
        if not active_tracks:
            return {}
        
        # Compute distance matrix: rows=tracks, cols=detections
        cost_matrix = np.full((len(active_tracks), len(detections)), np.inf)
        for i, track in enumerate(active_tracks):
            for j, det in enumerate(detections):
                dist = np.linalg.norm(np.array(track.get_position()) - np.array([det[0], det[1]]))
                if dist < self.gating_threshold:
                    cost_matrix[i, j] = dist
        
        # Hungarian algorithm (handle all-inf matrix)
        if np.all(np.isinf(cost_matrix)):
            # No feasible assignments
            track_indices, det_indices = [], []
        else:
            track_indices, det_indices = linear_sum_assignment(cost_matrix)
        
        result = {}
        for tid in self.tracks:
            result[tid] = None
        
        for t_idx, d_idx in zip(track_indices, det_indices):
            if cost_matrix[t_idx, d_idx] < np.inf:
                result[active_tracks[t_idx].id] = d_idx
        
        return result
    
    def update(self, detections: List[Tuple[float, float, float]]) -> Dict[str, Dict]:
        """
        Update tracker with new detections.
        
        Args:
            detections: list of (range_idx, doppler_idx, value)
        
        Returns:
            dict: track_id -> {'position': (x, y), 'state': str, 'confidence': float, 'measurement_count': int}
        """
        self.time_step += 1
        
        # Predict
        self.predict_all()
        
        # Associate detections
        associations = self.associate_detections(detections)
        
        # Update matched tracks
        matched_detections = set()
        for track_id, det_idx in associations.items():
            track = self.tracks[track_id]
            if det_idx is not None:
                track.update(detections[det_idx])
                matched_detections.add(det_idx)
                # Promote to confirmed if enough measurements
                if track.state == 'tentative' and track.measurement_count >= self.confirmation_threshold:
                    track.confirm()
            else:
                track.miss()
                # Delete if too many misses
                if track.missed_count > self.max_missed:
                    track.delete()
        
        # Create new tracks for unmatched detections
        if len(self.tracks) < self.max_tracks:
            for d_idx, det in enumerate(detections):
                if d_idx not in matched_detections:
                    new_track = Track(det, 
                                     process_noise=self.process_noise,
                                     measurement_noise=self.measurement_noise)
                    self.tracks[new_track.id] = new_track
        
        # Clean up deleted tracks periodically
        if self.time_step % 10 == 0:
            self.tracks = {tid: t for tid, t in self.tracks.items() if t.state != 'deleted'}
        
        # Return current tracks
        result = {}
        for tid, track in self.tracks.items():
            if track.state != 'deleted':
                result[tid] = {
                    'position': track.get_position(),
                    'state': track.state,
                    'confidence': track.get_confidence(),
                    'measurement_count': track.measurement_count,
                    'velocity': (float(track.kf.x[2]), float(track.kf.x[3])),
                    'value': track.detection_value
                }
        
        return result
    
    def get_active_tracks(self) -> Dict[str, Dict]:
        """Return only confirmed and high-confidence tracks."""
        result = {}
        for tid, track in self.tracks.items():
            if track.state == 'confirmed' and track.get_confidence() > 0.6:
                result[tid] = {
                    'position': track.get_position(),
                    'state': track.state,
                    'confidence': track.get_confidence(),
                    'measurement_count': track.measurement_count,
                    'velocity': (float(track.kf.x[2]), float(track.kf.x[3])),
                    'value': track.detection_value
                }
        return result
    
    def reset(self):
        """Reset tracker state."""
        self.tracks.clear()
        self.time_step = 0


# Example usage
if __name__ == "__main__":
    # Create tracker
    tracker = MultiTargetTracker({
        'max_missed': 5,
        'confirmation_threshold': 3,
        'gating_threshold': 20.0,
    })
    
    # Simulate detections over time
    print("=== Multi-Target Tracker Demo ===")
    for t in range(10):
        print(f"\n--- Time step {t} ---")
        
        # Simulate detections: two objects with constant velocity
        detections = [
            (10.0 + t * 0.5, 5.0 + t * 0.2, 0.8),  # Object 1
            (50.0 - t * 0.3, 20.0 - t * 0.1, 0.7),  # Object 2
        ]
        if t > 5:
            detections.append((100.0 + (t - 6) * 0.4, 30.0, 0.6))  # Object 3 starts
        
        # Update tracker
        active_tracks = tracker.update(detections)
        
        print(f"Active tracks: {len(active_tracks)}")
        for tid, info in active_tracks.items():
            print(f"  ID {tid}: pos={info['position']}, "
                  f"state={info['state']}, conf={info['confidence']:.2f}, "
                  f"meas={info['measurement_count']}")
