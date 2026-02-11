"""
EW Subsystem
============

Cognitive EW engine subsystem.

Waits safely for radar intelligence data.
Supports threaded execution for continuous polling.
"""

import logging
import threading
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class EWSubsystem:
    """
    EW engine subsystem wrapper.
    
    Provides fault-isolated EW operations that wait safely for radar data.
    Supports threaded execution for continuous event bus polling.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize EW subsystem.
        
        Args:
            config: EW configuration dictionary
        """
        self.config = config
        self.pipeline = None
        self.publisher = None
        self.initialized = False
        self.waiting_for_data = True
        self.last_update: Optional[Dict[str, Any]] = None
        self.intelligence_count = 0
        self.decision_count = 0
        self.tactical_state = None
        
        # Threading support
        self.thread: Optional[threading.Thread] = None
        self.running = False
        self.stop_event = threading.Event()
    
    def initialize(self, tactical_state = None) -> bool:
        """
        Initialize EW engine.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            from cognitive.intelligence_pipeline import EWIntelligencePipeline
            from cognitive.ew_feedback_publisher import EWFeedbackPublisher
            
            # Create intelligence pipeline
            self.pipeline = EWIntelligencePipeline(
                enable_ingestion=True,
                ingestion_mode=self.config.get('ingestion_mode', 'event_bus'),
                source_directory=self.config.get('intelligence_export_dir', './intelligence_export'),
                staleness_threshold_s=self.config.get('staleness_threshold_s', 2.0),
                poll_interval_s=self.config.get('ew_poll_interval_s', 0.1),
                log_all_updates=self.config.get('log_all_updates', True)
            )
            self.pipeline.start()
            
            # Create feedback publisher
            effector_id = self.config.get('effector_id', 'EW_UNKNOWN')
            self.publisher = EWFeedbackPublisher(effector_id)
            
            self.tactical_state = tactical_state
            
            self.initialized = True
            logger.info("✓ EW engine initialized")
            logger.info(f"  Effector ID: {effector_id}")
            logger.info(f"  Ingestion mode: {self.config.get('ingestion_mode', 'event_bus')}")
            return True
            
        except Exception as e:
            logger.error(f"✗ EW initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def tick(self) -> Dict[str, Any]:
        """
        Process intelligence (non-blocking).
        
        Returns:
            Dictionary with EW results or status
        """
        if not self.initialized:
            return {'error': 'EW not initialized'}
        
        try:
            # Attempt to process next intelligence message (non-blocking)
            # Timeout 0 means return immediately if empty
            assessment = self.pipeline.process_next_intelligence(timeout=0)
            
            if assessment:
                self.waiting_for_data = False
                self.intelligence_count += 1
                
                # Mock decision count increment for now as assessment doesn't expose it directly
                # In full implementation we would check assessment details
                self.decision_count += 1 
                
                result = {
                    'status': 'processed',
                    'intelligence_count': self.intelligence_count,
                    'decision_count': self.decision_count,
                    'result': assessment
                }
                self.last_update = result
                
                # Update shared tactical state
                if self.tactical_state:
                    # Determine active jamming based on recommendation
                    rec = assessment.get('engagement_recommendation', 'MONITOR')
                    jamming = rec in ['JAMMING', 'DECEPTION']
                    
                    self.tactical_state.update_ew(
                        status="ENGAGING",
                        decision_count=self.decision_count,
                        last_assessment=assessment.to_dict() if hasattr(assessment, 'to_dict') else assessment,
                        active_jamming=jamming
                    )
                
                return result
            else:
                # No data available
                if self.tactical_state and self.waiting_for_data:
                     self.tactical_state.update_ew("WAITING", self.decision_count, {}, False)
                     
                return {
                    'status': 'waiting',
                    'waiting': self.waiting_for_data,
                    'intelligence_count': self.intelligence_count
                }
                
        except Exception as e:
            logger.error(f"EW tick failed: {e}")
            return {
                'error': str(e),
                'intelligence_count': self.intelligence_count
            }
                
        except Exception as e:
            logger.error(f"EW tick failed: {e}")
            return {
                'error': str(e),
                'intelligence_count': self.intelligence_count
            }
    
    def is_healthy(self) -> bool:
        """
        Check if EW is healthy.
        
        Returns:
            True if operational, False otherwise
        """
        return self.initialized and self.pipeline is not None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get EW statistics.
        
        Returns:
            Dictionary with EW stats
        """
        stats = {
            'initialized': self.initialized,
            'waiting_for_data': self.waiting_for_data,
            'intelligence_count': self.intelligence_count,
            'decision_count': self.decision_count,
            'effector_id': self.config.get('effector_id', 'UNKNOWN'),
            'last_assessment': None
        }
        
        if self.last_update and 'result' in self.last_update:
            data = self.last_update['result']
            stats['last_assessment'] = data.to_dict() if hasattr(data, 'to_dict') else str(data)
            
        return stats
    
    def shutdown(self):
        """Graceful shutdown of EW engine."""
        try:
            if self.pipeline:
                logger.info("Shutting down EW engine...")
                self.pipeline.stop()
                self.pipeline = None
                self.publisher = None
                self.initialized = False
                logger.info(f"✓ EW shutdown complete (processed {self.intelligence_count} intel packets)")
        except Exception as e:
            logger.error(f"EW shutdown error: {e}")
    
    # Threading support
    
    def start_thread(self):
        """
        Start EW in dedicated thread.
        
        Runs EW polling loop continuously in background thread.
        """
        if self.thread and self.thread.is_alive():
            logger.warning("EW thread already running")
            return
        
        self.running = True
        self.stop_event.clear()
        
        self.thread = threading.Thread(
            target=self._ew_loop,
            name="EWThread",
            daemon=False  # Not daemon - wait for clean shutdown
        )
        self.thread.start()
        logger.info("[THREAD] EW thread started")
    
    def _ew_loop(self):
        """
        EW polling loop.
        
        Runs in dedicated thread, polling event bus for intelligence.
        """
        logger.info("[THREAD] EW loop active")
        poll_interval = 0.1  # Poll every 100ms
        
        while self.running and not self.stop_event.is_set():
            try:
                # Poll event bus (non-blocking)
                result = self.tick()
                
                # Sleep if waiting for data
                if result.get('status') == 'waiting':
                    time.sleep(poll_interval)
                else:
                    # Small sleep even when processing
                    time.sleep(0.01)
                    
            except Exception as e:
                logger.error(f"[THREAD] EW loop error: {e}")
                # Continue running despite errors
                time.sleep(poll_interval)
        
        logger.info("[THREAD] EW loop exited")
    
    def stop_thread(self):
        """
        Stop EW thread gracefully.
        
        Sets stop event and waits for thread to exit with timeout.
        """
        if not self.thread or not self.thread.is_alive():
            return
        
        logger.info("[THREAD] Stopping EW thread...")
        self.running = False
        self.stop_event.set()
        
        # Wait for thread to exit (with timeout)
        self.thread.join(timeout=5.0)
        
        if self.thread.is_alive():
            logger.warning("[THREAD] EW thread did not exit cleanly")
        else:
            logger.info("[THREAD] EW thread stopped")
    
    def is_thread_alive(self) -> bool:
        """
        Check if EW thread is alive.
        
        Returns:
            True if thread is running, False otherwise
        """
        return self.thread is not None and self.thread.is_alive()

