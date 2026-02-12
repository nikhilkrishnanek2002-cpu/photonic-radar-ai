
import threading
import time
import json
import os
from typing import Dict, List, Any, Optional
from collections import deque

class TacticalState:
    """
    Single source of truth for system tactical state.
    Shared between Radar, EW, API, and UI.
    Thread-safe.
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        
        # System status
        self.initialized = False
        self.running = False
        self.start_time = time.time()
        self.tick_count = 0
        
        # Radar State
        self.radar_status = "OFFLINE"
        self.radar_tracks: List[Dict] = []
        self.radar_telemetry_history: deque = deque(maxlen=200)
        self.radar_detection_history: deque = deque(maxlen=500)
        self.radar_threats: List[Dict] = []
        
        # EW State
        self.ew_status = "OFFLINE"
        self.ew_active_jamming = False
        self.ew_decision_count = 0
        self.ew_last_assessment: Dict = {}
        
        # Queue Stats
        self.queue_sizes: Dict[str, int] = {}
        
        # Persistence
        self.persistence_path = "runtime/shared_state.json"
        self.last_persist_time = 0
        self.persistence_lock = threading.Lock()
        
    def _persist(self):
        """Write state to disk for IPC."""
        # Throttle to 10Hz max to avoid I/O thrashing
        now = time.time()
        if now - self.last_persist_time < 0.1:
            return
            
        try:
            snapshot = self.get_snapshot()
            # Convert collections.deque to list for JSON serialization logic (handled in get_snapshot)
            # We need to ensure all data is json serializable
            
            # Custom serializer for numpy types
            def default_serializer(obj):
                if hasattr(obj, 'tolist'):
                    return obj.tolist()
                if hasattr(obj, '__dict__'):
                    return obj.__dict__
                return str(obj)

            with self.persistence_lock:
                with open(self.persistence_path + '.tmp', 'w') as f:
                    json.dump(snapshot, f, default=default_serializer)
                
                os.rename(self.persistence_path + '.tmp', self.persistence_path)
            
            self.last_persist_time = now
        except Exception as e:
            print(f"State persistence failed: {e}")
            # pass

    def update_tick(self, tick: int):
        """Update simulation tick."""
        with self._lock:
            self.tick_count = tick
        self._persist()
            
    def update_radar(self, status: str, tracks: List[Dict], threats: List[Dict], telemetry: Optional[Dict] = None, detection_record: Optional[Dict] = None):
        """Update radar state."""
        with self._lock:
            self.radar_status = status
            self.radar_tracks = tracks
            self.radar_threats = threats
            
            if telemetry:
                self.radar_telemetry_history.append(telemetry)
                
            if detection_record:
                self.radar_detection_history.append(detection_record)
        self._persist()
                
    def update_ew(self, status: str, decision_count: int, last_assessment: Dict, active_jamming: bool):
        """Update EW state."""
        with self._lock:
            self.ew_status = status
            self.ew_decision_count = decision_count
            self.ew_last_assessment = last_assessment
            self.ew_active_jamming = active_jamming
        self._persist()
            
    def update_queues(self, sizes: Dict[str, int]):
        """Update queue statistics."""
        with self._lock:
            self.queue_sizes = sizes
        self._persist()
            
    def get_snapshot(self) -> Dict[str, Any]:
        """Get a complete state snapshot for the API."""
        with self._lock:
            return {
                "tick": self.tick_count,
                "uptime": time.time() - self.start_time,
                "radar": {
                    "status": self.radar_status,
                    "tracks": list(self.radar_tracks), # Copy
                    "threats": list(self.radar_threats), # Copy
                    "telemetry_history": list(self.radar_telemetry_history),
                    "detection_history": list(self.radar_detection_history)
                },
                "ew": {
                    "status": self.ew_status,
                    "decision_count": self.ew_decision_count,
                    "last_assessment": self.ew_last_assessment.copy() if self.ew_last_assessment else {},
                    "active_jamming": self.ew_active_jamming
                },
                "queues": self.queue_sizes.copy()
            }
