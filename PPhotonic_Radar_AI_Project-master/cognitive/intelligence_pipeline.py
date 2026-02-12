"""
EW Intelligence Pipeline
========================

High-level pipeline orchestrating intelligence reception and cognitive processing.
Integrates subscriber, validation, and cognitive engine.

Author: Cognitive EW Systems Team
"""

import logging
import time
from typing import Optional, Dict, List
from pathlib import Path

from interfaces.subscriber import IntelligenceSubscriber, NullSubscriber, ReceivedIntelligence
from interfaces.message_schema import TacticalPictureMessage
from cognitive.engine import CognitiveRadarEngine, SituationAssessment, AdaptationCommand

logger = logging.getLogger(__name__)


class EWIntelligencePipeline:
    """
    Complete intelligence ingestion and processing pipeline for Cognitive EW-AI.
    
    Workflow:
    1. Subscriber receives intelligence files
    2. Validate schema and quality
    3. Extract tracks and threats
    4. Feed to cognitive engine
    5. Generate EW adaptations
    6. Log all processing
    """
    
    def __init__(self,
                 enable_ingestion: bool = True,
                 ingestion_mode: str = 'file',
                 source_directory: str = 'runtime/intelligence',
                 staleness_threshold_s: float = 2.0,
                 poll_interval_s: float = 0.1,
                 log_all_updates: bool = True):
        """
        Initialize EW intelligence pipeline.
        
        Args:
            enable_ingestion: Enable/disable intelligence ingestion
            ingestion_mode: 'file' (legacy) or 'event_bus' (new)
            source_directory: Directory to monitor for intelligence (file mode only)
            staleness_threshold_s: Staleness threshold in seconds
            poll_interval_s: Polling interval for new data
            log_all_updates: Log every intelligence update
        """
        self.enable_ingestion = enable_ingestion
        self.ingestion_mode = ingestion_mode
        
        # Initialize cognitive engine
        self.cognitive_engine = CognitiveRadarEngine()
        
        # Initialize subscriber based on mode
        if enable_ingestion:
            if ingestion_mode == 'event_bus':
                from interfaces.event_bus_subscriber import EventBusIntelligenceSubscriber
                self.subscriber = EventBusIntelligenceSubscriber(
                    staleness_threshold_s=staleness_threshold_s,
                    poll_interval_s=poll_interval_s,
                    message_callback=self._on_intelligence_received,
                    log_all_updates=log_all_updates
                )
                logger.info("EW Intelligence Pipeline initialized with EVENT BUS mode")
            else:  # file mode (legacy)
                self.subscriber = IntelligenceSubscriber(
                    source_directory=source_directory,
                    staleness_threshold_s=staleness_threshold_s,
                    poll_interval_s=poll_interval_s,
                    message_callback=self._on_intelligence_received,
                    log_all_updates=log_all_updates
                )
                logger.info(f"EW Intelligence Pipeline initialized with FILE mode: {source_directory}")
        else:
            self.subscriber = NullSubscriber()
            logger.info("EW Intelligence Pipeline initialized with ingestion DISABLED")
        
        # Initialize feedback publisher
        from cognitive.ew_feedback_publisher import EWFeedbackPublisher
        self.feedback_publisher = EWFeedbackPublisher(
            effector_id='COGNITIVE_EW_01',
            export_directory='runtime/ew_feedback',
            enable_export=True,
            enable_event_bus=enable_ingestion and ingestion_mode == 'event_bus',
            log_all_transmissions=log_all_updates
        )
        
        # Processing statistics
        self.messages_processed = 0
        self.messages_rejected = 0
        self.last_valid_intelligence: Optional[ReceivedIntelligence] = None
        self.last_assessment: Optional[SituationAssessment] = None
        self.last_adaptation_command: Optional[AdaptationCommand] = None

    
    def start(self):
        """Start the intelligence pipeline."""
        self.subscriber.start()
        logger.info("EW Intelligence Pipeline started")
    
    def stop(self):
        """Stop the intelligence pipeline."""
        self.subscriber.stop()
        logger.info(f"EW Intelligence Pipeline stopped. Processed {self.messages_processed} messages")
    
    def _on_intelligence_received(self, received: ReceivedIntelligence):
        """
        Callback invoked when intelligence is received.
        
        Validates quality and processes through cognitive engine.
        """
        try:
            # Validate message quality
            quality = self._validate_intelligence_quality(received)
            
            if not quality['acceptable']:
                self.messages_rejected += 1
                logger.warning(f"[INTEL-REJECT] {quality['reason']}")
                return
            
            # Process through cognitive engine
            assessment = self._process_intelligence(received.message)
            
            # Generate adaptation command
            adaptation_cmd = self.cognitive_engine.decide_adaptation(assessment)
            
            # Publish attack packet to radar
            if received.message.threat_assessments:
                self.feedback_publisher.publish_attack_packet(
                    threat_assessments=received.message.threat_assessments,
                    adaptation_command=adaptation_cmd,
                    tracks=received.message.tracks
                )
            
            # Store for reference
            self.last_valid_intelligence = received
            self.last_assessment = assessment
            self.last_adaptation_command = adaptation_cmd
            self.messages_processed += 1
            
            logger.info(f"[INTEL-PROCESSED] Frame {received.message.frame_id}: "
                       f"Scene={assessment.scene_type.value}, "
                       f"Tracks={assessment.num_confirmed_tracks}, "
                       f"Confidence={assessment.mean_classification_confidence:.2f}")
            
        except Exception as e:
            logger.error(f"[INTEL-ERROR] Failed to process intelligence: {e}", exc_info=True)
            self.messages_rejected += 1
    
    def _validate_intelligence_quality(self, received: ReceivedIntelligence) -> Dict:
        """
        Validate quality and freshness of received intelligence.
        
        Returns:
            Dict with 'acceptable' (bool) and 'reason' (str)
        """
        # Check schema validation
        if not received.is_valid:
            return {
                'acceptable': False,
                'reason': f"Schema validation failed: {received.validation_errors}"
            }
        
        # Check staleness
        if received.is_stale:
            logger.warning(f"[INTEL-WARN] Stale intelligence: {received.age_seconds:.2f}s old "
                          f"(threshold: {self.subscriber.staleness_threshold}s)")
            # Still process stale data, but log warning
        
        # Check for missing critical data
        msg = received.message
        if len(msg.tracks) == 0 and len(msg.threat_assessments) == 0:
            logger.info(f"[INTEL-INFO] Empty intelligence (no tracks/threats) - likely search mode")
            # Still acceptable - might be search mode
        
        return {'acceptable': True, 'reason': 'OK'}
    
    def _process_intelligence(self, message: TacticalPictureMessage) -> SituationAssessment:
        """
        Process tactical picture message through cognitive engine.
        
        Extracts data and creates situation assessment.
        """
        # Extract tracks for cognitive engine format
        tracks = []
        for track in message.tracks:
            tracks.append({
                'track_id': track.track_id,
                'state': 'CONFIRMED',  # Assume all exported tracks are confirmed
                'age': track.track_age_frames,
                'hits': track.track_age_frames,  # Approximate
                'stability_score': track.track_quality,
                'velocity': track.radial_velocity_m_s,
                'range': track.range_m
            })
        
        # Extract AI predictions from threat assessments
        ai_predictions = []
        for threat in message.threat_assessments:
            ai_predictions.append({
                'track_id': threat.track_id,
                'class': threat.target_type,
                'confidence': threat.classification_confidence,
                'class_probabilities': [threat.classification_confidence, 
                                       1.0 - threat.classification_confidence]
            })
        
        # Extract detections (if available)
        detections = []
        if message.detections:
            for det in message.detections:
                detections.append((det.range_m, det.doppler_velocity_m_s))
        
        # Create situation assessment
        assessment = self.cognitive_engine.assess_situation(
            frame_id=message.frame_id,
            timestamp=message.timestamp,
            detections=detections,
            tracks=tracks,
            ai_predictions=ai_predictions,
            rd_map=None  # Not available from intelligence message
        )
        
        # Override with scene context if available
        if message.scene_context:
            assessment.num_confirmed_tracks = message.scene_context.num_confirmed_tracks
            assessment.clutter_ratio = message.scene_context.clutter_ratio
            assessment.estimated_snr_db = message.scene_context.mean_snr_db
        
        return assessment
    
    def process_next_intelligence(self, timeout: Optional[float] = None) -> Optional[SituationAssessment]:
        """
        Process next intelligence message from queue.
        
        Args:
            timeout: Max time to wait for message
            
        Returns:
            SituationAssessment or None if no message available
        """
        received = self.subscriber.get_next_message(timeout=timeout)
        if received is None:
            return None
        
        self._on_intelligence_received(received)
        return self.last_assessment
    
    def get_latest_assessment(self) -> Optional[SituationAssessment]:
        """Get the most recent situation assessment."""
        return self.last_assessment
    
    def get_statistics(self) -> Dict:
        """Get pipeline statistics."""
        subscriber_stats = self.subscriber.get_statistics()
        
        return {
            'ingestion_mode': self.ingestion_mode if self.enable_ingestion else 'disabled',
            'subscriber': subscriber_stats,
            'pipeline': {
                'messages_processed': self.messages_processed,
                'messages_rejected': self.messages_rejected,
                'has_valid_intelligence': self.last_valid_intelligence is not None,
                'last_intelligence_age_s': (time.time() - self.last_valid_intelligence.reception_timestamp)
                    if self.last_valid_intelligence else None
            },
            'cognitive_engine': self.cognitive_engine.get_state_summary()
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
