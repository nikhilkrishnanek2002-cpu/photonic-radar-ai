"""
Integration Loop
================

Coordination loop for radar-EW integration.

Handles fault-tolerant execution of both subsystems.
"""

import logging
import time
from typing import Optional

from .radar_subsystem import RadarSubsystem
from .ew_subsystem import EWSubsystem

logger = logging.getLogger(__name__)


class IntegrationLoop:
    """
    Integration loop for radar-EW coordination.
    
    Provides fault-tolerant execution with graceful degradation.
    """
    
    def __init__(self, radar: RadarSubsystem, ew: Optional[EWSubsystem] = None):
        """
        Initialize integration loop.
        
        Args:
            radar: Radar subsystem (required)
            ew: EW subsystem (optional)
        """
        self.radar = radar
        self.ew = ew
        self.running = False
        self.frame_count = 0
        
        # Try to import ticker (optional)
        try:
            from ui.integration_ticker import IntegrationTicker
            self.ticker = IntegrationTicker()
            self.has_ticker = True
        except ImportError:
            self.ticker = None
            self.has_ticker = False
            logger.warning("Integration ticker not available")
    
    def run(self, max_frames: int = 1000, frame_dt: float = 0.1):
        """
        Run integration loop.
        
        Args:
            max_frames: Maximum number of frames to run
            frame_dt: Time between frames (seconds)
        """
        self.running = True
        self.frame_count = 0
        
        logger.info("")
        logger.info("="*70)
        logger.info("INTEGRATION LOOP ACTIVE")
        logger.info("="*70)
        logger.info(f"Max frames: {max_frames}")
        logger.info(f"Frame rate: {1.0/frame_dt:.1f} Hz")
        logger.info(f"EW enabled: {self.ew is not None}")
        logger.info(f"Ticker enabled: {self.has_ticker}")
        logger.info("")
        
        try:
            while self.running and self.frame_count < max_frames:
                if self.has_ticker:
                    self.ticker.start_cycle(self.frame_count)
                
                # Radar tick (always runs)
                radar_result = self._safe_radar_tick()
                radar_ok = 'error' not in radar_result
                
                # EW tick (only if available and radar OK)
                ew_result = {}
                if self.ew and radar_ok:
                    ew_result = self._safe_ew_tick()
                
                # Update ticker
                if self.has_ticker:
                    self._update_ticker(radar_result, ew_result)
                    self.ticker.end_cycle()
                    
                    # Print ticker every 10 frames
                    if self.frame_count % 10 == 0:
                        self.ticker.print_ticker()
                
                # Log cycle every 10 frames
                if self.frame_count % 10 == 0:
                    self._log_cycle(radar_result, ew_result)
                
                self.frame_count += 1
                time.sleep(frame_dt)
                
        except KeyboardInterrupt:
            logger.info("Integration loop interrupted by user")
        except Exception as e:
            logger.error(f"Integration loop error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            logger.info(f"Integration loop stopped after {self.frame_count} frames")
    
    def _safe_radar_tick(self) -> dict:
        """
        Run radar tick with fault isolation.
        
        Returns:
            Radar result dictionary
        """
        try:
            return self.radar.tick()
        except Exception as e:
            logger.error(f"Radar tick exception: {e}")
            return {'error': str(e)}
    
    def _safe_ew_tick(self) -> dict:
        """
        Run EW tick with fault isolation.
        
        Returns:
            EW result dictionary
        """
        try:
            return self.ew.tick()
        except Exception as e:
            logger.error(f"EW tick exception: {e}")
            return {'error': str(e)}
    
    def _update_ticker(self, radar_result: dict, ew_result: dict):
        """Update integration ticker."""
        if not self.has_ticker:
            return
        
        # Radar stage
        num_detections = radar_result.get('num_detections', 0)
        num_tracks = radar_result.get('num_tracks', 0)
        self.ticker.update_radar(num_detections, num_tracks)
        
        # Intel stage
        num_threats = len([t for t in radar_result.get('tracks', []) 
                          if t.get('threat_class') == 'HOSTILE'])
        intel_sent = radar_result.get('intelligence_exported', False)
        self.ticker.update_intel(num_threats, intel_sent)
        
        # EW stage
        ew_status = ew_result.get('status', 'unavailable')
        ew_processed = ew_status == 'processed'
        num_decisions = ew_result.get('decision_count', 0) if ew_processed else 0
        self.ticker.update_ew(num_decisions, ew_processed or num_threats > 0)
        
        # Jam stage
        ew_effects = radar_result.get('ew_effects_applied', False)
        num_cms = 1 if ew_effects else 0
        self.ticker.update_jam(num_cms, ew_effects)
        
        # Effect stage
        num_effects = 1 if ew_effects else 0
        self.ticker.update_effect(num_effects, ew_effects)
    
    def _log_cycle(self, radar_result: dict, ew_result: dict):
        """Log cycle summary."""
        radar_status = "OK" if 'error' not in radar_result else "ERROR"
        ew_status = ew_result.get('status', 'N/A') if self.ew else "DISABLED"
        
        logger.info(
            f"Frame {self.frame_count:4d} | "
            f"Radar: {radar_status:5s} ({radar_result.get('num_tracks', 0)} tracks) | "
            f"EW: {ew_status:10s}"
        )
    
    def stop(self):
        """Stop integration loop."""
        self.running = False
        logger.info("Integration loop stop requested")
