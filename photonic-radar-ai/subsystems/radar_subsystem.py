"""
Radar Subsystem
===============

Photonic radar engine subsystem.

Can run independently without EW.
Supports threaded execution for continuous operation.
"""

import logging
import threading
import time
from typing import Dict, Any, Optional
from collections import deque

logger = logging.getLogger(__name__)


class RadarSubsystem:
    """
    Radar engine subsystem wrapper.
    
    Provides fault-isolated radar operations that can run independently.
    Supports threaded execution for continuous radar operation.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize radar subsystem.
        
        Args:
            config: Radar configuration dictionary
        """
        self.config = config
        self.orchestrator: Optional[Any] = None
        self.initialized: bool = False
        self.frame_count: int = 0
        
        # Threading support
        self.thread: Optional[threading.Thread] = None
        self.running: bool = False
        self.stop_event = threading.Event()
        self.last_result: Optional[Dict[str, Any]] = None
        self.telemetry_history: deque = deque(maxlen=200)
        self.detection_history: deque = deque(maxlen=500)
        self.tactical_state: Optional[Any] = None
    
    def initialize(self, initial_targets: Optional[list] = None, event_bus: Optional[Any] = None, tactical_state: Optional[Any] = None) -> bool:
        """
        Initialize radar engine.
        
        Args:
            initial_targets: List of initial target states
            event_bus: Optional DefenseEventBus instance
            tactical_state: Shared tactical state container
        
        Returns:
            True if successful, False otherwise
        """
        try:
            from simulation_engine.orchestrator import SimulationOrchestrator
            
            # Use empty list if no targets provided
            if initial_targets is None:
                initial_targets = []
            
            # Create orchestrator
            self.orchestrator = SimulationOrchestrator(
                self.config, 
                initial_targets,
                event_bus=event_bus
            )
            
            self.tactical_state = tactical_state
            self.initialized = True
            
            logger.info("✓ Radar engine initialized")
            logger.info(f"  Sensor ID: {self.config.get('sensor_id', 'UNKNOWN')}")
            logger.info(f"  Frame rate: {1.0/self.config.get('frame_dt', 0.1):.1f} Hz")
            return True
            
        except Exception:
            logger.exception("✗ Radar initialization failed")
            return False
    
    def tick(self) -> Dict[str, Any]:
        """
        Run one radar frame.
        
        Returns:
            Dictionary with radar results or error
        """
        if not self.initialized or self.orchestrator is None:
            return {'error': 'Radar not initialized'}
        
        try:
            # Run radar tick
            result = self.orchestrator.tick()
            self.frame_count += 1
            
            # Add frame count
            result['frame'] = self.frame_count
            
            # Store telemetry history
            telemetry_point = None
            if 'telemetry' in result:
                telemetry_point = result['telemetry'].copy()
                telemetry_point['frame'] = self.frame_count
                telemetry_point['timestamp'] = result.get('timestamp', time.time())
                self.telemetry_history.append(telemetry_point)
            
            # Store detection history (rolling buffer)
            dt_record = None
            if 'tracks' in result:
                dt_record = {
                    'frame': self.frame_count,
                    'timestamp': result.get('timestamp', time.time()),
                    'count': len(result['tracks']),
                    'tracks': [t.to_dict() if hasattr(t, 'to_dict') else str(t) for t in result['tracks']]
                }
                self.detection_history.append(dt_record)
            
            # Update shared tactical state
            if self.tactical_state:
                self.tactical_state.update_radar(
                    status="ONLINE",
                    tracks=result.get('tracks', []),
                    threats=result.get('threats', []),
                    telemetry=telemetry_point,
                    detection_record=dt_record
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Radar tick failed at frame {self.frame_count}: {e}")
            if self.tactical_state:
                self.tactical_state.update_radar("ERROR", [], [], None, None)
            return {
                'error': str(e),
                'frame': self.frame_count
            }
    
    def is_healthy(self) -> bool:
        """Check if radar is healthy."""
        return self.initialized and self.orchestrator is not None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get radar statistics with track and threat data.
        
        Returns:
            Dictionary with radar stats
        """
        stats = {
            'initialized': self.initialized,
            'frame_count': self.frame_count,
            'sensor_id': self.config.get('sensor_id', 'UNKNOWN'),
            'track_count': 0,
            'threat_count': 0,
            'tracks': [],
            'threats': []
        }
        
        if self.last_result:
            # Extract tracks
            if 'tracks' in self.last_result:
                tracks = self.last_result['tracks']
                stats['track_count'] = len(tracks)
                stats['tracks'] = [t.to_dict() if hasattr(t, 'to_dict') else str(t) for t in tracks]
                
            # Extract threats
            if 'threats' in self.last_result:
                threats = self.last_result['threats']
                stats['threat_count'] = len(threats)
                stats['threats'] = [t.to_dict() if hasattr(t, 'to_dict') else str(t) for t in threats]
        
        # Add telemetry data
        stats['telemetry'] = {
            'history': list(self.telemetry_history),
            'current': self.telemetry_history[-1] if self.telemetry_history else {}
        }
        
        # Add detection history
        stats['detection_history'] = list(self.detection_history)
        
        return stats
    
    def shutdown(self):
        """Graceful shutdown of radar engine."""
        try:
            if self.orchestrator:
                logger.info("Shutting down radar engine...")
                self.orchestrator.stop()
                self.orchestrator = None
                self.initialized = False
                logger.info(f"✓ Radar shutdown complete (processed {self.frame_count} frames)")
        except Exception:
            logger.exception("Radar shutdown error")
    
    # Threading support
    
    def start_thread(self):
        """Start radar in dedicated thread."""
        if self.thread and self.thread.is_alive():
            logger.warning("Radar thread already running")
            return
        
        self.running = True
        self.stop_event.clear()
        
        self.thread = threading.Thread(
            target=self._radar_loop,
            name="RadarThread",
            daemon=False
        )
        self.thread.start()
        logger.info("[THREAD] Radar thread started")
    
    def _radar_loop(self):
        """Continuous radar execution loop."""
        logger.info("[THREAD] Radar loop active")
        frame_dt = self.config.get('frame_dt', 0.1)
        
        while self.running and not self.stop_event.is_set():
            try:
                result = self.tick()
                self.last_result = result
                time.sleep(frame_dt)
            except Exception:
                logger.exception("[THREAD] Critical radar loop error")
                time.sleep(frame_dt)  # Still wait to avoid busy loop on error
        
        logger.info("[THREAD] Radar loop exited")
    
    def stop_thread(self):
        """Stop radar thread gracefully."""
        if not self.thread or not self.thread.is_alive():
            return
        
        logger.info("[THREAD] Stopping radar thread...")
        self.running = False
        self.stop_event.set()
        
        self.thread.join(timeout=5.0)
        
        if self.thread.is_alive():
            logger.warning("[THREAD] Radar thread did not exit cleanly")
        else:
            logger.info("[THREAD] Radar thread stopped")
    
    def is_thread_alive(self) -> bool:
        """Check if radar thread is alive."""
        return self.thread is not None and self.thread.is_alive()

