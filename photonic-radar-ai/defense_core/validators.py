"""
Defense Core - Validators
==========================

Message validation utilities for defense system integration.
Ensures data integrity and contract compliance.

Author: Defense Core Team
"""

import logging
from typing import Tuple, List, Optional
from defense_core.schemas import (
    TacticalPictureMessage, EWFeedbackMessage,
    Track, ThreatAssessment, Countermeasure, EngagementStatus,
    ThreatClass, TargetType, EngagementRecommendation,
    CountermeasureType, EngagementState
)

logger = logging.getLogger(__name__)


# ============================================================================
# Validation Rules
# ============================================================================

class ValidationRules:
    """Validation rules for defense messages."""
    
    # Track validation
    MIN_RANGE_M = 0.0
    MAX_RANGE_M = 100000.0  # 100 km
    MIN_AZIMUTH_DEG = -180.0
    MAX_AZIMUTH_DEG = 360.0
    MIN_ELEVATION_DEG = -90.0
    MAX_ELEVATION_DEG = 90.0
    MIN_VELOCITY_M_S = -1000.0  # Mach 3
    MAX_VELOCITY_M_S = 1000.0
    MIN_QUALITY = 0.0
    MAX_QUALITY = 1.0
    
    # Threat assessment validation
    MIN_CONFIDENCE = 0.0
    MAX_CONFIDENCE = 1.0
    MIN_PRIORITY = 0
    MAX_PRIORITY = 10
    
    # Countermeasure validation
    MIN_POWER_DBM = 0.0
    MAX_POWER_DBM = 60.0  # 1 MW
    MIN_FREQUENCY_MHZ = 1000.0  # 1 GHz
    MAX_FREQUENCY_MHZ = 100000.0  # 100 GHz
    MIN_EFFECTIVENESS = 0.0
    MAX_EFFECTIVENESS = 1.0
    
    # Message age validation
    MAX_MESSAGE_AGE_S = 5.0  # Messages older than 5s are stale


# ============================================================================
# Track Validation
# ============================================================================

def validate_track(track: Track) -> Tuple[bool, List[str]]:
    """
    Validate a track message.
    
    Args:
        track: Track to validate
        
    Returns:
        (is_valid, error_messages)
    """
    errors = []
    
    # Range validation
    if not (ValidationRules.MIN_RANGE_M <= track.range_m <= ValidationRules.MAX_RANGE_M):
        errors.append(f"Track {track.track_id}: Invalid range {track.range_m}m")
    
    # Azimuth validation
    if not (ValidationRules.MIN_AZIMUTH_DEG <= track.azimuth_deg <= ValidationRules.MAX_AZIMUTH_DEG):
        errors.append(f"Track {track.track_id}: Invalid azimuth {track.azimuth_deg}°")
    
    # Elevation validation
    if not (ValidationRules.MIN_ELEVATION_DEG <= track.elevation_deg <= ValidationRules.MAX_ELEVATION_DEG):
        errors.append(f"Track {track.track_id}: Invalid elevation {track.elevation_deg}°")
    
    # Velocity validation
    if not (ValidationRules.MIN_VELOCITY_M_S <= track.radial_velocity_m_s <= ValidationRules.MAX_VELOCITY_M_S):
        errors.append(f"Track {track.track_id}: Invalid velocity {track.radial_velocity_m_s}m/s")
    
    # Quality validation
    if not (ValidationRules.MIN_QUALITY <= track.track_quality <= ValidationRules.MAX_QUALITY):
        errors.append(f"Track {track.track_id}: Invalid quality {track.track_quality}")
    
    # Track age validation
    if track.track_age_frames < 0:
        errors.append(f"Track {track.track_id}: Negative track age")
    
    return len(errors) == 0, errors


# ============================================================================
# Threat Assessment Validation
# ============================================================================

def validate_threat_assessment(threat: ThreatAssessment) -> Tuple[bool, List[str]]:
    """
    Validate a threat assessment.
    
    Args:
        threat: Threat assessment to validate
        
    Returns:
        (is_valid, error_messages)
    """
    errors = []
    
    # Threat class validation
    valid_classes = [e.value for e in ThreatClass]
    if threat.threat_class not in valid_classes:
        errors.append(f"Threat {threat.track_id}: Invalid threat class '{threat.threat_class}'")
    
    # Target type validation
    valid_types = [e.value for e in TargetType]
    if threat.target_type not in valid_types:
        errors.append(f"Threat {threat.track_id}: Invalid target type '{threat.target_type}'")
    
    # Confidence validation
    if not (ValidationRules.MIN_CONFIDENCE <= threat.classification_confidence <= ValidationRules.MAX_CONFIDENCE):
        errors.append(f"Threat {threat.track_id}: Invalid confidence {threat.classification_confidence}")
    
    # Priority validation
    if not (ValidationRules.MIN_PRIORITY <= threat.threat_priority <= ValidationRules.MAX_PRIORITY):
        errors.append(f"Threat {threat.track_id}: Invalid priority {threat.threat_priority}")
    
    # Engagement recommendation validation
    valid_recommendations = [e.value for e in EngagementRecommendation]
    if threat.engagement_recommendation not in valid_recommendations:
        errors.append(f"Threat {threat.track_id}: Invalid recommendation '{threat.engagement_recommendation}'")
    
    return len(errors) == 0, errors


# ============================================================================
# Tactical Picture Validation
# ============================================================================

def validate_tactical_picture(message: TacticalPictureMessage) -> Tuple[bool, List[str]]:
    """
    Validate a tactical picture message.
    
    Args:
        message: Tactical picture message to validate
        
    Returns:
        (is_valid, error_messages)
    """
    errors = []
    
    # Message ID validation
    if not message.message_id:
        errors.append("Missing message ID")
    
    # Timestamp validation
    if message.timestamp <= 0:
        errors.append("Invalid timestamp")
    
    # Sensor ID validation
    if not message.sensor_id:
        errors.append("Missing sensor ID")
    
    # Frame ID validation
    if message.frame_id < 0:
        errors.append("Negative frame ID")
    
    # Tracks validation
    if not message.tracks:
        logger.warning("Tactical picture has no tracks")
    
    for track in message.tracks:
        is_valid, track_errors = validate_track(track)
        if not is_valid:
            errors.extend(track_errors)
    
    # Threat assessments validation
    for threat in message.threat_assessments:
        is_valid, threat_errors = validate_threat_assessment(threat)
        if not is_valid:
            errors.extend(threat_errors)
    
    # Scene context validation
    if message.scene_context.clutter_ratio < 0 or message.scene_context.clutter_ratio > 1:
        errors.append(f"Invalid clutter ratio {message.scene_context.clutter_ratio}")
    
    if message.scene_context.num_confirmed_tracks < 0:
        errors.append("Negative confirmed tracks count")
    
    return len(errors) == 0, errors


# ============================================================================
# Countermeasure Validation
# ============================================================================

def validate_countermeasure(cm: Countermeasure) -> Tuple[bool, List[str]]:
    """
    Validate a countermeasure.
    
    Args:
        cm: Countermeasure to validate
        
    Returns:
        (is_valid, error_messages)
    """
    errors = []
    
    # CM type validation
    valid_types = [e.value for e in CountermeasureType]
    if cm.cm_type not in valid_types:
        errors.append(f"CM {cm.countermeasure_id}: Invalid type '{cm.cm_type}'")
    
    # Power validation
    if cm.power_level_dbm is not None:
        if not (ValidationRules.MIN_POWER_DBM <= cm.power_level_dbm <= ValidationRules.MAX_POWER_DBM):
            errors.append(f"CM {cm.countermeasure_id}: Invalid power {cm.power_level_dbm}dBm")
    
    # Frequency validation
    if cm.frequency_mhz is not None:
        if not (ValidationRules.MIN_FREQUENCY_MHZ <= cm.frequency_mhz <= ValidationRules.MAX_FREQUENCY_MHZ):
            errors.append(f"CM {cm.countermeasure_id}: Invalid frequency {cm.frequency_mhz}MHz")
    
    # Effectiveness validation
    if cm.effectiveness_score is not None:
        if not (ValidationRules.MIN_EFFECTIVENESS <= cm.effectiveness_score <= ValidationRules.MAX_EFFECTIVENESS):
            errors.append(f"CM {cm.countermeasure_id}: Invalid effectiveness {cm.effectiveness_score}")
    
    # Timing validation
    if cm.start_time <= 0:
        errors.append(f"CM {cm.countermeasure_id}: Invalid start time")
    
    if cm.end_time is not None and cm.end_time < cm.start_time:
        errors.append(f"CM {cm.countermeasure_id}: End time before start time")
    
    return len(errors) == 0, errors


# ============================================================================
# EW Feedback Validation
# ============================================================================

def validate_ew_feedback(message: EWFeedbackMessage) -> Tuple[bool, List[str]]:
    """
    Validate an EW feedback message.
    
    Args:
        message: EW feedback message to validate
        
    Returns:
        (is_valid, error_messages)
    """
    errors = []
    
    # Message ID validation
    if not message.message_id:
        errors.append("Missing message ID")
    
    # Timestamp validation
    if message.timestamp <= 0:
        errors.append("Invalid timestamp")
    
    # Effector ID validation
    if not message.effector_id:
        errors.append("Missing effector ID")
    
    # Countermeasures validation
    for cm in message.active_countermeasures:
        is_valid, cm_errors = validate_countermeasure(cm)
        if not is_valid:
            errors.extend(cm_errors)
    
    # Engagement status validation
    for engagement in message.engagement_status:
        valid_states = [e.value for e in EngagementState]
        if engagement.engagement_state not in valid_states:
            errors.append(f"Engagement {engagement.track_id}: Invalid state '{engagement.engagement_state}'")
        
        if engagement.kill_probability is not None:
            if not (0.0 <= engagement.kill_probability <= 1.0):
                errors.append(f"Engagement {engagement.track_id}: Invalid kill probability")
    
    # Effector health validation
    if message.effector_health is not None:
        if not (0.0 <= message.effector_health <= 1.0):
            errors.append(f"Invalid effector health {message.effector_health}")
    
    return len(errors) == 0, errors


# ============================================================================
# Message Age Validation
# ============================================================================

def is_message_stale(message_timestamp: float, current_time: float) -> bool:
    """
    Check if a message is stale.
    
    Args:
        message_timestamp: Message timestamp
        current_time: Current time
        
    Returns:
        True if message is stale
    """
    age = current_time - message_timestamp
    return age > ValidationRules.MAX_MESSAGE_AGE_S
