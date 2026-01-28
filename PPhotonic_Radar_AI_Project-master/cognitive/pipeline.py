"""
Cognitive Radar Pipeline Integration
====================================

Integrates the cognitive decision engine with the existing DSP pipeline.
Provides high-level orchestration for closed-loop adaptation.

This module:
1. Bridges cognitive engine output to DSP parameter inputs
2. Manages frame-to-frame adaptive feedback
3. Provides unified API for cognitive radar operation
4. Maintains backward compatibility with static radar mode

Author: Pipeline Integration Team
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import asdict

from cognitive.engine import (
    CognitiveRadarEngine,
    SituationAssessment,
    AdaptationCommand,
    create_track_dict_for_cognitive,
)
from cognitive.parameters import (
    AdaptiveParameterManager,
    RadarWaveformParameters,
    convert_config_to_waveform_params,
)

logger = logging.getLogger(__name__)


class CognitiveRadarPipeline:
    """
    High-level interface for cognitive radar operation.
    
    Seamlessly integrates cognitive adaptation into existing DSP pipeline.
    """
    
    def __init__(self, enable_cognitive: bool = True):
        """
        Initialize cognitive radar pipeline.
        
        Args:
            enable_cognitive: If False, operates as static radar (backward compatible)
        """
        self.enable_cognitive = enable_cognitive
        self.cognitive_engine = CognitiveRadarEngine() if enable_cognitive else None
        self.parameter_manager = AdaptiveParameterManager()
        
        # State tracking
        self.current_params = RadarWaveformParameters()
        self.last_assessment = None
        self.last_command = None
        self.frame_count = 0
        
        self.logger = logging.getLogger(__name__)
    
    def initialize_from_config(self, config: Dict) -> RadarWaveformParameters:
        """
        Initialize waveform parameters from configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Initial waveform parameters
        """
        self.current_params = convert_config_to_waveform_params(config)
        self.parameter_manager.update_cache(0, self.current_params)
        
        self.logger.info(
            f"Cognitive Radar Pipeline initialized (cognitive_enabled={self.enable_cognitive})"
        )
        
        return self.current_params
    
    def process_radar_frame(self,
                           detections: List[Tuple[float, float]],
                           tracks: List,  # RadarTrack objects
                           ai_predictions: List[Dict],
                           rd_map: Optional[np.ndarray] = None,
                           timestamp: float = 0.0) \
            -> Tuple[RadarWaveformParameters, Optional[AdaptationCommand], str]:
        """
        Process one complete radar frame through cognitive pipeline.
        
        This is the main entry point for frame-by-frame processing.
        
        Args:
            detections: List of (range_m, doppler_m_s) tuples
            tracks: List of RadarTrack objects from tracking module
            ai_predictions: List of {class, confidence, entropy} dicts
            rd_map: Optional Range-Doppler power map (for SNR estimation)
            timestamp: Frame timestamp (seconds)
            
        Returns:
            (next_frame_params, adaptation_command, xai_narrative)
            - next_frame_params: Parameters to use for NEXT frame
            - adaptation_command: Command object (None if static mode)
            - xai_narrative: Human-readable explanation (empty if static)
        """
        self.frame_count += 1
        
        if not self.enable_cognitive:
            # Static radar mode: no adaptation
            return self.current_params, None, "(Cognitive mode disabled)"
        
        # ========== COGNITIVE LOOP ==========
        
        # 1. Convert tracking.RadarTrack to cognitive-compatible dicts
        track_dicts = [create_track_dict_for_cognitive(t) for t in tracks]
        
        # 2. ASSESS SITUATION
        assessment = self.cognitive_engine.assess_situation(
            frame_id=self.frame_count,
            timestamp=timestamp,
            detections=detections,
            tracks=track_dicts,
            ai_predictions=ai_predictions,
            rd_map=rd_map
        )
        self.last_assessment = assessment
        
        # 3. MAKE DECISION
        adaptation_cmd = self.cognitive_engine.decide_adaptation(assessment)
        self.last_command = adaptation_cmd
        
        # 4. APPLY TO PARAMETERS
        next_params = self.parameter_manager.apply_adaptation_command(
            adaptation_cmd,
            self.current_params
        )
        
        # 5. VALIDATE & ENFORCE CONSTRAINTS
        is_valid, issues = self.parameter_manager.validate_parameters(next_params)
        if not is_valid:
            self.logger.error(f"Parameter validation failed: {issues}")
            # Fall back to current (safeguard)
            next_params = self.current_params
        
        # 6. CACHE FOR NEXT FRAME
        self.parameter_manager.update_cache(self.frame_count, next_params)
        self.current_params = next_params
        
        # 7. GENERATE XAI NARRATIVE
        xai_narrative = self.cognitive_engine.generate_xai_narrative(assessment, adaptation_cmd)
        
        self.logger.debug(f"Frame {self.frame_count}: Scene={assessment.scene_type.value}, "
                         f"Conf={assessment.mean_classification_confidence:.1%}")
        
        return next_params, adaptation_cmd, xai_narrative
    
    def get_next_waveform_parameters(self) -> RadarWaveformParameters:
        """
        Get waveform parameters for next TX pulse.
        
        These are the parameters that should be applied to the signal generator.
        They represent the cognitive adaptation from the previous frame.
        
        Returns:
            RadarWaveformParameters for next pulse
        """
        return self.current_params
    
    def get_adaptive_cfar_alpha(self) -> float:
        """
        Get current adaptive CFAR alpha threshold.
        Used by detection module for real-time threshold update.
        
        Returns:
            CFAR alpha threshold (scalar)
        """
        if self.current_params.cfar_alpha is not None:
            return self.current_params.cfar_alpha
        else:
            # Fallback: compute from Pfa
            return self.parameter_manager._compute_cfar_alpha(
                self.current_params.cfar_pfa,
                self.current_params.cfar_guard,
                self.current_params.cfar_train
            )
    
    def get_status_report(self) -> Dict:
        """
        Get comprehensive status report for monitoring/UI.
        
        Returns:
            Dict with current state and recent history
        """
        report = {
            'enabled': self.enable_cognitive,
            'frame_count': self.frame_count,
            'current_parameters': asdict(self.current_params) if self.current_params else None,
            'last_assessment': asdict(self.last_assessment) if self.last_assessment else None,
            'last_command': {
                'bandwidth_scaling': self.last_command.bandwidth_scaling,
                'prf_scale': self.last_command.prf_scale,
                'tx_power_scaling': self.last_command.tx_power_scaling,
                'cfar_alpha_scale': self.last_command.cfar_alpha_scale,
                'dwell_time_scale': self.last_command.dwell_time_scale,
                'reasoning': self.last_command.reasoning,
            } if self.last_command else None,
            'cognitive_engine_state': self.cognitive_engine.get_state_summary() if self.cognitive_engine else None,
            'parameter_manager_cache': {
                'frame_id': self.parameter_manager.cache.current_frame_id,
                'num_history_entries': len(self.parameter_manager.cache.parameter_history),
            }
        }
        return report


# ============================================================================
# Integration Points for Existing Pipeline
# ============================================================================

class CognitiveRadarBridge:
    """
    Bridge between cognitive pipeline and existing DSP modules.
    
    Provides adapters for:
    - Signal generation (photonic/signals.py)
    - Detection (signal_processing/detection.py)
    - Tracking (tracking/manager.py)
    - Inference (ai_models/inference.py)
    """
    
    def __init__(self, cognitive_pipeline: CognitiveRadarPipeline):
        """Initialize bridge."""
        self.pipeline = cognitive_pipeline
        self.logger = logging.getLogger(__name__)
    
    def get_signal_generation_config(self) -> Dict:
        """
        Prepare signal generation config from current cognitive parameters.
        
        Returns:
            Config dict for photonic.signals.generate_photonic_signal()
        """
        params = self.pipeline.get_next_waveform_parameters()
        
        return {
            'bandwidth': params.bandwidth,
            'duration': params.chirp_duration,
            'carrier_freq': params.center_frequency,
            'prf': params.prf,
            'fs': 8 * params.bandwidth,  # Sampling rate = 8× bandwidth (typical)
            'optical_power_dbm': 10 * np.log10(params.tx_power_watts / 1e-3),  # Convert W to dBm
        }
    
    def get_detection_config(self) -> Dict:
        """
        Prepare detection config with adaptive CFAR parameters.
        
        Returns:
            Config dict for signal_processing.detection.ca_cfar()
        """
        params = self.pipeline.get_next_waveform_parameters()
        alpha = self.pipeline.get_adaptive_cfar_alpha()
        
        return {
            'cfar_alpha': alpha,
            'cfar_pfa': params.cfar_pfa,
            'cfar_guard': params.cfar_guard,
            'cfar_train': params.cfar_train,
            'adaptive': self.pipeline.enable_cognitive,
        }
    
    def post_frame_update(self,
                         detections: List[Tuple[float, float]],
                         tracks: List,
                         ai_predictions: List[Dict],
                         rd_map: Optional[np.ndarray] = None,
                         timestamp: float = 0.0) -> Dict:
        """
        Called AFTER each frame completes (after inference).
        Triggers cognitive decision and prepares adaptation for next frame.
        
        Returns:
            Report with adaptation info
        """
        next_params, cmd, xai_narrative = self.pipeline.process_radar_frame(
            detections=detections,
            tracks=tracks,
            ai_predictions=ai_predictions,
            rd_map=rd_map,
            timestamp=timestamp
        )
        
        return {
            'frame_id': self.pipeline.frame_count,
            'timestamp': timestamp,
            'next_waveform_params': next_params,
            'adaptation_command': cmd,
            'xai_narrative': xai_narrative,
        }


# ============================================================================
# Scenario-Based Decision Logic (Optional)
# ============================================================================

class CognitiveScenarioPlanner:
    """
    Optional: Higher-level scenario planning for defensive operations.
    
    Can layer multi-frame planning on top of frame-by-frame adaptation.
    """
    
    def __init__(self, cognitive_pipeline: CognitiveRadarPipeline):
        """Initialize planner."""
        self.pipeline = cognitive_pipeline
        self.scenario_history = []
        self.logger = logging.getLogger(__name__)
    
    def analyze_multi_frame_trend(self, num_frames: int = 20) -> Dict:
        """
        Analyze trends over multiple frames to detect sustained conditions.
        
        Returns:
            Dict with trend analysis
        """
        if not self.pipeline.cognitive_engine:
            return {}
        
        recent_scenes = self.pipeline.cognitive_engine.state.scene_history[-num_frames:]
        if not recent_scenes:
            return {}
        
        from collections import Counter
        scene_counts = Counter([s.value for s in recent_scenes])
        dominant_scene = scene_counts.most_common(1)[0][0] if scene_counts else "Unknown"
        
        confidence_trend = self.pipeline.cognitive_engine.state.mean_confidence_trend
        stability_trend = self.pipeline.cognitive_engine.state.track_stability_trend
        clutter_trend = self.pipeline.cognitive_engine.state.clutter_trend
        
        return {
            'dominant_scene': dominant_scene,
            'confidence_trend': confidence_trend,
            'stability_trend': stability_trend,
            'clutter_trend': clutter_trend,
            'frames_analyzed': len(recent_scenes),
        }
    
    def recommend_sustained_adaptation(self) -> Dict:
        """
        If a trend persists, recommend sustained adaptive parameters.
        
        Returns:
            Recommended parameter adjustments
        """
        trend = self.analyze_multi_frame_trend()
        
        if not trend:
            return {}
        
        recommendations = {}
        
        if trend['dominant_scene'] == 'Cluttered' and trend['clutter_trend'] > 0.25:
            recommendations['adaptive_mode'] = 'Clutter-Rejection'
            recommendations['recommendation'] = "Sustained clutter environment detected. " \
                                               "Maintain high bandwidth and conservative CFAR."
        
        elif trend['dominant_scene'] == 'Dense' and trend['confidence_trend'] > 0.8:
            recommendations['adaptive_mode'] = 'Dense-Target'
            recommendations['recommendation'] = "Dense target swarm sustained. " \
                                               "Maintain expanded bandwidth for separation."
        
        elif trend['stability_trend'] < 0.5:
            recommendations['adaptive_mode'] = 'Track-Stabilization'
            recommendations['recommendation'] = "Low track stability detected. " \
                                               "Extend coherent integration time."
        
        return recommendations


# ============================================================================
# Module-Level Initialization
# ============================================================================

# Global cognitive pipeline (can be initialized at app startup)
_global_cognitive_pipeline = None


def initialize_global_cognitive_radar(config: Dict, enable: bool = True) -> CognitiveRadarPipeline:
    """
    Initialize and return global cognitive radar pipeline.
    
    Args:
        config: Configuration dictionary
        enable: Enable cognitive adaptation (default True)
        
    Returns:
        Initialized CognitiveRadarPipeline
    """
    global _global_cognitive_pipeline
    
    _global_cognitive_pipeline = CognitiveRadarPipeline(enable_cognitive=enable)
    _global_cognitive_pipeline.initialize_from_config(config)
    
    return _global_cognitive_pipeline


def get_global_cognitive_pipeline() -> Optional[CognitiveRadarPipeline]:
    """Get the global cognitive radar pipeline instance."""
    return _global_cognitive_pipeline
