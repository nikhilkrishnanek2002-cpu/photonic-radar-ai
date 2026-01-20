"""
Electronic Warfare (EW) Defense - Attack Detection & Cognitive Countermeasures.

Implements:
- Noise jamming detection (SNR degradation)
- Deception jamming detection (false target clusters)
- False target discrimination (ML-based validation)
- Cognitive countermeasures: frequency hopping and waveform randomization
- Full logging and explainability
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import time
from scipy.signal import spectrogram
from scipy import stats


@dataclass
class JammingThreat:
    """Detected jamming threat."""
    threat_type: str           # 'noise_jam', 'deception_jam', 'false_target'
    confidence: float          # [0, 1]
    severity: str              # 'low', 'medium', 'high', 'critical'
    affected_bands: List[Tuple[float, float]]  # frequency ranges affected
    timestamp: float = field(default_factory=time.time)
    details: Dict = field(default_factory=dict)


@dataclass
class CountermeasureAction:
    """Cognitive countermeasure to apply."""
    action_type: str           # 'freq_hop', 'waveform_randomize', 'pattern_shift'
    parameters: Dict           # action-specific parameters
    priority: str              # 'low', 'medium', 'high'
    reason: str                # explanation
    timestamp: float = field(default_factory=time.time)


class NoiseJammingDetector:
    """Detect noise jamming via SNR degradation analysis."""
    
    def __init__(self, history_size: int = 50, snr_threshold_db: float = -5.0):
        """
        Initialize noise jamming detector.
        
        Args:
            history_size: number of frames to track
            snr_threshold_db: SNR degradation threshold (dB)
        """
        self.history_size = history_size
        self.snr_threshold_db = snr_threshold_db
        self.snr_history = []
        self.jam_detection_threshold = 3  # consecutive low-SNR frames
        self.consecutive_low_snr = 0
    
    def compute_snr(self, signal: np.ndarray, fs: float = 4096.0) -> float:
        """
        Estimate SNR of received signal.
        
        Uses spectrogram to separate signal and noise power.
        """
        try:
            # Compute spectrogram
            f, t, Sxx = spectrogram(signal, fs=fs, nperseg=256)
            
            # Signal power in central band (strongest component)
            signal_band_idx = np.argsort(np.mean(Sxx, axis=1))[-5:]  # top 5 frequencies
            signal_power = np.mean(Sxx[signal_band_idx, :])
            
            # Noise power in quiet band
            noise_band_idx = np.argsort(np.mean(Sxx, axis=1))[:5]  # lowest 5 frequencies
            noise_power = np.mean(Sxx[noise_band_idx, :])
            
            # SNR in dB
            snr_db = 10 * np.log10(signal_power / (noise_power + 1e-10))
            return float(np.clip(snr_db, -30, 50))
        except Exception as e:
            return 0.0
    
    def detect(self, signal: np.ndarray) -> Optional[JammingThreat]:
        """
        Detect noise jamming from signal.
        
        Returns:
            JammingThreat if jamming detected, else None
        """
        snr = self.compute_snr(signal)
        self.snr_history.append(snr)
        if len(self.snr_history) > self.history_size:
            self.snr_history.pop(0)
        
        # Check for prolonged low SNR
        if snr < self.snr_threshold_db:
            self.consecutive_low_snr += 1
        else:
            self.consecutive_low_snr = 0
        
        if self.consecutive_low_snr >= self.jam_detection_threshold:
            # Compute degradation
            recent_mean = np.mean(self.snr_history[-10:]) if len(self.snr_history) >= 10 else snr
            historical_mean = np.mean(self.snr_history[:-10]) if len(self.snr_history) > 10 else recent_mean
            degradation = historical_mean - recent_mean
            
            severity = self._classify_severity(snr, degradation)
            
            threat = JammingThreat(
                threat_type='noise_jam',
                confidence=min(self.consecutive_low_snr / (self.jam_detection_threshold * 2), 1.0),
                severity=severity,
                affected_bands=[(0, 2048)],  # Broadband noise jam
                details={
                    'snr_db': snr,
                    'degradation_db': degradation,
                    'consecutive_frames': self.consecutive_low_snr
                }
            )
            return threat
        
        return None
    
    def _classify_severity(self, snr: float, degradation: float) -> str:
        """Classify jamming severity."""
        if snr < -15 or degradation > 20:
            return 'critical'
        elif snr < -10 or degradation > 15:
            return 'high'
        elif snr < -5 or degradation > 10:
            return 'medium'
        else:
            return 'low'


class DeceptionJammingDetector:
    """Detect deception jamming via false target clustering."""
    
    def __init__(self, max_detections_per_frame: int = 50):
        """
        Initialize deception jamming detector.
        
        Args:
            max_detections_per_frame: expected max detections per frame
        """
        self.max_detections_per_frame = max_detections_per_frame
        self.detection_history = []
        self.history_size = 20
    
    def detect(self, detections: List[Tuple[float, float, float]]) -> Optional[JammingThreat]:
        """
        Detect deception jamming via anomalous detection patterns.
        
        Args:
            detections: list of (range, doppler, value) detections
        
        Returns:
            JammingThreat if deception jamming detected, else None
        """
        num_detections = len(detections)
        self.detection_history.append(num_detections)
        if len(self.detection_history) > self.history_size:
            self.detection_history.pop(0)
        
        # Detect burst of detections (typical of deception jam)
        if num_detections > self.max_detections_per_frame:
            historical_mean = np.mean(self.detection_history[:-1]) if len(self.detection_history) > 1 else num_detections / 2
            excess_factor = num_detections / max(historical_mean, 1)
            
            if excess_factor > 2.5:  # More than 2.5x normal detections
                confidence = min((excess_factor - 2.5) / 2.5, 1.0)
                
                threat = JammingThreat(
                    threat_type='deception_jam',
                    confidence=confidence,
                    severity=self._classify_detection_severity(excess_factor),
                    affected_bands=[(0, 2048)],
                    details={
                        'detections': num_detections,
                        'historical_mean': historical_mean,
                        'excess_factor': excess_factor
                    }
                )
                return threat
        
        return None
    
    def _classify_detection_severity(self, excess_factor: float) -> str:
        """Classify deception jamming severity."""
        if excess_factor > 5:
            return 'critical'
        elif excess_factor > 4:
            return 'high'
        elif excess_factor > 3:
            return 'medium'
        else:
            return 'low'


class FalseTargetDiscriminator:
    """Discriminate false targets from real detections using statistical analysis."""
    
    def __init__(self, ml_confidence_threshold: float = 0.7):
        """
        Initialize false target discriminator.
        
        Args:
            ml_confidence_threshold: AI model confidence threshold
        """
        self.ml_confidence_threshold = ml_confidence_threshold
        self.target_consistency_memory = defaultdict(list)
        self.memory_size = 10
    
    def discriminate(self, 
                    detections: List[Tuple[float, float, float]],
                    ai_labels: List[str],
                    ai_confidences: List[float]) -> Tuple[List[bool], Optional[JammingThreat]]:
        """
        Discriminate false targets from real detections.
        
        Args:
            detections: list of (range, doppler, value)
            ai_labels: AI classification labels for each detection
            ai_confidences: AI confidence scores for each detection
        
        Returns:
            (is_real: list of bools, threat: JammingThreat or None)
        """
        is_real = []
        false_count = 0
        
        for i, (det, label, conf) in enumerate(zip(detections, ai_labels, ai_confidences)):
            # Rule 1: Low AI confidence suggests false target
            confidence_score = conf >= self.ml_confidence_threshold
            
            # Rule 2: Clutter detected suggests false target or secondary echo
            if label == 'Clutter':
                confidence_score = False
            
            # Rule 3: Check for unrealistic positions or velocities
            range_idx, doppler_idx, value = det
            unrealistic = self._check_unrealistic(range_idx, doppler_idx)
            confidence_score = confidence_score and not unrealistic
            
            is_real.append(confidence_score)
            if not confidence_score:
                false_count += 1
        
        threat = None
        if len(detections) > 0 and false_count / len(detections) > 0.5:
            threat = JammingThreat(
                threat_type='false_target',
                confidence=min(false_count / len(detections), 1.0),
                severity='medium' if false_count / len(detections) > 0.7 else 'low',
                affected_bands=[(0, 2048)],
                details={
                    'false_targets': false_count,
                    'total_detections': len(detections),
                    'false_ratio': false_count / len(detections)
                }
            )
        
        return is_real, threat
    
    def _check_unrealistic(self, range_idx: float, doppler_idx: float) -> bool:
        """Check if detection is at unrealistic position/velocity."""
        # Unrealistic if beyond expected operational range
        if range_idx > 120 or range_idx < 1:  # Assuming 128 range bins
            return True
        # Unrealistic if doppler way off center
        if abs(doppler_idx - 64) > 60:  # Assuming 128 doppler bins
            return True
        return False


class FrequencyHopper:
    """Frequency hopping countermeasure."""
    
    def __init__(self, base_freq_hz: float = 10e9, hop_set_size: int = 10):
        """
        Initialize frequency hopper.
        
        Args:
            base_freq_hz: base carrier frequency (Hz)
            hop_set_size: number of frequencies to hop across
        """
        self.base_freq_hz = base_freq_hz
        self.hop_set_size = hop_set_size
        self.freq_offset_step = 50e6  # 50 MHz steps
        self.current_hop_index = 0
        self.hop_sequence = []
        self._generate_hop_sequence()
    
    def _generate_hop_sequence(self):
        """Generate pseudo-random frequency hop sequence."""
        np.random.seed(int(time.time()) % 1000)  # Semi-random based on time
        self.hop_sequence = np.random.permutation(self.hop_set_size)
    
    def get_next_hop(self) -> float:
        """Get next hopping frequency."""
        hop_idx = self.hop_sequence[self.current_hop_index % len(self.hop_sequence)]
        freq_offset = (hop_idx - self.hop_set_size / 2) * self.freq_offset_step
        next_freq = self.base_freq_hz + freq_offset
        self.current_hop_index += 1
        return float(next_freq)
    
    def get_current_freq(self) -> float:
        """Get current hopping frequency."""
        hop_idx = self.hop_sequence[(self.current_hop_index - 1) % len(self.hop_sequence)]
        freq_offset = (hop_idx - self.hop_set_size / 2) * self.freq_offset_step
        return float(self.base_freq_hz + freq_offset)


class WaveformRandomizer:
    """Waveform randomization countermeasure."""
    
    def __init__(self, config: Dict = None):
        """
        Initialize waveform randomizer.
        
        Args:
            config: dict with 'pulse_width_variation', 'chirp_randomization', etc.
        """
        self.config = config or {}
        self.pulse_widths = [1e-6, 2e-6, 5e-6, 10e-6]  # microseconds
        self.prf_values = [10e3, 15e3, 20e3, 25e3]      # Hz
        self.randomization_state = 0
    
    def get_random_waveform_params(self) -> Dict:
        """Generate randomized waveform parameters."""
        pulse_width = np.random.choice(self.pulse_widths)
        prf = np.random.choice(self.prf_values)
        chirp_bandwidth = np.random.choice([10e6, 20e6, 50e6, 100e6])
        
        params = {
            'pulse_width_us': pulse_width * 1e6,
            'prf_hz': prf,
            'chirp_bandwidth_hz': chirp_bandwidth,
            'pattern_seed': np.random.randint(0, 10000)
        }
        
        return params


class EWDefenseController:
    """Top-level EW defense orchestrator."""
    
    def __init__(self, config: Dict = None):
        """
        Initialize EW defense system.
        
        Args:
            config: dict with EW parameters
        """
        self.config = config or {}
        
        # Initialize detectors
        self.noise_detector = NoiseJammingDetector(
            history_size=self.config.get('noise_history_size', 50),
            snr_threshold_db=self.config.get('snr_threshold_db', -5.0)
        )
        self.deception_detector = DeceptionJammingDetector(
            max_detections_per_frame=self.config.get('max_detections', 50)
        )
        self.false_target_discriminator = FalseTargetDiscriminator(
            ml_confidence_threshold=self.config.get('ml_threshold', 0.7)
        )
        
        # Initialize countermeasures
        self.freq_hopper = FrequencyHopper(
            base_freq_hz=self.config.get('base_freq_hz', 10e9),
            hop_set_size=self.config.get('hop_set_size', 10)
        )
        self.waveform_randomizer = WaveformRandomizer(self.config)
        
        # State tracking
        self.threats = []
        self.countermeasures = []
        self.ew_active = False
        self.threat_level = 'green'  # green, yellow, orange, red
    
    def analyze(self,
               signal: np.ndarray,
               detections: List[Tuple[float, float, float]],
               ai_labels: List[str] = None,
               ai_confidences: List[float] = None) -> Dict:
        """
        Comprehensive EW threat analysis.
        
        Args:
            signal: received radar signal
            detections: list of (range, doppler, value)
            ai_labels: AI classification labels
            ai_confidences: AI confidence scores
        
        Returns:
            dict with threats, countermeasures, recommendations
        """
        self.threats = []
        self.countermeasures = []
        
        # Step 1: Noise jamming detection
        noise_threat = self.noise_detector.detect(signal)
        if noise_threat:
            self.threats.append(noise_threat)
        
        # Step 2: Deception jamming detection
        deception_threat = self.deception_detector.detect(detections)
        if deception_threat:
            self.threats.append(deception_threat)
        
        # Step 3: False target discrimination
        if ai_labels and ai_confidences:
            is_real, false_threat = self.false_target_discriminator.discriminate(
                detections, ai_labels, ai_confidences
            )
            if false_threat:
                self.threats.append(false_threat)
        else:
            is_real = [True] * len(detections)
        
        # Step 4: Generate countermeasures
        if self.threats:
            self.ew_active = True
            self._generate_countermeasures()
            self._update_threat_level()
        else:
            self.ew_active = False
            self.threat_level = 'green'
        
        return {
            'threats': self.threats,
            'countermeasures': self.countermeasures,
            'threat_level': self.threat_level,
            'ew_active': self.ew_active,
            'real_detections': is_real,
            'recommendations': self._get_recommendations()
        }
    
    def _generate_countermeasures(self):
        """Generate cognitive countermeasures based on threats."""
        total_confidence = sum(t.confidence for t in self.threats)
        
        if total_confidence > 0.7:
            # Activate frequency hopping
            next_freq = self.freq_hopper.get_next_hop()
            self.countermeasures.append(CountermeasureAction(
                action_type='freq_hop',
                parameters={'frequency_hz': next_freq},
                priority='high',
                reason=f"High EW threat detected (confidence: {total_confidence:.2f})"
            ))
            
            # Activate waveform randomization
            wf_params = self.waveform_randomizer.get_random_waveform_params()
            self.countermeasures.append(CountermeasureAction(
                action_type='waveform_randomize',
                parameters=wf_params,
                priority='high',
                reason="Randomizing waveform to defeat adaptive jamming"
            ))
        elif total_confidence > 0.4:
            # Moderate threat: pattern shift
            self.countermeasures.append(CountermeasureAction(
                action_type='pattern_shift',
                parameters={'shift_factor': np.random.uniform(0.8, 1.2)},
                priority='medium',
                reason="Moderate EW threat detected, applying pattern shift"
            ))
    
    def _update_threat_level(self):
        """Update overall threat level."""
        max_confidence = max((t.confidence for t in self.threats), default=0.0)
        max_severity = max(
            {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}.get(t.severity, 0) 
            for t in self.threats
        ) if self.threats else 0
        
        threat_score = max_confidence * 0.7 + (max_severity / 4) * 0.3
        
        if threat_score > 0.75:
            self.threat_level = 'red'
        elif threat_score > 0.5:
            self.threat_level = 'orange'
        elif threat_score > 0.25:
            self.threat_level = 'yellow'
        else:
            self.threat_level = 'green'
    
    def _get_recommendations(self) -> List[str]:
        """Get operator recommendations."""
        recommendations = []
        
        for threat in self.threats:
            if threat.threat_type == 'noise_jam':
                recommendations.append("⚠️ NOISE JAMMING: Increase transmit power or reduce integration time")
            elif threat.threat_type == 'deception_jam':
                recommendations.append("⚠️ DECEPTION JAMMING: Activate multi-frequency radar or waveform diversity")
            elif threat.threat_type == 'false_target':
                recommendations.append("⚠️ FALSE TARGETS: Increase AI confidence threshold or manual review detections")
        
        if self.ew_active:
            recommendations.append("✓ EW Defense Active: Applying frequency hopping and waveform randomization")
        
        return recommendations
    
    def get_status(self) -> Dict:
        """Get EW defense status."""
        return {
            'ew_active': self.ew_active,
            'threat_level': self.threat_level,
            'num_threats': len(self.threats),
            'num_countermeasures': len(self.countermeasures),
            'current_frequency_hz': self.freq_hopper.get_current_freq(),
            'threat_types': [t.threat_type for t in self.threats],
            'threat_confidences': [t.confidence for t in self.threats]
        }


# Example usage
if __name__ == "__main__":
    print("=== Electronic Warfare Defense Demo ===\n")
    
    ew_controller = EWDefenseController({
        'snr_threshold_db': -5.0,
        'max_detections': 50,
        'ml_threshold': 0.7
    })
    
    # Simulate 10 radar frames
    for frame in range(10):
        print(f"Frame {frame}:")
        
        # Simulate signal with random noise (sometimes jammed)
        signal = np.random.randn(4096)
        if frame > 5:
            signal *= np.random.uniform(0.1, 0.5)  # Add jamming effect
        
        # Simulate detections (with occasional false targets)
        num_detections = np.random.randint(5, 20)
        if frame > 6:
            num_detections *= 3  # Simulate deception jam burst
        
        detections = [(np.random.uniform(10, 120), np.random.uniform(0, 128), 0.5) 
                     for _ in range(num_detections)]
        
        # Simulate AI labels and confidences
        labels = [np.random.choice(['Drone', 'Aircraft', 'Clutter']) for _ in detections]
        confidences = [np.random.uniform(0.4, 1.0) for _ in detections]
        
        # Analyze
        result = ew_controller.analyze(signal, detections, labels, confidences)
        
        print(f"  Threat Level: {result['threat_level']}")
        if result['threats']:
            for t in result['threats']:
                print(f"    - {t.threat_type} (conf={t.confidence:.2f}, sev={t.severity})")
        
        if result['countermeasures']:
            for cm in result['countermeasures']:
                print(f"    ⚡ {cm.action_type}: {cm.reason}")
        
        status = ew_controller.get_status()
        print(f"  Status: {status['threat_level']}, Current Freq: {status['current_frequency_hz']/1e9:.2f} GHz\n")
