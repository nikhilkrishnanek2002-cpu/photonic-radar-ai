# Enhanced Defense Core Schemas

## Overview

Strongly-typed message schemas with field validation, confidence metrics, and extensibility for defense system integration.

---

## Key Features

✅ **Field Validation** - Automatic validation on creation  
✅ **Required Field Enforcement** - Prevents missing critical fields  
✅ **Confidence Metrics** - Track data quality and effectiveness  
✅ **Timestamps** - Auto-generated for all messages  
✅ **Extensibility** - Custom fields for future sensors  

---

## Message Schemas

### 1. RadarIntelligencePacket (Radar → EW)

**Purpose**: Strongly-typed tactical picture from sensor to effector

**Required Fields**:
- `message_id` (auto-generated)
- `timestamp` (auto-generated)
- `frame_id` (must be ≥ 0)
- `sensor_id` (non-empty string)

**Confidence Metrics**:
- `overall_confidence` (0.0 to 1.0) - Overall packet confidence
- `data_quality` (0.0 to 1.0) - Data quality score
- `sensor_health` (0.0 to 1.0) - Sensor health status

**Extensibility**:
- `sensor_metadata: Dict[str, Any]` - Custom sensor-specific data
- `sensor_specific` in Track - Custom track data

**Example**:
```python
from defense_core import RadarIntelligencePacket, Track, ThreatAssessment, SceneContext

track = Track(
    track_id=101,
    range_m=5000.0,
    azimuth_deg=45.0,
    radial_velocity_m_s=-200.0,
    track_quality=0.92,
    position_uncertainty_m=10.0,  # CEP
    sensor_specific={'snr_db': 20.5}  # Custom data
)

threat = ThreatAssessment(
    track_id=101,
    threat_class='HOSTILE',
    target_type='MISSILE',
    classification_confidence=0.88,
    model_confidence=0.90,
    feature_quality=0.85,
    threat_priority=10
)

scene = SceneContext(
    scene_type='TRACKING',
    clutter_ratio=0.1,
    mean_snr_db=20.0,
    num_confirmed_tracks=1
)

intel = RadarIntelligencePacket.create(
    frame_id=0,
    sensor_id='RADAR_01',
    tracks=[track],
    threat_assessments=[threat],
    scene_context=scene,
    overall_confidence=0.95,  # High confidence
    data_quality=0.92  # High quality
)

# Validation happens automatically
print(f"Confidence: {intel.overall_confidence}")
print(f"Quality: {intel.data_quality}")
print(f"Health: {intel.sensor_health}")
```

---

### 2. ElectronicAttackPacket (EW → Radar)

**Purpose**: Strongly-typed EW feedback from effector to sensor

**Required Fields**:
- `message_id` (auto-generated)
- `timestamp` (auto-generated)
- `effector_id` (non-empty string)

**Confidence Metrics**:
- `overall_effectiveness` (0.0 to 1.0) - Attack effectiveness
- `decision_confidence` (0.0 to 1.0) - CM selection confidence
- `expected_impact` (0.0 to 1.0) - Expected sensor impact
- `effector_health` (0.0 to 1.0) - Effector health

**Extensibility**:
- `effector_metadata: Dict[str, Any]` - Custom effector data
- `cm_parameters` in Countermeasure - Custom CM parameters

**Example**:
```python
from defense_core import ElectronicAttackPacket, Countermeasure, EngagementStatus
import time

cm = Countermeasure(
    countermeasure_id=1,
    target_track_id=101,
    cm_type='NOISE_JAM',
    start_time=time.time(),
    power_level_dbm=40.0,
    effectiveness_score=0.8,
    confidence=0.85,  # Confidence in effectiveness
    predicted_snr_reduction_db=12.0,
    cm_parameters={'sweep_rate_hz': 1000}  # Custom data
)

engagement = EngagementStatus(
    track_id=101,
    engagement_state='ENGAGING',
    kill_probability=0.75
)

attack = ElectronicAttackPacket.create(
    effector_id='EW_01',
    countermeasures=[cm],
    engagements=[engagement],
    overall_effectiveness=0.82,  # Expected effectiveness
    decision_confidence=0.90,  # High confidence in decision
    effector_health=1.0
)

print(f"Effectiveness: {attack.overall_effectiveness}")
print(f"Confidence: {attack.decision_confidence}")
print(f"Threats: {attack.threat_count}")
```

---

## Validation

### Automatic Validation

All schemas validate fields automatically on creation:

```python
# This will raise ValueError
track = Track(
    track_id=101,
    range_m=-1000.0,  # ❌ Negative range
    azimuth_deg=45.0
)
# ValueError: range_m must be between 0.0 and 100000.0, got -1000.0

# This will raise ValueError
track = Track(
    track_id=101,
    range_m=5000.0,
    azimuth_deg=500.0  # ❌ Invalid azimuth
)
# ValueError: azimuth_deg must be between -180.0 and 360.0, got 500.0

# This will raise ValueError
track = Track(
    track_id=101,
    range_m=5000.0,
    azimuth_deg=45.0,
    track_quality=1.5  # ❌ Invalid quality
)
# ValueError: track_quality must be between 0.0 and 1.0, got 1.5
```

### Validation Rules

**Track**:
- `range_m`: 0.0 to 100,000.0 m
- `azimuth_deg`: -180.0 to 360.0°
- `elevation_deg`: -90.0 to 90.0°
- `radial_velocity_m_s`: -1000.0 to 1000.0 m/s
- `track_quality`: 0.0 to 1.0
- `track_age_frames`: ≥ 0

**ThreatAssessment**:
- `classification_confidence`: 0.0 to 1.0
- `model_confidence`: 0.0 to 1.0
- `feature_quality`: 0.0 to 1.0
- `threat_priority`: 0 to 10

**Countermeasure**:
- `countermeasure_id`: ≥ 0
- `target_track_id`: ≥ 0
- `power_level_dbm`: 0.0 to 60.0 dBm
- `effectiveness_score`: 0.0 to 1.0
- `confidence`: 0.0 to 1.0

---

## Confidence Metrics

### Radar Intelligence Packet

| Metric | Range | Description |
|--------|-------|-------------|
| `overall_confidence` | 0.0-1.0 | Overall packet confidence |
| `data_quality` | 0.0-1.0 | Data quality score |
| `sensor_health` | 0.0-1.0 | Sensor health status |
| `track_quality` | 0.0-1.0 | Individual track quality |
| `classification_confidence` | 0.0-1.0 | AI classification confidence |
| `model_confidence` | 0.0-1.0 | AI model confidence |
| `feature_quality` | 0.0-1.0 | Feature extraction quality |

### Electronic Attack Packet

| Metric | Range | Description |
|--------|-------|-------------|
| `overall_effectiveness` | 0.0-1.0 | Overall attack effectiveness |
| `decision_confidence` | 0.0-1.0 | CM selection confidence |
| `expected_impact` | 0.0-1.0 | Expected sensor impact |
| `effector_health` | 0.0-1.0 | Effector health status |
| `effectiveness_score` | 0.0-1.0 | CM effectiveness |
| `confidence` | 0.0-1.0 | Confidence in effectiveness |

---

## Extensibility

### Sensor-Specific Data

```python
# Add custom sensor data
track = Track(
    track_id=101,
    range_m=5000.0,
    azimuth_deg=45.0,
    sensor_specific={
        'snr_db': 20.5,
        'doppler_bin': 42,
        'range_bin': 128,
        'antenna_id': 3
    }
)

intel = RadarIntelligencePacket.create(
    frame_id=0,
    sensor_id='RADAR_01',
    tracks=[track],
    threat_assessments=[],
    scene_context=scene,
    sensor_metadata={
        'waveform_type': 'FMCW',
        'integration_time_ms': 50,
        'antenna_config': 'MIMO_4x4'
    }
)
```

### Effector-Specific Data

```python
# Add custom CM parameters
cm = Countermeasure(
    countermeasure_id=1,
    target_track_id=101,
    cm_type='NOISE_JAM',
    start_time=time.time(),
    cm_parameters={
        'modulation': 'BPSK',
        'sweep_rate_hz': 1000,
        'duty_cycle': 0.8,
        'polarization': 'CIRCULAR'
    }
)

attack = ElectronicAttackPacket.create(
    effector_id='EW_01',
    countermeasures=[cm],
    engagements=[],
    effector_metadata={
        'jammer_type': 'DRFM',
        'antenna_pattern': 'DIRECTIONAL',
        'cooling_status': 'NORMAL'
    }
)
```

---

## Backward Compatibility

Aliases provided for existing code:

```python
# New names (recommended)
from defense_core import RadarIntelligencePacket, ElectronicAttackPacket

# Old names (still work)
from defense_core import TacticalPictureMessage, EWFeedbackMessage

# They are the same
assert RadarIntelligencePacket == TacticalPictureMessage
assert ElectronicAttackPacket == EWFeedbackMessage
```

---

## Summary

Enhanced schemas provide:

✅ **Validation** - Automatic field validation prevents invalid data  
✅ **Confidence** - Comprehensive metrics for data quality  
✅ **Extensibility** - Custom fields for future sensors  
✅ **Type Safety** - Strongly-typed with dataclasses  
✅ **Timestamps** - Auto-generated for all messages  
✅ **Backward Compatible** - Aliases for existing code  

These schemas ensure data integrity and enable sophisticated sensor-effector integration while maintaining flexibility for future enhancements.
