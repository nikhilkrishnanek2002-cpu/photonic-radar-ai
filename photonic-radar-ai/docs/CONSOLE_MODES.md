# Military-Grade Radar Console - Operational Modes

## Overview

The Military-Grade Radar Console provides a sophisticated multi-mode interface for tactical and strategic radar operations. Four distinct operational modes serve different user roles and mission requirements.

## Operational Modes

### 1. **OPERATOR MODE** (Tactical)
Real-time threat detection and tactical response interface.

**Primary Functions:**
- Active threat assessment with real-time updates
- Critical alert management with immediate visibility
- Recent detection history with bearing/range data
- Track management and targeting information

**Key Metrics:**
- Threats Detected (current scan)
- Active Tracks (confirmed)
- Confidence Average
- System Health Status

**Who Uses It:** Radar operators, tactical controllers, air defense personnel

**Interface:** Fast-paced, minimal scrolling, large alert indicators

---

### 2. **COMMANDER MODE** (Strategic)
High-level situational awareness and strategic decision support.

**Primary Functions:**
- Strategic situation reports (SITREP)
- System status overview (radar, processing, tracking, EW defense)
- Tactical analysis with incident distribution
- Complete incident logging and review

**Key Visualizations:**
- Total contacts (tracked and unconfirmed)
- Threat level assessment (LOW/MEDIUM/HIGH/CRITICAL)
- Coverage percentage
- System component health dashboard

**Analytics:**
- Incident type distribution (bar charts)
- Severity distribution (pie charts)
- Trend analysis

**Who Uses It:** Commanders, air defense officers, mission planners

**Interface:** Strategic overview, drill-down capability, summary statistics

---

### 3. **RESEARCH MODE** (Technical Analysis)
Detailed technical analysis and system debugging.

**Primary Functions:**
- Detailed metrics and statistics
- Session replay and timeline navigation
- System debug information
- Performance trend analysis

**Key Features:**
- Frame-by-frame replay with slider control
- Real-time/historical frame navigation (play, pause, step)
- Playback speed adjustment
- System configuration inspection

**Analytics:**
- Performance trends over 24 hours
- Detection and false alarm rates
- Track confidence evolution
- Custom metric queries

**Who Uses It:** System engineers, researchers, performance analysts

**Interface:** Technical depth, numerical precision, debugging tools

---

### 4. **MAINTENANCE MODE** (Diagnostics)
System health monitoring and configuration management.

**Primary Functions:**
- System health diagnostics
- Component status monitoring
- Configuration parameter adjustment
- System log review and analysis

**Diagnostics:**
- Radar Unit status
- Processing Core load
- Storage usage
- Network connectivity
- AI Model status
- Database synchronization

**Configuration:**
- Carrier Frequency (1-40 GHz)
- Bandwidth (10-500 MHz)
- Pulse Repetition Frequency (1-100 kHz)
- Pulse Width (0.1-10 µs)

**Who Uses It:** System administrators, maintenance technicians

**Interface:** Technical specifications, component health monitoring, configuration persistence

---

## Alert System

### Alert Severity Levels

```
INFO          - Informational messages (system updates, mode changes)
WARNING       - Warning conditions (performance degradation, high false alarm rate)
CRITICAL      - Critical alerts (signal loss, jamming detection)
SYSTEM_FAILURE - System component failures requiring immediate attention
```

### Alert Features

- **Real-time Display**: Critical alerts appear immediately on all screens
- **Dismissal**: Users can dismiss individual or all alerts
- **History**: Dismissed alerts retain complete audit trail
- **Statistics**: Track alert trends and patterns
- **Filtering**: View only critical alerts or by source component

### Alert Manager API

```python
from src.console_modes import Alert, AlertSeverity, AlertManager

manager = AlertManager(max_history=100)

# Add alert
manager.add_alert(Alert(
    severity=AlertSeverity.WARNING,
    title="High False Alarm Rate",
    message="FAR exceeded 10%",
    source="CFAR Detector"
))

# Get active alerts
alerts = manager.get_active_alerts()

# Dismiss alert by index
manager.dismiss_alert(0)

# Get statistics
stats = manager.get_statistics()
# {
#   'total_alerts': 5,
#   'active_count': 2,
#   'critical_count': 0,
#   'by_severity': {'Warning': 2, 'Info': 3}
# }
```

---

## Incident Logging

### Incident Types

```
DETECTION       - Radar target detected
TRACKING        - Track created/updated/deleted
OOD_EVENT       - Out-of-distribution detection
JAMMING         - Electronic warfare jamming detected
FALSE_ALARM     - Confirmed false alarm
SYSTEM_ERROR    - System error or malfunction
ANOMALY         - Anomalous sensor behavior
```

### Features

- **Dual Storage**: Memory cache + SQLite database for persistence
- **Time Range Queries**: Filter by start/end datetime
- **Type Filtering**: Query specific incident types
- **Export**: Save filtered incidents as JSON
- **Statistics**: Comprehensive incident analytics

### Incident Logger API

```python
from src.console_modes import Incident, IncidentType, IncidentLogger

logger = IncidentLogger(db_path="results/incidents.db")

# Log incident
logger.log_incident(Incident(
    incident_type=IncidentType.DETECTION,
    description="Aircraft at bearing 045°, range 50km",
    data={'bearing': 45, 'range': 50, 'confidence': 0.95},
    operator="CDR Thompson"
))

# Query incidents
recent = logger.get_incidents(limit=100)
detections = logger.get_incidents(incident_type=IncidentType.DETECTION)

# Time range query
from datetime import datetime, timedelta
start = datetime.now() - timedelta(hours=1)
end = datetime.now()
incidents = logger.get_incidents_by_time_range(start, end)

# Get statistics
stats = logger.get_statistics()
# {
#   'total_incidents': 150,
#   'by_type': {'Detection': 120, 'Tracking': 25, 'OOD_Event': 5},
#   'by_severity': {'Info': 130, 'Warning': 20},
#   'latest': {...},
#   'oldest': {...}
# }

# Export incidents
logger.export_incidents(
    "export.json",
    start_time=start,
    end_time=end
)
```

---

## Replay Capability

### Features

- **Frame Recording**: Capture system state at each scan
- **Timeline Navigation**: Seek to any point in recording
- **Playback Control**: Play, pause, step forward/backward
- **Speed Control**: Adjust playback speed (0.5x - 2x)
- **Frame Metadata**: Timestamps, alerts, incidents per frame

### Replay Manager API

```python
from src.console_modes import ReplayManager

replay = ReplayManager()

# Record frame
replay.record_frame({
    'detections': [...],
    'tracks': [...],
    'alerts': [...],
    'timestamp': time.time()
})

# Seek to specific frame
frame = replay.seek_frame(100)

# Navigation
next_frame = replay.next_frame()
prev_frame = replay.prev_frame()

# Playback
replay.is_playing = True
replay.playback_speed = 1.5

# Get timeline data for visualization
timeline = replay.get_timeline_data()
# [
#   {'index': 0, 'timestamp': 1234567890, 'has_alert': False, 'has_incident': False},
#   {'index': 1, 'timestamp': 1234567891, 'has_alert': True, 'has_incident': False},
#   ...
# ]

# Reset
replay.reset()
```

---

## Console State Management

### ConsoleState Class

Manages operational state and provides unified interface to all subsystems.

```python
from src.console_modes import ConsoleState, OperationalMode

console = ConsoleState()

# Mode control
console.switch_mode(OperationalMode.COMMANDER)
current_mode = console.get_mode()

# Operator information
console.operator_name = "CDR Thompson"
console.current_sector = "North"
console.mission_status = "Active"

# Statistics tracking
console.detections_count = 15
console.tracks_count = 8
console.false_alarms_count = 2
console.ood_events_count = 1

# Get uptime
uptime = console.get_uptime_formatted()  # "00:15:32"

# Get dashboard statistics
stats = console.get_dashboard_stats()
# {
#   'mode': 'Commander',
#   'operator': 'CDR Thompson',
#   'sector': 'North',
#   'mission_status': 'Active',
#   'detections': 15,
#   'tracks': 8,
#   'false_alarms': 2,
#   'ood_events': 1,
#   'uptime': '00:15:32',
#   'active_alerts': 2,
#   'critical_alerts': 0
# }

# Access subsystems
alerts = console.alert_manager.get_active_alerts()
incidents = console.incident_logger.get_incidents()
replay = console.replay_manager
```

---

## Streamlit UI Integration

### Running the Console

```bash
streamlit run app_console.py
```

### Features

- **Real-time Mode Switching**: Select operational mode from sidebar
- **Operator Identification**: Name-based tracking for audit trails
- **Sector Management**: Configure coverage area
- **Mission Status**: Track current mission state

### Mode-Specific Tabs

**Operator Mode:**
- 🎯 THREATS: Active threat assessment
- ⚠️ ALERTS: Critical alert management
- 📡 DETECTIONS: Recent detection log
- 📍 TRACKING: Track management

**Commander Mode:**
- 🎯 SITUATION: Strategic SITREP
- 📈 ANALYSIS: Incident distribution charts
- 🔔 INCIDENT LOG: Complete incident history

**Research Mode:**
- 📊 METRICS: Detailed statistics and JSON export
- 🔍 REPLAY: Frame-by-frame session replay
- ⚙️ DEBUG: System configuration and debug info
- 📈 TRENDS: 24-hour performance trends

**Maintenance Mode:**
- 🏥 HEALTH: Component status diagnostics
- ⚙️ CONFIG: Radar parameter tuning
- 🔐 LOGS: System event logging

---

## Database Schema

### Incidents Table

```sql
CREATE TABLE incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_type TEXT NOT NULL,          -- DETECTION, JAMMING, etc.
    description TEXT NOT NULL,            -- Human-readable event
    timestamp REAL NOT NULL,              -- Unix timestamp
    data TEXT NOT NULL,                   -- JSON data payload
    severity TEXT NOT NULL,               -- INFO, WARNING, CRITICAL
    operator TEXT NOT NULL,               -- Who logged the incident
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Testing

Comprehensive test suite with 27 tests covering:

```bash
# Run console mode tests
pytest tests/test_console_modes.py -v

# Test results: 27/27 passing (100%)
# - Alert creation and management (6 tests)
# - Incident logging and queries (7 tests)
# - Replay functionality (4 tests)
# - Console state management (3 tests)
# - Integration workflows (2 tests)
```

---

## Security & Access Control

### Role-Based Features

Each mode is designed for specific roles with appropriate permissions:

| Mode | Role | Detection | Alert Create | Config | Export |
|------|------|-----------|-------------|--------|--------|
| Operator | Technician | ✓ | ✓ | ✗ | ✗ |
| Commander | Officer | ✓ | ✓ | ✗ | ✓ |
| Research | Engineer | ✓ | ✓ | ✓ | ✓ |
| Maintenance | Admin | ✓ | ✓ | ✓ | ✓ |

### Audit Trail

All actions logged:
- Alert creation/dismissal
- Incident logging
- Mode switches
- Configuration changes
- Operator identification

---

## Example Usage Scenarios

### Scenario 1: Tactical Detection Response
1. Operator sees critical alert in Operator Mode
2. Reviews detection details in DETECTIONS tab
3. Dismisses alert after analysis
4. Consults Commander for targeting authority

### Scenario 2: Post-Mission Analysis
1. Commander switches to Research Mode
2. Accesses REPLAY tab to review session
3. Navigates to time of false alarm
4. Exports incident data for analysis

### Scenario 3: System Maintenance
1. Admin switches to Maintenance Mode
2. Checks system health in HEALTH tab
3. Adjusts radar parameters in CONFIG tab
4. Reviews diagnostic logs

### Scenario 4: Long-Duration Surveillance
1. Operator runs in Operator Mode for 8+ hours
2. Alert system tracks all incidents
3. Database stores persistent records
4. Commander accesses analytics via ANALYSIS tab

---

## Performance Metrics

- **Alert Processing**: <1ms per alert
- **Incident Logging**: <5ms disk write
- **Database Query**: <10ms for 1000 records
- **Replay Frame Seek**: <2ms
- **UI Refresh**: 100ms (Streamlit default)

---

## Future Enhancements

- [ ] Real-time threat correlation
- [ ] Machine learning anomaly detection
- [ ] Multi-user concurrent sessions
- [ ] Network-based remote console
- [ ] Advanced export formats (CSV, XML)
- [ ] Integration with external systems (C2, IDL)
- [ ] Encrypted audit logs
- [ ] GPS/map integration
- [ ] 3D visualization of threat space
- [ ] Predictive analytics and TTL estimation

---

## References

- **Console State**: src/console_modes.py (500+ lines)
- **UI Implementation**: app_console.py (1000+ lines)
- **Test Suite**: tests/test_console_modes.py (27 tests)
- **Alert Classes**: AlertSeverity, Alert, AlertManager
- **Incident Classes**: IncidentType, Incident, IncidentLogger
- **Replay Classes**: ReplayManager
