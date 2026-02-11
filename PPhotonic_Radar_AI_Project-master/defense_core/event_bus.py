"""
Defense Core - Event-Driven Communication System
=================================================

Dual-queue event bus for radar-EW communication.

Features:
- Non-blocking reads
- Safe writes
- No busy waiting
- Thread-safe design
- Swappable backend (Queue, Kafka, Redis, ZeroMQ)

Author: Defense Core Team
"""

import logging
from typing import Optional, Any, Protocol
from queue import Queue, Empty, Full
import threading
import time
from abc import ABC, abstractmethod

from defense_core.schemas import RadarIntelligencePacket, ElectronicAttackPacket

logger = logging.getLogger(__name__)


# ============================================================================
# Message Broker Interface (for swappable backends)
# ============================================================================

class MessageBroker(Protocol):
    """
    Protocol for message broker backends.
    
    This allows swapping Queue with Kafka, Redis, ZeroMQ, etc.
    """
    
    def put(self, message: Any, timeout: Optional[float] = None) -> bool:
        """
        Put message in queue.
        
        Args:
            message: Message to send
            timeout: Timeout in seconds (None = blocking)
            
        Returns:
            True if successful, False if timeout/full
        """
        ...
    
    def get(self, timeout: Optional[float] = None) -> Optional[Any]:
        """
        Get message from queue.
        
        Args:
            timeout: Timeout in seconds (None = blocking)
            
        Returns:
            Message or None if timeout/empty
        """
        ...
    
    def qsize(self) -> int:
        """Get approximate queue size."""
        ...
    
    def empty(self) -> bool:
        """Check if queue is empty."""
        ...


# ============================================================================
# Queue Backend (default implementation)
# ============================================================================

class QueueBackend:
    """
    Python Queue-based message broker.
    
    Thread-safe, non-blocking, no busy waiting.
    """
    
    def __init__(self, maxsize: int = 100):
        """
        Initialize queue backend.
        
        Args:
            maxsize: Maximum queue size (0 = unlimited)
        """
        self.queue = Queue(maxsize=maxsize)
        self.messages_sent = 0
        self.messages_received = 0
        self.messages_dropped = 0
    
    def put(self, message: Any, timeout: Optional[float] = None) -> bool:
        """Put message in queue (non-blocking by default)."""
        try:
            if timeout is None:
                # Non-blocking put
                self.queue.put_nowait(message)
            else:
                # Blocking put with timeout
                self.queue.put(message, timeout=timeout)
            
            self.messages_sent += 1
            return True
            
        except Full:
            self.messages_dropped += 1
            logger.warning("Queue full, message dropped")
            return False
    
    def get(self, timeout: Optional[float] = None) -> Optional[Any]:
        """Get message from queue (non-blocking by default)."""
        try:
            if timeout is None:
                # Non-blocking get
                message = self.queue.get_nowait()
            else:
                # Blocking get with timeout
                message = self.queue.get(timeout=timeout)
            
            self.messages_received += 1
            return message
            
        except Empty:
            return None
    
    def qsize(self) -> int:
        """Get approximate queue size."""
        return self.queue.qsize()
    
    def empty(self) -> bool:
        """Check if queue is empty."""
        return self.queue.empty()
    
    def get_statistics(self) -> dict:
        """Get queue statistics."""
        return {
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'messages_dropped': self.messages_dropped,
            'queue_size': self.qsize(),
            'drop_rate': self.messages_dropped / max(1, self.messages_sent)
        }


# ============================================================================
# Dual-Queue Event Bus
# ============================================================================

class DefenseEventBus:
    """
    Event-driven communication system for radar-EW integration.
    
    Features:
    - Separate queues for radar→EW and EW→radar
    - Non-blocking reads (no stalling)
    - Safe writes (drop on full)
    - Thread-safe
    - Swappable backend
    """
    
    def __init__(self,
                 radar_to_ew_maxsize: int = 100,
                 ew_to_radar_maxsize: int = 100,
                 backend_type: str = 'queue'):
        """
        Initialize dual-queue event bus.
        
        Args:
            radar_to_ew_maxsize: Max size for radar→EW queue
            ew_to_radar_maxsize: Max size for EW→radar queue
            backend_type: Backend type ('queue', 'kafka', 'redis', 'zeromq')
        """
        self.backend_type = backend_type
        
        # Create queues based on backend type
        if backend_type == 'queue':
            self.radar_to_ew_bus = QueueBackend(maxsize=radar_to_ew_maxsize)
            self.ew_to_radar_bus = QueueBackend(maxsize=ew_to_radar_maxsize)
        else:
            raise NotImplementedError(f"Backend '{backend_type}' not implemented yet")
        
        self.lock = threading.Lock()
        self.running = True
        
        logger.info(f"Defense event bus initialized (backend={backend_type})")
    
    # ========================================================================
    # Radar Interface
    # ========================================================================
    
    def publish_intelligence(self,
                            message: RadarIntelligencePacket,
                            timeout: Optional[float] = None) -> bool:
        """
        Publish radar intelligence to EW (non-blocking).
        
        Args:
            message: Radar intelligence packet
            timeout: Timeout in seconds (None = non-blocking)
            
        Returns:
            True if published, False if dropped
        """
        if not self.running:
            logger.warning("Event bus not running")
            return False
        
        success = self.radar_to_ew_bus.put(message, timeout=timeout)
        
        if success:
            logger.debug(f"Published intelligence: frame={message.frame_id}, "
                        f"tracks={len(message.tracks)}")
        else:
            logger.warning(f"Dropped intelligence: frame={message.frame_id}")
        
        return success
    
    def receive_ew_feedback(self,
                           timeout: float = 0.0) -> Optional[ElectronicAttackPacket]:
        """
        Receive EW feedback (non-blocking).
        
        Args:
            timeout: Timeout in seconds (0.0 = immediate return)
            
        Returns:
            EW feedback packet or None
        """
        if not self.running:
            return None
        
        message = self.ew_to_radar_bus.get(timeout=timeout)
        
        if message:
            logger.debug(f"Received EW feedback: {len(message.active_countermeasures)} CMs")
        
        return message
    
    # ========================================================================
    # EW Interface
    # ========================================================================
    
    def receive_intelligence(self,
                            timeout: float = 0.0) -> Optional[RadarIntelligencePacket]:
        """
        Receive radar intelligence (non-blocking).
        
        Args:
            timeout: Timeout in seconds (0.0 = immediate return)
            
        Returns:
            Radar intelligence packet or None
        """
        if not self.running:
            return None
        
        message = self.radar_to_ew_bus.get(timeout=timeout)
        
        if message:
            logger.debug(f"Received intelligence: frame={message.frame_id}, "
                        f"tracks={len(message.tracks)}")
        
        return message
    
    def publish_feedback(self,
                        message: ElectronicAttackPacket,
                        timeout: Optional[float] = None) -> bool:
        """
        Publish EW feedback to radar (non-blocking).
        
        Args:
            message: EW feedback packet
            timeout: Timeout in seconds (None = non-blocking)
            
        Returns:
            True if published, False if dropped
        """
        if not self.running:
            logger.warning("Event bus not running")
            return False
        
        success = self.ew_to_radar_bus.put(message, timeout=timeout)
        
        if success:
            logger.debug(f"Published feedback: {len(message.active_countermeasures)} CMs")
        else:
            logger.warning("Dropped EW feedback")
        
        return success
    
    # ========================================================================
    # Management
    # ========================================================================
    
    def get_statistics(self) -> dict:
        """Get event bus statistics."""
        return {
            'backend_type': self.backend_type,
            'running': self.running,
            'radar_to_ew': self.radar_to_ew_bus.get_statistics(),
            'ew_to_radar': self.ew_to_radar_bus.get_statistics()
        }
    
    def clear(self):
        """Clear all queues."""
        # Drain queues
        while not self.radar_to_ew_bus.empty():
            self.radar_to_ew_bus.get(timeout=0.0)
        
        while not self.ew_to_radar_bus.empty():
            self.ew_to_radar_bus.get(timeout=0.0)
        
        logger.info("Event bus cleared")
    
    def stop(self):
        """Stop event bus."""
        self.running = False
        logger.info("Event bus stopped")


# ============================================================================
# Global Event Bus (Singleton)
# ============================================================================

_global_defense_bus = None
_bus_lock = threading.Lock()


def get_defense_bus() -> DefenseEventBus:
    """Get global defense event bus (singleton)."""
    global _global_defense_bus
    
    if _global_defense_bus is None:
        with _bus_lock:
            if _global_defense_bus is None:
                _global_defense_bus = DefenseEventBus()
    
    return _global_defense_bus


def reset_defense_bus():
    """Reset global defense event bus (for testing)."""
    global _global_defense_bus
    
    with _bus_lock:
        if _global_defense_bus:
            _global_defense_bus.stop()
            _global_defense_bus.clear()
        _global_defense_bus = None
