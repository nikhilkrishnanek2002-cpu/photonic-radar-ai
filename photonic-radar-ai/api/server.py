
import logging
import threading
import time
import webbrowser
import json
import os
from flask import Flask, jsonify
from typing import Optional, Dict, Any, List
from collections import deque
from datetime import datetime
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

from pathlib import Path
# Determine PROJECT_ROOT: api/..
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SHARED_STATE_PATH = PROJECT_ROOT / "runtime" / "shared_state.json"

# Flask App
app = Flask(__name__)

# Event Log System
class EventLog:
    """Circular buffer for system events."""
    
    def __init__(self, max_size: int = 100):
        self.events = deque(maxlen=max_size)
        self.lock = threading.Lock()
    
    def add_event(self, event_type: str, severity: str, message: str, data: Optional[Dict] = None):
        """Add an event to the log."""
        with self.lock:
            event = {
                'timestamp': datetime.now().strftime('%H:%M:%S.%f')[:-3],
                'type': event_type,
                'severity': severity,  # INFO, WARNING, CRITICAL
                'message': message,
                'data': data or {}
            }
            self.events.append(event)
    
    def get_recent(self, count: int = 20) -> List[Dict]:
        """Get recent events in reverse chronological order."""
        with self.lock:
            # Return last N events, newest first
            return list(reversed(list(self.events)))[:count]

# Shared State Container
class StateContainer:
    def __init__(self):
        self.state = None
        self.event_log = EventLog()
        self.last_track_ids = set()
        self.last_threat_ids = set()
        self.last_decision_count = 0
        self.monitor = None

_SHARED = StateContainer()

@app.route('/')
def home():
    """Root endpoint."""
    return jsonify({
        'message': 'Phoenix Radar API Server Online',
        'endpoints': ['/state', '/health', '/events']
    })

@app.route('/health')
def health():
    """System health status."""
    # Check file freshness for IPC mode
    fresh = False
    uptime = 0
    
    try:
         if SHARED_STATE_PATH.exists():
            mtime = SHARED_STATE_PATH.stat().st_mtime
            if time.time() - mtime < 5.0:
                fresh = True
                # Try to read uptime
                try:
                    with open(SHARED_STATE_PATH, 'r') as f:
                        data = json.load(f)
                        uptime = data.get('uptime', 0)
                except Exception as read_e:
                    pass
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    if _SHARED.state:
        fresh = _SHARED.state.running
        uptime = _SHARED.state.clock.tick_count * 0.1

    return jsonify({
        'status': 'active' if fresh else 'stopped',
        'shutdown_requested': False, # approximated
        'uptime': uptime
    })

@app.route('/state')
def get_state():
    """Full system state."""
    snapshot = None
    
    # Try reading from shared state file (IPC mode)
    # Try reading from shared state file (IPC mode)
    try:
        if SHARED_STATE_PATH.exists():
            # Check modification time to ensure freshness
            mtime = SHARED_STATE_PATH.stat().st_mtime
            if time.time() - mtime < 2.0: # Only accept if fresh
                with open(SHARED_STATE_PATH, 'r') as f:
                    snapshot = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read shared state file: {e}")

    # Fallback to memory state if available (Legacy/Thread mode)
    if not snapshot and _SHARED.state:
        s = _SHARED.state
        try:
            if hasattr(s, 'tactical_state') and s.tactical_state:
                snapshot = s.tactical_state.get_snapshot()
        except Exception as e:
            logger.error(f"Failed to get tactical state snapshot: {e}")

    if not snapshot:
        return jsonify({'error': 'State unavailable'}), 503
            
    radar_data = snapshot.get('radar', {})
    ew_data = snapshot.get('ew', {})
    
    # Mock s.running for file mode
    system_running = snapshot.get('ew', {}).get('status') != 'OFFLINE'
    
    # Create response structure
    # Create response structure
    
    # Extract raw detections from latest history record if available
    latest_detections = []
    det_history = radar_data.get('detection_history', [])
    if det_history:
        latest_detections = det_history[-1].get('detections', [])

    response = {
        "radar": {
            "detections": latest_detections,
            "detection_history": det_history,
            "snr_history": [
                {'frame': h['frame'], 'snr': h['mean_snr_db']} 
                for h in radar_data.get('telemetry_history', [])
            ],
            "tracks": radar_data.get('tracks', []),
            "threats": radar_data.get('threats', [])
        },
        "ew": {
            "active_jamming": "ACTIVE" if ew_data.get('active_jamming', False) else "INACTIVE",
            "decision": ew_data.get('last_assessment', {}).get('engagement_recommendation', 'MONITOR'),
            "confidence": ew_data.get('last_assessment', {}).get('classification_confidence', 0.0),
            "threat_level": ew_data.get('last_assessment', {}).get('threat_priority', 0),
            "threat_class": ew_data.get('last_assessment', {}).get('threat_class', 'UNKNOWN')
        },
        "system": {
            "tick": snapshot.get('tick', 0),
            "health": "OK" if system_running else "STOPPED",
            "uptime": snapshot.get('uptime', 0)
        }
    }

    return jsonify(response)

@app.route('/events')
def get_events():
    """Recent events."""
    events = _SHARED.event_log.get_recent(20)
    return jsonify({
        'events': events,
        'count': len(events)
    })

class EventMonitor:
    """Background monitor that watches for state changes and generates events."""
    
    def __init__(self, state_container: StateContainer):
        self._shared = state_container
        self.running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Start the monitor thread."""
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._monitor_loop, name="EventMonitor")
            self._thread.daemon = True
            self._thread.start()
            logger.info("[UI] Event monitor thread started")

    def _monitor_loop(self):
        """Main loop that polls shared state and generates events."""
        while self.running:
            try:
                # Read snapshot from file (IPC mode)
                if SHARED_STATE_PATH.exists():
                    mtime = SHARED_STATE_PATH.stat().st_mtime
                    if time.time() - mtime < 2.0:
                        with open(SHARED_STATE_PATH, 'r') as f:
                            snapshot = json.load(f)
                        self._process_snapshot(snapshot)
            except Exception as e:
                logger.error(f"Event monitor error: {e}")
            
            time.sleep(0.1)  # 10Hz polling

    def _process_snapshot(self, snapshot: Dict[str, Any]):
        """Detect changes and generate events using ID tracking."""
        radar_data = snapshot.get('radar', {})
        ew_data = snapshot.get('ew', {})
        
        current_tracks = radar_data.get('tracks', [])
        current_threats = radar_data.get('threats', [])
        current_decision_count = ew_data.get('decision_count', 0)
        
        # Extract IDs - support both 'id' and 'track_id'
        current_track_ids = {str(t.get('id') or t.get('track_id')) for t in current_tracks if (t.get('id') is not None or t.get('track_id') is not None)}
        current_threat_ids = {str(t.get('id') or t.get('track_id')) for t in current_threats if (t.get('id') is not None or t.get('track_id') is not None)}
        
        # 1. Detect new/removed tracks
        new_tracks = current_track_ids - self._shared.last_track_ids
        lost_tracks = self._shared.last_track_ids - current_track_ids
        
        for tid in new_tracks:
            self._shared.event_log.add_event(
                'TRACK_DETECTION', 'INFO',
                f'Track {tid} entered radar field',
                {'track_id': tid}
            )
        
        for tid in lost_tracks:
            self._shared.event_log.add_event(
                'TRACK_EXIT', 'INFO',
                f'Track {tid} lost or exited field',
                {'track_id': tid}
            )
            
        # 2. Detect new/removed threats
        new_threats = current_threat_ids - self._shared.last_threat_ids
        for tid in new_threats:
            # Find the threat details
            threat_info = next((t for t in current_threats if str(t.get('track_id')) == tid), {})
            threat_class = threat_info.get('threat_class', 'UNKNOWN')
            priority = threat_info.get('threat_priority', 0)
            severity = 'CRITICAL' if priority >= 7 else 'WARNING' if priority >= 4 else 'INFO'
            
            self._shared.event_log.add_event(
                'THREAT_ASSESSMENT', severity,
                f'{threat_class} threat detected: ID {tid} (Priority: {priority})',
                {'track_id': tid, 'threat_class': threat_class, 'priority': priority}
            )
        
        # 3. Log new EW decisions
        if current_decision_count > self._shared.last_decision_count:
            diff = current_decision_count - self._shared.last_decision_count
            self._shared.event_log.add_event(
                'EW_DECISION', 'INFO',
                f'{diff} new EW decision(s) made',
                {'count': diff, 'total': current_decision_count}
            )
        
        # Update state
        self._shared.last_track_ids = current_track_ids
        self._shared.last_threat_ids = current_threat_ids
        self._shared.last_decision_count = current_decision_count

# Process-local monitor tracking
_MONITOR_INITIALIZED = False

def ensure_monitor():
    """Ensure the event monitor is running in this process."""
    global _MONITOR_INITIALIZED
    if not _MONITOR_INITIALIZED:
        if _SHARED.monitor is None:
            _SHARED.monitor = EventMonitor(_SHARED)
        _SHARED.monitor.start()
        _MONITOR_INITIALIZED = True
        logger.info(f"[UI] Event monitor initialized in process {os.getpid()}")

@app.before_request
def check_monitor():
    """Check monitor on every request (first one will trigger initialization)."""
    ensure_monitor()

def run_server_thread():
    """Target for the server thread."""
    logger.info("[UI] Starting API Server on port 5000...")
    # Disable reloader and debugger for thread safety
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

def start_server(shared_state_obj):
    """
    Start the API server in a daemon thread.
    
    Args:
        shared_state_obj: The LauncherState instance
    """
    _SHARED.state = shared_state_obj
    
    # Start Event Monitor first
    monitor = EventMonitor(_SHARED)
    monitor.start()
    
    t = threading.Thread(target=run_server_thread, name="APIServer")
    t.daemon = True
    t.start()
    logger.info("[UI] API Server thread started")
    
    # Auto-open browser
    def open_browser():
        time.sleep(1.5)  # Wait for server startup
        url = "http://localhost:5000"
        logger.info(f"[UI] Opening browser at {url}")
        webbrowser.open(url)
        
    threading.Thread(target=open_browser, daemon=True).start()

if __name__ == "__main__":
    # Start Event Monitor if running as standalone process
    monitor = EventMonitor(_SHARED)
    monitor.start()
    
    try:
        import uvicorn
        # Run using Uvicorn (Production-grade ASGI/WSGI server)
        # We specify interface='wsgi' because Flask is a WSGI app
        uvicorn.run(
            "api.server:app", 
            host="0.0.0.0", 
            port=5000, 
            log_level="warning",
            interface="wsgi"
        )
    except ImportError:
        # Fallback to Flask development server if uvicorn is missing
        logger.warning("[UI] Uvicorn not found, falling back to Flask dev server")
        app.run(host="0.0.0.0", port=5000, debug=False)
