"""
Unit tests for military-grade console modes and operational features.

Tests:
- Alert management (creation, dismissal, statistics)
- Incident logging (memory, database, export)
- Console state transitions
- Replay functionality
- Time range queries
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import sqlite3

from src.console_modes import (
    Alert, Incident, AlertSeverity, AlertManager, IncidentLogger,
    IncidentType, ConsoleState, OperationalMode, ReplayManager
)


class TestAlert:
    """Test Alert dataclass."""
    
    def test_alert_creation(self):
        """Test alert creation with all fields."""
        alert = Alert(
            severity=AlertSeverity.WARNING,
            title="Test Alert",
            message="This is a test"
        )
        
        assert alert.severity == AlertSeverity.WARNING
        assert alert.title == "Test Alert"
        assert alert.message == "This is a test"
        assert alert.dismissed is False
        assert alert.timestamp > 0
    
    def test_alert_to_dict(self):
        """Test alert serialization."""
        alert = Alert(
            severity=AlertSeverity.CRITICAL,
            title="Critical",
            message="Critical event"
        )
        
        alert_dict = alert.to_dict()
        
        assert alert_dict['severity'] == "Critical"
        assert alert_dict['title'] == "Critical"
        assert 'formatted_time' in alert_dict
        assert alert_dict['dismissed'] is False
    
    def test_alert_string_severity(self):
        """Test alert creation with string severity."""
        alert = Alert(
            severity="Warning",
            title="Test",
            message="Test"
        )
        
        assert alert.severity == AlertSeverity.WARNING


class TestIncident:
    """Test Incident dataclass."""
    
    def test_incident_creation(self):
        """Test incident creation."""
        incident = Incident(
            incident_type=IncidentType.DETECTION,
            description="Test detection",
            data={'bearing': 45, 'range': 50}
        )
        
        assert incident.incident_type == IncidentType.DETECTION
        assert incident.description == "Test detection"
        assert incident.data['bearing'] == 45
        assert incident.severity == AlertSeverity.INFO
    
    def test_incident_to_dict(self):
        """Test incident serialization."""
        incident = Incident(
            incident_type=IncidentType.JAMMING,
            description="Jamming detected",
            severity=AlertSeverity.CRITICAL
        )
        
        incident_dict = incident.to_dict()
        
        assert incident_dict['incident_type'] == "Jamming"
        assert incident_dict['severity'] == "Critical"
        assert 'formatted_time' in incident_dict


class TestAlertManager:
    """Test alert management functionality."""
    
    @pytest.fixture
    def manager(self):
        """Create alert manager."""
        return AlertManager(max_history=50)
    
    def test_add_alert(self, manager):
        """Test adding alerts."""
        alert = Alert(
            severity=AlertSeverity.INFO,
            title="Test",
            message="Test alert"
        )
        
        manager.add_alert(alert)
        
        assert len(manager.get_active_alerts()) == 1
        assert manager.get_active_alerts()[0].title == "Test"
    
    def test_dismiss_alert(self, manager):
        """Test dismissing alerts."""
        alert = Alert(
            severity=AlertSeverity.WARNING,
            title="Dismissible",
            message="This can be dismissed"
        )
        
        manager.add_alert(alert)
        assert len(manager.get_active_alerts()) == 1
        
        manager.dismiss_alert(0)
        
        assert len(manager.get_active_alerts()) == 0
        assert len(manager.get_history()) == 1
    
    def test_dismiss_all_alerts(self, manager):
        """Test dismissing all alerts."""
        for i in range(5):
            manager.add_alert(Alert(
                severity=AlertSeverity.INFO,
                title=f"Alert {i}",
                message=f"Message {i}"
            ))
        
        assert len(manager.get_active_alerts()) == 5
        
        manager.dismiss_all()
        
        assert len(manager.get_active_alerts()) == 0
        assert len(manager.get_history()) >= 5
    
    def test_get_critical_alerts(self, manager):
        """Test filtering critical alerts."""
        manager.add_alert(Alert(
            severity=AlertSeverity.INFO,
            title="Info",
            message="Info message"
        ))
        manager.add_alert(Alert(
            severity=AlertSeverity.CRITICAL,
            title="Critical",
            message="Critical message"
        ))
        manager.add_alert(Alert(
            severity=AlertSeverity.SYSTEM_FAILURE,
            title="Failure",
            message="System failure"
        ))
        
        critical = manager.get_critical_alerts()
        
        assert len(critical) == 2
        assert all(a.severity in [AlertSeverity.CRITICAL, AlertSeverity.SYSTEM_FAILURE] for a in critical)
    
    def test_alert_statistics(self, manager):
        """Test alert statistics."""
        manager.add_alert(Alert(severity=AlertSeverity.WARNING, title="W", message="W"))
        manager.add_alert(Alert(severity=AlertSeverity.WARNING, title="W2", message="W2"))
        manager.add_alert(Alert(severity=AlertSeverity.CRITICAL, title="C", message="C"))
        
        stats = manager.get_statistics()
        
        assert stats['total_alerts'] == 3
        assert stats['active_count'] == 3
        assert stats['critical_count'] == 1
        assert stats['by_severity']['Warning'] == 2
        assert stats['by_severity']['Critical'] == 1
    
    def test_history_limit(self, manager):
        """Test that history respects max size."""
        manager.max_history = 10
        
        for i in range(15):
            alert = Alert(
                severity=AlertSeverity.INFO,
                title=f"Alert {i}",
                message=f"Message {i}"
            )
            manager.add_alert(alert)
            manager.dismiss_alert(0)
        
        assert len(manager.get_history()) <= manager.max_history


class TestIncidentLogger:
    """Test incident logging functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test.db"
            yield db_path
    
    @pytest.fixture
    def logger(self, temp_db):
        """Create incident logger with temp database."""
        return IncidentLogger(db_path=temp_db)
    
    def test_log_incident_memory(self, logger):
        """Test logging to memory."""
        incident = Incident(
            incident_type=IncidentType.DETECTION,
            description="Test detection"
        )
        
        logger.log_incident(incident)
        
        assert len(logger.memory_log) == 1
        assert logger.memory_log[0].description == "Test detection"
    
    def test_log_incident_database(self, logger):
        """Test logging to database."""
        incident = Incident(
            incident_type=IncidentType.JAMMING,
            description="Test jamming",
            data={'power': 100}
        )
        
        logger.log_incident(incident)
        
        # Verify in database
        conn = sqlite3.connect(logger.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM incidents")
        count = c.fetchone()[0]
        conn.close()
        
        assert count == 1
    
    def test_get_incidents(self, logger):
        """Test retrieving incidents."""
        for i in range(5):
            logger.log_incident(Incident(
                incident_type=IncidentType.DETECTION,
                description=f"Detection {i}"
            ))
        
        incidents = logger.get_incidents(limit=3)
        
        assert len(incidents) == 3
        assert incidents[0].description == "Detection 2"
    
    def test_get_incidents_by_type(self, logger):
        """Test filtering incidents by type."""
        logger.log_incident(Incident(
            incident_type=IncidentType.DETECTION,
            description="Detection"
        ))
        logger.log_incident(Incident(
            incident_type=IncidentType.JAMMING,
            description="Jamming"
        ))
        logger.log_incident(Incident(
            incident_type=IncidentType.DETECTION,
            description="Detection 2"
        ))
        
        detections = logger.get_incidents(incident_type=IncidentType.DETECTION)
        
        assert len(detections) == 2
        assert all(i.incident_type == IncidentType.DETECTION for i in detections)
    
    def test_get_incidents_by_time_range(self, logger):
        """Test filtering incidents by time range."""
        now = datetime.now()
        
        # Log incident 2 hours ago
        past_incident = Incident(
            incident_type=IncidentType.DETECTION,
            description="Past"
        )
        past_incident.timestamp = (now - timedelta(hours=2)).timestamp()
        logger.log_incident(past_incident)
        
        # Log incident now
        current_incident = Incident(
            incident_type=IncidentType.DETECTION,
            description="Current"
        )
        logger.log_incident(current_incident)
        
        # Query last 90 minutes (should only get current)
        start_time = now - timedelta(minutes=90)
        end_time = now + timedelta(seconds=1)  # Add 1 second buffer
        
        incidents = logger.get_incidents_by_time_range(start_time, end_time)
        
        assert len(incidents) == 1
        assert incidents[0].description == "Current"
    
    def test_incident_statistics(self, logger):
        """Test incident statistics."""
        logger.log_incident(Incident(
            incident_type=IncidentType.DETECTION,
            severity=AlertSeverity.INFO,
            description="D1"
        ))
        logger.log_incident(Incident(
            incident_type=IncidentType.DETECTION,
            severity=AlertSeverity.INFO,
            description="D2"
        ))
        logger.log_incident(Incident(
            incident_type=IncidentType.JAMMING,
            severity=AlertSeverity.CRITICAL,
            description="J1"
        ))
        
        stats = logger.get_statistics()
        
        assert stats['total_incidents'] == 3
        assert stats['by_type']['Detection'] == 2
        assert stats['by_type']['Jamming'] == 1
        assert stats['by_severity']['Info'] == 2
        assert stats['by_severity']['Critical'] == 1
    
    def test_export_incidents(self, logger, temp_db):
        """Test exporting incidents."""
        logger.log_incident(Incident(
            incident_type=IncidentType.DETECTION,
            description="D1"
        ))
        logger.log_incident(Incident(
            incident_type=IncidentType.JAMMING,
            description="J1"
        ))
        
        export_path = f"{Path(temp_db).parent}/export.json"
        success = logger.export_incidents(export_path)
        
        assert success
        assert Path(export_path).exists()
        
        with open(export_path) as f:
            data = json.load(f)
        
        assert len(data) == 2
        assert data[0]['incident_type'] in ['Detection', 'Jamming']


class TestReplayManager:
    """Test replay and timeline functionality."""
    
    @pytest.fixture
    def replay(self):
        """Create replay manager."""
        return ReplayManager()
    
    def test_record_frame(self, replay):
        """Test recording frames."""
        frame = {'timestamp': time.time(), 'data': 'test'}
        replay.record_frame(frame)
        
        assert replay.get_frame_count() == 1
        assert replay.get_current_frame()['data'] == 'test'
    
    def test_seek_frame(self, replay):
        """Test seeking to frames."""
        for i in range(5):
            replay.record_frame({'frame': i})
        
        frame = replay.seek_frame(2)
        
        assert frame['frame'] == 2
        assert replay.current_frame == 2
    
    def test_navigation(self, replay):
        """Test frame navigation."""
        for i in range(5):
            replay.record_frame({'index': i})
        
        # Forward
        replay.next_frame()
        assert replay.current_frame == 1
        
        replay.next_frame()
        assert replay.current_frame == 2
        
        # Backward
        replay.prev_frame()
        assert replay.current_frame == 1
    
    def test_reset(self, replay):
        """Test replay reset."""
        for i in range(5):
            replay.record_frame({'index': i})
        
        replay.seek_frame(4)
        replay.reset()
        
        assert replay.current_frame == 0
        assert replay.is_playing is False


class TestConsoleState:
    """Test console operational state."""
    
    @pytest.fixture
    def console(self):
        """Create console state."""
        return ConsoleState()
    
    def test_mode_switching(self, console):
        """Test mode switching."""
        assert console.get_mode() == OperationalMode.OPERATOR
        
        console.switch_mode(OperationalMode.COMMANDER)
        
        assert console.get_mode() == OperationalMode.COMMANDER
    
    def test_uptime_tracking(self, console):
        """Test uptime calculation."""
        uptime_str = console.get_uptime_formatted()
        
        assert ':' in uptime_str
        parts = uptime_str.split(':')
        assert len(parts) == 3
    
    def test_dashboard_statistics(self, console):
        """Test dashboard statistics."""
        console.operator_name = "TestOp"
        console.current_sector = "North"
        console.detections_count = 10
        console.tracks_count = 5
        
        stats = console.get_dashboard_stats()
        
        assert stats['operator'] == "TestOp"
        assert stats['sector'] == "North"
        assert stats['detections'] == 10
        assert stats['tracks'] == 5
        assert 'uptime' in stats


class TestIntegration:
    """Integration tests for complete workflow."""
    
    @pytest.fixture
    def console_with_managers(self):
        """Create full console setup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            console = ConsoleState()
            console.incident_logger.db_path = f"{tmpdir}/incidents.db"
            console.incident_logger._init_db()
            yield console
    
    def test_full_alert_incident_workflow(self, console_with_managers):
        """Test complete alert and incident workflow."""
        console = console_with_managers
        
        # Add alert
        console.alert_manager.add_alert(Alert(
            severity=AlertSeverity.WARNING,
            title="Test Alert",
            message="Test message"
        ))
        
        # Log incident
        console.incident_logger.log_incident(Incident(
            incident_type=IncidentType.DETECTION,
            description="Test detection"
        ))
        
        # Verify alert
        assert len(console.alert_manager.get_active_alerts()) == 1
        
        # Verify incident
        assert len(console.incident_logger.get_incidents()) == 1
        
        # Dismiss alert
        console.alert_manager.dismiss_alert(0)
        
        # Verify dismissal
        assert len(console.alert_manager.get_active_alerts()) == 0
        assert len(console.alert_manager.get_history()) == 1
    
    def test_statistics_tracking(self, console_with_managers):
        """Test statistics across managers."""
        console = console_with_managers
        
        # Generate activity
        for i in range(3):
            console.alert_manager.add_alert(Alert(
                severity=AlertSeverity.INFO,
                title=f"Alert {i}",
                message=f"Message {i}"
            ))
        
        for i in range(5):
            console.incident_logger.log_incident(Incident(
                incident_type=IncidentType.DETECTION,
                description=f"Detection {i}"
            ))
        
        # Get statistics
        alert_stats = console.alert_manager.get_statistics()
        incident_stats = console.incident_logger.get_statistics()
        
        assert alert_stats['total_alerts'] == 3
        assert incident_stats['total_incidents'] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
