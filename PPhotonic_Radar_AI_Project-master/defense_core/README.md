# Defense Core Module - Complete Reference

## Overview

The `defense_core` module is a **neutral interface layer** for defense system integration, providing strongly-typed message schemas, event-driven communication, and comprehensive validation.

---

## Module Structure

```
defense_core/
├── __init__.py           # Public API
├── schemas.py            # Message schemas with validation
├── event_bus.py          # Event-driven communication
├── validators.py         # Message validation utilities
├── README.md             # Module overview
├── SCHEMAS.md            # Schema documentation
└── EVENT_BUS.md          # Event bus documentation
```

---

## Quick Start

### Installation

```python
# Import defense_core
from defense_core import (
    # Schemas
    RadarIntelligencePacket,
    ElectronicAttackPacket,
    Track,
    ThreatAssessment,
    Countermeasure,
    
    # Event bus
    get_defense_bus,
    
    # Validators
    validate_tactical_picture,
)
```

### Basic Usage

```python
import time
from defense_core import *

# Create track
track = Track(
    track_id=101,
    range_m=5000.0,
    azimuth_deg=45.0,
    track_quality=0.92
)

# Create threat assessment
threat = ThreatAssessment(
    track_id=101,
    threat_class='HOSTILE',
    target_type='MISSILE',
    classification_confidence=0.88,
    threat_priority=10
)

# Create intelligence packet
intel = RadarIntelligencePacket.create(
    frame_id=0,
    sensor_id='RADAR_01',
    tracks=[track],
    threat_assessments=[threat],
    scene_context=scene,
    overall_confidence=0.95
)

# Publish via event bus
bus = get_defense_bus()
bus.publish_intelligence(intel)

# Receive intelligence (EW side)
received = bus.receive_intelligence(timeout=0.1)
```

---

## Core Components

### 1. Message Schemas (`schemas.py`)

**Purpose**: Strongly-typed data contracts with validation

**Key Features**:
- Field validation (ranges, types)
- Required field enforcement
- Confidence metrics
- Auto-generated timestamps
- Extensibility fields

**Main Schemas**:

| Schema | Direction | Purpose |
|--------|-----------|---------|
| `RadarIntelligencePacket` | Radar → EW | Tactical picture |
| `ElectronicAttackPacket` | EW → Radar | Countermeasures |
| `Track` | - | Target state |
| `ThreatAssessment` | - | AI classification |
| `Countermeasure` | - | EW action |
| `EngagementStatus` | - | Engagement state |

**Example**:
```python
# Automatic validation
track = Track(
    track_id=101,
    range_m=5000.0,      # Validated: 0-100,000m
    azimuth_deg=45.0,    # Validated: -180 to 360°
    track_quality=0.92   # Validated: 0.0-1.0
)
# ValueError raised if invalid
```

### 2. Event Bus (`event_bus.py`)

**Purpose**: Event-driven communication with dual queues

**Key Features**:
- Non-blocking reads
- Safe writes (drop on full)
- Thread-safe design
- No busy waiting
- Swappable backend

**Queues**:
- `radar_to_ew_bus` - Intelligence flow
- `ew_to_radar_bus` - Feedback flow

**Example**:
```python
bus = get_defense_bus()

# Radar: publish intelligence (non-blocking)
success = bus.publish_intelligence(intel)

# EW: receive intelligence (non-blocking)
intel = bus.receive_intelligence(timeout=0.0)

# EW: publish feedback (non-blocking)
bus.publish_feedback(attack)

# Radar: receive feedback (non-blocking)
feedback = bus.receive_ew_feedback(timeout=0.0)
```

### 3. Validators (`validators.py`)

**Purpose**: Message validation and integrity checks

**Key Features**:
- Range validation
- Type checking
- Staleness detection
- Contract compliance

**Example**:
```python
from defense_core import validate_tactical_picture

is_valid, errors = validate_tactical_picture(intel)
if not is_valid:
    print(f"Validation errors: {errors}")
```

---

## Design Principles

### 1. Loose Coupling

**No Cross-Dependencies**:
```python
# ✓ CORRECT: defense_core has no dependencies
from defense_core import RadarIntelligencePacket

# ✗ WRONG: defense_core should not import from systems
# from simulation_engine import ...  # NO!
# from cognitive import ...          # NO!
```

### 2. Validation First

**Automatic Validation**:
```python
# Validation happens automatically
track = Track(
    track_id=101,
    range_m=-1000.0  # ✗ ValueError: range must be 0-100,000
)
```

### 3. Non-Blocking Communication

**Radar Never Stalls**:
```python
# Publish 1000 messages (never blocks)
for i in range(1000):
    bus.publish_intelligence(intel)  # ~1ms total
```

### 4. Extensibility

**Custom Fields**:
```python
# Add sensor-specific data
track = Track(
    track_id=101,
    range_m=5000.0,
    azimuth_deg=45.0,
    sensor_specific={
        'snr_db': 20.5,
        'doppler_bin': 42
    }
)
```

---

## Integration Patterns

### Radar System Integration

```python
from defense_core import get_defense_bus, RadarIntelligencePacket

class RadarSystem:
    def __init__(self):
        self.bus = get_defense_bus()
        self.sensor_id = 'RADAR_01'
    
    def tick(self, frame_id):
        # 1. Detect targets
        tracks = self.detect_targets()
        
        # 2. Classify threats
        threats = self.classify_threats(tracks)
        
        # 3. Create intelligence packet
        intel = RadarIntelligencePacket.create(
            frame_id=frame_id,
            sensor_id=self.sensor_id,
            tracks=tracks,
            threat_assessments=threats,
            scene_context=self.get_scene(),
            overall_confidence=0.95,
            data_quality=0.92
        )
        
        # 4. Publish (non-blocking)
        self.bus.publish_intelligence(intel)
        
        # 5. Check for EW feedback (non-blocking)
        feedback = self.bus.receive_ew_feedback(timeout=0.0)
        if feedback:
            self.apply_ew_effects(feedback)
```

### EW System Integration

```python
from defense_core import get_defense_bus, ElectronicAttackPacket

class EWSystem:
    def __init__(self):
        self.bus = get_defense_bus()
        self.effector_id = 'EW_01'
    
    def process(self):
        # 1. Receive intelligence (non-blocking)
        intel = self.bus.receive_intelligence(timeout=0.0)
        
        if not intel:
            return
        
        # 2. Analyze threats
        high_priority_threats = [
            t for t in intel.threat_assessments
            if t.threat_priority >= 8
        ]
        
        # 3. Generate countermeasures
        countermeasures = self.generate_countermeasures(
            high_priority_threats
        )
        
        # 4. Create feedback packet
        feedback = ElectronicAttackPacket.create(
            effector_id=self.effector_id,
            countermeasures=countermeasures,
            engagements=self.get_engagements(),
            overall_effectiveness=0.82,
            decision_confidence=0.90
        )
        
        # 5. Publish (non-blocking)
        self.bus.publish_feedback(feedback)
```

---

## API Reference

### Schemas

```python
# Create track
track = Track(
    track_id: int,
    range_m: float,              # 0-100,000m
    azimuth_deg: float,          # -180 to 360°
    track_quality: float = 0.0   # 0.0-1.0
)

# Create threat assessment
threat = ThreatAssessment(
    track_id: int,
    threat_class: str,
    target_type: str,
    classification_confidence: float,  # 0.0-1.0
    threat_priority: int = 0           # 0-10
)

# Create intelligence packet
intel = RadarIntelligencePacket.create(
    frame_id: int,
    sensor_id: str,
    tracks: List[Track],
    threat_assessments: List[ThreatAssessment],
    scene_context: SceneContext,
    overall_confidence: float = 0.9,
    data_quality: float = 0.9
)

# Create countermeasure
cm = Countermeasure(
    countermeasure_id: int,
    target_track_id: int,
    cm_type: str,
    start_time: float,
    effectiveness_score: float = 0.0  # 0.0-1.0
)

# Create attack packet
attack = ElectronicAttackPacket.create(
    effector_id: str,
    countermeasures: List[Countermeasure],
    engagements: List[EngagementStatus],
    overall_effectiveness: float = 0.8,
    decision_confidence: float = 0.9
)
```

### Event Bus

```python
# Get global bus
bus = get_defense_bus()

# Radar interface
success = bus.publish_intelligence(intel, timeout=None)
feedback = bus.receive_ew_feedback(timeout=0.0)

# EW interface
intel = bus.receive_intelligence(timeout=0.0)
success = bus.publish_feedback(attack, timeout=None)

# Management
stats = bus.get_statistics()
bus.clear()
bus.stop()
```

### Validators

```python
# Validate messages
is_valid, errors = validate_track(track)
is_valid, errors = validate_threat_assessment(threat)
is_valid, errors = validate_tactical_picture(intel)
is_valid, errors = validate_countermeasure(cm)
is_valid, errors = validate_ew_feedback(attack)

# Check staleness
is_stale = is_message_stale(timestamp, current_time)
```

---

## Test Results

```
✓ All schemas validated successfully
✓ Event bus: non-blocking reads
✓ Event bus: safe writes
✓ Event bus: thread safety
✓ Event bus: no stalling
✓ Event bus: bidirectional communication
```

---

## Documentation

- **[README.md](README.md)** - Module overview
- **[SCHEMAS.md](SCHEMAS.md)** - Schema documentation
- **[EVENT_BUS.md](EVENT_BUS.md)** - Event bus documentation

---

## Summary

The `defense_core` module provides:

✅ **Strongly-Typed Schemas** - Validation and confidence metrics  
✅ **Event-Driven Communication** - Non-blocking dual queues  
✅ **Loose Coupling** - No system dependencies  
✅ **Thread-Safe** - Concurrent access supported  
✅ **Extensible** - Custom fields for future sensors  
✅ **Observable** - Statistics and monitoring  

This architecture enables sophisticated closed-loop cognitive defense while maintaining system modularity and real-time performance.
