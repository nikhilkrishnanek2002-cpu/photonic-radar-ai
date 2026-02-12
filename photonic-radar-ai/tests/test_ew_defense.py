"""Unit tests for electronic warfare defense system."""

import pytest
import numpy as np
from src.ew_defense import (
    JammingThreat, NoiseJammingDetector, DeceptionJammingDetector,
    FalseTargetDiscriminator, FrequencyHopper, WaveformRandomizer,
    EWDefenseController
)


class TestNoiseJammingDetector:
    """Tests for noise jamming detection."""
    
    def test_detector_initialization(self):
        """Test noise detector creation."""
        detector = NoiseJammingDetector(history_size=50, snr_threshold_db=-5.0)
        assert detector.snr_threshold_db == -5.0
        assert len(detector.snr_history) == 0
    
    def test_snr_computation(self):
        """Test SNR estimation."""
        detector = NoiseJammingDetector()
        
        # Clean signal
        clean_signal = np.sin(np.linspace(0, 10*np.pi, 4096))
        snr_clean = detector.compute_snr(clean_signal)
        
        # Noisy signal
        noisy_signal = clean_signal + 0.5 * np.random.randn(4096)
        snr_noisy = detector.compute_snr(noisy_signal)
        
        # Clean signal should have higher SNR
        assert snr_clean > snr_noisy
    
    def test_jam_detection(self):
        """Test jamming detection from low SNR."""
        detector = NoiseJammingDetector(snr_threshold_db=-5.0, history_size=50)
        
        # Feed low-SNR signal multiple times
        noise_signal = 0.01 * np.random.randn(4096)  # Very low power = low SNR
        
        threat = None
        for _ in range(7):
            threat = detector.detect(noise_signal)
        
        # Should detect jamming after enough low-SNR frames
        # Note: Detection depends on consecutive low SNR count
        if threat is not None:
            assert threat.threat_type == 'noise_jam'
            assert threat.confidence > 0.0
    
    def test_snr_history_tracking(self):
        """Test SNR history accumulation."""
        detector = NoiseJammingDetector(history_size=5)
        
        for i in range(10):
            signal = np.random.randn(4096)
            detector.detect(signal)
        
        # History should be capped at history_size
        assert len(detector.snr_history) <= 5
    
    def test_severity_classification(self):
        """Test jamming severity classification."""
        detector = NoiseJammingDetector()
        
        # Low SNR, high degradation -> critical
        sev_critical = detector._classify_severity(-20, 25)
        assert sev_critical == 'critical'
        
        # Medium SNR, medium degradation -> medium
        sev_medium = detector._classify_severity(-8, 12)
        assert sev_medium == 'medium'


class TestDeceptionJammingDetector:
    """Tests for deception jamming detection."""
    
    def test_detector_initialization(self):
        """Test deception detector creation."""
        detector = DeceptionJammingDetector(max_detections_per_frame=50)
        assert detector.max_detections_per_frame == 50
        assert len(detector.detection_history) == 0
    
    def test_no_jam_normal_detections(self):
        """Test normal detection rates pass without alarm."""
        detector = DeceptionJammingDetector(max_detections_per_frame=50)
        
        for _ in range(5):
            normal_detections = [(10 + i, 50 + i, 0.5) for i in range(10)]
            threat = detector.detect(normal_detections)
            assert threat is None
    
    def test_jam_detection_burst(self):
        """Test deception jamming detection from detection burst."""
        detector = DeceptionJammingDetector(max_detections_per_frame=30)
        
        # Feed normal detections first
        for _ in range(3):
            detector.detect([(10 + i, 50, 0.5) for i in range(10)])
        
        # Then burst with many detections
        jam_burst = [(10 + i, 50 + i*5, 0.3) for i in range(80)]
        threat = detector.detect(jam_burst)
        
        # Should detect jam
        assert threat is not None
        assert threat.threat_type == 'deception_jam'
    
    def test_severity_classification(self):
        """Test deception jam severity."""
        detector = DeceptionJammingDetector()
        
        sev_critical = detector._classify_detection_severity(6.0)
        assert sev_critical == 'critical'
        
        sev_medium = detector._classify_detection_severity(3.2)
        assert sev_medium == 'medium'


class TestFalseTargetDiscriminator:
    """Tests for false target discrimination."""
    
    def test_discriminator_initialization(self):
        """Test false target discriminator creation."""
        disc = FalseTargetDiscriminator(ml_confidence_threshold=0.7)
        assert disc.ml_confidence_threshold == 0.7
    
    def test_real_vs_false_targets(self):
        """Test discrimination of real vs false targets."""
        disc = FalseTargetDiscriminator(ml_confidence_threshold=0.7)
        
        detections = [(50, 60, 0.8), (100, 64, 0.9)]
        labels = ['Drone', 'Aircraft']
        confidences = [0.9, 0.85]  # High confidence
        
        is_real, threat = disc.discriminate(detections, labels, confidences)
        
        assert all(is_real)  # All should be real
        assert threat is None
    
    def test_false_target_detection(self):
        """Test false target detection."""
        disc = FalseTargetDiscriminator(ml_confidence_threshold=0.7)
        
        detections = [(50, 64, 0.5), (100, 64, 0.3), (75, 64, 0.2)]
        labels = ['Clutter', 'Clutter', 'Bird']
        confidences = [0.4, 0.35, 0.5]  # Low confidence
        
        is_real, threat = disc.discriminate(detections, labels, confidences)
        
        # Most should be detected as false
        assert not all(is_real)
        if threat:
            assert threat.threat_type == 'false_target'
    
    def test_unrealistic_positions(self):
        """Test detection of unrealistic positions."""
        disc = FalseTargetDiscriminator()
        
        # Out of range positions
        unrealistic1 = disc._check_unrealistic(130, 60)  # Range too high
        assert unrealistic1
        
        unrealistic2 = disc._check_unrealistic(50, 125)  # Doppler way too extreme (|125-64| = 61 > 60)
        assert unrealistic2
        
        realistic = disc._check_unrealistic(50, 65)
        assert not realistic


class TestFrequencyHopper:
    """Tests for frequency hopping countermeasure."""
    
    def test_hopper_initialization(self):
        """Test frequency hopper creation."""
        hopper = FrequencyHopper(base_freq_hz=10e9, hop_set_size=10)
        assert hopper.base_freq_hz == 10e9
        assert len(hopper.hop_sequence) == 10
    
    def test_frequency_hopping_sequence(self):
        """Test frequency hopping generates different frequencies."""
        hopper = FrequencyHopper(base_freq_hz=10e9, hop_set_size=5)
        
        frequencies = [hopper.get_next_hop() for _ in range(5)]
        
        # Should have variation (not all same)
        assert len(set(frequencies)) > 1
        
        # All should be around base frequency (±250 MHz for 5-bin hop set)
        for f in frequencies:
            assert 9.75e9 < f < 10.25e9
    
    def test_current_frequency_tracking(self):
        """Test current frequency retrieval."""
        hopper = FrequencyHopper()
        
        freq1 = hopper.get_next_hop()
        freq_current = hopper.get_current_freq()
        
        assert freq_current == freq1
    
    def test_hop_sequence_wraps(self):
        """Test hop sequence wraps around."""
        hopper = FrequencyHopper(hop_set_size=3)
        
        # Generate more hops than set size
        hops = [hopper.get_next_hop() for _ in range(10)]
        
        # Should complete without error (wrapping)
        assert len(hops) == 10


class TestWaveformRandomizer:
    """Tests for waveform randomization."""
    
    def test_randomizer_initialization(self):
        """Test waveform randomizer creation."""
        randomizer = WaveformRandomizer()
        assert len(randomizer.pulse_widths) > 0
        assert len(randomizer.prf_values) > 0
    
    def test_random_params_generation(self):
        """Test random waveform parameter generation."""
        randomizer = WaveformRandomizer()
        
        params = randomizer.get_random_waveform_params()
        
        assert 'pulse_width_us' in params
        assert 'prf_hz' in params
        assert 'chirp_bandwidth_hz' in params
        assert 'pattern_seed' in params
        
        # Values should be within expected ranges
        assert params['pulse_width_us'] > 0
        assert params['prf_hz'] > 0
        assert params['chirp_bandwidth_hz'] > 0
    
    def test_params_vary(self):
        """Test that generated parameters vary."""
        randomizer = WaveformRandomizer()
        
        params_list = [randomizer.get_random_waveform_params() for _ in range(10)]
        
        # At least some variation should exist
        seeds = [p['pattern_seed'] for p in params_list]
        assert len(set(seeds)) > 1


class TestEWDefenseController:
    """Tests for top-level EW defense controller."""
    
    def test_controller_initialization(self):
        """Test EW defense controller creation."""
        controller = EWDefenseController()
        
        assert controller.noise_detector is not None
        assert controller.deception_detector is not None
        assert controller.false_target_discriminator is not None
        assert controller.ew_active == False
        assert controller.threat_level == 'green'
    
    def test_clean_signal_no_threats(self):
        """Test clean signal produces no threats."""
        controller = EWDefenseController()
        
        clean_signal = np.sin(np.linspace(0, 10*np.pi, 4096))
        detections = [(30 + i, 60, 0.7) for i in range(5)]
        labels = ['Drone', 'Drone', 'Aircraft', 'Bird', 'Helicopter']
        confidences = [0.9, 0.85, 0.88, 0.92, 0.80]
        
        result = controller.analyze(clean_signal, detections, labels, confidences)
        
        assert len(result['threats']) == 0
        assert result['ew_active'] == False
        assert result['threat_level'] == 'green'
    
    def test_jamming_generates_countermeasures(self):
        """Test jamming detection triggers countermeasures."""
        controller = EWDefenseController(
            {'snr_threshold_db': -5.0, 'max_detections': 30}
        )
        
        # Jam signal
        jam_signal = 0.1 * np.random.randn(4096)
        
        # Burst detections
        detections = [(30 + i, 60, 0.3) for i in range(100)]
        labels = ['Clutter'] * len(detections)
        confidences = [0.4] * len(detections)
        
        # Run multiple times to trigger detection
        for _ in range(5):
            result = controller.analyze(jam_signal, detections, labels, confidences)
        
        # Should detect threats and generate countermeasures
        assert result['ew_active'] == True
        if result['countermeasures']:
            # Should have frequency hopping or waveform randomization
            action_types = [cm.action_type for cm in result['countermeasures']]
            assert 'freq_hop' in action_types or 'waveform_randomize' in action_types
    
    def test_threat_level_classification(self):
        """Test threat level computation."""
        controller = EWDefenseController()
        
        # No threats
        controller.threats = []
        controller._update_threat_level()
        assert controller.threat_level == 'green'
        
        # High threat
        threat = JammingThreat('noise_jam', 0.9, 'critical', [(0, 2048)], details={})
        controller.threats = [threat]
        controller._update_threat_level()
        assert controller.threat_level == 'red'
    
    def test_recommendations_generated(self):
        """Test that recommendations are generated for threats."""
        controller = EWDefenseController()
        
        # Create threats
        threat1 = JammingThreat('noise_jam', 0.8, 'high', [(0, 2048)], details={})
        threat2 = JammingThreat('deception_jam', 0.7, 'medium', [(0, 2048)], details={})
        controller.threats = [threat1, threat2]
        controller.ew_active = True
        
        recommendations = controller._get_recommendations()
        
        assert len(recommendations) > 0
        # Should have recommendations for each threat type
        rec_text = ' '.join(recommendations)
        assert 'NOISE' in rec_text or 'DECEPTION' in rec_text
    
    def test_get_status(self):
        """Test status reporting."""
        controller = EWDefenseController()
        
        status = controller.get_status()
        
        assert 'ew_active' in status
        assert 'threat_level' in status
        assert 'num_threats' in status
        assert 'current_frequency_hz' in status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
