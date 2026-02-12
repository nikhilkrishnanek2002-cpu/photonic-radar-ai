"""
Non-Blocking Intelligence Publisher
====================================

Exports radar intelligence packets without blocking radar processing.
Implements fire-and-forget pattern with optional logging.

Author: Defense Systems Integration Team
"""

import logging
import queue
import threading
import time
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime

from interfaces.message_schema import TacticalPictureMessage

logger = logging.getLogger(__name__)


class IntelligencePublisher:
    """
    Non-blocking publisher for radar intelligence packets.
    
    Design principles:
    - Never blocks radar processing
    - Gracefully handles unavailable consumers
    - Optional file logging for debugging
    - Thread-safe operation
    """
    
    def __init__(self, 
                 sensor_id: str,
                 enable_file_export: bool = True,
                 export_directory: Optional[str] = None,
                 enable_network_export: bool = False,
                 network_callback: Optional[Callable] = None,
                 queue_size: int = 100):
        """
        Initialize the intelligence publisher.
        
        Args:
            sensor_id: Unique sensor identifier
            enable_file_export: Write messages to JSON files
            export_directory: Directory for exported files (default: ./intelligence_export)
            enable_network_export: Enable network publishing (future)
            network_callback: Custom callback for network publishing
            queue_size: Maximum queue size before dropping messages
        """
        self.sensor_id = sensor_id
        self.enable_file_export = enable_file_export
        self.enable_network_export = enable_network_export
        self.network_callback = network_callback
        
        # Setup export directory
        if export_directory is None:
            export_directory = "./intelligence_export"
        self.export_dir = Path(export_directory)
        if self.enable_file_export:
            self.export_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Intelligence export directory: {self.export_dir.absolute()}")
        
        # Non-blocking queue
        self.message_queue = queue.Queue(maxsize=queue_size)
        
        # Statistics
        self.messages_published = 0
        self.messages_dropped = 0
        self.messages_exported = 0
        
        # Worker thread
        self.running = False
        self.worker_thread = None
        
    def start(self):
        """Start the background export worker thread."""
        if self.running:
            logger.warning("Publisher already running")
            return
            
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info(f"Intelligence publisher started for sensor: {self.sensor_id}")
    
    def stop(self):
        """Stop the background worker thread."""
        if not self.running:
            return
            
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=2.0)
        logger.info(f"Intelligence publisher stopped. Stats: {self.get_statistics()}")
    
    def publish(self, message: TacticalPictureMessage) -> bool:
        """
        Publish a tactical picture message (non-blocking).
        
        Args:
            message: TacticalPictureMessage to publish
            
        Returns:
            True if queued successfully, False if queue is full (message dropped)
        """
        try:
            # Non-blocking put - drops message if queue is full
            self.message_queue.put_nowait(message)
            self.messages_published += 1
            return True
        except queue.Full:
            self.messages_dropped += 1
            if self.messages_dropped % 10 == 1:  # Log every 10th drop
                logger.warning(f"Message queue full - dropped {self.messages_dropped} messages")
            return False
    
    def _worker_loop(self):
        """Background worker thread that processes the message queue."""
        logger.info("Intelligence export worker thread started")
        
        while self.running:
            try:
                # Block with timeout to allow clean shutdown
                message = self.message_queue.get(timeout=0.5)
                
                # Export the message
                self._export_message(message)
                self.messages_exported += 1
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in export worker: {e}", exc_info=True)
        
        # Drain remaining messages on shutdown
        while not self.message_queue.empty():
            try:
                message = self.message_queue.get_nowait()
                self._export_message(message)
                self.messages_exported += 1
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"Error draining queue: {e}")
        
        logger.info("Intelligence export worker thread stopped")
    
    def _export_message(self, message: TacticalPictureMessage):
        """
        Export a message to configured outputs.
        
        This method is called from the worker thread, so it can block
        without affecting radar processing.
        """
        # File export
        if self.enable_file_export:
            self._export_to_file(message)
        
        # Network export (future implementation)
        if self.enable_network_export and self.network_callback:
            try:
                self.network_callback(message)
            except Exception as e:
                logger.error(f"Network export callback failed: {e}")
    
    def _export_to_file(self, message: TacticalPictureMessage):
        """Export message to JSON file."""
        try:
            # Create filename with timestamp and frame ID
            timestamp_str = datetime.fromtimestamp(message.timestamp).strftime("%Y%m%d_%H%M%S")
            filename = f"intel_{timestamp_str}_frame{message.frame_id:06d}.json"
            filepath = self.export_dir / filename
            
            # Write JSON with pretty formatting
            with open(filepath, 'w') as f:
                f.write(message.to_json(indent=2))
                
        except Exception as e:
            logger.error(f"Failed to export message to file: {e}")
    
    def get_statistics(self) -> dict:
        """Get publisher statistics."""
        return {
            'messages_published': self.messages_published,
            'messages_exported': self.messages_exported,
            'messages_dropped': self.messages_dropped,
            'queue_size': self.message_queue.qsize(),
            'drop_rate': self.messages_dropped / max(1, self.messages_published)
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


class NullPublisher:
    """
    Null publisher that does nothing.
    
    Used when intelligence export is disabled.
    """
    
    def __init__(self, *args, **kwargs):
        pass
    
    def start(self):
        pass
    
    def stop(self):
        pass
    
    def publish(self, message: TacticalPictureMessage) -> bool:
        return True
    
    def get_statistics(self) -> dict:
        return {'enabled': False}
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
