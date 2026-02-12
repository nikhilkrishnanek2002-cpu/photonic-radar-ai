"""
Execution Trace Logger
======================

Logs detection → decision → response cycles for closed-loop simulation.
Provides comprehensive tracing of sensor-effector interactions.

Author: Closed-Loop Simulation Team
"""

import json
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
import time

logger = logging.getLogger(__name__)


@dataclass
class DetectionEvent:
    """Radar detection event."""
    track_id: int
    range_m: float
    velocity_m_s: float
    quality: float
    timestamp: float


@dataclass
class ClassificationEvent:
    """AI classification event."""
    track_id: int
    threat_class: str
    target_type: str
    confidence: float
    priority: int
    recommendation: str


@dataclass
class EWDecisionEvent:
    """EW decision event."""
    track_id: int
    cm_type: str
    power_dbm: Optional[float]
    effectiveness: float
    engagement_state: str


@dataclass
class RadarResponseEvent:
    """Radar response to EW action."""
    track_id: int
    snr_reduction_db: float
    quality_before: float
    quality_after: float
    degraded: bool


@dataclass
class FrameTrace:
    """Complete trace for one simulation frame."""
    frame_id: int
    simulation_time: float
    detections: List[DetectionEvent]
    classifications: List[ClassificationEvent]
    ew_decisions: List[EWDecisionEvent]
    radar_responses: List[RadarResponseEvent]
    timing_metrics: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'frame_id': self.frame_id,
            'simulation_time': self.simulation_time,
            'detections': [asdict(d) for d in self.detections],
            'classifications': [asdict(c) for c in self.classifications],
            'ew_decisions': [asdict(e) for e in self.ew_decisions],
            'radar_responses': [asdict(r) for r in self.radar_responses],
            'timing_metrics': self.timing_metrics
        }


class ExecutionTraceLogger:
    """
    Logs complete execution trace of closed-loop simulation.
    
    Captures detection → decision → response cycles.
    """
    
    def __init__(self, log_directory: str = './closed_loop_logs', enable_logging: bool = True):
        """
        Initialize execution trace logger.
        
        Args:
            log_directory: Directory for trace logs
            enable_logging: Enable/disable logging
        """
        self.log_dir = Path(log_directory)
        self.enable_logging = enable_logging
        
        if self.enable_logging:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.frame_traces: List[FrameTrace] = []
        self.current_frame_trace: Optional[FrameTrace] = None
        
        logger.info(f"Execution trace logger initialized: {self.log_dir}")
    
    def start_frame(self, frame_id: int, simulation_time: float):
        """Start logging a new frame."""
        self.current_frame_trace = FrameTrace(
            frame_id=frame_id,
            simulation_time=simulation_time,
            detections=[],
            classifications=[],
            ew_decisions=[],
            radar_responses=[],
            timing_metrics={}
        )
    
    def log_detection(self, track_id: int, range_m: float, velocity_m_s: float, 
                     quality: float, timestamp: float):
        """Log a radar detection."""
        if self.current_frame_trace is None:
            return
        
        event = DetectionEvent(
            track_id=track_id,
            range_m=range_m,
            velocity_m_s=velocity_m_s,
            quality=quality,
            timestamp=timestamp
        )
        
        self.current_frame_trace.detections.append(event)
        
        logger.info(f"[RADAR-DETECT] Track {track_id}: range={range_m:.0f}m, "
                   f"velocity={velocity_m_s:.0f}m/s, quality={quality:.2f}")
    
    def log_classification(self, track_id: int, threat_class: str, target_type: str,
                          confidence: float, priority: int, recommendation: str):
        """Log an AI classification."""
        if self.current_frame_trace is None:
            return
        
        event = ClassificationEvent(
            track_id=track_id,
            threat_class=threat_class,
            target_type=target_type,
            confidence=confidence,
            priority=priority,
            recommendation=recommendation
        )
        
        self.current_frame_trace.classifications.append(event)
        
        logger.info(f"[RADAR-CLASSIFY] Track {track_id}: {threat_class} {target_type}, "
                   f"confidence={confidence:.2f}, priority={priority}")
    
    def log_ew_decision(self, track_id: int, cm_type: str, power_dbm: Optional[float],
                       effectiveness: float, engagement_state: str):
        """Log an EW decision."""
        if self.current_frame_trace is None:
            return
        
        event = EWDecisionEvent(
            track_id=track_id,
            cm_type=cm_type,
            power_dbm=power_dbm,
            effectiveness=effectiveness,
            engagement_state=engagement_state
        )
        
        self.current_frame_trace.ew_decisions.append(event)
        
        power_str = f"power={power_dbm:.0f}dBm" if power_dbm else "power=N/A"
        logger.info(f"[EW-DECISION] Track {track_id}: {engagement_state} with {cm_type}, "
                   f"{power_str}, effectiveness={effectiveness:.2f}")
    
    def log_radar_response(self, track_id: int, snr_reduction_db: float,
                          quality_before: float, quality_after: float):
        """Log radar response to EW action."""
        if self.current_frame_trace is None:
            return
        
        event = RadarResponseEvent(
            track_id=track_id,
            snr_reduction_db=snr_reduction_db,
            quality_before=quality_before,
            quality_after=quality_after,
            degraded=(quality_after < quality_before)
        )
        
        self.current_frame_trace.radar_responses.append(event)
        
        logger.info(f"[RADAR-RESPONSE] Track {track_id}: SNR reduced {snr_reduction_db:.1f}dB, "
                   f"quality degraded {quality_before:.2f}→{quality_after:.2f}")
    
    def add_timing_metric(self, name: str, value: float):
        """Add a timing metric to current frame."""
        if self.current_frame_trace:
            self.current_frame_trace.timing_metrics[name] = value
    
    def end_frame(self):
        """End current frame and save trace."""
        if self.current_frame_trace is None:
            return
        
        # Add to trace history
        self.frame_traces.append(self.current_frame_trace)
        
        # Log summary
        logger.info(f"[FRAME {self.current_frame_trace.frame_id}] t={self.current_frame_trace.simulation_time:.3f}s: "
                   f"{len(self.current_frame_trace.detections)} detections, "
                   f"{len(self.current_frame_trace.ew_decisions)} EW decisions, "
                   f"{len(self.current_frame_trace.radar_responses)} responses")
        
        # Save to file
        if self.enable_logging:
            self._save_frame_trace(self.current_frame_trace)
        
        self.current_frame_trace = None
    
    def _save_frame_trace(self, frame_trace: FrameTrace):
        """Save frame trace to JSON file."""
        filename = f"frame_{frame_trace.frame_id:06d}_trace.json"
        filepath = self.log_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(frame_trace.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save frame trace: {e}")
    
    def get_trace_summary(self) -> Dict[str, Any]:
        """Get summary of execution trace."""
        if len(self.frame_traces) == 0:
            return {'frames': 0}
        
        total_detections = sum(len(ft.detections) for ft in self.frame_traces)
        total_ew_decisions = sum(len(ft.ew_decisions) for ft in self.frame_traces)
        total_responses = sum(len(ft.radar_responses) for ft in self.frame_traces)
        
        return {
            'frames': len(self.frame_traces),
            'total_detections': total_detections,
            'total_ew_decisions': total_ew_decisions,
            'total_radar_responses': total_responses,
            'simulation_duration_s': self.frame_traces[-1].simulation_time if self.frame_traces else 0
        }
    
    def save_complete_trace(self, filename: str = 'complete_trace.json'):
        """Save complete execution trace."""
        if not self.enable_logging:
            return
        
        filepath = self.log_dir / filename
        
        trace_data = {
            'summary': self.get_trace_summary(),
            'frames': [ft.to_dict() for ft in self.frame_traces]
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(trace_data, f, indent=2)
            logger.info(f"Saved complete trace: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save complete trace: {e}")
