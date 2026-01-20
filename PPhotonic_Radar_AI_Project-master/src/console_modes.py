"""
Military-Grade Radar Console Operational Modes.

Implements:
- Operator Mode (real-time tactical operations)
- Commander Mode (strategic overview, threat assessment)
- Research Mode (detailed analysis, debugging)
- Maintenance Mode (system diagnostics, configuration)
- Alert system with severity levels
- Incident logging and replay capability
"""

import json
import time
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import sqlite3
import threading
from pathlib import Path


class OperationalMode(Enum):
    """Console operational modes."""
    OPERATOR = "Operator"
    COMMANDER = "Commander"
    RESEARCH = "Research"
    MAINTENANCE = "Maintenance"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "Info"
    WARNING = "Warning"
    CRITICAL = "Critical"
    SYSTEM_FAILURE = "System Failure"


class IncidentType(Enum):
    """Incident classification."""
    DETECTION = "Detection"
    TRACKING = "Tracking"
    OOD_EVENT = "OOD Event"
    JAMMING = "Jamming"
    FALSE_ALARM = "False Alarm"
    SYSTEM_ERROR = "System Error"
    ANOMALY = "Anomaly"


@dataclass
class Alert:
    """Structured alert message."""
    severity: AlertSeverity
    title: str
    message: str
    timestamp: float = field(default_factory=time.time)
    dismissed: bool = False
    source: str = "System"  # Component that generated the alert
    
    def __post_init__(self):
        if isinstance(self.severity, str):
            self.severity = AlertSeverity(self.severity)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'severity': self.severity.value,
            'title': self.title,
            'message': self.message,
            'timestamp': self.timestamp,
            'dismissed': self.dismissed,
            'source': self.source,
            'formatted_time': datetime.fromtimestamp(self.timestamp).isoformat()
        }


@dataclass
class Incident:
    """Structured incident log entry."""
    incident_type: IncidentType
    description: str
    timestamp: float = field(default_factory=time.time)
    data: Dict = field(default_factory=dict)
    severity: AlertSeverity = AlertSeverity.INFO
    operator: str = "System"
    
    def __post_init__(self):
        if isinstance(self.incident_type, str):
            self.incident_type = IncidentType(self.incident_type)
        if isinstance(self.severity, str):
            self.severity = AlertSeverity(self.severity)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'incident_type': self.incident_type.value,
            'description': self.description,
            'timestamp': self.timestamp,
            'data': self.data,
            'severity': self.severity.value,
            'operator': self.operator,
            'formatted_time': datetime.fromtimestamp(self.timestamp).isoformat()
        }


class AlertManager:
    """Manages alert queue and history."""
    
    def __init__(self, max_history: int = 100):
        """
        Initialize alert manager.
        
        Args:
            max_history: maximum alerts to keep in memory
        """
        self.active_alerts: List[Alert] = []
        self.history: List[Alert] = []
        self.max_history = max_history
    
    def add_alert(self, alert: Alert):
        """Add new alert."""
        self.active_alerts.append(alert)
    
    def dismiss_alert(self, index: int):
        """Dismiss alert by index."""
        if 0 <= index < len(self.active_alerts):
            alert = self.active_alerts[index]
            alert.dismissed = True
            self.history.append(alert)
            self.active_alerts.pop(index)
            
            # Trim history
            if len(self.history) > self.max_history:
                self.history = self.history[-self.max_history:]
    
    def dismiss_all(self):
        """Dismiss all active alerts."""
        for alert in self.active_alerts:
            alert.dismissed = True
            self.history.append(alert)
        self.active_alerts.clear()
    
    def get_active_alerts(self) -> List[Alert]:
        """Get list of active alerts."""
        return self.active_alerts.copy()
    
    def get_critical_alerts(self) -> List[Alert]:
        """Get only critical/system failure alerts."""
        return [a for a in self.active_alerts if a.severity in [
            AlertSeverity.CRITICAL, AlertSeverity.SYSTEM_FAILURE
        ]]
    
    def get_history(self, limit: int = 50) -> List[Alert]:
        """Get recent alert history."""
        return self.history[-limit:]
    
    def get_statistics(self) -> Dict:
        """Get alert statistics."""
        all_alerts = self.active_alerts + self.history
        
        if not all_alerts:
            return {
                'total_alerts': 0,
                'active_count': 0,
                'critical_count': 0,
                'by_severity': {}
            }
        
        severity_counts = {}
        for alert in all_alerts:
            key = alert.severity.value
            severity_counts[key] = severity_counts.get(key, 0) + 1
        
        return {
            'total_alerts': len(all_alerts),
            'active_count': len(self.active_alerts),
            'critical_count': len(self.get_critical_alerts()),
            'by_severity': severity_counts
        }


class IncidentLogger:
    """Logs and manages incidents with replay capability."""
    
    def __init__(self, db_path: str = "results/incidents.db"):
        """
        Initialize incident logger.
        
        Args:
            db_path: path to SQLite database for persistence
        """
        self.db_path = db_path
        self.memory_log: List[Incident] = []
        self.max_memory = 500
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_type TEXT NOT NULL,
                description TEXT NOT NULL,
                timestamp REAL NOT NULL,
                data TEXT NOT NULL,
                severity TEXT NOT NULL,
                operator TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_incident(self, incident: Incident):
        """Log incident to memory and database."""
        # Memory log
        self.memory_log.append(incident)
        if len(self.memory_log) > self.max_memory:
            self.memory_log.pop(0)
        
        # Database persistence
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('''
                INSERT INTO incidents 
                (incident_type, description, timestamp, data, severity, operator)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                incident.incident_type.value,
                incident.description,
                incident.timestamp,
                json.dumps(incident.data),
                incident.severity.value,
                incident.operator
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error logging to database: {e}")
    
    def get_incidents(self, limit: int = 100, 
                     incident_type: Optional[IncidentType] = None) -> List[Incident]:
        """Get incidents from memory."""
        incidents = self.memory_log.copy()
        
        if incident_type:
            incidents = [i for i in incidents if i.incident_type == incident_type]
        
        return incidents[-limit:]
    
    def get_incidents_by_time_range(self, start_time: datetime, 
                                   end_time: datetime) -> List[Incident]:
        """Get incidents within time range."""
        start_ts = start_time.timestamp()
        end_ts = end_time.timestamp()
        
        return [i for i in self.memory_log 
                if start_ts <= i.timestamp <= end_ts]
    
    def replay_incidents(self, start_idx: int = 0, 
                        count: int = 10) -> List[Incident]:
        """Replay incidents for timeline analysis."""
        return self.memory_log[start_idx:start_idx + count]
    
    def get_incident_timeline(self, duration_minutes: int = 60) -> List[Incident]:
        """Get timeline of recent incidents."""
        cutoff_time = (datetime.now() - timedelta(minutes=duration_minutes)).timestamp()
        return [i for i in self.memory_log if i.timestamp >= cutoff_time]
    
    def get_statistics(self) -> Dict:
        """Get incident statistics."""
        if not self.memory_log:
            return {
                'total_incidents': 0,
                'by_type': {},
                'by_severity': {},
                'latest': None
            }
        
        type_counts = {}
        severity_counts = {}
        
        for incident in self.memory_log:
            type_key = incident.incident_type.value
            sev_key = incident.severity.value
            
            type_counts[type_key] = type_counts.get(type_key, 0) + 1
            severity_counts[sev_key] = severity_counts.get(sev_key, 0) + 1
        
        return {
            'total_incidents': len(self.memory_log),
            'by_type': type_counts,
            'by_severity': severity_counts,
            'latest': self.memory_log[-1].to_dict() if self.memory_log else None,
            'oldest': self.memory_log[0].to_dict() if self.memory_log else None
        }
    
    def export_incidents(self, filepath: str, 
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> bool:
        """Export incidents to JSON file."""
        try:
            incidents = self.memory_log.copy()
            
            if start_time and end_time:
                incidents = self.get_incidents_by_time_range(start_time, end_time)
            
            with open(filepath, 'w') as f:
                json.dump([i.to_dict() for i in incidents], f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error exporting incidents: {e}")
            return False


class ReplayManager:
    """Manages session replay and timeline navigation."""
    
    def __init__(self):
        """Initialize replay manager."""
        self.frames: List[Dict] = []
        self.current_frame: int = 0
        self.is_playing: bool = False
        self.playback_speed: float = 1.0
        self.last_playback_time: float = time.time()
    
    def record_frame(self, frame_data: Dict):
        """Record a frame."""
        frame_data['frame_index'] = len(self.frames)
        frame_data['recorded_time'] = time.time()
        self.frames.append(frame_data)
    
    def seek_frame(self, frame_index: int):
        """Seek to specific frame."""
        if 0 <= frame_index < len(self.frames):
            self.current_frame = frame_index
            return self.frames[frame_index]
        return None
    
    def next_frame(self) -> Optional[Dict]:
        """Get next frame."""
        if self.current_frame < len(self.frames) - 1:
            self.current_frame += 1
            return self.frames[self.current_frame]
        self.is_playing = False
        return None
    
    def prev_frame(self) -> Optional[Dict]:
        """Get previous frame."""
        if self.current_frame > 0:
            self.current_frame -= 1
            return self.frames[self.current_frame]
        return None
    
    def get_current_frame(self) -> Optional[Dict]:
        """Get current frame."""
        if 0 <= self.current_frame < len(self.frames):
            return self.frames[self.current_frame]
        return None
    
    def get_frame_count(self) -> int:
        """Get total frame count."""
        return len(self.frames)
    
    def reset(self):
        """Reset replay to beginning."""
        self.current_frame = 0
        self.is_playing = False
    
    def get_timeline_data(self) -> List[Dict]:
        """Get timeline data for visualization."""
        return [
            {
                'index': i,
                'timestamp': f.get('recorded_time', 0),
                'has_alert': 'alert' in f,
                'has_incident': 'incident' in f
            }
            for i, f in enumerate(self.frames)
        ]


class ConsoleState:
    """Manages console operational state."""
    
    def __init__(self):
        """Initialize console state."""
        self.mode: OperationalMode = OperationalMode.OPERATOR
        self.alert_manager = AlertManager()
        self.incident_logger = IncidentLogger()
        self.replay_manager = ReplayManager()
        
        # Statistics
        self.detections_count: int = 0
        self.tracks_count: int = 0
        self.false_alarms_count: int = 0
        self.ood_events_count: int = 0
        self.system_uptime: float = time.time()
        
        # Operator info
        self.operator_name: str = "System"
        self.current_sector: str = "Full Coverage"
        self.mission_status: str = "Active"
    
    def switch_mode(self, mode: OperationalMode):
        """Switch operational mode."""
        self.mode = mode
        self.incident_logger.log_incident(
            Incident(
                incident_type=IncidentType.SYSTEM_ERROR,
                description=f"Mode switched to {mode.value}",
                severity=AlertSeverity.INFO,
                operator=self.operator_name
            )
        )
    
    def get_mode(self) -> OperationalMode:
        """Get current mode."""
        return self.mode
    
    def get_uptime_formatted(self) -> str:
        """Get formatted uptime."""
        elapsed = time.time() - self.system_uptime
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics."""
        return {
            'mode': self.mode.value,
            'operator': self.operator_name,
            'sector': self.current_sector,
            'mission_status': self.mission_status,
            'detections': self.detections_count,
            'tracks': self.tracks_count,
            'false_alarms': self.false_alarms_count,
            'ood_events': self.ood_events_count,
            'uptime': self.get_uptime_formatted(),
            'active_alerts': len(self.alert_manager.get_active_alerts()),
            'critical_alerts': len(self.alert_manager.get_critical_alerts())
        }


if __name__ == "__main__":
    print("=== Console Modes Demo ===\n")
    
    # Test alert system
    am = AlertManager()
    am.add_alert(Alert(
        severity=AlertSeverity.WARNING,
        title="High False Alarm Rate",
        message="False alarm rate exceeded 10%"
    ))
    am.add_alert(Alert(
        severity=AlertSeverity.CRITICAL,
        title="Signal Lost",
        message="Radar signal reception degraded below threshold"
    ))
    
    print("Active Alerts:")
    for alert in am.get_active_alerts():
        print(f"  [{alert.severity.value}] {alert.title}: {alert.message}")
    
    print(f"\nAlert Stats: {am.get_statistics()}\n")
    
    # Test incident logging
    il = IncidentLogger()
    il.log_incident(Incident(
        incident_type=IncidentType.DETECTION,
        description="Aircraft detected at bearing 045, range 50km",
        data={'bearing': 45, 'range': 50, 'confidence': 0.95}
    ))
    il.log_incident(Incident(
        incident_type=IncidentType.OOD_EVENT,
        description="Anomalous signal pattern detected",
        severity=AlertSeverity.WARNING
    ))
    
    print("Incident Statistics:")
    stats = il.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test console state
    cs = ConsoleState()
    cs.operator_name = "CDR Thompson"
    cs.detections_count = 15
    cs.tracks_count = 8
    
    print(f"\nConsole State: {cs.get_dashboard_stats()}")
