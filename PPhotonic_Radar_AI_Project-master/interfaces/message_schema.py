"""
Sensor-Effector Message Schema
===============================

Implements the tactical picture message format for radar intelligence export.
Based on the sensor-effector interface specification.

Author: Defense Systems Integration Team
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from enum import Enum
import time
import uuid
import json


# ============================================================================
# Enumerations
# ============================================================================

class ThreatClass(Enum):
    """Threat classification categories."""
    HOSTILE = "HOSTILE"
    FRIENDLY = "FRIENDLY"
    NEUTRAL = "NEUTRAL"
    UNKNOWN = "UNKNOWN"


class TargetType(Enum):
    """Target type classifications."""
    AIRCRAFT = "AIRCRAFT"
    MISSILE = "MISSILE"
    UAV = "UAV"
    GROUND_VEHICLE = "GROUND_VEHICLE"
    SHIP = "SHIP"
    UNKNOWN = "UNKNOWN"


class EngagementRecommendation(Enum):
    """Engagement action recommendations."""
    ENGAGE = "ENGAGE"
    MONITOR = "MONITOR"
    IGNORE = "IGNORE"


class SceneType(Enum):
    """Scene classification types."""
    SEARCH = "SEARCH"
    SPARSE = "SPARSE"
    TRACKING = "TRACKING"
    DENSE = "DENSE"
    CLUTTERED = "CLUTTERED"


class OperationalStatus(Enum):
    """System operational status."""
    OPERATIONAL = "OPERATIONAL"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"


# ============================================================================
# Core Data Structures
# ============================================================================

@dataclass
class Track:
    """
    Confirmed kinematic track from Kalman filter.
    
    Mandatory fields ensure minimum operational capability.
    Optional fields provide enhanced situational awareness.
    """
    # Mandatory fields
    track_id: int
    range_m: float
    azimuth_deg: float
    radial_velocity_m_s: float
    track_quality: float  # [0.0, 1.0]
    track_age_frames: int
    last_update_timestamp: float
    
    # Optional fields
    elevation_deg: Optional[float] = None
    radial_acceleration_m_s2: Optional[float] = None
    position_x_m: Optional[float] = None
    position_y_m: Optional[float] = None
    velocity_x_m_s: Optional[float] = None
    velocity_y_m_s: Optional[float] = None
    covariance_matrix: Optional[List[float]] = None  # Flattened 3x3 or 6x6
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class Detection:
    """Raw radar detection (CFAR output)."""
    detection_id: int
    range_m: float
    doppler_velocity_m_s: float
    snr_db: float
    azimuth_deg: Optional[float] = None
    amplitude: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ThreatAssessment:
    """
    AI-driven threat classification and priority.
    
    Includes confidence and uncertainty metrics as required.
    """
    # Mandatory fields
    track_id: int
    threat_class: str  # ThreatClass enum value
    target_type: str   # TargetType enum value
    classification_confidence: float  # [0.0, 1.0] - AI model confidence
    threat_priority: int  # [1, 10] - 10 is highest
    engagement_recommendation: str  # EngagementRecommendation enum value
    
    # Optional fields
    kinematic_signature: Optional[str] = None
    rcs_estimate_dbsm: Optional[float] = None
    predicted_trajectory: Optional[List[Dict]] = None
    
    # Uncertainty metrics
    classification_uncertainty: Optional[float] = None  # Entropy or variance
    position_uncertainty_m: Optional[float] = None  # From covariance
    velocity_uncertainty_m_s: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class SceneContext:
    """Environmental and clutter characterization."""
    scene_type: str  # SceneType enum value
    clutter_ratio: float  # [0.0, 1.0]
    mean_snr_db: float
    num_confirmed_tracks: int
    num_provisional_tracks: Optional[int] = None
    weather_condition: Optional[str] = None
    jamming_detected: Optional[bool] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class SensorHealth:
    """Sensor system status and diagnostics."""
    operational_status: str  # OperationalStatus enum value
    transmit_power_dbm: Optional[float] = None
    receiver_noise_figure_db: Optional[float] = None
    processing_latency_ms: Optional[float] = None
    cpu_utilization_pct: Optional[float] = None
    error_flags: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class TacticalPictureMessage:
    """
    Complete tactical picture message from sensor to effector.
    
    This is the primary message exported at every simulation tick.
    """
    # Mandatory fields
    message_id: str
    timestamp: float  # UNIX epoch seconds
    frame_id: int
    sensor_id: str
    tracks: List[Track]
    threat_assessments: List[ThreatAssessment]
    
    # Optional fields
    detections: Optional[List[Detection]] = None
    scene_context: Optional[SceneContext] = None
    sensor_health: Optional[SensorHealth] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entire message to dictionary."""
        result = {
            'message_id': self.message_id,
            'timestamp': self.timestamp,
            'frame_id': self.frame_id,
            'sensor_id': self.sensor_id,
            'tracks': [t.to_dict() for t in self.tracks],
            'threat_assessments': [ta.to_dict() for ta in self.threat_assessments]
        }
        
        if self.detections is not None:
            result['detections'] = [d.to_dict() for d in self.detections]
        if self.scene_context is not None:
            result['scene_context'] = self.scene_context.to_dict()
        if self.sensor_health is not None:
            result['sensor_health'] = self.sensor_health.to_dict()
            
        return result
    
    def to_json(self, indent: Optional[int] = None) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def create(cls, 
               frame_id: int,
               sensor_id: str,
               tracks: List[Track],
               threat_assessments: List[ThreatAssessment],
               detections: Optional[List[Detection]] = None,
               scene_context: Optional[SceneContext] = None,
               sensor_health: Optional[SensorHealth] = None) -> 'TacticalPictureMessage':
        """
        Factory method to create a tactical picture message with auto-generated ID and timestamp.
        """
        return cls(
            message_id=str(uuid.uuid4()),
            timestamp=time.time(),
            frame_id=frame_id,
            sensor_id=sensor_id,
            tracks=tracks,
            threat_assessments=threat_assessments,
            detections=detections,
            scene_context=scene_context,
            sensor_health=sensor_health
        )


# ============================================================================
# Utility Functions
# ============================================================================

def validate_tactical_message(msg: TacticalPictureMessage) -> tuple[bool, List[str]]:
    """
    Validate a tactical picture message for completeness and correctness.
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Check mandatory fields
    if not msg.message_id:
        errors.append("Missing message_id")
    if msg.timestamp <= 0:
        errors.append("Invalid timestamp")
    if msg.frame_id < 0:
        errors.append("Invalid frame_id")
    if not msg.sensor_id:
        errors.append("Missing sensor_id")
    
    # Validate tracks
    for i, track in enumerate(msg.tracks):
        if track.track_quality < 0.0 or track.track_quality > 1.0:
            errors.append(f"Track {i}: quality out of range [0,1]")
        if track.range_m < 0:
            errors.append(f"Track {i}: negative range")
    
    # Validate threat assessments
    for i, threat in enumerate(msg.threat_assessments):
        if threat.classification_confidence < 0.0 or threat.classification_confidence > 1.0:
            errors.append(f"Threat {i}: confidence out of range [0,1]")
        if threat.threat_priority < 1 or threat.threat_priority > 10:
            errors.append(f"Threat {i}: priority out of range [1,10]")
    
    return (len(errors) == 0, errors)

# ============================================================================
# EW Feedback Messages (Effector → Sensor)
# ============================================================================

class CountermeasureType(Enum):
    """Electronic warfare countermeasure types."""
    NOISE_JAM = "NOISE_JAM"
    DECEPTION_JAM = "DECEPTION_JAM"
    CHAFF = "CHAFF"
    FLARE = "FLARE"
    CYBER = "CYBER"


class EngagementState(Enum):
    """Engagement status states."""
    MONITORING = "MONITORING"
    ENGAGING = "ENGAGING"
    NEUTRALIZED = "NEUTRALIZED"
    LOST = "LOST"


@dataclass
class Countermeasure:
    """
    Electronic warfare countermeasure being applied.
    
    Describes active EW actions against specific tracks.
    """
    # Mandatory fields
    countermeasure_id: int
    target_track_id: int
    cm_type: str  # CountermeasureType enum value
    start_time: float  # UNIX epoch seconds
    
    # Optional fields
    power_level_dbm: Optional[float] = None
    frequency_mhz: Optional[float] = None
    bandwidth_mhz: Optional[float] = None
    effectiveness_score: Optional[float] = None  # [0.0, 1.0] - estimated effectiveness
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class EngagementStatus:
    """
    Status of threat engagement by EW system.
    
    Provides feedback on how threats are being handled.
    """
    # Mandatory fields
    track_id: int
    engagement_state: str  # EngagementState enum value
    
    # Optional fields
    time_to_threat_s: Optional[float] = None
    kill_probability: Optional[float] = None  # [0.0, 1.0]
    countermeasures_active: Optional[int] = None  # Number of active CMs
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class EWFeedbackMessage:
    """
    Feedback message from EW effector to radar sensor.
    
    Provides information about active countermeasures and engagement status
    to enable radar to model expected degradation.
    """
    # Mandatory fields
    message_id: str
    timestamp: float  # UNIX epoch seconds
    effector_id: str
    active_countermeasures: List[Countermeasure]
    engagement_status: List[EngagementStatus]
    
    # Optional fields
    effector_health: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entire message to dictionary."""
        result = {
            'message_id': self.message_id,
            'timestamp': self.timestamp,
            'effector_id': self.effector_id,
            'active_countermeasures': [cm.to_dict() for cm in self.active_countermeasures],
            'engagement_status': [es.to_dict() for es in self.engagement_status]
        }
        
        if self.effector_health is not None:
            result['effector_health'] = self.effector_health
            
        return result
    
    def to_json(self, indent: Optional[int] = None) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def create(cls,
               effector_id: str,
               countermeasures: List[Countermeasure],
               engagements: List[EngagementStatus],
               effector_health: Optional[Dict[str, Any]] = None) -> 'EWFeedbackMessage':
        """
        Factory method to create EW feedback message with auto-generated ID and timestamp.
        """
        return cls(
            message_id=str(uuid.uuid4()),
            timestamp=time.time(),
            effector_id=effector_id,
            active_countermeasures=countermeasures,
            engagement_status=engagements,
            effector_health=effector_health
        )


def validate_ew_feedback_message(msg: EWFeedbackMessage) -> tuple[bool, List[str]]:
    """
    Validate an EW feedback message for completeness and correctness.
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Check mandatory fields
    if not msg.message_id:
        errors.append("Missing message_id")
    if msg.timestamp <= 0:
        errors.append("Invalid timestamp")
    if not msg.effector_id:
        errors.append("Missing effector_id")
    
    # Validate countermeasures
    for i, cm in enumerate(msg.active_countermeasures):
        if cm.effectiveness_score is not None:
            if cm.effectiveness_score < 0.0 or cm.effectiveness_score > 1.0:
                errors.append(f"Countermeasure {i}: effectiveness out of range [0,1]")
        if cm.start_time <= 0:
            errors.append(f"Countermeasure {i}: invalid start_time")
    
    # Validate engagement status
    for i, eng in enumerate(msg.engagement_status):
        if eng.kill_probability is not None:
            if eng.kill_probability < 0.0 or eng.kill_probability > 1.0:
                errors.append(f"Engagement {i}: kill_probability out of range [0,1]")
    
    return (len(errors) == 0, errors)
