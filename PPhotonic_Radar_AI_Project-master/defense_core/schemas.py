"""
Defense Core - Message Schemas
================================

Strongly-typed message schemas for defense system integration.
No dependencies on radar or EW internals.

Features:
- Field validation
- Required field enforcement
- Confidence metrics
- Timestamps
- Extensibility

Author: Defense Core Team
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Union
from enum import Enum
import time
import uuid
import json


# ============================================================================
# Validation Helpers
# ============================================================================

def _validate_range(value: float, min_val: float, max_val: float, field_name: str):
    """Validate numeric range."""
    if not (min_val <= value <= max_val):
        raise ValueError(f"{field_name} must be between {min_val} and {max_val}, got {value}")


def _validate_required(value: Any, field_name: str):
    """Validate required field."""
    if value is None:
        raise ValueError(f"{field_name} is required")


def _validate_confidence(value: float, field_name: str = "confidence"):
    """Validate confidence score (0.0 to 1.0)."""
    _validate_range(value, 0.0, 1.0, field_name)


# ============================================================================
# Enumerations
# ============================================================================

class ThreatClass(Enum):
    """Threat classification."""
    FRIENDLY = "FRIENDLY"
    NEUTRAL = "NEUTRAL"
    HOSTILE = "HOSTILE"
    UNKNOWN = "UNKNOWN"


class TargetType(Enum):
    """Target type classification."""
    AIRCRAFT = "AIRCRAFT"
    MISSILE = "MISSILE"
    UAV = "UAV"
    SHIP = "SHIP"
    GROUND = "GROUND"
    UNKNOWN = "UNKNOWN"


class EngagementRecommendation(Enum):
    """Engagement recommendation."""
    IGNORE = "IGNORE"
    MONITOR = "MONITOR"
    ENGAGE = "ENGAGE"


class CountermeasureType(Enum):
    """Countermeasure types."""
    NOISE_JAM = "NOISE_JAM"
    DECEPTION_JAM = "DECEPTION_JAM"
    CHAFF = "CHAFF"
    FLARE = "FLARE"
    CYBER = "CYBER"


class EngagementState(Enum):
    """Engagement state."""
    MONITORING = "MONITORING"
    ENGAGING = "ENGAGING"
    NEUTRALIZED = "NEUTRALIZED"
    LOST = "LOST"


# ============================================================================
# Sensor Messages (Radar → EW)
# ============================================================================

@dataclass
class Track:
    """
    Target track information with validation.
    
    Required fields: track_id, range_m, azimuth_deg
    Confidence metric: track_quality (0.0 to 1.0)
    """
    # Required fields
    track_id: int
    range_m: float
    azimuth_deg: float
    
    # Optional positional fields
    elevation_deg: float = 0.0
    radial_velocity_m_s: float = 0.0
    
    # Confidence metrics
    track_quality: float = 0.0  # 0.0 to 1.0
    position_uncertainty_m: float = 0.0  # CEP in meters
    velocity_uncertainty_m_s: float = 0.0
    
    # Metadata
    track_age_frames: int = 0
    last_update_timestamp: float = field(default_factory=time.time)
    
    # Extensibility: custom sensor data
    sensor_specific: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate fields after initialization."""
        _validate_required(self.track_id, "track_id")
        _validate_range(self.range_m, 0.0, 100000.0, "range_m")
        _validate_range(self.azimuth_deg, -180.0, 360.0, "azimuth_deg")
        _validate_range(self.elevation_deg, -90.0, 90.0, "elevation_deg")
        _validate_range(self.radial_velocity_m_s, -1000.0, 1000.0, "radial_velocity_m_s")
        _validate_confidence(self.track_quality, "track_quality")
        
        if self.track_age_frames < 0:
            raise ValueError("track_age_frames cannot be negative")
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ThreatAssessment:
    """
    AI threat assessment with confidence metrics.
    
    Required fields: track_id, threat_class, target_type, classification_confidence
    Confidence metrics: classification_confidence, classification_uncertainty
    """
    # Required fields
    track_id: int
    threat_class: str  # ThreatClass enum value
    target_type: str  # TargetType enum value
    classification_confidence: float  # 0.0 to 1.0
    
    # Threat metrics
    threat_priority: int = 0  # 0 (low) to 10 (critical)
    engagement_recommendation: str = "MONITOR"  # EngagementRecommendation enum value
    
    # Confidence metrics
    classification_uncertainty: float = 0.0  # 0.0 to 1.0
    model_confidence: float = 0.0  # AI model confidence (0.0 to 1.0)
    feature_quality: float = 0.0  # Feature extraction quality (0.0 to 1.0)
    
    # Threat timing
    time_to_threat_s: Optional[float] = None
    threat_velocity_m_s: Optional[float] = None
    
    # AI model metadata
    model_version: str = "unknown"
    inference_time_ms: float = 0.0
    
    # Timestamp
    assessment_timestamp: float = field(default_factory=time.time)
    
    # Extensibility: AI-specific data
    ai_specific: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate fields after initialization."""
        _validate_required(self.track_id, "track_id")
        _validate_required(self.threat_class, "threat_class")
        _validate_required(self.target_type, "target_type")
        _validate_confidence(self.classification_confidence, "classification_confidence")
        _validate_confidence(self.classification_uncertainty, "classification_uncertainty")
        _validate_confidence(self.model_confidence, "model_confidence")
        _validate_confidence(self.feature_quality, "feature_quality")
        _validate_range(self.threat_priority, 0, 10, "threat_priority")
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SceneContext:
    """Radar scene context."""
    scene_type: str
    clutter_ratio: float
    mean_snr_db: float
    num_confirmed_tracks: int
    weather_condition: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RadarIntelligencePacket:
    """
    Radar Intelligence Packet (Radar → EW).
    
    Strongly-typed message with validation and confidence metrics.
    
    Required fields: message_id, timestamp, frame_id, sensor_id
    Confidence metrics: overall_confidence, data_quality
    """
    # Message metadata (auto-generated)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    
    # Required identification
    frame_id: int = -1
    sensor_id: str = ""
    
    # Tactical data
    tracks: List[Track] = field(default_factory=list)
    threat_assessments: List[ThreatAssessment] = field(default_factory=list)
    scene_context: Optional['SceneContext'] = None
    
    # Confidence metrics
    overall_confidence: float = 0.0  # Overall packet confidence (0.0 to 1.0)
    data_quality: float = 0.0  # Data quality score (0.0 to 1.0)
    processing_latency_ms: float = 0.0  # Processing time
    
    # Sensor health
    sensor_health: float = 1.0  # Sensor health (0.0 to 1.0)
    sensor_mode: str = "NORMAL"  # Operating mode
    
    # Message versioning
    schema_version: str = "1.0.0"
    
    # Extensibility: sensor-specific metadata
    sensor_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate required fields."""
        _validate_required(self.message_id, "message_id")
        _validate_required(self.sensor_id, "sensor_id")
        
        if self.frame_id < 0:
            raise ValueError("frame_id must be non-negative")
        
        if self.timestamp <= 0:
            raise ValueError("timestamp must be positive")
        
        _validate_confidence(self.overall_confidence, "overall_confidence")
        _validate_confidence(self.data_quality, "data_quality")
        _validate_confidence(self.sensor_health, "sensor_health")
        
        # Validate tracks
        for track in self.tracks:
            if not isinstance(track, Track):
                raise TypeError("All tracks must be Track instances")
        
        # Validate threat assessments
        for threat in self.threat_assessments:
            if not isinstance(threat, ThreatAssessment):
                raise TypeError("All threat_assessments must be ThreatAssessment instances")
    
    @classmethod
    def create(cls,
               frame_id: int,
               sensor_id: str,
               tracks: List[Track],
               threat_assessments: List[ThreatAssessment],
               scene_context: 'SceneContext',
               overall_confidence: float = 0.9,
               data_quality: float = 0.9) -> 'RadarIntelligencePacket':
        """Factory method to create validated packet."""
        return cls(
            frame_id=frame_id,
            sensor_id=sensor_id,
            tracks=tracks,
            threat_assessments=threat_assessments,
            scene_context=scene_context,
            overall_confidence=overall_confidence,
            data_quality=data_quality
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'message_id': self.message_id,
            'timestamp': self.timestamp,
            'frame_id': self.frame_id,
            'sensor_id': self.sensor_id,
            'tracks': [t.to_dict() for t in self.tracks],
            'threat_assessments': [ta.to_dict() for ta in self.threat_assessments],
            'scene_context': self.scene_context.to_dict() if self.scene_context else None,
            'overall_confidence': self.overall_confidence,
            'data_quality': self.data_quality,
            'processing_latency_ms': self.processing_latency_ms,
            'sensor_health': self.sensor_health,
            'sensor_mode': self.sensor_mode,
            'schema_version': self.schema_version,
            'sensor_metadata': self.sensor_metadata
        }
    
    def to_json(self, indent: Optional[int] = None) -> str:
        return json.dumps(self.to_dict(), indent=indent)


# Alias for backward compatibility
TacticalPictureMessage = RadarIntelligencePacket


# ============================================================================
# Effector Messages (EW → Radar)
# ============================================================================

@dataclass
class Countermeasure:
    """
    Active countermeasure with validation.
    
    Required fields: countermeasure_id, target_track_id, cm_type, start_time
    Confidence metrics: effectiveness_score, confidence
    """
    # Required fields
    countermeasure_id: int = -1
    target_track_id: int = -1
    cm_type: str = ""  # CountermeasureType enum value
    start_time: float = field(default_factory=time.time)
    
    # Optional timing
    end_time: Optional[float] = None
    duration_s: Optional[float] = None
    
    # RF parameters
    power_level_dbm: Optional[float] = None
    frequency_mhz: Optional[float] = None
    bandwidth_mhz: Optional[float] = None
    
    # Effectiveness metrics
    effectiveness_score: float = 0.0  # 0.0 to 1.0
    confidence: float = 0.0  # Confidence in effectiveness (0.0 to 1.0)
    predicted_snr_reduction_db: float = 0.0
    
    # Status
    status: str = "ACTIVE"  # ACTIVE, COMPLETED, FAILED
    
    # Extensibility: CM-specific parameters
    cm_parameters: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate fields after initialization."""
        if self.countermeasure_id < 0:
            raise ValueError("countermeasure_id must be non-negative")
        
        if self.target_track_id < 0:
            raise ValueError("target_track_id must be non-negative")
        
        _validate_required(self.cm_type, "cm_type")
        
        if self.start_time <= 0:
            raise ValueError("start_time must be positive")
        
        if self.end_time is not None and self.end_time < self.start_time:
            raise ValueError("end_time cannot be before start_time")
        
        _validate_confidence(self.effectiveness_score, "effectiveness_score")
        _validate_confidence(self.confidence, "confidence")
        
        if self.power_level_dbm is not None:
            _validate_range(self.power_level_dbm, 0.0, 60.0, "power_level_dbm")
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EngagementStatus:
    """Engagement status for a track."""
    track_id: int
    engagement_state: str
    time_to_threat_s: Optional[float] = None
    kill_probability: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ElectronicAttackPacket:
    """
    Electronic Attack Packet (EW → Radar).
    
    Strongly-typed message with validation and confidence metrics.
    
    Required fields: message_id, timestamp, effector_id
    Confidence metrics: overall_effectiveness, decision_confidence
    """
    # Message metadata (auto-generated)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    
    # Required identification
    effector_id: str = ""
    
    # Attack data
    active_countermeasures: List[Countermeasure] = field(default_factory=list)
    engagement_status: List['EngagementStatus'] = field(default_factory=list)
    
    # Confidence metrics
    overall_effectiveness: float = 0.0  # Overall attack effectiveness (0.0 to 1.0)
    decision_confidence: float = 0.0  # Confidence in CM selection (0.0 to 1.0)
    expected_impact: float = 0.0  # Expected impact on sensor (0.0 to 1.0)
    
    # Effector status
    effector_health: float = 1.0  # Effector health (0.0 to 1.0)
    effector_mode: str = "DEFENSIVE"  # DEFENSIVE, OFFENSIVE, STANDBY
    power_available_dbm: float = 50.0  # Available jammer power
    
    # Decision metadata
    decision_latency_ms: float = 0.0  # Decision processing time
    threat_count: int = 0  # Number of threats being engaged
    
    # Message versioning
    schema_version: str = "1.0.0"
    
    # Extensibility: effector-specific metadata
    effector_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate required fields."""
        _validate_required(self.message_id, "message_id")
        _validate_required(self.effector_id, "effector_id")
        
        if self.timestamp <= 0:
            raise ValueError("timestamp must be positive")
        
        _validate_confidence(self.overall_effectiveness, "overall_effectiveness")
        _validate_confidence(self.decision_confidence, "decision_confidence")
        _validate_confidence(self.expected_impact, "expected_impact")
        _validate_confidence(self.effector_health, "effector_health")
        
        if self.threat_count < 0:
            raise ValueError("threat_count cannot be negative")
        
        # Validate countermeasures
        for cm in self.active_countermeasures:
            if not isinstance(cm, Countermeasure):
                raise TypeError("All countermeasures must be Countermeasure instances")
        
        # Validate engagements
        for engagement in self.engagement_status:
            if not isinstance(engagement, EngagementStatus):
                raise TypeError("All engagements must be EngagementStatus instances")
    
    @classmethod
    def create(cls,
               effector_id: str,
               countermeasures: List[Countermeasure],
               engagements: List['EngagementStatus'],
               overall_effectiveness: float = 0.8,
               decision_confidence: float = 0.9,
               effector_health: float = 1.0) -> 'ElectronicAttackPacket':
        """Factory method to create validated packet."""
        return cls(
            effector_id=effector_id,
            active_countermeasures=countermeasures,
            engagement_status=engagements,
            overall_effectiveness=overall_effectiveness,
            decision_confidence=decision_confidence,
            effector_health=effector_health,
            threat_count=len(engagements)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'message_id': self.message_id,
            'timestamp': self.timestamp,
            'effector_id': self.effector_id,
            'active_countermeasures': [cm.to_dict() for cm in self.active_countermeasures],
            'engagement_status': [es.to_dict() for es in self.engagement_status],
            'overall_effectiveness': self.overall_effectiveness,
            'decision_confidence': self.decision_confidence,
            'expected_impact': self.expected_impact,
            'effector_health': self.effector_health,
            'effector_mode': self.effector_mode,
            'power_available_dbm': self.power_available_dbm,
            'decision_latency_ms': self.decision_latency_ms,
            'threat_count': self.threat_count,
            'schema_version': self.schema_version,
            'effector_metadata': self.effector_metadata
        }
    
    def to_json(self, indent: Optional[int] = None) -> str:
        return json.dumps(self.to_dict(), indent=indent)


# Alias for backward compatibility
EWFeedbackMessage = ElectronicAttackPacket


# ============================================================================
# Event Types
# ============================================================================

class EventType(Enum):
    """Event types for event bus."""
    TACTICAL_PICTURE_PUBLISHED = "TACTICAL_PICTURE_PUBLISHED"
    TACTICAL_PICTURE_RECEIVED = "TACTICAL_PICTURE_RECEIVED"
    EW_FEEDBACK_PUBLISHED = "EW_FEEDBACK_PUBLISHED"
    EW_FEEDBACK_RECEIVED = "EW_FEEDBACK_RECEIVED"
    MESSAGE_VALIDATION_FAILED = "MESSAGE_VALIDATION_FAILED"
    MESSAGE_DROPPED = "MESSAGE_DROPPED"


@dataclass
class Event:
    """Generic event for event bus."""
    event_type: EventType
    timestamp: float
    data: Dict[str, Any]
    source: str
    
    @classmethod
    def create(cls, event_type: EventType, data: Dict[str, Any], source: str) -> 'Event':
        return cls(
            event_type=event_type,
            timestamp=time.time(),
            data=data,
            source=source
        )
