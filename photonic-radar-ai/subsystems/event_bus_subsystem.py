"""
Event Bus Subsystem
===================

Foundation subsystem providing event bus for radar-EW communication.

Critical: All other subsystems depend on this.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EventBusSubsystem:
    """
    Event bus subsystem wrapper.
    
    Provides fault-isolated initialization and shutdown of the defense event bus.
    """
    
    def __init__(self):
        """Initialize subsystem."""
        self.bus = None
        self.initialized = False
    
    def initialize(self) -> bool:
        """
        Initialize event bus.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            from defense_core import reset_defense_bus, get_defense_bus
            
            # Reset to clean state
            reset_defense_bus()
            
            # Get bus instance
            self.bus = get_defense_bus()
            
            if self.bus is None:
                logger.error("Event bus initialization returned None")
                return False
            
            self.initialized = True
            logger.info("✓ Event bus initialized")
            return True
            
        except Exception as e:
            logger.error(f"✗ Event bus initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def is_healthy(self) -> bool:
        """
        Check if event bus is healthy.
        
        Returns:
            True if operational, False otherwise
        """
        return self.initialized and self.bus is not None
    
    def shutdown(self):
        """Graceful shutdown of event bus."""
        try:
            if self.bus:
                logger.info("Shutting down event bus...")
                # Event bus cleanup happens automatically
                self.bus = None
                self.initialized = False
                logger.info("✓ Event bus shutdown complete")
        except Exception as e:
            logger.error(f"Event bus shutdown error: {e}")
    
    def get_bus(self):
        """Get event bus instance."""
        return self.bus

    def get_statistics(self) -> dict:
        """
        Get event bus statistics.
        
        Returns:
            Dict with bus statistics
        """
        return self.bus.get_statistics() if self.bus else {}

    def get_queue_sizes(self) -> dict:
        """
        Get current queue sizes.
        
        Returns:
            Dict with 'radar_to_ew' and 'ew_to_radar' sizes
        """
        if not self.bus:
            return {'radar_to_ew': 0, 'ew_to_radar': 0}
            
        stats = self.bus.get_statistics()
        return {
            'radar_to_ew': stats['radar_to_ew']['queue_size'],
            'ew_to_radar': stats['ew_to_radar']['queue_size']
        }
