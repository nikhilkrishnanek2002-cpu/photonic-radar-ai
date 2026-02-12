"""
EW Feedback Subscriber
======================

Receives EW feedback messages on the radar side.
Monitors EW feedback directory and validates messages.

Author: Sensor-Effector Integration Team
"""

import logging
import time
import json
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass
import threading
import queue

from interfaces.message_schema import EWFeedbackMessage, Countermeasure, EngagementStatus, validate_ew_feedback_message

logger = logging.getLogger(__name__)


@dataclass
class ReceivedEWFeedback:
    """Wrapper for received EW feedback message."""
    message: EWFeedbackMessage
    reception_timestamp: float
    file_path: str
    age_seconds: float = 0.0


class EWFeedbackSubscriber:
    """
    Receives EW feedback messages from cognitive EW system.
    
    Monitors feedback directory and validates messages.
    """
    
    def __init__(self,
                 source_directory: str = './ew_feedback',
                 poll_interval_s: float = 0.1,
                 log_all_updates: bool = True):
        """
        Initialize EW feedback subscriber.
        
        Args:
            source_directory: Directory to monitor for feedback files
            poll_interval_s: Polling interval
            log_all_updates: Log every received feedback
        """
        self.source_dir = Path(source_directory)
        self.poll_interval = poll_interval_s
        self.log_all_updates = log_all_updates
        
        self.message_queue = queue.Queue(maxsize=50)
        self.processed_files = set()
        
        self.running = False
        self.monitor_thread = None
        
        self.messages_received = 0
        
        logger.info(f"EW Feedback subscriber initialized: {self.source_dir}")
    
    def start(self):
        """Start monitoring thread."""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("EW Feedback subscriber started")
    
    def stop(self):
        """Stop monitoring thread."""
        if not self.running:
            return
        
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        logger.info(f"EW Feedback subscriber stopped. Received {self.messages_received} messages")
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.running:
            try:
                if not self.source_dir.exists():
                    time.sleep(self.poll_interval)
                    continue
                
                feedback_files = sorted(self.source_dir.glob('ew_feedback_*.json'))
                
                for file_path in feedback_files:
                    if file_path.name not in self.processed_files:
                        self._process_feedback_file(file_path)
                        self.processed_files.add(file_path.name)
                
                # Cleanup
                if len(self.processed_files) > 500:
                    self.processed_files = set(list(self.processed_files)[-250:])
                
                time.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Error in EW feedback monitor: {e}")
                time.sleep(self.poll_interval)
    
    def _process_feedback_file(self, file_path: Path):
        """Process a single feedback file."""
        try:
            reception_time = time.time()
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Convert to EWFeedbackMessage
            message = self._dict_to_feedback_message(data)
            
            # Validate
            is_valid, errors = validate_ew_feedback_message(message)
            
            if not is_valid:
                logger.warning(f"[EW-FEEDBACK] Invalid message: {errors}")
                return
            
            age_seconds = reception_time - message.timestamp
            
            received = ReceivedEWFeedback(
                message=message,
                reception_timestamp=reception_time,
                file_path=str(file_path),
                age_seconds=age_seconds
            )
            
            self.messages_received += 1
            
            # Log
            if self.log_all_updates:
                logger.info(f"[EW-FEEDBACK] Received from {message.effector_id}: "
                           f"{len(message.active_countermeasures)} CMs, "
                           f"{len(message.engagement_status)} engagements")
            
            # Queue
            try:
                self.message_queue.put_nowait(received)
            except queue.Full:
                logger.warning("EW feedback queue full")
                
        except Exception as e:
            logger.error(f"Failed to process EW feedback {file_path.name}: {e}")
    
    def _dict_to_feedback_message(self, data: Dict) -> EWFeedbackMessage:
        """Convert dictionary to EWFeedbackMessage."""
        countermeasures = []
        for cm_data in data.get('active_countermeasures', []):
            countermeasures.append(Countermeasure(**cm_data))
        
        engagements = []
        for eng_data in data.get('engagement_status', []):
            engagements.append(EngagementStatus(**eng_data))
        
        return EWFeedbackMessage(
            message_id=data['message_id'],
            timestamp=data['timestamp'],
            effector_id=data['effector_id'],
            active_countermeasures=countermeasures,
            engagement_status=engagements,
            effector_health=data.get('effector_health')
        )
    
    def get_next_message(self, timeout: Optional[float] = None) -> Optional[ReceivedEWFeedback]:
        """Get next feedback message from queue."""
        try:
            if timeout is None:
                return self.message_queue.get_nowait()
            else:
                return self.message_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_statistics(self) -> Dict:
        """Get subscriber statistics."""
        return {
            'messages_received': self.messages_received,
            'queue_size': self.message_queue.qsize()
        }


class NullEWFeedbackSubscriber:
    """Null subscriber when EW feedback is disabled."""
    
    def start(self):
        pass
    
    def stop(self):
        pass
    
    def get_next_message(self, timeout=None):
        return None
    
    def get_statistics(self):
        return {'enabled': False}
