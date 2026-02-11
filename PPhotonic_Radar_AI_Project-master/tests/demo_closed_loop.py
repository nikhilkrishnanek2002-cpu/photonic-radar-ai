"""
Closed-Loop Simulation Demo
============================

Simple demonstration of closed-loop sensor-effector simulation.

This demo shows:
- Time synchronization
- Detection → Decision → Response logging
- No deadlocks

Author: Integration Demo Team
"""

import sys
import time
import shutil
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from interfaces.message_schema import (
    Track, ThreatAssessment, SceneContext, TacticalPictureMessage,
    Countermeasure, EngagementStatus, EWFeedbackMessage, CountermeasureType
)
from interfaces.publisher import IntelligencePublisher
from interfaces.subscriber import IntelligenceSubscriber
from interfaces.ew_feedback_subscriber import EWFeedbackSubscriber
from cognitive.ew_feedback_publisher import EWFeedbackPublisher
from simulation_engine.ew_degradation import EWDegradationModel
from simulation_engine.execution_trace import ExecutionTraceLogger

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def demo_closed_loop():
    """Demonstrate closed-loop simulation."""
    print("\n" + "="*70)
    print("CLOSED-LOOP SENSOR-EFFECTOR SIMULATION DEMO")
    print("="*70)
    
    # Setup directories
    intel_dir = Path('./demo_intel')
    feedback_dir = Path('./demo_feedback')
    log_dir = Path('./demo_logs')
    
    for d in [intel_dir, feedback_dir, log_dir]:
        if d.exists():
            shutil.rmtree(d)
        d.mkdir()
    
    try:
        # Initialize components
        radar_publisher = IntelligencePublisher(
            sensor_id='DEMO_RADAR',
            enable_file_export=True,
            export_directory=str(intel_dir)
        )
        radar_publisher.start()
        
        ew_subscriber = IntelligenceSubscriber(
            source_directory=str(intel_dir),
            poll_interval_s=0.05
        )
        ew_subscriber.start()
        
        ew_publisher = EWFeedbackPublisher(
            effector_id='DEMO_EW',
            export_directory=str(feedback_dir),
            enable_export=True
        )
        
        radar_feedback_subscriber = EWFeedbackSubscriber(
            source_directory=str(feedback_dir),
            poll_interval_s=0.05
        )
        radar_feedback_subscriber.start()
        
        degradation_model = EWDegradationModel()
        
        trace_logger = ExecutionTraceLogger(
            log_directory=str(log_dir),
            enable_logging=True
        )
        
        # Simulation parameters
        num_frames = 10
        dt = 0.05  # 20 Hz
        simulation_time = 0.0
        
        print(f"\nRunning {num_frames} frames @ {1/dt:.0f} Hz...\n")
        
        # Simulation loop
        for frame_id in range(num_frames):
            trace_logger.start_frame(frame_id, simulation_time)
            
            print(f"[FRAME {frame_id}] t={simulation_time:.3f}s")
            
            # 1. RADAR: Generate and export intelligence
            tracks = [
                Track(
                    track_id=101,
                    range_m=5000.0 - frame_id * 100,  # Approaching
                    azimuth_deg=45.0,
                    radial_velocity_m_s=-200.0,
                    track_quality=0.92,
                    track_age_frames=frame_id + 1,
                    last_update_timestamp=simulation_time
                )
            ]
            
            threats = [
                ThreatAssessment(
                    track_id=101,
                    threat_class="HOSTILE",
                    target_type="MISSILE",
                    classification_confidence=0.88,
                    threat_priority=10,
                    engagement_recommendation="ENGAGE"
                )
            ]
            
            scene = SceneContext(
                scene_type="TRACKING",
                clutter_ratio=0.1,
                mean_snr_db=20.0,
                num_confirmed_tracks=1
            )
            
            intel_msg = TacticalPictureMessage.create(
                frame_id=frame_id,
                sensor_id='DEMO_RADAR',
                tracks=tracks,
                threat_assessments=threats,
                scene_context=scene
            )
            
            radar_publisher.publish(intel_msg)
            
            # Log detection
            trace_logger.log_detection(
                track_id=101,
                range_m=tracks[0].range_m,
                velocity_m_s=tracks[0].radial_velocity_m_s,
                quality=tracks[0].track_quality,
                timestamp=simulation_time
            )
            
            trace_logger.log_classification(
                track_id=101,
                threat_class="HOSTILE",
                target_type="MISSILE",
                confidence=0.88,
                priority=10,
                recommendation="ENGAGE"
            )
            
            print(f"  [RADAR-DETECT] Track 101: range={tracks[0].range_m:.0f}m, velocity=-200m/s, quality=0.92")
            print(f"  [RADAR-CLASSIFY] Track 101: HOSTILE MISSILE, confidence=0.88, priority=10")
            
            # 2. EW: Ingest intelligence and generate feedback
            time.sleep(0.1)  # Allow file I/O
            
            intel = ew_subscriber.get_next_message(timeout=0.2)
            
            if intel:
                # Generate EW feedback
                ew_publisher.publish_feedback(threats)
                
                # Log EW decision
                if ew_publisher.active_cms:
                    cm = ew_publisher.active_cms[0]
                    trace_logger.log_ew_decision(
                        track_id=cm.target_track_id,
                        cm_type=cm.cm_type,
                        power_dbm=cm.power_level_dbm,
                        effectiveness=cm.effectiveness_score or 0.8,
                        engagement_state="ENGAGING"
                    )
                    print(f"  [EW-DECISION] Track 101: ENGAGE with {cm.cm_type}, power={cm.power_level_dbm:.0f}dBm, effectiveness=0.80")
            
            # 3. RADAR: Receive feedback and apply degradation
            time.sleep(0.1)  # Allow file I/O
            
            feedback = radar_feedback_subscriber.get_next_message(timeout=0.2)
            
            if feedback:
                # Apply degradation
                import numpy as np
                rd_power = np.random.rand(64, 128) * 100
                rd_degraded = degradation_model.apply_jamming(rd_power, feedback.message.active_countermeasures)
                
                # Degrade track quality
                track_dict = [{'track_id': 101, 'quality': 0.92, 'range': tracks[0].range_m, 'velocity': -200}]
                degraded_tracks = degradation_model.degrade_tracks(track_dict, feedback.message.active_countermeasures)
                
                # Log radar response
                metrics = degradation_model.get_metrics()
                trace_logger.log_radar_response(
                    track_id=101,
                    snr_reduction_db=metrics.snr_reduction_db,
                    quality_before=0.92,
                    quality_after=degraded_tracks[0]['quality']
                )
                
                print(f"  [RADAR-RESPONSE] Track 101: SNR reduced {metrics.snr_reduction_db:.1f}dB, quality degraded 0.92→{degraded_tracks[0]['quality']:.2f}")
            
            trace_logger.end_frame()
            simulation_time += dt
            print()
        
        # Save complete trace
        trace_logger.save_complete_trace()
        
        # Summary
        summary = trace_logger.get_trace_summary()
        print("="*70)
        print("SIMULATION COMPLETE")
        print("="*70)
        print(f"Frames: {summary['frames']}")
        print(f"Total detections: {summary['total_detections']}")
        print(f"Total EW decisions: {summary['total_ew_decisions']}")
        print(f"Total radar responses: {summary['total_radar_responses']}")
        print(f"Simulation duration: {summary['simulation_duration_s']:.3f}s")
        print(f"\nLogs saved to: {log_dir}")
        
        print("\n✓ DEMO SUCCESSFUL\n")
        
    finally:
        # Cleanup
        radar_publisher.stop()
        ew_subscriber.stop()
        radar_feedback_subscriber.stop()
        
        # Keep logs for inspection
        print(f"Log files preserved in: {log_dir}")


if __name__ == '__main__':
    demo_closed_loop()
