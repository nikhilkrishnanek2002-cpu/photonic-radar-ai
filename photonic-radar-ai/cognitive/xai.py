"""
Cognitive Radar XAI (Explainable AI) Feedback Module
===================================================

Provides transparent, interpretable explanations for all cognitive decisions.
Maps neural network decisions and radar parameters to human-readable narratives.

This module:
1. Generates decision justifications (rule-based, not black-box)
2. Explains parameter changes in radar physics terms
3. Provides confidence scores for each decision
4. Correlates XAI to operator understanding

Author: Explainable AI Systems
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum


class DecisionRationale(Enum):
    """Enum for common decision justifications."""
    
    # Power decisions
    LOW_CONFIDENCE_BOOST = "Low detection confidence requires transmit power boost"
    HIGH_CONFIDENCE_REDUCE = "High confidence enables power reduction for efficiency"
    STABLE_TRACKS_REDUCE = "Stable tracks allow power reduction"
    WEAK_TARGETS_BOOST = "Weak signal environment requires power boost"
    
    # Bandwidth decisions
    CLUTTER_RICH_EXPAND = "Clutter-rich environment benefits from bandwidth expansion (range resolution)"
    DENSE_TARGETS_EXPAND = "Dense target swarm requires wider bandwidth for separation"
    SEARCH_MODE_STANDARD = "Search mode uses standard bandwidth"
    TRACKING_MODE_STANDARD = "Tracking mode uses standard bandwidth"
    
    # CFAR decisions
    HIGH_CONFIDENCE_TIGHT = "High confidence enables aggressive (tight) CFAR threshold"
    CLUTTER_DEFENSE_RELAX = "Clutter defense requires relaxed (loose) CFAR threshold"
    NORMAL_CONDITIONS_NOMINAL = "Normal operating conditions, nominal CFAR"
    
    # Dwell time decisions
    UNSTABLE_TRACKS_EXTEND = "Unstable tracks need extended coherent integration time"
    STABLE_TRACKS_NOMINAL = "Stable tracks support nominal dwell time"
    FLUCTUATING_TARGET_EXTEND = "Fluctuating target requires extended observation"
    
    # PRF decisions
    HIGH_VELOCITY_SPREAD_REDUCE = "High velocity spread requires reduced PRF (widen Doppler unambiguity)"
    NORMAL_VELOCITIES_NOMINAL = "Velocity spread within normal bounds, nominal PRF"


@dataclass
class ParameterExplanation:
    """Explanation for a single parameter decision."""
    parameter_name: str
    scaling_factor: float
    rationale: DecisionRationale
    radar_principle: str
    quantitative_justification: Dict  # e.g., {'confidence': 0.55, 'threshold': 0.60}
    expected_effect: str


@dataclass
class CognitiveDecisionNarrative:
    """Complete XAI narrative for a cognitive frame."""
    frame_id: int
    timestamp: float
    
    # Scene characterization
    scene_type: str
    scene_metrics: Dict
    
    # Individual parameter explanations
    parameter_explanations: List[ParameterExplanation]
    
    # Overall decision confidence
    decision_confidence: float  # 0-1
    
    # Operator-friendly text
    executive_summary: str
    detailed_explanation: str
    
    # Risk assessment
    potential_risks: List[str]
    
    # Comparison to baseline
    comparison_to_static: str


class CognitiveRadarXAI:
    """
    Explainable AI module for cognitive radar decisions.
    
    Generates human-interpretable narratives for all adaptive decisions.
    """
    
    # Radar physics principles (for explanation)
    RADAR_PRINCIPLES = {
        'tx_power': {
            'principle': 'Radar equation: SNR ∝ Ptx',
            'explanation': 'Transmitted power directly increases signal-to-noise ratio'
        },
        'bandwidth': {
            'principle': 'Range resolution: Δr = c/(2B)',
            'explanation': 'Wider bandwidth improves range resolution for target separation'
        },
        'cfar_alpha': {
            'principle': 'CFAR detection: Pfa = exp(-α)',
            'explanation': 'Alpha threshold controls false alarm rate vs. detection probability trade-off'
        },
        'dwell_time': {
            'principle': 'Processing gain: G = 10·log10(N)',
            'explanation': 'Coherent integration of N pulses improves SNR by factor N'
        },
        'prf': {
            'principle': 'Unambiguous range: R_ua = c/(2·PRF)',
            'explanation': 'PRF determines maximum unambiguous range and Doppler coverage'
        },
    }
    
    def __init__(self):
        """Initialize XAI module."""
        self.logger = None
    
    def explain_situation_assessment(self, assessment) -> str:
        """
        Generate narrative explaining scene assessment.
        
        Args:
            assessment: SituationAssessment object
            
        Returns:
            Formatted text explaining current scene
        """
        narrative = f"""
┌─ SCENE ASSESSMENT ─────────────────────────────────────────┐
│                                                              │
│ Scene Type: {assessment.scene_type.value}
│ 
│ Detection Environment:
│   • Active Confirmed Tracks: {assessment.num_confirmed_tracks}
│   • Provisional Tracks: {assessment.num_provisional_tracks}
│   • Total Detections: {assessment.num_detections}
│   • Estimated False Alarms: {assessment.num_false_alarms}
│   • Clutter Ratio: {assessment.clutter_ratio:.1%}
│ """
        
        if assessment.clutter_ratio > 0.2:
            narrative += "│   ⚠️  Clutter-rich environment detected\n"
        elif assessment.clutter_ratio < 0.05:
            narrative += "│   ✓ Clean environment (low clutter)\n"
        
        narrative += f"""│
│ Classification Performance:
│   • Mean Confidence: {assessment.mean_classification_confidence:.1%}
│   • Class Uncertainty (entropy): {assessment.mean_class_entropy:.2f}
│ """
        
        if assessment.mean_classification_confidence > 0.8:
            narrative += "│   ✓ High confidence in classifications\n"
        elif assessment.mean_classification_confidence < 0.6:
            narrative += "│   ⚠️  Low confidence - more data needed\n"
        
        narrative += f"""│
│ Track Quality:
│   • Mean Stability: {assessment.mean_track_stability:.2f}
│   • Mean Track Age: {assessment.mean_track_age:.1f} frames
│   • Velocity Spread: {assessment.mean_velocity_spread:.1f} m/s
│ """
        
        if assessment.mean_track_stability > 0.8:
            narrative += "│   ✓ Stable, high-confidence tracks\n"
        elif assessment.mean_track_stability < 0.5:
            narrative += "│   ⚠️  Unstable tracks require attention\n"
        
        narrative += f"""│
│ Signal Characteristics:
│   • Estimated SNR: {assessment.estimated_snr_db:.1f} dB
│   • Mean Signal Power: {assessment.mean_signal_power:.2e}
│   • Noise Floor: {assessment.mean_noise_power:.2e}
│
└────────────────────────────────────────────────────────────┘
"""
        return narrative
    
    def explain_tx_power_decision(self, 
                                  confidence: float,
                                  track_stability: float,
                                  snr_db: float,
                                  scaling: float) -> ParameterExplanation:
        """Generate explanation for TX power adaptation."""
        
        if confidence < 0.6:
            rationale = DecisionRationale.LOW_CONFIDENCE_BOOST
            effect = f"Boost transmit power {scaling:.0%} to improve weak target SNR"
            justification = {
                'confidence': confidence,
                'threshold': 0.6,
                'reasoning': 'Confidence below threshold triggers power boost'
            }
        elif track_stability > 0.9 and snr_db > 20:
            rationale = DecisionRationale.HIGH_CONFIDENCE_REDUCE
            effect = f"Reduce transmit power {(1-scaling):.0%} for efficiency"
            justification = {
                'track_stability': track_stability,
                'snr_db': snr_db,
                'reasoning': 'Stable tracks + high SNR enable power conservation'
            }
        else:
            rationale = DecisionRationale.NORMAL_CONDITIONS_NOMINAL
            effect = "Maintain nominal transmit power"
            justification = {'scaling': scaling}
        
        return ParameterExplanation(
            parameter_name='TX Power',
            scaling_factor=scaling,
            rationale=rationale,
            radar_principle=self.RADAR_PRINCIPLES['tx_power']['principle'],
            quantitative_justification=justification,
            expected_effect=effect
        )
    
    def explain_bandwidth_decision(self,
                                   scene_type: str,
                                   clutter_ratio: float,
                                   num_confirmed: int,
                                   scaling: float) -> ParameterExplanation:
        """Generate explanation for bandwidth adaptation."""
        
        if scene_type == 'Cluttered' and clutter_ratio > 0.2:
            rationale = DecisionRationale.CLUTTER_RICH_EXPAND
            effect = f"Expand bandwidth {scaling:.0%} for clutter rejection via range resolution"
            justification = {
                'clutter_ratio': clutter_ratio,
                'threshold': 0.2,
                'reasoning': 'Clutter-rich environments benefit from improved range resolution'
            }
        elif scene_type == 'Dense' and num_confirmed > 5:
            rationale = DecisionRationale.DENSE_TARGETS_EXPAND
            effect = f"Expand bandwidth {scaling:.0%} to separate {num_confirmed} closely-spaced targets"
            justification = {
                'num_targets': num_confirmed,
                'reasoning': 'Dense swarm requires better target separation'
            }
        else:
            rationale = DecisionRationale.SEARCH_MODE_STANDARD
            effect = "Maintain standard bandwidth"
            justification = {'scaling': scaling}
        
        return ParameterExplanation(
            parameter_name='Chirp Bandwidth',
            scaling_factor=scaling,
            rationale=rationale,
            radar_principle=self.RADAR_PRINCIPLES['bandwidth']['principle'],
            quantitative_justification=justification,
            expected_effect=effect
        )
    
    def explain_cfar_decision(self,
                             confidence: float,
                             scene_type: str,
                             clutter_ratio: float,
                             scaling: float) -> ParameterExplanation:
        """Generate explanation for CFAR threshold adaptation."""
        
        if confidence > 0.85:
            rationale = DecisionRationale.HIGH_CONFIDENCE_TIGHT
            effect = f"Tighten CFAR threshold {(1-scaling):.0%} for aggressive detection"
            justification = {
                'confidence': confidence,
                'threshold': 0.85,
                'reasoning': 'High confidence enables tight threshold without false alarm risk'
            }
        elif scene_type == 'Cluttered' and clutter_ratio > 0.2:
            rationale = DecisionRationale.CLUTTER_DEFENSE_RELAX
            effect = f"Relax CFAR threshold {scaling:.0%} to reduce clutter false alarms"
            justification = {
                'clutter_ratio': clutter_ratio,
                'reasoning': 'Conservative threshold prevents clutter-induced false alarms'
            }
        else:
            rationale = DecisionRationale.NORMAL_CONDITIONS_NOMINAL
            effect = "Maintain nominal CFAR threshold"
            justification = {'scaling': scaling}
        
        return ParameterExplanation(
            parameter_name='CFAR Threshold Alpha',
            scaling_factor=scaling,
            rationale=rationale,
            radar_principle=self.RADAR_PRINCIPLES['cfar_alpha']['principle'],
            quantitative_justification=justification,
            expected_effect=effect
        )
    
    def explain_dwell_time_decision(self,
                                    track_stability: float,
                                    scaling: float) -> ParameterExplanation:
        """Generate explanation for dwell time adaptation."""
        
        if track_stability < 0.5:
            rationale = DecisionRationale.UNSTABLE_TRACKS_EXTEND
            effect = f"Extend coherent dwell time {scaling:.0%} to stabilize weak targets"
            justification = {
                'track_stability': track_stability,
                'threshold': 0.5,
                'reasoning': 'Unstable tracks need more observations for stability'
            }
        else:
            rationale = DecisionRationale.STABLE_TRACKS_NOMINAL
            effect = "Maintain standard dwell time"
            justification = {'scaling': scaling}
        
        return ParameterExplanation(
            parameter_name='Coherent Dwell Time',
            scaling_factor=scaling,
            rationale=rationale,
            radar_principle=self.RADAR_PRINCIPLES['dwell_time']['principle'],
            quantitative_justification=justification,
            expected_effect=effect
        )
    
    def explain_prf_decision(self,
                            velocity_spread: float,
                            scaling: float) -> ParameterExplanation:
        """Generate explanation for PRF adaptation."""
        
        if velocity_spread > 100:
            rationale = DecisionRationale.HIGH_VELOCITY_SPREAD_REDUCE
            effect = f"Reduce PRF {(1-scaling):.0%} to widen Doppler unambiguous range"
            justification = {
                'velocity_spread': velocity_spread,
                'threshold': 100,
                'reasoning': 'High velocity spread risks Doppler aliasing'
            }
        else:
            rationale = DecisionRationale.NORMAL_VELOCITIES_NOMINAL
            effect = "Maintain nominal PRF"
            justification = {'scaling': scaling}
        
        return ParameterExplanation(
            parameter_name='Pulse Repetition Frequency',
            scaling_factor=scaling,
            rationale=rationale,
            radar_principle=self.RADAR_PRINCIPLES['prf']['principle'],
            quantitative_justification=justification,
            expected_effect=effect
        )
    
    def build_complete_narrative(self,
                                assessment,
                                cmd,
                                parameter_explanations: List[ParameterExplanation]) -> CognitiveDecisionNarrative:
        """
        Build complete XAI narrative for a cognitive decision.
        
        Args:
            assessment: SituationAssessment
            cmd: AdaptationCommand
            parameter_explanations: List of ParameterExplanation objects
            
        Returns:
            CognitiveDecisionNarrative
        """
        
        # Executive summary
        exec_summary = f"Frame {assessment.frame_id}: {assessment.scene_type.value} environment "
        exec_summary += f"(Conf={assessment.mean_classification_confidence:.0%}, "
        exec_summary += f"Clutter={assessment.clutter_ratio:.0%}). "
        
        num_decisions_aggressive = sum(1 for s in [cmd.tx_power_scaling, cmd.bandwidth_scaling] if s > 1.0)
        num_decisions_conservative = sum(1 for s in [cmd.cfar_alpha_scale, cmd.prf_scale] if s > 1.0)
        
        if num_decisions_aggressive >= 2:
            exec_summary += "AGGRESSIVE posture: Boost sensing resources."
        elif num_decisions_conservative >= 2:
            exec_summary += "CONSERVATIVE posture: Reduce false alarms."
        else:
            exec_summary += "NOMINAL operations."
        
        # Detailed explanation
        detailed = "PARAMETER-BY-PARAMETER ANALYSIS:\n\n"
        for exp in parameter_explanations:
            detailed += f"• {exp.parameter_name} (×{exp.scaling_factor:.2f})\n"
            detailed += f"  Rationale: {exp.rationale.value}\n"
            detailed += f"  Physics: {exp.radar_principle}\n"
            detailed += f"  Expected: {exp.expected_effect}\n\n"
        
        # Risk assessment
        risks = []
        if cmd.tx_power_scaling > 1.8:
            risks.append("⚠️  Very high power consumption (1.8×+)")
        if cmd.bandwidth_scaling > 1.4:
            risks.append("⚠️  Very wide bandwidth may exceed hardware specs")
        if cmd.cfar_alpha_scale > 1.2:
            risks.append("⚠️  Loose CFAR may increase false alarms")
        if assessment.clutter_ratio > 0.4:
            risks.append("⚠️  Very high clutter environment - consider tactical retreat")
        if assessment.mean_classification_confidence < 0.5:
            risks.append("⚠️  Very low classification confidence - uncertain identifications")
        
        # Comparison to static
        comparison = "vs. STATIC RADAR:\n"
        comparison += f"  • TX Power: {cmd.tx_power_scaling:.0%} (static: fixed)\n"
        comparison += f"  • Bandwidth: {cmd.bandwidth_scaling:.0%} (static: fixed)\n"
        comparison += f"  • CFAR: {cmd.cfar_alpha_scale:.0%} (static: fixed)\n"
        comparison += f"  • SNR Gain: +{cmd.predicted_snr_improvement_db:.1f} dB vs. static\n"
        
        narrative = CognitiveDecisionNarrative(
            frame_id=assessment.frame_id,
            timestamp=assessment.timestamp,
            scene_type=assessment.scene_type.value,
            scene_metrics={
                'num_targets': assessment.num_confirmed_tracks,
                'clutter_ratio': assessment.clutter_ratio,
                'confidence': assessment.mean_classification_confidence,
                'stability': assessment.mean_track_stability,
                'snr_db': assessment.estimated_snr_db,
            },
            parameter_explanations=parameter_explanations,
            decision_confidence=cmd.decision_confidence,
            executive_summary=exec_summary,
            detailed_explanation=detailed,
            potential_risks=risks,
            comparison_to_static=comparison,
        )
        
        return narrative
    
    def format_narrative_for_display(self, narrative: CognitiveDecisionNarrative) -> str:
        """
        Format complete narrative for operator display.
        
        Returns:
            Pretty-printed string for UI/logs
        """
        output = f"""
╔════════════════════════════════════════════════════════════════════╗
║         COGNITIVE RADAR ADAPTIVE DECISION REPORT                   ║
║                    Frame {narrative.frame_id}                                     ║
╚════════════════════════════════════════════════════════════════════╝

EXECUTIVE SUMMARY:
  {narrative.executive_summary}

SCENE CHARACTERISTICS:
  • Type: {narrative.scene_type}
  • Active Targets: {narrative.scene_metrics['num_targets']}
  • Clutter Ratio: {narrative.scene_metrics['clutter_ratio']:.1%}
  • Classification Confidence: {narrative.scene_metrics['confidence']:.1%}
  • Track Stability: {narrative.scene_metrics['stability']:.2f}
  • SNR: {narrative.scene_metrics['snr_db']:.1f} dB

COGNITIVE DECISIONS (Confidence: {narrative.decision_confidence:.0%}):

{narrative.detailed_explanation}

RISK ASSESSMENT:
"""
        if narrative.potential_risks:
            for risk in narrative.potential_risks:
                output += f"  {risk}\n"
        else:
            output += "  ✓ No significant risks detected\n"
        
        output += f"""
PERFORMANCE vs. STATIC RADAR:
{narrative.comparison_to_static}

╚════════════════════════════════════════════════════════════════════╝
"""
        return output
