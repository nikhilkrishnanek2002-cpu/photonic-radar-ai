"""
Defense Core Module
===================

Neutral interface layer for defense system integration.

This module provides:
- Message schemas (data contracts)
- Event bus (publish/subscribe)
- Validators (data integrity)

No dependencies on radar or EW internals.

Author: Defense Core Team
"""

from defense_core.schemas import (
    # Enumerations
    ThreatClass,
    TargetType,
    EngagementRecommendation,
    CountermeasureType,
    EngagementState,
    EventType,
    
    # Sensor messages
    Track,
    ThreatAssessment,
    SceneContext,
    RadarIntelligencePacket,  # New strongly-typed schema
    TacticalPictureMessage,  # Alias for backward compatibility
    
    # Effector messages
    Countermeasure,
    EngagementStatus,
    ElectronicAttackPacket,  # New strongly-typed schema
    EWFeedbackMessage,  # Alias for backward compatibility
    
    # Events
    Event,
)

from defense_core.event_bus import (
    DefenseEventBus,
    get_defense_bus,
    reset_defense_bus,
    QueueBackend,
)

from defense_core.validators import (
    ValidationRules,
    validate_track,
    validate_threat_assessment,
    validate_tactical_picture,
    validate_countermeasure,
    validate_ew_feedback,
    is_message_stale,
)

__all__ = [
    # Enumerations
    'ThreatClass',
    'TargetType',
    'EngagementRecommendation',
    'CountermeasureType',
    'EngagementState',
    'EventType',
    
    # Sensor messages
    'Track',
    'ThreatAssessment',
    'SceneContext',
    'RadarIntelligencePacket',
    'TacticalPictureMessage',
    
    # Effector messages
    'Countermeasure',
    'EngagementStatus',
    'ElectronicAttackPacket',
    'EWFeedbackMessage',
    
    # Events
    'Event',
    
    # Event bus
    'DefenseEventBus',
    'get_defense_bus',
    'reset_defense_bus',
    'QueueBackend',
    
    # Validators
    'ValidationRules',
    'validate_track',
    'validate_threat_assessment',
    'validate_tactical_picture',
    'validate_countermeasure',
    'validate_ew_feedback',
    'is_message_stale',
]

__version__ = '1.0.0'
