"""
Event Bus Intelligence Subscriber
==================================

Receives and validates radar intelligence packets from defense_core event bus.
Non-blocking polling with graceful handling of missing/delayed data.

Author: Defense Systems Integration Team
"""

import logging
import time
from pathlib import Path
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass, field
import threading
import queue

from defense_core import get_defense_bus, RadarIntelligencePacket
from interfaces.subscriber import ReceivedIntelligence, SubscriberStatistics
from interfaces.message_schema import (
    Track, ThreatAssessment, SceneContext, TacticalPictureMessage
)

logger = logging.getLogger(__name__)


class EventBusIntelligenceSubscriber:
    """
    Non-blocking intelligence packet receiver from event bus.
    
    Polls defense_core event bus for radar intelligence packets,
    validates schema, and queues for processing.
    
    Design principles:
    - Never blocks EW processing
    - Validates all incoming packets
    - Detects missing/stale data
    - Comprehensive logging
    - Graceful degradation
    """
    
    def __init__(self,
                 staleness_threshold_s: float = 2.0,
                 poll_interval_s: float = 0.05,
                 message_callback: Optional[Callable] = None,
                 log_all_updates: bool = True):
        """
        Initialize event bus intelligence subscriber.
        
        Args:
            staleness_threshold_s: Messages older than this are flagged as stale
            poll_interval_s: How often to poll event bus (default 50ms)
            message_callback: Optional callback for each valid message
            log_all_updates: Log every received intelligence update
        """
        self.staleness_threshold = staleness_threshold_s
        self.poll_interval = poll_interval_s
        self.message_callback = message_callback
        self.log_all_updates = log_all_updates
        
        # Get global defense bus
        self.defense_bus = get_defense_bus()
        
        # Message queue for processing
        self.message_queue = queue.Queue(maxsize=100)
        
        # Statistics
        self.stats = SubscriberStatistics()
        self.stats.start_time = time.time()
        
        # Worker thread
        self.running = False
        self.poll_thread = None
        
        logger.info("Event bus intelligence subscriber initialized")
    
    def start(self):
        """Start the background polling thread."""
        if self.running:
            logger.warning("Event bus subscriber already running")
            return
        
        self.running = True
        self.poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.poll_thread.start()
        logger.info("Event bus intelligence subscriber started")
    
    def stop(self):
        """Stop the polling thread."""
        if not self.running:
            return
        
        self.running = False
        if self.poll_thread:
            self.poll_thread.join(timeout=2.0)
        logger.info(f"Event bus intelligence subscriber stopped. Stats: {self.stats.to_dict()}")
    
    def _poll_loop(self):
        """Background thread that polls event bus for intelligence packets."""
        logger.info("Event bus polling thread started")
        
        while self.running:
            try:
                # Non-blocking receive with timeout
                # This prevents busy waiting while allowing responsive polling
                packet = self.defense_bus.receive_intelligence(timeout=self.poll_interval)
                
                if packet:
                    self._process_packet(packet)
                
                # No explicit sleep needed - timeout handles delay
                
            except Exception as e:
                logger.error(f"Error in event bus poll loop: {e}", exc_info=True)
                time.sleep(self.poll_interval)
        
        logger.info("Event bus polling thread stopped")
    
    def _process_packet(self, packet: RadarIntelligencePacket):
        """
        Process a received intelligence packet.
        
        Validates, checks staleness, converts to legacy format, and queues.
        """
        try:
            reception_time = time.time()
            
            # Convert to ReceivedIntelligence format (for compatibility)
            received = self._packet_to_received_intelligence(packet, reception_time)
            
            # Update statistics
            self.stats.messages_received += 1
            self.stats.last_message_time = reception_time
            
            if received.is_valid:
                self.stats.messages_valid += 1
            else:
                self.stats.messages_invalid += 1
                self.stats.validation_errors += len(received.validation_errors)
            
            if received.is_stale:
                self.stats.messages_stale += 1
            
            # Log reception
            self._log_intelligence_reception(received)
            
            # Queue for processing
            try:
                self.message_queue.put_nowait(received)
            except queue.Full:
                logger.warning("[INTEL-WARN] Intelligence message queue full - dropping message")
            
            # Call callback if provided
            if self.message_callback and received.is_valid:
                try:
                    self.message_callback(received)
                except Exception as e:
                    logger.error(f"Message callback failed: {e}")
        
        except Exception as e:
            logger.error(f"[INTEL-ERROR] Failed to process packet: {e}", exc_info=True)
            self.stats.messages_invalid += 1
    
    def _packet_to_received_intelligence(self,
                                         packet: RadarIntelligencePacket,
                                         reception_time: float) -> ReceivedIntelligence:
        """
        Convert RadarIntelligencePacket to ReceivedIntelligence.
        
        Maintains compatibility with existing EW pipeline.
        """
        # Convert defense_core tracks to legacy format
        legacy_tracks = []
        for track in packet.tracks:
            legacy_track = Track(
                track_id=track.track_id,
                range_m=track.range_m,
                azimuth_deg=track.azimuth_deg,
                radial_velocity_m_s=track.radial_velocity_m_s,
                track_quality=track.track_quality,
                track_age_frames=track.track_age_frames,
                last_update_timestamp=track.last_update_timestamp,
                elevation_deg=track.elevation_deg if hasattr(track, 'elevation_deg') else None
            )
            legacy_tracks.append(legacy_track)
        
        # Convert defense_core threats to legacy format
        legacy_threats = []
        for threat in packet.threat_assessments:
            legacy_threat = ThreatAssessment(
                track_id=threat.track_id,
                threat_class=threat.threat_class,
                target_type=threat.target_type,
                classification_confidence=threat.classification_confidence,
                threat_priority=threat.threat_priority,
                engagement_recommendation=threat.engagement_recommendation,
                classification_uncertainty=threat.classification_uncertainty if hasattr(threat, 'classification_uncertainty') else (1.0 - threat.classification_confidence)
            )
            legacy_threats.append(legacy_threat)
        
        # Convert scene context
        legacy_scene = None
        if packet.scene_context:
            legacy_scene = SceneContext(
                scene_type=packet.scene_context.scene_type,
                clutter_ratio=packet.scene_context.clutter_ratio,
                mean_snr_db=packet.scene_context.mean_snr_db,
                num_confirmed_tracks=packet.scene_context.num_confirmed_tracks,
                weather_condition=packet.scene_context.weather_condition if hasattr(packet.scene_context, 'weather_condition') else None
            )
        
        # Create legacy tactical picture message
        legacy_message = TacticalPictureMessage(
            message_id=packet.message_id,
            timestamp=packet.timestamp,
            frame_id=packet.frame_id,
            sensor_id=packet.sensor_id,
            tracks=legacy_tracks,
            threat_assessments=legacy_threats,
            scene_context=legacy_scene
        )
        
        # Calculate age and staleness
        age_seconds = reception_time - packet.timestamp
        is_stale = age_seconds > self.staleness_threshold
        
        # Create received intelligence wrapper
        return ReceivedIntelligence(
            message=legacy_message,
            reception_timestamp=reception_time,
            file_path=f"event_bus://{packet.sensor_id}/frame_{packet.frame_id}",
            age_seconds=age_seconds,
            is_stale=is_stale,
            validation_errors=[]  # Already validated by defense_core
        )
    
    def _log_intelligence_reception(self, received: ReceivedIntelligence):
        """Log intelligence reception with appropriate level."""
        msg = received.message
        
        # Build log message
        log_msg = (f"[INTEL-RX-BUS] Frame {msg.frame_id} from {msg.sensor_id}: "
                  f"{len(msg.tracks)} tracks, {len(msg.threat_assessments)} threats")
        
        if msg.scene_context:
            log_msg += f", Scene={msg.scene_context.scene_type}, SNR={msg.scene_context.mean_snr_db:.1f}dB"
        
        log_msg += f", Age={received.age_seconds:.3f}s"
        
        # Log based on quality
        if not received.is_valid:
            logger.warning(f"{log_msg} [VALIDATION FAILED]")
            for error in received.validation_errors:
                logger.warning(f"[INTEL-WARN] Validation error: {error}")
        elif received.is_stale:
            logger.warning(f"{log_msg} [STALE - threshold {self.staleness_threshold}s]")
        elif self.log_all_updates:
            logger.info(log_msg)
    
    def get_next_message(self, timeout: Optional[float] = None) -> Optional[ReceivedIntelligence]:
        """
        Get next intelligence message from queue.
        
        Args:
            timeout: Max time to wait for message (None = non-blocking)
            
        Returns:
            ReceivedIntelligence or None if queue empty
        """
        try:
            if timeout is None:
                return self.message_queue.get_nowait()
            else:
                return self.message_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_statistics(self) -> Dict:
        """Get subscriber statistics."""
        return self.stats.to_dict()
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
