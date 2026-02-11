
import logging
import threading
import time
import webbrowser
from flask import Flask, jsonify
from typing import Optional, Dict, Any, List
from collections import deque
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

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
        self.last_track_count = 0
        self.last_threat_count = 0
        self.last_decision_count = 0

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
    if not _SHARED.state:
        return jsonify({'status': 'initializing', 'uptime': 0})
    
    return jsonify({
        'status': 'active' if _SHARED.state.running else 'stopped',
        'shutdown_requested': _SHARED.state.shutdown_requested,
        'uptime': _SHARED.state.clock.tick_count * 0.1  # approx
    })

@app.route('/state')
def get_state():
    """Full system state."""
    if not _SHARED.state:
        return jsonify({'error': 'Not initialized'}), 503

    s = _SHARED.state
    
    # Get snapshot from shared tactical state
    try:
        if hasattr(s, 'tactical_state') and s.tactical_state:
            snapshot = s.tactical_state.get_snapshot()
        else:
            # Fallback if tactical_state not available (shouldn't happen if launched correctly)
            return jsonify({'error': 'Tactical state unavailable'}), 503
    except Exception as e:
        logger.error(f"Failed to get tactical state snapshot: {e}")
        return jsonify({'error': 'State error'}), 500
            
    radar_data = snapshot.get('radar', {})
    ew_data = snapshot.get('ew', {})
    
    # Event logging: detect changes and log events
    try:
        current_track_count = len(radar_data.get('tracks', []))
        current_threat_count = len(radar_data.get('threats', []))
        current_decision_count = ew_data.get('decision_count', 0)
        
        # Log new tracks
        if current_track_count > _SHARED.last_track_count:
            new_tracks = current_track_count - _SHARED.last_track_count
            _SHARED.event_log.add_event(
                'TRACK_DETECTION',
                'INFO',
                f'{new_tracks} new track(s) detected',
                {'count': new_tracks, 'total': current_track_count}
            )
        
        # Log new threats
        if current_threat_count > _SHARED.last_threat_count:
            new_threats = current_threat_count - _SHARED.last_threat_count
            threats = radar_data.get('threats', [])
            # Get the latest threat for details
            if threats:
                latest_threat = threats[-1] if isinstance(threats[-1], dict) else {}
                threat_class = latest_threat.get('threat_class', 'UNKNOWN')
                priority = latest_threat.get('threat_priority', 0)
                severity = 'CRITICAL' if priority >= 7 else 'WARNING' if priority >= 4 else 'INFO'
                
                _SHARED.event_log.add_event(
                    'THREAT_ASSESSMENT',
                    severity,
                    f'{threat_class} threat detected (Priority: {priority})',
                    {'threat_class': threat_class, 'priority': priority}
                )
        
        # Log new EW decisions
        if current_decision_count > _SHARED.last_decision_count:
            new_decisions = current_decision_count - _SHARED.last_decision_count
            _SHARED.event_log.add_event(
                'EW_DECISION',
                'INFO',
                f'{new_decisions} new EW decision(s) made',
                {'count': new_decisions, 'total': current_decision_count}
            )
        
        # Update counters
        _SHARED.last_track_count = current_track_count
        _SHARED.last_threat_count = current_threat_count
        _SHARED.last_decision_count = current_decision_count
        
    except Exception as e:
        logger.warning(f"Event logging error: {e}")
            
    # Create response structure
    response = {
        "radar": {
            "detections": radar_data.get('tracks', []),
            "detection_history": radar_data.get('detection_history', []),
            "snr_history": [
                {'frame': h['frame'], 'snr': h['mean_snr_db']} 
                for h in radar_data.get('telemetry_history', [])
            ],
            "tracks": radar_data.get('tracks', [])
        },
        "ew": {
            "active_jamming": "ACTIVE" if ew_data.get('active_jamming', False) else "INACTIVE",
            "decision": ew_data.get('last_assessment', {}).get('engagement_recommendation', 'MONITOR'),
            "confidence": ew_data.get('last_assessment', {}).get('classification_confidence', 0.0)
        },
        "system": {
            "tick": snapshot.get('tick', 0),
            "health": "OK" if s.running else "STOPPED",
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
