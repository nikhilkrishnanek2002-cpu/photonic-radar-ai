"""
EW Degradation Models
=====================

Models the effects of electronic warfare countermeasures on radar performance.
Implements degradation for noise jamming, deception jamming, and tracking confidence.

Author: EW Systems Integration Team
"""

import numpy as np
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from interfaces.message_schema import Countermeasure, CountermeasureType

logger = logging.getLogger(__name__)


@dataclass
class DegradationMetrics:
    """Metrics describing EW degradation effects."""
    snr_reduction_db: float = 0.0
    false_tracks_injected: int = 0
    tracks_degraded: int = 0
    mean_quality_reduction: float = 0.0
    detection_probability_reduction: float = 0.0
    range_drift_m: float = 0.0
    velocity_drift_m_s: float = 0.0


class EWDegradationModel:
    """
    Models EW effects on radar performance.
    
    Implements:
    - Noise jamming (SNR reduction)
    - Deception jamming (false track injection)
    - Tracking confidence degradation
    """
    
    def __init__(self,
                 max_snr_degradation_db: float = 20.0,
                 max_quality_degradation: float = 0.5,
                 false_track_probability: float = 0.3):
        """
        Initialize degradation model.
        
        Args:
            max_snr_degradation_db: Maximum SNR reduction from jamming
            max_quality_degradation: Maximum track quality reduction (0-1)
            false_track_probability: Probability of false track per deception CM
        """
        self.max_snr_degradation_db = max_snr_degradation_db
        self.max_quality_degradation = max_quality_degradation
        self.false_track_probability = false_track_probability
        
        self.metrics = DegradationMetrics()
        
        logger.info(f"EW Degradation Model initialized: "
                   f"max_snr_deg={max_snr_degradation_db}dB, "
                   f"max_quality_deg={max_quality_degradation}")
    
    def apply_jamming(self,
                     rd_power: np.ndarray,
                     countermeasures: List[Countermeasure]) -> np.ndarray:
        """
        Apply noise jamming degradation to Range-Doppler map.
        
        Noise jamming increases the noise floor, reducing SNR.
        
        Args:
            rd_power: Range-Doppler power map
            countermeasures: Active countermeasures
            
        Returns:
            Degraded Range-Doppler map
        """
        if len(countermeasures) == 0:
            return rd_power
        
        # Filter for noise jamming countermeasures
        noise_jammers = [cm for cm in countermeasures 
                        if cm.cm_type == CountermeasureType.NOISE_JAM.value]
        
        if len(noise_jammers) == 0:
            return rd_power
        
        # Calculate total jamming power
        total_jammer_power_dbm = self._calculate_total_jammer_power(noise_jammers)
        
        # Estimate signal power (peak of RD map)
        signal_power = np.max(rd_power)
        signal_power_dbm = 10 * np.log10(signal_power + 1e-10)
        
        # Calculate J/S ratio (jammer-to-signal)
        j_s_ratio_db = total_jammer_power_dbm - signal_power_dbm
        
        # SNR degradation: SNR_degraded = SNR / (1 + J/S)
        j_s_linear = 10 ** (j_s_ratio_db / 10)
        snr_degradation_factor = 1.0 / (1.0 + j_s_linear)
        
        # Limit degradation
        snr_reduction_db = -10 * np.log10(snr_degradation_factor)
        snr_reduction_db = min(snr_reduction_db, self.max_snr_degradation_db)
        
        # Apply degradation
        degradation_linear = 10 ** (-snr_reduction_db / 10)
        rd_power_degraded = rd_power * degradation_linear
        
        # Update metrics
        self.metrics.snr_reduction_db = snr_reduction_db
        
        logger.info(f"[EW-DEGRADE] Noise jamming: {len(noise_jammers)} jammers, "
                   f"J/S={j_s_ratio_db:.1f}dB, SNR reduction={snr_reduction_db:.1f}dB")
        
        return rd_power_degraded
    
    def _calculate_total_jammer_power(self, jammers: List[Countermeasure]) -> float:
        """
        Calculate total effective jammer power.
        
        Combines multiple jammers (power sum in linear domain).
        """
        total_power_linear = 0.0
        
        for jammer in jammers:
            if jammer.power_level_dbm is not None:
                # Apply effectiveness score
                effectiveness = jammer.effectiveness_score if jammer.effectiveness_score else 0.7
                power_dbm = jammer.power_level_dbm * effectiveness
                power_linear = 10 ** (power_dbm / 10)
                total_power_linear += power_linear
        
        # Convert back to dBm
        if total_power_linear > 0:
            return 10 * np.log10(total_power_linear)
        else:
            return -100.0  # Very low power
    
    def inject_false_tracks(self,
                           tracks: List[Dict],
                           countermeasures: List[Countermeasure],
                           frame_time: float) -> List[Dict]:
        """
        Inject false tracks from deception jamming.
        
        Creates ghost targets near real tracks to confuse tracking.
        
        Args:
            tracks: Current track list
            countermeasures: Active countermeasures
            frame_time: Current simulation time
            
        Returns:
            Track list with false tracks added
        """
        # Filter for deception jamming
        deception_jammers = [cm for cm in countermeasures
                            if cm.cm_type == CountermeasureType.DECEPTION_JAM.value]
        
        if len(deception_jammers) == 0:
            return tracks
        
        false_tracks = []
        
        for jammer in deception_jammers:
            # Find target track
            target_track = next((t for t in tracks if t.get('track_id') == jammer.target_track_id), None)
            
            if target_track is None:
                continue
            
            # Probabilistic false track generation
            if np.random.random() < self.false_track_probability:
                false_track = self._create_false_track(target_track, jammer, frame_time)
                false_tracks.append(false_track)
        
        # Update metrics
        self.metrics.false_tracks_injected = len(false_tracks)
        
        if len(false_tracks) > 0:
            logger.info(f"[EW-DEGRADE] Deception jamming: {len(false_tracks)} false tracks injected")
        
        return tracks + false_tracks
    
    def _create_false_track(self,
                           real_track: Dict,
                           jammer: Countermeasure,
                           frame_time: float) -> Dict:
        """
        Create a false track near a real track.
        
        Offsets range and velocity to create confusion.
        """
        # Random offsets
        range_offset_m = np.random.uniform(-200, 200)
        velocity_offset_m_s = np.random.uniform(-30, 30)
        
        # Effectiveness affects how convincing the false track is
        effectiveness = jammer.effectiveness_score if jammer.effectiveness_score else 0.5
        quality = 0.3 + 0.3 * effectiveness  # Lower quality than real tracks
        
        false_track = {
            'track_id': 9000 + jammer.countermeasure_id,  # High ID for false tracks
            'range': real_track.get('range', 0) + range_offset_m,
            'velocity': real_track.get('velocity', 0) + velocity_offset_m_s,
            'quality': quality,
            'age': 1,  # New track
            'state': 'PROVISIONAL',  # Not confirmed
            'is_false_track': True,  # Mark as false for analysis
            'source_cm_id': jammer.countermeasure_id
        }
        
        return false_track
    
    def degrade_tracks(self,
                      tracks: List[Dict],
                      countermeasures: List[Countermeasure]) -> List[Dict]:
        """
        Degrade track quality based on active countermeasures.
        
        Reduces track quality for tracks under jamming.
        
        Args:
            tracks: Current track list
            countermeasures: Active countermeasures
            
        Returns:
            Track list with degraded quality scores
        """
        if len(countermeasures) == 0:
            return tracks
        
        degraded_count = 0
        total_quality_reduction = 0.0
        
        for track in tracks:
            # Find countermeasures targeting this track
            targeting_cms = [cm for cm in countermeasures 
                           if cm.target_track_id == track.get('track_id')]
            
            if len(targeting_cms) == 0:
                continue
            
            # Calculate quality degradation
            original_quality = track.get('quality', 1.0)
            quality_reduction = 0.0
            
            for cm in targeting_cms:
                effectiveness = cm.effectiveness_score if cm.effectiveness_score else 0.5
                
                # Different CM types have different effects
                if cm.cm_type == CountermeasureType.NOISE_JAM.value:
                    quality_reduction += 0.2 * effectiveness
                elif cm.cm_type == CountermeasureType.DECEPTION_JAM.value:
                    quality_reduction += 0.3 * effectiveness
            
            # Limit degradation
            quality_reduction = min(quality_reduction, self.max_quality_degradation)
            
            # Apply degradation
            new_quality = max(0.1, original_quality * (1.0 - quality_reduction))
            track['quality'] = new_quality
            track['ew_degraded'] = True
            track['quality_reduction'] = quality_reduction
            
            degraded_count += 1
            total_quality_reduction += quality_reduction
        
        # Update metrics
        self.metrics.tracks_degraded = degraded_count
        if degraded_count > 0:
            self.metrics.mean_quality_reduction = total_quality_reduction / degraded_count
        
        if degraded_count > 0:
            logger.info(f"[EW-DEGRADE] Track quality: {degraded_count} tracks degraded, "
                       f"mean reduction={self.metrics.mean_quality_reduction:.2%}")
        
        return tracks
    
    def apply_drift_to_tracks(self,
                              tracks: List[Dict],
                              countermeasures: List[Countermeasure]) -> List[Dict]:
        """
        Apply range and velocity drift to tracks under jamming.
        
        Drift is proportional to SNR degradation - higher jamming = more drift.
        Physically plausible: degraded SNR reduces tracking accuracy.
        
        Args:
            tracks: Current track list
            countermeasures: Active countermeasures
            
        Returns:
            Track list with drift applied
        """
        if len(countermeasures) == 0:
            return tracks
        
        total_range_drift = 0.0
        total_velocity_drift = 0.0
        drift_count = 0
        
        for track in tracks:
            # Skip false tracks
            if track.get('is_false_track', False):
                continue
            
            # Find countermeasures targeting this track
            targeting_cms = [cm for cm in countermeasures
                           if cm.target_track_id == track.get('track_id')]
            
            if len(targeting_cms) == 0:
                continue
            
            # Calculate drift based on jamming effectiveness
            max_effectiveness = max(cm.effectiveness_score if cm.effectiveness_score else 0.5
                                   for cm in targeting_cms)
            
            # Drift factor: 0.0 (no jamming) to 1.0 (max effectiveness)
            drift_factor = max_effectiveness
            
            # Range drift: 5-50m based on effectiveness
            range_drift_m = np.random.uniform(-5, 5) * (1 + 9 * drift_factor)
            
            # Velocity drift: 1-10 m/s based on effectiveness
            velocity_drift_m_s = np.random.uniform(-1, 1) * (1 + 9 * drift_factor)
            
            # Apply drift
            if 'range' in track:
                track['range'] += range_drift_m
            if 'velocity' in track:
                track['velocity'] += velocity_drift_m_s
            
            # Mark track as drifted
            track['ew_drift_applied'] = True
            track['range_drift_m'] = range_drift_m
            track['velocity_drift_m_s'] = velocity_drift_m_s
            
            total_range_drift += abs(range_drift_m)
            total_velocity_drift += abs(velocity_drift_m_s)
            drift_count += 1
        
        # Update metrics
        if drift_count > 0:
            self.metrics.range_drift_m = total_range_drift / drift_count
            self.metrics.velocity_drift_m_s = total_velocity_drift / drift_count
            
            logger.info(f"[EW-DEGRADE] Drift applied: {drift_count} tracks, "
                       f"mean range drift={self.metrics.range_drift_m:.1f}m, "
                       f"mean velocity drift={self.metrics.velocity_drift_m_s:.1f}m/s")
        
        return tracks
    
    def log_before_after_metrics(self,
                                 before: Dict,
                                 after: Dict,
                                 frame_id: int):
        """
        Log before and after tracking metrics to show jamming impact.
        
        Args:
            before: Metrics before jamming (dict with keys: num_tracks, mean_quality, etc.)
            after: Metrics after jamming
            frame_id: Current frame ID
        """
        logger.info(f"[EW-BEFORE] Frame {frame_id}: "
                   f"Tracks={before.get('num_tracks', 0)}, "
                   f"Quality={before.get('mean_quality', 0.0):.2f}, "
                   f"Detections={before.get('num_detections', 0)}, "
                   f"SNR={before.get('mean_snr_db', 0.0):.1f}dB")
        
        logger.info(f"[EW-AFTER] Frame {frame_id}: "
                   f"Tracks={after.get('num_tracks', 0)}, "
                   f"Quality={after.get('mean_quality', 0.0):.2f}, "
                   f"FalseTracks={after.get('num_false_tracks', 0)}, "
                   f"SNR_reduction={after.get('snr_reduction_db', 0.0):.1f}dB")
        
        # Calculate impact
        track_loss = before.get('num_tracks', 0) - (after.get('num_tracks', 0) - after.get('num_false_tracks', 0))
        quality_loss = before.get('mean_quality', 0.0) - after.get('mean_quality', 0.0)
        
        if track_loss > 0 or quality_loss > 0.05 or after.get('num_false_tracks', 0) > 0:
            logger.warning(f"[EW-IMPACT] Frame {frame_id}: "
                          f"TrackLoss={track_loss}, "
                          f"QualityLoss={quality_loss:.2f}, "
                          f"FalseTracksAdded={after.get('num_false_tracks', 0)}")
    
    def get_metrics(self) -> DegradationMetrics:
        """Get current degradation metrics."""
        return self.metrics
    
    def reset_metrics(self):
        """Reset degradation metrics for new frame."""
        self.metrics = DegradationMetrics()
