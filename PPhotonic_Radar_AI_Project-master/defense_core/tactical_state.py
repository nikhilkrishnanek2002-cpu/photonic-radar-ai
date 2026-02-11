
import threading
import time
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
        
    def update_tick(self, tick: int):
        """Update simulation tick."""
        with self._lock:
            self.tick_count = tick
            
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
                
    def update_ew(self, status: str, decision_count: int, last_assessment: Dict, active_jamming: bool):
        """Update EW state."""
        with self._lock:
            self.ew_status = status
            self.ew_decision_count = decision_count
            self.ew_last_assessment = last_assessment
            self.ew_active_jamming = active_jamming
            
    def update_queues(self, sizes: Dict[str, int]):
        """Update queue statistics."""
        with self._lock:
            self.queue_sizes = sizes
            
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
