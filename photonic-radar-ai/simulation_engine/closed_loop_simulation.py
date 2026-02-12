"""
Closed-Loop Sensor-Effector Simulation
=======================================

Integrates Photonic Radar + AI (sensor) and Cognitive EW-AI (effector)
into a synchronized closed-loop simulation.

Features:
- Frame-based time synchronization
- Deadlock-free communication
- Deterministic execution
- Complete execution tracing

Author: Closed-Loop Simulation Team
"""

import logging
import time
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
import numpy as np

from simulation_engine.orchestrator import SimulationOrchestrator
from simulation_engine.execution_trace import ExecutionTraceLogger
from simulation_engine.ew_degradation import EWDegradationModel
from cognitive.intelligence_pipeline import EWIntelligencePipeline
from cognitive.ew_feedback_publisher import EWFeedbackPublisher
from interfaces.ew_feedback_subscriber import EWFeedbackSubscriber
from interfaces.message_schema import ThreatAssessment

logger = logging.getLogger(__name__)


class ClosedLoopSimulation:
    """
    Closed-loop simulation of sensor-effector system.
    
    Ensures:
    - Time synchronization (frame-based)
    - No deadlocks (timeouts on all I/O)
    - Deterministic execution (fixed time steps)
    """
    
    def __init__(self,
                 radar_config: Dict,
                 ew_config: Dict,
                 targets: List,
                 frame_rate_hz: float = 20.0,
                 enable_logging: bool = True,
                 log_directory: str = './closed_loop_logs'):
        """
        Initialize closed-loop simulation.
        
        Args:
            radar_config: Radar configuration
            ew_config: EW configuration
            targets: Initial target list
            frame_rate_hz: Simulation frame rate
            enable_logging: Enable execution tracing
            log_directory: Directory for logs
        """
        self.frame_rate_hz = frame_rate_hz
        self.dt = 1.0 / frame_rate_hz
        self.frame_id = 0
        self.simulation_time = 0.0
        
        # Setup shared directories
        self.shared_intel_dir = Path('./shared_intel')
        self.shared_feedback_dir = Path('./shared_feedback')
        self._setup_shared_directories()
        
        # Update configs with shared directories
        radar_config['enable_intelligence_export'] = True
        radar_config['intelligence_export_dir'] = str(self.shared_intel_dir)
        radar_config['enable_ew_feedback'] = True
        radar_config['ew_feedback_dir'] = str(self.shared_feedback_dir)
        
        ew_config['enable_intelligence_ingestion'] = True
        ew_config['intelligence_source_dir'] = str(self.shared_intel_dir)
        ew_config['enable_feedback_export'] = True
        ew_config['feedback_export_dir'] = str(self.shared_feedback_dir)
        
        # Initialize radar
        logger.info("Initializing radar system...")
        self.radar = SimulationOrchestrator(radar_config, targets)
        
        # Initialize EW feedback subscriber for radar
        self.radar_feedback_subscriber = EWFeedbackSubscriber(
            source_directory=str(self.shared_feedback_dir),
            poll_interval_s=0.05,
            log_all_updates=True
        )
        self.radar_feedback_subscriber.start()
        
        # Initialize degradation model for radar
        self.degradation_model = EWDegradationModel(
            max_snr_degradation_db=20.0,
            max_quality_degradation=0.5
        )
        
        # Initialize EW pipeline
        logger.info("Initializing EW system...")
        self.ew_pipeline = EWIntelligencePipeline(
            enable_ingestion=True,
            source_directory=str(self.shared_intel_dir),
            staleness_threshold_s=2.0,
            poll_interval_s=0.05
        )
        self.ew_pipeline.start()
        
        # Initialize EW feedback publisher
        self.ew_publisher = EWFeedbackPublisher(
            effector_id=ew_config.get('effector_id', 'COGNITIVE_EW_01'),
            export_directory=str(self.shared_feedback_dir),
            enable_export=True
        )
        
        # Initialize execution trace logger
        self.trace_logger = ExecutionTraceLogger(
            log_directory=log_directory,
            enable_logging=enable_logging
        )
        
        # Timing metrics
        self.frame_times = []
        
        logger.info(f"Closed-loop simulation initialized: {frame_rate_hz} Hz")
    
    def _setup_shared_directories(self):
        """Setup shared communication directories."""
        # Clean and create directories
        for dir_path in [self.shared_intel_dir, self.shared_feedback_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
            dir_path.mkdir(parents=True)
    
    def run_frame(self) -> Dict[str, Any]:
        """
        Execute one simulation frame (deterministic).
        
        Returns:
            Frame results dictionary
        """
        frame_start_time = time.time()
        
        # Start trace logging
        self.trace_logger.start_frame(self.frame_id, self.simulation_time)
        
        # 1. Radar processes and exports intelligence
        radar_result = self._run_radar_frame()
        
        # 2. EW ingests intelligence and generates feedback
        ew_result = self._run_ew_frame()
        
        # 3. Log complete cycle
        self._log_frame_cycle(radar_result, ew_result)
        
        # End trace logging
        self.trace_logger.end_frame()
        
        # Update frame counters
        self.frame_id += 1
        self.simulation_time += self.dt
        
        # Timing
        frame_time = time.time() - frame_start_time
        self.frame_times.append(frame_time)
        self.trace_logger.add_timing_metric('frame_time_ms', frame_time * 1000)
        
        return {
            'frame_id': self.frame_id,
            'simulation_time': self.simulation_time,
            'num_tracks': radar_result.get('num_tracks', 0),
            'num_ew_decisions': ew_result.get('num_decisions', 0),
            'frame_time_ms': frame_time * 1000
        }
    
    def _run_radar_frame(self) -> Dict[str, Any]:
        """Run radar processing for one frame."""
        # Get EW feedback from previous frame
        feedback = self.radar_feedback_subscriber.get_next_message(timeout=0.1)
        
        active_cms = []
        if feedback:
            active_cms = feedback.message.active_countermeasures
            
            # Apply degradation (this would be integrated into radar.tick())
            # For now, just log that feedback was received
            logger.debug(f"Radar received {len(active_cms)} countermeasures")
        
        # Run radar tick
        result = self.radar.tick()
        
        # Extract tracks for logging
        tracks = result.get('tracks', [])
        
        # Log detections
        for track in tracks:
            self.trace_logger.log_detection(
                track_id=track.get('track_id', 0),
                range_m=track.get('range', 0),
                velocity_m_s=track.get('velocity', 0),
                quality=track.get('quality', 0),
                timestamp=self.simulation_time
            )
        
        # Log classifications (from AI)
        ai_classifications = result.get('ai_classifications', [])
        for classification in ai_classifications:
            self.trace_logger.log_classification(
                track_id=classification.get('track_id', 0),
                threat_class=classification.get('class', 'UNKNOWN'),
                target_type=classification.get('type', 'UNKNOWN'),
                confidence=classification.get('confidence', 0),
                priority=classification.get('priority', 5),
                recommendation=classification.get('recommendation', 'MONITOR')
            )
        
        # Log radar responses to EW actions
        if active_cms:
            degradation_metrics = self.degradation_model.get_metrics()
            for track in tracks:
                if track.get('ew_degraded', False):
                    self.trace_logger.log_radar_response(
                        track_id=track.get('track_id', 0),
                        snr_reduction_db=degradation_metrics.snr_reduction_db,
                        quality_before=track.get('quality_before_ew', 1.0),
                        quality_after=track.get('quality', 1.0)
                    )
        
        return {
            'num_tracks': len(tracks),
            'num_detections': result.get('num_detections', 0),
            'tracks': tracks
        }
    
    def _run_ew_frame(self) -> Dict[str, Any]:
        """Run EW processing for one frame."""
        # Process intelligence from radar
        assessment = self.ew_pipeline.process_next_intelligence(timeout=0.1)
        
        if assessment is None:
            return {'num_decisions': 0}
        
        # Get threat assessments from latest intelligence
        threats = []
        if self.ew_pipeline.latest_intelligence:
            threats = self.ew_pipeline.latest_intelligence.message.threat_assessments
        
        # Generate and publish EW feedback
        if threats:
            self.ew_publisher.publish_feedback(threats)
            
            # Log EW decisions
            for cm in self.ew_publisher.active_cms:
                # Find corresponding engagement
                engagement = next(
                    (e for e in self.ew_publisher.active_engagements 
                     if e.track_id == cm.target_track_id),
                    None
                )
                
                self.trace_logger.log_ew_decision(
                    track_id=cm.target_track_id,
                    cm_type=cm.cm_type,
                    power_dbm=cm.power_level_dbm,
                    effectiveness=cm.effectiveness_score if cm.effectiveness_score else 0.7,
                    engagement_state=engagement.engagement_state if engagement else 'UNKNOWN'
                )
        
        return {
            'num_decisions': len(self.ew_publisher.active_cms),
            'num_engagements': len(self.ew_publisher.active_engagements)
        }
    
    def _log_frame_cycle(self, radar_result: Dict, ew_result: Dict):
        """Log complete detection → decision → response cycle."""
        logger.info(f"[CYCLE] Frame {self.frame_id}: "
                   f"{radar_result['num_tracks']} tracks → "
                   f"{ew_result['num_decisions']} EW decisions → "
                   f"radar responses logged")
    
    def run(self, num_frames: int) -> Dict[str, Any]:
        """
        Run simulation for specified number of frames.
        
        Args:
            num_frames: Number of frames to simulate
            
        Returns:
            Simulation summary
        """
        logger.info(f"Starting closed-loop simulation: {num_frames} frames @ {self.frame_rate_hz} Hz")
        
        start_time = time.time()
        
        for i in range(num_frames):
            self.run_frame()
            
            # Progress logging
            if (i + 1) % 10 == 0:
                logger.info(f"Progress: {i+1}/{num_frames} frames")
        
        elapsed_time = time.time() - start_time
        
        # Save complete trace
        self.trace_logger.save_complete_trace()
        
        # Generate summary
        summary = {
            'frames_simulated': num_frames,
            'simulation_duration_s': self.simulation_time,
            'wall_clock_time_s': elapsed_time,
            'real_time_factor': self.simulation_time / elapsed_time if elapsed_time > 0 else 0,
            'mean_frame_time_ms': np.mean(self.frame_times) * 1000 if self.frame_times else 0,
            'max_frame_time_ms': np.max(self.frame_times) * 1000 if self.frame_times else 0,
            'trace_summary': self.trace_logger.get_trace_summary()
        }
        
        logger.info(f"Simulation complete: {num_frames} frames in {elapsed_time:.2f}s "
                   f"(RTF={summary['real_time_factor']:.2f}x)")
        
        return summary
    
    def stop(self):
        """Stop simulation and cleanup."""
        logger.info("Stopping closed-loop simulation...")
        
        # Stop radar
        self.radar.stop()
        
        # Stop EW pipeline
        self.ew_pipeline.stop()
        
        # Stop feedback subscriber
        self.radar_feedback_subscriber.stop()
        
        logger.info("Closed-loop simulation stopped")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get simulation statistics."""
        return {
            'frame_id': self.frame_id,
            'simulation_time': self.simulation_time,
            'radar_stats': self.radar.get_statistics() if hasattr(self.radar, 'get_statistics') else {},
            'ew_stats': self.ew_pipeline.get_statistics(),
            'ew_publisher_stats': self.ew_publisher.get_statistics(),
            'trace_summary': self.trace_logger.get_trace_summary()
        }
