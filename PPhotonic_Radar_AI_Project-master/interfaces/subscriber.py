"""
Intelligence Subscriber
=======================

Receives and validates radar intelligence packets for Cognitive EW-AI system.
Monitors intelligence export directory and processes tactical picture messages.

Author: Defense Systems Integration Team
"""

import logging
import time
import json
from pathlib import Path
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
import threading
import queue

from interfaces.message_schema import TacticalPictureMessage, validate_tactical_message

logger = logging.getLogger(__name__)


@dataclass
class ReceivedIntelligence:
    """
    Wrapper for received and validated intelligence message.
    
    Includes metadata about reception time and quality.
    """
    message: TacticalPictureMessage
    reception_timestamp: float
    file_path: str
    
    # Quality metrics
    age_seconds: float = 0.0  # Time since message was created
    is_stale: bool = False
    validation_errors: List[str] = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        """Check if message passed validation."""
        return len(self.validation_errors) == 0


@dataclass
class SubscriberStatistics:
    """Statistics for intelligence subscriber."""
    messages_received: int = 0
    messages_valid: int = 0
    messages_invalid: int = 0
    messages_stale: int = 0
    validation_errors: int = 0
    last_message_time: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            'messages_received': self.messages_received,
            'messages_valid': self.messages_valid,
            'messages_invalid': self.messages_invalid,
            'messages_stale': self.messages_stale,
            'validation_errors': self.validation_errors,
            'last_message_time': self.last_message_time,
            'uptime_seconds': time.time() - self.start_time if hasattr(self, 'start_time') else 0
        }


class IntelligenceSubscriber:
    """
    Non-blocking intelligence packet receiver.
    
    Monitors intelligence export directory for new messages,
    validates schema, and queues for processing.
    
    Design principles:
    - Never blocks EW processing
    - Validates all incoming messages
    - Detects missing/stale data
    - Comprehensive logging
    """
    
    def __init__(self,
                 source_directory: str = './intelligence_export',
                 staleness_threshold_s: float = 2.0,
                 poll_interval_s: float = 0.1,
                 message_callback: Optional[Callable] = None,
                 log_all_updates: bool = True):
        """
        Initialize intelligence subscriber.
        
        Args:
            source_directory: Directory to monitor for intelligence files
            staleness_threshold_s: Messages older than this are flagged as stale
            poll_interval_s: How often to check for new files
            message_callback: Optional callback for each valid message
            log_all_updates: Log every received intelligence update
        """
        self.source_dir = Path(source_directory)
        self.staleness_threshold = staleness_threshold_s
        self.poll_interval = poll_interval_s
        self.message_callback = message_callback
        self.log_all_updates = log_all_updates
        
        # Message queue for processing
        self.message_queue = queue.Queue(maxsize=100)
        
        # Track processed files to avoid duplicates
        self.processed_files = set()
        
        # Statistics
        self.stats = SubscriberStatistics()
        self.stats.start_time = time.time()
        
        # Worker thread
        self.running = False
        self.monitor_thread = None
        
        logger.info(f"Intelligence subscriber initialized: {self.source_dir}")
    
    def start(self):
        """Start the background monitoring thread."""
        if self.running:
            logger.warning("Subscriber already running")
            return
        
        if not self.source_dir.exists():
            logger.warning(f"Intelligence source directory does not exist: {self.source_dir}")
            logger.info("Subscriber will wait for directory to be created...")
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"Intelligence subscriber started, monitoring: {self.source_dir}")
    
    def stop(self):
        """Stop the monitoring thread."""
        if not self.running:
            return
        
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        logger.info(f"Intelligence subscriber stopped. Stats: {self.stats.to_dict()}")
    
    def _monitor_loop(self):
        """Background thread that monitors for new intelligence files."""
        logger.info("Intelligence monitor thread started")
        
        while self.running:
            try:
                # Wait for directory to exist
                if not self.source_dir.exists():
                    time.sleep(self.poll_interval)
                    continue
                
                # Scan for new intelligence files
                intel_files = sorted(self.source_dir.glob('intel_*.json'))
                
                for file_path in intel_files:
                    if file_path.name not in self.processed_files:
                        self._process_intelligence_file(file_path)
                        self.processed_files.add(file_path.name)
                
                # Cleanup old processed files set (keep last 1000)
                if len(self.processed_files) > 1000:
                    # Remove oldest entries (simple heuristic)
                    self.processed_files = set(list(self.processed_files)[-500:])
                
                time.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}", exc_info=True)
                time.sleep(self.poll_interval)
        
        logger.info("Intelligence monitor thread stopped")
    
    def _process_intelligence_file(self, file_path: Path):
        """
        Process a single intelligence file.
        
        Validates schema, checks staleness, and queues for processing.
        """
        try:
            reception_time = time.time()
            
            # Read JSON file
            with open(file_path, 'r') as f:
                message_dict = json.load(f)
            
            # Convert to TacticalPictureMessage
            message = self._dict_to_tactical_message(message_dict)
            
            # Validate schema
            is_valid, validation_errors = validate_tactical_message(message)
            
            # Calculate age
            age_seconds = reception_time - message.timestamp
            is_stale = age_seconds > self.staleness_threshold
            
            # Create received intelligence wrapper
            received = ReceivedIntelligence(
                message=message,
                reception_timestamp=reception_time,
                file_path=str(file_path),
                age_seconds=age_seconds,
                is_stale=is_stale,
                validation_errors=validation_errors
            )
            
            # Update statistics
            self.stats.messages_received += 1
            self.stats.last_message_time = reception_time
            
            if is_valid:
                self.stats.messages_valid += 1
            else:
                self.stats.messages_invalid += 1
                self.stats.validation_errors += len(validation_errors)
            
            if is_stale:
                self.stats.messages_stale += 1
            
            # Log reception
            self._log_intelligence_reception(received)
            
            # Queue for processing
            try:
                self.message_queue.put_nowait(received)
            except queue.Full:
                logger.warning("Intelligence message queue full - dropping message")
            
            # Call callback if provided
            if self.message_callback and is_valid:
                try:
                    self.message_callback(received)
                except Exception as e:
                    logger.error(f"Message callback failed: {e}")
            
        except json.JSONDecodeError as e:
            logger.error(f"[INTEL-ERROR] Failed to parse JSON from {file_path.name}: {e}")
            self.stats.messages_invalid += 1
        except Exception as e:
            logger.error(f"[INTEL-ERROR] Failed to process {file_path.name}: {e}", exc_info=True)
            self.stats.messages_invalid += 1
    
    def _dict_to_tactical_message(self, data: Dict) -> TacticalPictureMessage:
        """Convert dictionary to TacticalPictureMessage."""
        from interfaces.message_schema import Track, ThreatAssessment, SceneContext
        
        # Convert tracks
        tracks = []
        for t in data.get('tracks', []):
            tracks.append(Track(**t))
        
        # Convert threat assessments
        threats = []
        for ta in data.get('threat_assessments', []):
            threats.append(ThreatAssessment(**ta))
        
        # Convert scene context
        scene_context = None
        if 'scene_context' in data:
            scene_context = SceneContext(**data['scene_context'])
        
        # Create message
        return TacticalPictureMessage(
            message_id=data['message_id'],
            timestamp=data['timestamp'],
            frame_id=data['frame_id'],
            sensor_id=data['sensor_id'],
            tracks=tracks,
            threat_assessments=threats,
            scene_context=scene_context
        )
    
    def _log_intelligence_reception(self, received: ReceivedIntelligence):
        """Log intelligence reception with appropriate level."""
        msg = received.message
        
        # Build log message
        log_msg = (f"[INTEL-RX] Frame {msg.frame_id} from {msg.sensor_id}: "
                  f"{len(msg.tracks)} tracks, {len(msg.threat_assessments)} threats")
        
        if msg.scene_context:
            log_msg += f", Scene={msg.scene_context.scene_type}, SNR={msg.scene_context.mean_snr_db:.1f}dB"
        
        log_msg += f", Age={received.age_seconds:.2f}s"
        
        # Log based on quality
        if not received.is_valid:
            logger.warning(f"{log_msg} [VALIDATION FAILED]")
            for error in received.validation_errors:
                logger.warning(f"[INTEL-WARN] Validation error: {error}")
        elif received.is_stale:
            logger.warning(f"{log_msg} [STALE - threshold {self.staleness_threshold}s]")
        elif self.log_all_updates:
            logger.info(log_msg)
    
    def get_next_message(self, timeout: Optional[float] = None) -> Optional[ReceivedIntelligence]:
        """
        Get next intelligence message from queue.
        
        Args:
            timeout: Max time to wait for message (None = non-blocking)
            
        Returns:
            ReceivedIntelligence or None if queue empty
        """
        try:
            if timeout is None:
                return self.message_queue.get_nowait()
            else:
                return self.message_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_statistics(self) -> Dict:
        """Get subscriber statistics."""
        return self.stats.to_dict()
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


class NullSubscriber:
    """
    Null subscriber that does nothing.
    
    Used when intelligence ingestion is disabled.
    """
    
    def __init__(self, *args, **kwargs):
        pass
    
    def start(self):
        pass
    
    def stop(self):
        pass
    
    def get_next_message(self, timeout=None):
        return None
    
    def get_statistics(self) -> Dict:
        return {'enabled': False}
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
