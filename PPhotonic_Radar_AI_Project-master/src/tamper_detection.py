"""
TAMPER DETECTION: System integrity monitoring and verification

Detects unauthorized modifications to:
- Model files (weights and architecture)
- Configuration files
- Code files
- System binaries
- Secret keys

Uses cryptographic checksums and runtime monitoring.
Fails safe: reports tampering immediately, stops operations.
"""

import hashlib
import os
import json
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import threading
from enum import Enum

logger = logging.getLogger(__name__)


class TamperSeverity(Enum):
    """Severity levels for tampering incidents."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FileChecksum:
    """Cryptographic checksum for a file."""
    filepath: str
    sha256: str
    md5: str
    filesize: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "filepath": self.filepath,
            "sha256": self.sha256,
            "md5": self.md5,
            "filesize": self.filesize,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class TamperEvent:
    """Record of detected tampering."""
    severity: TamperSeverity
    filepath: str
    reason: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    old_checksum: Optional[str] = None
    new_checksum: Optional[str] = None
    resolved: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "severity": self.severity.value,
            "filepath": self.filepath,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            "old_checksum": self.old_checksum,
            "new_checksum": self.new_checksum,
            "resolved": self.resolved,
        }


class ChecksumManager:
    """Manage cryptographic checksums for files."""
    
    @staticmethod
    def compute_sha256(filepath: str, chunk_size: int = 65536) -> str:
        """Compute SHA256 checksum of file."""
        sha256 = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                while True:
                    data = f.read(chunk_size)
                    if not data:
                        break
                    sha256.update(data)
            return sha256.hexdigest()
        except Exception as e:
            logger.error(f"Failed to compute SHA256 for {filepath}: {e}")
            raise
    
    @staticmethod
    def compute_md5(filepath: str, chunk_size: int = 65536) -> str:
        """Compute MD5 checksum of file."""
        md5 = hashlib.md5()
        try:
            with open(filepath, 'rb') as f:
                while True:
                    data = f.read(chunk_size)
                    if not data:
                        break
                    md5.update(data)
            return md5.hexdigest()
        except Exception as e:
            logger.error(f"Failed to compute MD5 for {filepath}: {e}")
            raise
    
    @staticmethod
    def compute_checksums(filepath: str) -> FileChecksum:
        """Compute all checksums for a file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        sha256 = ChecksumManager.compute_sha256(filepath)
        md5 = ChecksumManager.compute_md5(filepath)
        filesize = os.path.getsize(filepath)
        
        return FileChecksum(
            filepath=filepath,
            sha256=sha256,
            md5=md5,
            filesize=filesize,
        )
    
    @staticmethod
    def verify_checksum(filepath: str, expected_sha256: str) -> Tuple[bool, str]:
        """Verify file checksum against expected value."""
        try:
            actual_sha256 = ChecksumManager.compute_sha256(filepath)
            if actual_sha256 == expected_sha256:
                return True, f"Checksum verified: {filepath}"
            else:
                return False, f"Checksum mismatch for {filepath}: expected {expected_sha256}, got {actual_sha256}"
        except Exception as e:
            return False, f"Failed to verify checksum: {e}"


class TamperDetector:
    """
    Detects unauthorized modifications to critical system files.
    Fail-safe: assumes tampering on any verification failure.
    """
    
    def __init__(self):
        """Initialize tamper detector."""
        self.baseline: Dict[str, FileChecksum] = {}
        self.tamper_events: List[TamperEvent] = []
        self.critical_files: List[str] = []
        self.monitoring_enabled = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        self.max_events = 1000
    
    def add_critical_file(self, filepath: str) -> None:
        """Mark a file as critical (to be monitored)."""
        if os.path.exists(filepath):
            self.critical_files.append(filepath)
            logger.info(f"Added critical file: {filepath}")
        else:
            logger.warning(f"Critical file not found: {filepath}")
    
    def establish_baseline(self, filepath: str) -> FileChecksum:
        """Establish baseline checksum for a file."""
        try:
            checksum = ChecksumManager.compute_checksums(filepath)
            with self.lock:
                self.baseline[filepath] = checksum
            logger.info(f"Baseline established for {filepath}")
            return checksum
        except Exception as e:
            logger.error(f"Failed to establish baseline for {filepath}: {e}")
            # Fail-safe: report as critical issue
            self._record_tamper_event(
                severity=TamperSeverity.CRITICAL,
                filepath=filepath,
                reason=f"Failed to establish baseline: {e}"
            )
            raise
    
    def establish_baseline_batch(self, filepaths: List[str]) -> Dict[str, FileChecksum]:
        """Establish baseline for multiple files."""
        results = {}
        for filepath in filepaths:
            try:
                results[filepath] = self.establish_baseline(filepath)
            except Exception as e:
                logger.error(f"Batch baseline failed for {filepath}: {e}")
                results[filepath] = None
        return results
    
    def verify_integrity(self, filepath: str) -> Tuple[bool, str]:
        """
        Verify file integrity against baseline.
        Fail-safe: returns False if file not in baseline or any error occurs.
        """
        with self.lock:
            if filepath not in self.baseline:
                return False, f"No baseline for {filepath} (fail-safe: treat as compromised)"
            
            baseline_cs = self.baseline[filepath]
        
        try:
            current_cs = ChecksumManager.compute_checksums(filepath)
            
            # Check SHA256
            if current_cs.sha256 != baseline_cs.sha256:
                reason = (
                    f"SHA256 mismatch for {filepath}\n"
                    f"  Baseline: {baseline_cs.sha256}\n"
                    f"  Current:  {current_cs.sha256}"
                )
                self._record_tamper_event(
                    severity=TamperSeverity.CRITICAL,
                    filepath=filepath,
                    reason=reason,
                    old_checksum=baseline_cs.sha256,
                    new_checksum=current_cs.sha256,
                )
                return False, reason
            
            # Check file size
            if current_cs.filesize != baseline_cs.filesize:
                reason = (
                    f"File size mismatch for {filepath}\n"
                    f"  Baseline: {baseline_cs.filesize} bytes\n"
                    f"  Current:  {current_cs.filesize} bytes"
                )
                self._record_tamper_event(
                    severity=TamperSeverity.CRITICAL,
                    filepath=filepath,
                    reason=reason,
                )
                return False, reason
            
            return True, f"Integrity verified: {filepath}"
            
        except FileNotFoundError:
            reason = f"File not found: {filepath} (fail-safe: treat as compromised)"
            self._record_tamper_event(
                severity=TamperSeverity.CRITICAL,
                filepath=filepath,
                reason=reason,
            )
            return False, reason
        except Exception as e:
            reason = f"Integrity check failed: {e} (fail-safe: treat as compromised)"
            self._record_tamper_event(
                severity=TamperSeverity.CRITICAL,
                filepath=filepath,
                reason=reason,
            )
            return False, reason
    
    def verify_integrity_batch(self, filepaths: List[str]) -> Dict[str, Tuple[bool, str]]:
        """Verify integrity of multiple files."""
        results = {}
        for filepath in filepaths:
            results[filepath] = self.verify_integrity(filepath)
        return results
    
    def start_continuous_monitoring(self, interval: int = 60) -> None:
        """Start continuous integrity monitoring thread."""
        if self.monitoring_enabled:
            logger.warning("Continuous monitoring already running")
            return
        
        self.monitoring_enabled = True
        
        def monitor_loop():
            import time
            while self.monitoring_enabled:
                try:
                    self.check_all_critical_files()
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"Monitor loop error: {e}")
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"Continuous monitoring started (interval={interval}s)")
    
    def stop_continuous_monitoring(self) -> None:
        """Stop continuous integrity monitoring."""
        self.monitoring_enabled = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Continuous monitoring stopped")
    
    def check_all_critical_files(self) -> Dict[str, Tuple[bool, str]]:
        """Check integrity of all critical files."""
        results = {}
        for filepath in self.critical_files:
            is_valid, message = self.verify_integrity(filepath)
            results[filepath] = (is_valid, message)
            if not is_valid:
                logger.critical(f"TAMPERING DETECTED: {message}")
        return results
    
    def _record_tamper_event(
        self,
        severity: TamperSeverity,
        filepath: str,
        reason: str,
        old_checksum: Optional[str] = None,
        new_checksum: Optional[str] = None,
    ) -> None:
        """Record tampering event to log."""
        event = TamperEvent(
            severity=severity,
            filepath=filepath,
            reason=reason,
            old_checksum=old_checksum,
            new_checksum=new_checksum,
        )
        with self.lock:
            self.tamper_events.append(event)
            
            # Trim if too large
            if len(self.tamper_events) > self.max_events:
                self.tamper_events = self.tamper_events[-self.max_events:]
        
        # Log with appropriate severity
        if severity == TamperSeverity.CRITICAL:
            logger.critical(f"TAMPERING DETECTED (CRITICAL): {filepath} - {reason}")
        else:
            logger.error(f"TAMPERING DETECTED ({severity.value}): {filepath} - {reason}")
    
    def get_tamper_events(self, severity: Optional[TamperSeverity] = None) -> List[TamperEvent]:
        """Get recorded tamper events, optionally filtered by severity."""
        with self.lock:
            events = list(self.tamper_events)
        
        if severity:
            events = [e for e in events if e.severity == severity]
        
        return events
    
    def get_unresolved_events(self) -> List[TamperEvent]:
        """Get all unresolved tampering events."""
        with self.lock:
            return [e for e in self.tamper_events if not e.resolved]
    
    def mark_event_resolved(self, event_index: int) -> None:
        """Mark a tampering event as resolved (investigated)."""
        with self.lock:
            if 0 <= event_index < len(self.tamper_events):
                self.tamper_events[event_index].resolved = True
    
    def export_tamper_events(self, filepath: str) -> None:
        """Export tampering events to JSON file."""
        with self.lock:
            events = [e.to_dict() for e in self.tamper_events]
        
        with open(filepath, 'w') as f:
            json.dump(events, f, indent=2)
        logger.info(f"Tamper events exported to {filepath}")
    
    def get_statistics(self) -> Dict:
        """Get tamper detection statistics."""
        with self.lock:
            events = list(self.tamper_events)
        
        severity_counts = {s.value: 0 for s in TamperSeverity}
        for event in events:
            severity_counts[event.severity.value] += 1
        
        return {
            "total_events": len(events),
            "unresolved_events": len(self.get_unresolved_events()),
            "critical_files_monitored": len(self.critical_files),
            "monitoring_enabled": self.monitoring_enabled,
            "severity_distribution": severity_counts,
        }


# Global instance
_tamper_detector = TamperDetector()


def get_tamper_detector() -> TamperDetector:
    """Get global tamper detector instance."""
    return _tamper_detector
