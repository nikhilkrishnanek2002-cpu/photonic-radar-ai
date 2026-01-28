"""
Cognitive Radar Integration Examples
====================================

Demonstrates how to use the cognitive radar module in various scenarios.

Run with:
  python examples_cognitive_radar.py

Author: Cognitive Systems Examples
"""

import numpy as np
import sys
from typing import List, Dict, Tuple

# Import cognitive modules
from cognitive.pipeline import CognitiveRadarPipeline, CognitiveRadarBridge
from cognitive.engine import create_track_dict_for_cognitive
from cognitive.parameters import RadarWaveformParameters
from cognitive.xai import CognitiveRadarXAI, DecisionRationale


# ============================================================================
# Example 1: Standalone Cognitive Engine
# ============================================================================

def example_1_standalone_cognitive_engine():
    """
    Example 1: Using cognitive engine without DSP integration.
    """
    print("\\n" + "="*70)
    print("EXAMPLE 1: Standalone Cognitive Engine")
    print("="*70)
    
    from cognitive.pipeline import CognitiveRadarPipeline
    
    # Initialize
    cognitive_radar = CognitiveRadarPipeline(enable_cognitive=True)
    config = {
        'photonic': {'bandwidth': 1e9, 'carrier_freq': 10e9, 'duration': 10e-6},
        'detection': {'pfa': 1e-6, 'guard': 2, 'train': 8}
    }
    cognitive_radar.initialize_from_config(config)
    
    # Scenario: Cluttered environment with weak targets
    print("\\nScenario: Cluttered urban environment")
    print("-" * 70)
    
    # Create synthetic data
    detections = [
        (100.0, 50.0), (102.0, 52.0),   # Target 1 & 2
        (150.0, -30.0),                  # Target 3
        (105.0, 0.0), (107.0, 2.0), (103.0, -1.0),  # Clutter
    ]
    
    tracks = []  # No tracks yet (search mode)
    
    predictions = [
        {'confidence': 0.58, 'class_probabilities': [0.3, 0.35, 0.35]},  # Low conf
        {'confidence': 0.55, 'class_probabilities': [0.4, 0.3, 0.3]},
        {'confidence': 0.52, 'class_probabilities': [0.35, 0.35, 0.3]},
    ]
    
    # Process frame
    next_params, cmd, xai_narrative = cognitive_radar.process_radar_frame(
        detections=detections,
        tracks=tracks,
        ai_predictions=predictions,
        timestamp=0.05
    )
    
    # Display results
    print(xai_narrative)
    
    print("\\nAdaptive Parameters (Next Frame):")
    print(f"  Bandwidth: {next_params.bandwidth/1e9:.2f} GHz (changed {cmd.bandwidth_scaling:.0%})")
    print(f"  TX Power: {next_params.tx_power_watts:.1f} W (changed {cmd.tx_power_scaling:.0%})")
    print(f"  CFAR Alpha: {next_params.cfar_alpha:.1f} (changed {cmd.cfar_alpha_scale:.0%})")
    print(f"  PRF: {next_params.prf/1e3:.1f} kHz (changed {cmd.prf_scale:.0%})")


# ============================================================================
# Example 2: Multi-Frame Scenario Progression
# ============================================================================

def example_2_scenario_progression():
    """
    Example 2: Track cognitive radar through multiple frames as scenario changes.
    """
    print("\\n" + "="*70)
    print("EXAMPLE 2: Multi-Frame Scenario Progression")
    print("="*70)
    
    cognitive_radar = CognitiveRadarPipeline(enable_cognitive=True)
    config = {
        'photonic': {'bandwidth': 1e9, 'carrier_freq': 10e9, 'duration': 10e-6},
        'detection': {'pfa': 1e-6, 'guard': 2, 'train': 8}
    }
    cognitive_radar.initialize_from_config(config)
    
    scenarios = [
        {
            'name': 'Frame 1: Search Mode (No Targets)',
            'detections': [],
            'predictions': [],
        },
        {
            'name': 'Frame 2-4: Single Weak Target Detected',
            'detections': [(100.0, 50.0)],
            'predictions': [{'confidence': 0.55, 'class_probabilities': [0.3, 0.4, 0.3]}],
        },
        {
            'name': 'Frame 5-10: Target Stabilizes (Confirmed)',
            'detections': [(100.5, 50.2), (101.0, 50.5)],  # Multiple measurements
            'predictions': [
                {'confidence': 0.78, 'class_probabilities': [0.1, 0.8, 0.1]},
                {'confidence': 0.75, 'class_probabilities': [0.15, 0.75, 0.1]},
            ],
        },
        {
            'name': 'Frame 11-20: Dense Swarm Environment',
            'detections': [
                (95.0, 45.0), (96.0, 46.0), (97.0, 47.0), (98.0, 48.0), (99.0, 49.0),
                (100.0, 50.0), (101.0, 51.0), (102.0, 52.0),
            ],
            'predictions': [
                {'confidence': 0.72, 'class_probabilities': [0.2, 0.7, 0.1]} for _ in range(8)
            ],
        },
    ]
    
    frame_id = 0
    for scenario in scenarios:
        print(f"\\n{scenario['name']}")
        print("-" * 70)
        
        # Simulate 3 frames per scenario
        for i in range(3):
            frame_id += 1
            
            next_params, cmd, _ = cognitive_radar.process_radar_frame(
                detections=scenario['detections'],
                tracks=[],
                ai_predictions=scenario['predictions'],
                timestamp=0.05 * frame_id
            )
            
            print(f"  Frame {frame_id}: "
                  f"BW×{cmd.bandwidth_scaling:.2f} "
                  f"Pwr×{cmd.tx_power_scaling:.2f} "
                  f"CFAR×{cmd.cfar_alpha_scale:.2f} "
                  f"Scene: {cmd.reasoning.get('bandwidth', 'N/A')[:40]}")


# ============================================================================
# Example 3: Parameter Adaptation and Validation
# ============================================================================

def example_3_parameter_adaptation():
    """
    Example 3: Demonstrates parameter adaptation and hardware constraint checking.
    """
    print("\\n" + "="*70)
    print("EXAMPLE 3: Parameter Adaptation & Hardware Constraints")
    print("="*70)
    
    from cognitive.parameters import AdaptiveParameterManager, RadarWaveformParameters
    
    manager = AdaptiveParameterManager()
    
    # Start with baseline parameters
    baseline_params = RadarWaveformParameters(
        bandwidth=1e9,
        prf=20e3,
        tx_power_watts=10.0,
        dwell_frames=4,
    )
    
    print("\\nBaseline Parameters:")
    print(f"  Bandwidth: {baseline_params.bandwidth/1e9:.2f} GHz")
    print(f"  PRF: {baseline_params.prf/1e3:.1f} kHz")
    print(f"  TX Power: {baseline_params.tx_power_watts:.1f} W")
    print(f"  Dwell Frames: {baseline_params.dwell_frames}")
    
    # Simulate adaptive command
    class MockCommand:
        def __init__(self):
            self.bandwidth_scaling = 2.0  # 200% - will be clipped
            self.prf_scale = 0.5
            self.tx_power_scaling = 1.5
            self.cfar_alpha_scale = 0.9
            self.dwell_time_scale = 1.5
            self.frame_id = 1
    
    cmd = MockCommand()
    
    # Apply adaptation
    adapted_params = manager.apply_adaptation_command(cmd, baseline_params)
    
    print("\\nAdaptation Command:")
    print(f"  BW Scale: {cmd.bandwidth_scaling:.1f}× (will be clipped to 1.5×)")
    print(f"  PRF Scale: {cmd.prf_scale:.1f}×")
    print(f"  Power Scale: {cmd.tx_power_scaling:.1f}×")
    print(f"  Dwell Scale: {cmd.dwell_time_scale:.1f}×")
    
    print("\\nAdapted Parameters (After Hardware Limits):")
    print(f"  Bandwidth: {adapted_params.bandwidth/1e9:.2f} GHz (clipped from 2.0 GHz)")
    print(f"  PRF: {adapted_params.prf/1e3:.1f} kHz")
    print(f"  TX Power: {adapted_params.tx_power_watts:.1f} W")
    print(f"  Dwell Frames: {adapted_params.dwell_frames}")
    
    # Derive parameters
    derived = manager.compute_derived_parameters(adapted_params)
    print("\\nDerived Performance Parameters:")
    print(f"  Range Resolution: ±{derived['range_resolution_m']:.1f} m")
    print(f"  Velocity Resolution: ±{derived['velocity_resolution_m_s']:.2f} m/s")
    print(f"  SNR Improvement: +{derived['snr_improvement_db']:.1f} dB")
    
    # Validation
    is_valid, issues = manager.validate_parameters(adapted_params)
    print(f"\\nValidation: {'✓ PASS' if is_valid else '✗ FAIL'}")
    if issues:
        for issue in issues:
            print(f"  • {issue}")


# ============================================================================
# Example 4: XAI Narrative Generation
# ============================================================================

def example_4_xai_explanations():
    """
    Example 4: Demonstrates XAI narrative generation for operator transparency.
    """
    print("\\n" + "="*70)
    print("EXAMPLE 4: XAI Explanations for Cognitive Decisions")
    print("="*70)
    
    from cognitive.xai import CognitiveRadarXAI
    
    xai = CognitiveRadarXAI()
    
    # Scenario: Clutter-rich, low-confidence scene
    print("\\nScenario: Clutter-rich environment with low classification confidence")
    print("-" * 70)
    
    # Create mock assessment and command
    class MockAssessment:
        def __init__(self):
            self.frame_id = 42
            self.timestamp = 2.1
            self.scene_type = type('obj', (object,), {'value': 'Cluttered'})()
            self.num_confirmed_tracks = 2
            self.num_false_alarms = 3
            self.clutter_ratio = 0.35
            self.mean_classification_confidence = 0.58
            self.mean_class_entropy = 0.95
            self.mean_track_stability = 0.65
            self.estimated_snr_db = 15.0
    
    class MockCommand:
        def __init__(self):
            self.frame_id = 42
            self.bandwidth_scaling = 1.3
            self.prf_scale = 1.0
            self.tx_power_scaling = 1.2
            self.cfar_alpha_scale = 1.1
            self.dwell_time_scale = 1.0
            self.decision_confidence = 0.82
            self.predicted_snr_improvement_db = 1.8
            self.reasoning = {
                'bandwidth': 'Clutter-rich environment detected',
                'tx_power': 'Low confidence requires power boost',
            }
    
    assessment = MockAssessment()
    cmd = MockCommand()
    
    # Generate explanations
    tx_exp = xai.explain_tx_power_decision(
        confidence=assessment.mean_classification_confidence,
        track_stability=assessment.mean_track_stability,
        snr_db=assessment.estimated_snr_db,
        scaling=cmd.tx_power_scaling
    )
    
    bw_exp = xai.explain_bandwidth_decision(
        scene_type='Cluttered',
        clutter_ratio=assessment.clutter_ratio,
        num_confirmed=assessment.num_confirmed_tracks,
        scaling=cmd.bandwidth_scaling
    )
    
    cfar_exp = xai.explain_cfar_decision(
        confidence=assessment.mean_classification_confidence,
        scene_type='Cluttered',
        clutter_ratio=assessment.clutter_ratio,
        scaling=cmd.cfar_alpha_scale
    )
    
    # Build narrative
    parameter_explanations = [tx_exp, bw_exp, cfar_exp]
    narrative = xai.build_complete_narrative(assessment, cmd, parameter_explanations)
    
    # Display
    display_text = xai.format_narrative_for_display(narrative)
    print(display_text)


# ============================================================================
# Example 5: Integration with DSP Pipeline
# ============================================================================

def example_5_dsp_integration():
    """
    Example 5: Shows how to integrate cognitive radar with DSP functions.
    """
    print("\\n" + "="*70)
    print("EXAMPLE 5: DSP Pipeline Integration")
    print("="*70)
    
    from cognitive.pipeline import CognitiveRadarBridge, CognitiveRadarPipeline
    
    # Initialize cognitive pipeline
    cognitive_pipeline = CognitiveRadarPipeline(enable_cognitive=True)
    config = {
        'photonic': {'bandwidth': 1e9, 'carrier_freq': 10e9, 'duration': 10e-6},
        'detection': {'pfa': 1e-6, 'guard': 2, 'train': 8}
    }
    cognitive_pipeline.initialize_from_config(config)
    
    # Create bridge
    bridge = CognitiveRadarBridge(cognitive_pipeline)
    
    print("\\nCognitive-DSP Bridge Interface:")
    print("-" * 70)
    
    # Get signal generation config
    sig_gen_config = bridge.get_signal_generation_config()
    print("\\nSignal Generation Config (for photonic module):")
    for key, val in sig_gen_config.items():
        if isinstance(val, float):
            if 'freq' in key:
                print(f"  {key}: {val/1e9:.2f} GHz")
            elif 'bandwidth' in key:
                print(f"  {key}: {val/1e9:.2f} GHz")
            else:
                print(f"  {key}: {val:.2e}")
        else:
            print(f"  {key}: {val}")
    
    # Get detection config
    det_config = bridge.get_detection_config()
    print("\\nDetection Config (for CA-CFAR module):")
    for key, val in det_config.items():
        print(f"  {key}: {val}")
    
    # Simulate frame update
    print("\\nSimulating post-frame update...")
    report = bridge.post_frame_update(
        detections=[(100.0, 50.0), (105.0, 55.0)],
        tracks=[],
        ai_predictions=[
            {'confidence': 0.72, 'class_probabilities': [0.2, 0.72, 0.08]}
        ],
        rd_map=np.random.randn(128, 128),
        timestamp=0.10
    )
    
    print(f"  Adaptation Frame ID: {report['frame_id']}")
    print(f"  Next TX Bandwidth: {report['next_waveform_params'].bandwidth/1e9:.2f} GHz")
    print(f"  Next TX Power: {report['next_waveform_params'].tx_power_watts:.1f} W")


# ============================================================================
# Example 6: Comparison Mode (Cognitive vs Static)
# ============================================================================

def example_6_cognitive_vs_static():
    """
    Example 6: Runs same scenario in cognitive and static modes for comparison.
    """
    print("\\n" + "="*70)
    print("EXAMPLE 6: Cognitive vs. Static Radar Comparison")
    print("="*70)
    
    config = {
        'photonic': {'bandwidth': 1e9, 'carrier_freq': 10e9, 'duration': 10e-6},
        'detection': {'pfa': 1e-6, 'guard': 2, 'train': 8}
    }
    
    # Scenario: Weak targets in clutter
    detections = [(100.0, 50.0), (150.0, -40.0), (105.0, 2.0), (107.0, -1.0)]
    predictions = [
        {'confidence': 0.55, 'class_probabilities': [0.3, 0.4, 0.3]},
        {'confidence': 0.48, 'class_probabilities': [0.4, 0.3, 0.3]},
        {'confidence': 0.50, 'class_probabilities': [0.35, 0.35, 0.3]},
        {'confidence': 0.52, 'class_probabilities': [0.3, 0.4, 0.3]},
    ]
    
    print("\\nTest Scenario: Weak targets in clutter")
    print("-" * 70)
    
    # STATIC MODE
    print("\\nSTATIC RADAR (Fixed Parameters):")
    static_radar = CognitiveRadarPipeline(enable_cognitive=False)
    static_params = static_radar.initialize_from_config(config)
    print(f"  Bandwidth: {static_params.bandwidth/1e9:.2f} GHz (fixed)")
    print(f"  TX Power: {static_params.tx_power_watts:.1f} W (fixed)")
    print(f"  CFAR Alpha: {static_params.cfar_alpha:.1f} (fixed)")
    
    # COGNITIVE MODE
    print("\\nCOGNITIVE RADAR (Adaptive Parameters):")
    cognitive_radar = CognitiveRadarPipeline(enable_cognitive=True)
    cognitive_radar.initialize_from_config(config)
    
    next_params, cmd, _ = cognitive_radar.process_radar_frame(
        detections=detections,
        tracks=[],
        ai_predictions=predictions,
        timestamp=0.05
    )
    
    print(f"  Bandwidth: {next_params.bandwidth/1e9:.2f} GHz (×{cmd.bandwidth_scaling:.2f})")
    print(f"  TX Power: {next_params.tx_power_watts:.1f} W (×{cmd.tx_power_scaling:.2f})")
    print(f"  CFAR Alpha: {next_params.cfar_alpha:.1f} (×{cmd.cfar_alpha_scale:.2f})")
    
    # Comparison
    print("\\nPERFORMANCE DELTA:")
    print(f"  SNR Improvement: +{cmd.predicted_snr_improvement_db:.1f} dB")
    print(f"  Pfa Change: {cmd.predicted_pfa_change:+.1%}")
    print(f"  Range Resolution: ±{cmd.predicted_range_resolution_m:.1f} m")


# ============================================================================
# Main
# ============================================================================

def main():
    """Run all examples."""
    
    print("\\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  COGNITIVE RADAR INTEGRATION EXAMPLES".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    examples = [
        ("Standalone Cognitive Engine", example_1_standalone_cognitive_engine),
        ("Multi-Frame Scenario Progression", example_2_scenario_progression),
        ("Parameter Adaptation & Hardware Constraints", example_3_parameter_adaptation),
        ("XAI Explanations", example_4_xai_explanations),
        ("DSP Pipeline Integration", example_5_dsp_integration),
        ("Cognitive vs. Static Comparison", example_6_cognitive_vs_static),
    ]
    
    print("\\nAvailable Examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\\nRunning all examples...")
    
    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\\n✗ Example failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\\n" + "█"*70)
    print("  Examples completed successfully!")
    print("█"*70 + "\\n")


if __name__ == '__main__':
    main()
