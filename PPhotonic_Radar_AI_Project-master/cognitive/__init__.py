"""
Cognitive Radar Module
======================

Provides AI-driven closed-loop adaptation for waveform and detection parameters.

Components:
  - engine.py: Core cognitive decision engine (situation assessment, decision logic)
  - parameters.py: Waveform parameter management and adaptation
  - pipeline.py: High-level integration with DSP pipeline
  
Usage:
  from cognitive.pipeline import CognitiveRadarPipeline
  
  # Initialize
  cognitive_radar = CognitiveRadarPipeline(enable_cognitive=True)
  cognitive_radar.initialize_from_config(config)
  
  # Each frame
  next_params, cmd, narrative = cognitive_radar.process_radar_frame(
      detections=detections,
      tracks=tracks,
      ai_predictions=predictions,
      rd_map=rd_map
  )
  
  # Apply next_params to signal generation
  # Use cmd for analysis/logging
  # Display narrative for operator awareness

Author: Cognitive Radar Systems Team
"""

from cognitive.engine import (
    CognitiveRadarEngine,
    SituationAssessment,
    SceneType,
    AdaptationCommand,
    CognitiveRadarState,
    create_track_dict_for_cognitive,
    extract_track_metrics,
)

from cognitive.parameters import (
    AdaptiveParameterManager,
    AdaptiveParameterCache,
    RadarWaveformParameters,
    convert_config_to_waveform_params,
    waveform_params_to_photonic_config,
)

from cognitive.pipeline import (
    ModularCognitiveIntelligenceBridge,
)

from cognitive.intelligence_pipeline import (
    EWIntelligencePipeline,
)

__version__ = "1.0.0"
__all__ = [
    # Engine components
    "CognitiveRadarEngine",
    "SituationAssessment",
    "AdaptationCommand",
    "SceneType",
    
    # Parameter management
    "RadarWaveformParameters",
    "AdaptiveParameterManager",
    "AdaptiveParameterCache",
    
    # Pipeline & integration
    "ModularCognitiveIntelligenceBridge",
    "EWIntelligencePipeline",
    
    # Utilities
    "create_track_dict_for_cognitive",
    "extract_track_metrics",
    "convert_config_to_waveform_params",
    "waveform_params_to_photonic_config",
]
