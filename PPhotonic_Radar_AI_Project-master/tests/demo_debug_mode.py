"""
Debug Mode Demo
===============

Demonstrates integration debug mode with:
- Message printing
- Data flow visualization
- Dropped/delayed packet detection

Author: Debug Demo Team
"""

import sys
import time
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from interfaces.message_schema import (
    Track, ThreatAssessment, SceneContext, TacticalPictureMessage
)
from interfaces.publisher import IntelligencePublisher
from interfaces.subscriber import IntelligenceSubscriber
from interfaces.ew_feedback_subscriber import EWFeedbackSubscriber
from cognitive.ew_feedback_publisher import EWFeedbackPublisher
from simulation_engine.debug_monitor import IntegrationDebugMonitor
import logging

logging.basicConfig(level=logging.WARNING)  # Reduce noise


def demo_debug_mode():
    """Demonstrate debug mode."""
    print("\n" + "="*70)
    print("INTEGRATION DEBUG MODE DEMO")
    print("="*70)
    
    # Setup
    intel_dir = Path('./debug_demo_intel')
    feedback_dir = Path('./debug_demo_feedback')
    
    for d in [intel_dir, feedback_dir]:
        if d.exists():
            shutil.rmtree(d)
        d.mkdir()
    
    try:
        # Initialize debug monitor
        debug_monitor = IntegrationDebugMonitor(
            enable_message_printing=True,
            enable_flow_visualization=True,
            latency_threshold_ms=50.0,
            log_directory='./debug_demo_logs'
        )
        
        # Initialize components
        radar_publisher = IntelligencePublisher(
            sensor_id='DEBUG_RADAR',
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
            effector_id='DEBUG_EW',
            export_directory=str(feedback_dir),
            enable_export=True
        )
        
        radar_feedback_subscriber = EWFeedbackSubscriber(
            source_directory=str(feedback_dir),
            poll_interval_s=0.05
        )
        radar_feedback_subscriber.start()
        
        # Run 5 frames with debug monitoring
        for frame_id in range(5):
            print(f"\n{'#'*70}")
            print(f"# FRAME {frame_id}")
            print(f"{'#'*70}")
            
            # 1. Radar sends intelligence
            tracks = [
                Track(
                    track_id=101,
                    range_m=5000.0 - frame_id * 200,
                    azimuth_deg=45.0,
                    radial_velocity_m_s=-200.0,
                    track_quality=0.92,
                    track_age_frames=frame_id + 1,
                    last_update_timestamp=time.time()
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
                sensor_id='DEBUG_RADAR',
                tracks=tracks,
                threat_assessments=threats,
                scene_context=scene
            )
            
            # Log message sent
            send_time = time.time()
            debug_monitor.log_message_sent(
                message_type='INTEL_TX',
                message_id=intel_msg.message_id,
                frame_id=frame_id,
                sender='RADAR',
                receiver='EW',
                payload_size=len(intel_msg.to_json())
            )
            
            radar_publisher.publish(intel_msg)
            
            # 2. EW receives intelligence
            time.sleep(0.05)  # Simulate processing delay
            
            intel = ew_subscriber.get_next_message(timeout=0.2)
            
            if intel:
                # Log message received
                debug_monitor.log_message_received(
                    message_type='INTEL_RX',
                    message_id=intel.message.message_id,
                    frame_id=frame_id,
                    receiver='EW'
                )
                
                # 3. EW sends feedback
                ew_publisher.publish_feedback(threats)
                
                if ew_publisher.active_cms:
                    feedback_msg_id = f"feedback_{frame_id}"
                    
                    # Log feedback sent
                    debug_monitor.log_message_sent(
                        message_type='FEEDBACK_TX',
                        message_id=feedback_msg_id,
                        frame_id=frame_id,
                        sender='EW',
                        receiver='RADAR',
                        payload_size=500  # Approximate
                    )
            
            # 4. Radar receives feedback
            time.sleep(0.05)
            
            feedback = radar_feedback_subscriber.get_next_message(timeout=0.2)
            
            if feedback:
                # Log feedback received
                debug_monitor.log_message_received(
                    message_type='FEEDBACK_RX',
                    message_id=f"feedback_{frame_id}",
                    frame_id=frame_id,
                    receiver='RADAR'
                )
            
            # Visualize frame flow
            debug_monitor.visualize_data_flow(frame_id)
        
        # Complete flow visualization
        debug_monitor.visualize_data_flow()
        
        # Print summary
        debug_monitor.print_summary()
        
        # Save debug log
        debug_monitor.save_debug_log()
        
        print("\n✓ DEBUG MODE DEMO COMPLETE\n")
        
    finally:
        # Cleanup
        radar_publisher.stop()
        ew_subscriber.stop()
        radar_feedback_subscriber.stop()
        
        for d in [intel_dir, feedback_dir]:
            if d.exists():
                shutil.rmtree(d)


if __name__ == '__main__':
    demo_debug_mode()
