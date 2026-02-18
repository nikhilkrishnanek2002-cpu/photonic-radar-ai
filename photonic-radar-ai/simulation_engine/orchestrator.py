"""
Real-Time Radar Orchestrator
============================

Manages the continuous simulation loop.
Coordinates:
1. Target positioning (Physics).
2. Photonic signal generation.
3. Signal processing (Range-Doppler).
4. AI Classification.
5. Tactical Tracking.
6. Intelligence Publishing (defense_core integration).

Author: Nikhil Krishna
"""

import time
import numpy as np
import math
import warnings
from typing import List, Dict, Optional
from simulation_engine.physics import TargetState, KinematicEngine
from simulation_engine.performance import PerformanceMonitor
from photonic.signals import generate_synthetic_photonic_signal
from signal_processing.engine import RadarDSPEngine
from signal_processing.detection import ca_cfar_detector, cluster_and_centroid_detections
from ai_models.architectures import TacticalHybridClassifier, initialize_tactical_model
from tracking.manager import TacticalTrackManager
from simulation_engine.evaluation import EvaluationManager
from interfaces.message_schema import (
    Track, ThreatAssessment, SceneContext, TacticalPictureMessage,
    ThreatClass, TargetType, EngagementRecommendation, SceneType
)
from interfaces.publisher import IntelligencePublisher, NullPublisher

# Defense Core Integration
from defense_core import (
    get_defense_bus,
    RadarIntelligencePacket,
    Track as DefenseTrack,
    ThreatAssessment as DefenseThreatAssessment,
    SceneContext as DefenseSceneContext
)

# Try to import torch, provide fallback if unavailable
try:
    import torch
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    warnings.warn("PyTorch not available - orchestrator will run in fallback mode", UserWarning)

class SimulationOrchestrator:
    def __init__(self, radar_config: Dict, initial_targets: List[TargetState] = [], event_bus=None):
        """
        Initialize simulation orchestrator using config dict.
        """
        self.config = radar_config
        self.dt = radar_config.get('frame_dt', 0.1)
        self.physics = KinematicEngine(self.dt)
        self.dsp = RadarDSPEngine(radar_config)
        self.tracker = TacticalTrackManager(sampling_period_s=self.dt)
        self.perf = PerformanceMonitor()
        
        # AI Logic
        self.ai_model = initialize_tactical_model(num_target_classes=5)
        if self.ai_model is not None:
            self.ai_model.eval()
        # Mock class labels
        self.class_labels = {0: "Noise", 1: "Drone", 2: "Bird", 3: "Aircraft", 4: "Missile"}
        
        self.targets = initial_targets
        self.frame_count = 0
        self.is_running = False
        
        # Evaluation
        self.eval_manager = EvaluationManager()

        # Scanning State
        self.scan_angle_deg = 0.0
        self.rpm = radar_config.get('rpm', 12.0) # 12 RPM default
        self.beamwidth_deg = radar_config.get('beamwidth_deg', 5.0)
        
        # Intelligence Export (Legacy - file-based)
        self.sensor_id = radar_config.get('sensor_id', 'PHOTONIC_RADAR_01')
        enable_export = radar_config.get('enable_intelligence_export', True)
        export_dir = radar_config.get('intelligence_export_dir', './intelligence_export')
        
        if enable_export:
            self.intelligence_publisher = IntelligencePublisher(
                sensor_id=self.sensor_id,
                enable_file_export=True,
                export_directory=export_dir
            )
            self.intelligence_publisher.start()
        else:
            self.intelligence_publisher = NullPublisher()
        
        # Defense Core Integration (Event Bus)
        self.enable_defense_core = radar_config.get('enable_defense_core', True)
        self.debug_packets = radar_config.get('debug_packets', False)
        self.packets_sent = 0
        self.packets_dropped = 0
        
        if self.enable_defense_core:
            self.defense_bus = event_bus if event_bus else get_defense_bus()
            print(f"[DEFENSE_CORE] Event bus initialized for sensor: {self.sensor_id}")
            if self.debug_packets:
                print(f"[DEFENSE_CORE] Debug mode ENABLED - packets will be printed")
        else:
            self.defense_bus = None
        
        # EW Degradation Model
        self.enable_ew_effects = radar_config.get('enable_ew_effects', True)
        self.ew_log_before_after = radar_config.get('ew_log_before_after', True)
        
        if self.enable_ew_effects:
            from simulation_engine.ew_degradation import EWDegradationModel
            self.ew_degradation = EWDegradationModel(
                max_snr_degradation_db=radar_config.get('ew_max_snr_degradation_db', 20.0),
                max_quality_degradation=radar_config.get('ew_max_quality_degradation', 0.5),
                false_track_probability=radar_config.get('ew_false_track_probability', 0.3)
            )
            self.last_ew_packet = None
            print(f"[EW-EFFECTS] EW degradation model ENABLED")
        else:
            self.ew_degradation = None
            print(f"[EW-EFFECTS] EW degradation model DISABLED")

    def _prepare_spectrogram(self, rd_map: np.ndarray):
        """Prepares RD map for CNN input (Reset to 128x128)."""
        if not TORCH_AVAILABLE:
            return None
        # 1. Log modulus if not already
        if np.iscomplexobj(rd_map):
            rd_abs = np.abs(rd_map)
        else:
            rd_abs = rd_map
        
        # 2. Normalize
        rd_norm = (rd_abs - np.min(rd_abs)) / (np.max(rd_abs) + 1e-9)
        
        # 3. To Tensor (1, 1, H, W)
        tensor = torch.from_numpy(rd_norm).float().unsqueeze(0).unsqueeze(0)
        
        # 4. Interpolate to 128x128 (Model Requirement)
        return F.interpolate(tensor, size=(128, 128), mode='bilinear', align_corners=False)

    def _prepare_timeseries(self, velocity: float):
        """Synthesizes Doppler time-series input based on track velocity."""
        if not TORCH_AVAILABLE:
            return None
        # Seq len 1000
        t = torch.linspace(0, 1, 1000)
        # Doppler shift proxy (just a frequency tone)
        freq = 10.0 + abs(velocity) # Base offset
        signal = torch.sin(2 * torch.pi * freq * t) + 0.1 * torch.randn(1000)
        return signal.unsqueeze(0) # (1, 1000)

    def tick(self) -> Dict:
        """
        Executes a real-time frame cycle: Physics -> Photonic -> DSP -> AI -> Track.
        """
        start_time = time.time()
        self.perf.start_phase("total")
        
        # 1. Physics Update (Advance all targets)
        self.perf.start_phase("physics")
        self.targets = [self.physics.update_state(t) for t in self.targets]
        self.perf.end_phase("physics")
        
        # 2. Scanning Update
        # Advance scan angle: omega = 360 * RPM / 60 = 6 * RPM (deg/s)
        # delta_deg = omega * dt
        scan_omega = 6.0 * self.rpm
        self.scan_angle_deg = (self.scan_angle_deg + scan_omega * self.dt) % 360.0
        
        # Determine Illuminated Targets
        illuminated_targets = []
        for t in self.targets:
            # Check angular difference
            az = t.azimuth_deg % 360.0
            beam_delta = abs(az - self.scan_angle_deg)
            # Handle wrap-around (e.g. 359 vs 1)
            if beam_delta > 180: beam_delta = 360 - beam_delta
            
            if beam_delta < (self.beamwidth_deg / 2.0):
                illuminated_targets.append(t)
        
        # 3. Photonic Signal Generation (Analytic De-chirped)
        self.perf.start_phase("photonic")
        sampling_rate_hz = self.config.get('sampling_rate_hz', 2e6)
        num_pulses = self.config.get('n_pulses', 64)
        samples_per_pulse = self.config.get('samples_per_pulse', 512)
        
        speed_of_light = 3e8
        carrier_freq_hz = self.config.get('start_frequency_hz', 77e9) 
        sweep_bandwidth_hz = self.config.get('sweep_bandwidth_hz', 150e6)
        chirp_duration_s = samples_per_pulse / sampling_rate_hz
        chirp_slope_hz_s = sweep_bandwidth_hz / chirp_duration_s
        
        total_samples = num_pulses * samples_per_pulse
        time_vector = np.arange(total_samples) / sampling_rate_hz
        beat_signal = np.zeros(total_samples, dtype=complex)
        
        # Helper: Pulse time vector for phase reset if needed
        t_pulse = np.arange(samples_per_pulse) / sampling_rate_hz
        t_matrix = np.tile(t_pulse, num_pulses)
        
        if illuminated_targets:
            for tgt in illuminated_targets:
                r = tgt.range_m
                v = tgt.radial_velocity
                
                # Physics:
                propagation_delay_tau = 2 * r / speed_of_light
                beat_frequency_hz = chirp_slope_hz_s * propagation_delay_tau
                doppler_frequency_hz = (2 * v * carrier_freq_hz) / speed_of_light
                
                # Phase: 2*pi*(fb + fd)*t + Phase_offset
                # Important: t must be local to pulse for Range term?
                # Actually for de-chirped:
                # Phase ~ 2*pi*( (S*tau + f_d)*t + fc*tau - 0.5*S*tau^2 )
                # The term 't' here resets every pulse for the S*tau part?
                # Yes, S*t is freq offset from current chirp start.
                
                total_phase = 2 * np.pi * carrier_freq_hz * propagation_delay_tau
                
                # Amplitude (Radar Equation scaling)
                amplitude = 1.0 / (r**2 + 1.0) * 1e5
                
                # Generate Tone
                tone = amplitude * np.exp(1j * 2 * np.pi * beat_frequency_hz * t_matrix) * \
                       np.exp(1j * 2 * np.pi * doppler_frequency_hz * time_vector) * \
                       np.exp(1j * total_phase)
                       
                beat_signal += tone
        
        # Add Noise (WDM/Thermal)
        noise_pwr = 10**(self.config.get('noise_level_db', -50)/10)
        beat_signal += np.random.normal(0, np.sqrt(noise_pwr), total_samples) + \
                       1j*np.random.normal(0, np.sqrt(noise_pwr), total_samples)
                       
        if self.frame_count % 10 == 0 and illuminated_targets:
            print(f"[DEBUG] Frame {self.frame_count}: {len(illuminated_targets)} targets illuminated.")
            print(f"        Beat Signal Max amp: {np.max(np.abs(beat_signal)):.4e}")
            
        self.perf.end_phase("photonic")
        
        # 3. DSP & Detection
        self.perf.start_phase("dsp")
        pulse_matrix = beat_signal.reshape(num_pulses, samples_per_pulse)
        rd_map, rd_power = self.dsp.process_frame(pulse_matrix) # Unpack dB and Linear maps
        det_map, _ = ca_cfar_detector(rd_power, power_floor=0.005) 
        
        detections = cluster_and_centroid_detections(det_map, rd_power) # Collapse redundant peaks
        
        if self.frame_count % 50 == 0:
            # Periodic debug only
            pass
            
        self.perf.end_phase("dsp")
        
        # 3.5 EW Effects Application
        # DEBUG: Check flags
        if self.frame_count % 50 == 0:
            print(f"DEBUG: EW Flags: enable={self.enable_ew_effects}, deg={self.ew_degradation is not None}, bus={self.defense_bus is not None}")

        if self.enable_ew_effects and self.ew_degradation and self.defense_bus:
            # Poll for EW attack packets (non-blocking)
            ew_packet = self.defense_bus.receive_ew_feedback(timeout=0.001)
            
            if ew_packet:
                self.last_ew_packet = ew_packet
                if self.frame_count % 10 == 0:
                    print(f"[EW-RX] Frame {self.frame_count}: Received EW packet with "
                          f"{len(ew_packet.active_countermeasures)} countermeasures")
            
            # Apply jamming if we have an active packet
            if self.last_ew_packet and len(self.last_ew_packet.active_countermeasures) > 0:
                # Reset metrics for this frame
                self.ew_degradation.reset_metrics()
                
                # Capture BEFORE metrics
                before_metrics = {
                    'num_detections': len(detections),
                    'mean_snr_db': float(np.mean(rd_power)) if len(rd_power) > 0 else 0.0
                }
                
                # Apply noise jamming to RD map
                rd_power = self.ew_degradation.apply_jamming(
                    rd_power,
                    self.last_ew_packet.active_countermeasures
                )
                
                # Re-run detection on jammed RD map
                det_map, _ = ca_cfar_detector(rd_power, power_floor=0.005)
                detections = cluster_and_centroid_detections(det_map, rd_power)
        
        # 4. AI & Tracking
        self.perf.start_phase("ai_tracking")
        
        # Calculate Resolutions
        n_fft_r = self.dsp.n_fft_range
        r_scale = (speed_of_light * samples_per_pulse) / (2 * sweep_bandwidth_hz * n_fft_r)
        
        # Velocity Res
        n_fft_d = self.dsp.n_fft_doppler
        wavelength = speed_of_light / carrier_freq_hz
        v_scale = wavelength / (2 * num_pulses * chirp_duration_s * (n_fft_d / num_pulses))
        
        obs_states = []
        for v_idx, r_idx in detections:
            # Map indices to physical units
            # v_idx is Doppler (Dim 0), r_idx is Range (Dim 1)
            
            r = r_idx * r_scale
            v_bin_centered = v_idx - (n_fft_d // 2)
            # Check sign logic: if target approaching, f_dopp > 0.
            # In FFT shift, right side is positive freq.
            v = v_bin_centered * v_scale
            
            # Simple threshold to filter unrealistic ranges (close to 0 usually DC leakage)
            if r > 10: 
                obs_states.append((r, v))
            
        tracks = self.tracker.update_pipeline(obs_states)
        
        # DEBUG: tracing the data flow
        if self.frame_count % 10 == 0:
            print(f"[DEBUG] Frame {self.frame_count}:")
            print(f"        Illuminated: {len(illuminated_targets)}")
            print(f"        Detections:  {len(detections)} (Raw)")
            print(f"        Valid Obs:   {len(obs_states)} (After filtering)")
            print(f"        Tracks:      {len(tracks)}")
        
        # --- AI INJECTION START ---
        # Critical Fix: Run Inference on confirmed tracks
        if TORCH_AVAILABLE and tracks and self.ai_model:
            with torch.no_grad():
                # Prepare batch
                spec_batch = self._prepare_spectrogram(rd_map) # Shared scene context
                
                for tr in tracks:
                    # In a real system, we'd crop the ROI per target. 
                    # Here we pass the full scene context + target-specific kinematic time-series.
                    ts_input = self._prepare_timeseries(tr['estimated_velocity_ms'])
                    
                    logits, _ = self.ai_model(spec_batch, ts_input)
                    probs = F.softmax(logits, dim=1)
                    conf, class_idx = torch.max(probs, dim=1)
                    
                    # Attach to track object
                    tr['class_id'] = int(class_idx.item())
                    tr['class_label'] = self.class_labels.get(tr['class_id'], "Unknown")
                    tr['confidence'] = float(conf.item())
        elif tracks and not TORCH_AVAILABLE:
            # Fallback: Use heuristic classification without AI
            for tr in tracks:
                tr['class_id'] = 1  # Default class
                tr['class_label'] = self.class_labels.get(1, "Unknown")
                tr['confidence'] = 0.5  # Low confidence without AI
        # --- AI INJECTION END ---

        self.perf.end_phase("ai_tracking")
        
        # 4.5 EW Track Degradation & Logging
        if self.enable_ew_effects and self.ew_degradation and self.last_ew_packet:
            if len(self.last_ew_packet.active_countermeasures) > 0:
                # Capture BEFORE track metrics
                before_track_metrics = {
                    'num_tracks': len(tracks),
                    'mean_quality': float(np.mean([t.get('quality', 1.0) for t in tracks])) if tracks else 0.0
                }
                before_track_metrics.update(before_metrics)  # Add detection/SNR metrics
                
                # Apply track quality degradation
                tracks = self.ew_degradation.degrade_tracks(
                    tracks,
                    self.last_ew_packet.active_countermeasures
                )
                
                # Inject false tracks from deception jamming
                tracks = self.ew_degradation.inject_false_tracks(
                    tracks,
                    self.last_ew_packet.active_countermeasures,
                    self.frame_count * self.dt
                )
                
                # Apply range/velocity drift
                tracks = self.ew_degradation.apply_drift_to_tracks(
                    tracks,
                    self.last_ew_packet.active_countermeasures
                )
                
                # Capture AFTER track metrics
                after_track_metrics = {
                    'num_tracks': len(tracks),
                    'mean_quality': float(np.mean([t.get('quality', 1.0) for t in tracks])) if tracks else 0.0,
                    'num_false_tracks': sum(1 for t in tracks if t.get('is_false_track', False)),
                    'snr_reduction_db': self.ew_degradation.metrics.snr_reduction_db
                }
                
                # Log before/after comparison
                if self.ew_log_before_after:
                    self.ew_degradation.log_before_after_metrics(
                        before_track_metrics,
                        after_track_metrics,
                        self.frame_count
                    )
        
        # 5. Intelligence Export (Non-blocking)
        # Export processed intelligence at every tick
        self._export_intelligence(tracks, rd_power, len(detections))
        
        # 6. Evaluation (Offline/Online Analysis)
        # Convert tracks to dict format for evaluator
        track_dicts = []
        for tr in tracks:
             # Basic transformation for eval matching
             track_dicts.append({
                 'id': tr['id'],
                 'range_m': tr['estimated_range_m'],
                 'velocity_m_s': tr['estimated_velocity_ms']
             })
             
        # Ground Truth (All targets, even those outside beam, for global tracking eval? 
        # Or only illuminated? Usually we want to know if we missed something existing)
        # Let's pass all active targets as Ground Truth
        gt_dicts = [vars(t) for t in self.targets]
        self.eval_manager.update(self.frame_count, gt_dicts, track_dicts)
        
        self.perf.end_phase("total")
        self.frame_count += 1
        
        # Calculate Telemetry Metrics
        # Peak Signal Power
        peak_power = float(np.max(rd_power)) if rd_power.size > 0 else 0.0
        
        # Mean SNR (Signal to Noise Ratio)
        # Assuming noise floor is roughly the mean of the lower 50% of values (heuristic)
        if rd_power.size > 0:
            sorted_power = np.sort(rd_power.flatten())
            noise_floor = np.mean(sorted_power[:int(len(sorted_power)*0.5)])
            signal_power = np.mean(sorted_power[int(len(sorted_power)*0.95):]) # Top 5%
            snr_linear = signal_power / (noise_floor + 1e-10)
            mean_snr_db = 10 * np.log10(snr_linear)
        else:
            mean_snr_db = 0.0
            
        return {
            "frame": self.frame_count,
            "timestamp": time.time(),
            "targets": [vars(t) for t in self.targets], # Send all targets for ground truth debug
            "scan_angle": self.scan_angle_deg,
            "illuminated_ids": [t.id for t in illuminated_targets],
            "rd_map": rd_map,
            "tracks": tracks,
            "metrics": self.perf.get_metrics(),
            "evaluation": self.eval_manager.get_summary(),
            "telemetry": {
                "peak_signal_power": peak_power,
                "mean_snr_db": mean_snr_db,
                "track_confidence": float(np.mean([t.get('confidence', 0.0) for t in tracks])) if tracks else 0.0
            }
        }

    def run_loop(self, max_frames: int = 100):
        """
        Standard blocking loop for testing.
        In streamlit/UI, this would be handled via a generator.
        """
        self.is_running = True
        try:
            for _ in range(max_frames):
                if not self.is_running: break
                frame_data = self.tick()
                yield frame_data
                
                # Maintain real-time pace
                elapsed = time.time() - frame_data["timestamp"]
                sleep_time = max(0, self.dt - elapsed)
                time.sleep(sleep_time)
        finally:
            self.is_running = False

    def stop(self):
        self.is_running = False
        # Stop intelligence publisher gracefully
        if hasattr(self, 'intelligence_publisher'):
            self.intelligence_publisher.stop()
    
    def _export_intelligence(self, tracks: List[Dict], rd_power: np.ndarray, num_detections: int):
        """
        Export radar intelligence as tactical picture message.
        
        This method never blocks radar processing - messages are queued
        and exported by background thread.
        
        Publishes to:
        1. File-based intelligence publisher (legacy)
        2. Defense core event bus (new)
        """
        try:
            # ================================================================
            # 1. Convert tracks to defense_core schema format
            # ================================================================
            defense_tracks = []
            defense_threats = []
            
            for tr in tracks:
                # Create defense_core Track
                defense_track = DefenseTrack(
                    track_id=tr['id'],
                    range_m=float(tr['estimated_range_m']),
                    azimuth_deg=self.scan_angle_deg,
                    radial_velocity_m_s=float(tr['estimated_velocity_ms']),
                    track_quality=float(tr.get('stability', 0.5)),
                    position_uncertainty_m=10.0 * (1.0 - float(tr.get('stability', 0.5))),
                    velocity_uncertainty_m_s=5.0 * (1.0 - float(tr.get('stability', 0.5))),
                    track_age_frames=int(tr.get('age', 0)),
                    last_update_timestamp=time.time()
                )
                defense_tracks.append(defense_track)
                
                # Create defense_core ThreatAssessment
                threat_class = self._map_class_to_threat(tr.get('class_label', 'Unknown'))
                target_type = self._map_class_to_target_type(tr.get('class_label', 'Unknown'))
                confidence = float(tr.get('confidence', 0.5))
                
                defense_threat = DefenseThreatAssessment(
                    track_id=tr['id'],
                    threat_class=threat_class,
                    target_type=target_type,
                    classification_confidence=confidence,
                    threat_priority=self._calculate_threat_priority(tr, threat_class),
                    engagement_recommendation=self._get_engagement_recommendation(tr, threat_class),
                    classification_uncertainty=1.0 - confidence,
                    model_confidence=confidence,
                    feature_quality=float(tr.get('stability', 0.5))
                )
                defense_threats.append(defense_threat)
            
            # ================================================================
            # 2. Create scene context
            # ================================================================
            mean_snr = float(np.mean(rd_power[rd_power > 0])) if np.any(rd_power > 0) else 0.0
            mean_snr_db = 10 * np.log10(mean_snr + 1e-10)
            
            defense_scene = DefenseSceneContext(
                scene_type=self._classify_scene_type(len(tracks), num_detections),
                clutter_ratio=self._calculate_clutter_ratio(len(tracks), num_detections),
                mean_snr_db=float(mean_snr_db),
                num_confirmed_tracks=len(tracks)
            )
            
            # ================================================================
            # 3. Create RadarIntelligencePacket
            # ================================================================
            packet = RadarIntelligencePacket.create(
                frame_id=self.frame_count,
                sensor_id=self.sensor_id,
                tracks=defense_tracks,
                threat_assessments=defense_threats,
                scene_context=defense_scene,
                overall_confidence=0.9,
                data_quality=0.9
            )
            
            # ================================================================
            # 4. Publish to event bus (non-blocking)
            # ================================================================
            if self.enable_defense_core and self.defense_bus:
                # Non-blocking publish with 10ms timeout
                success = self.defense_bus.publish_intelligence(packet, timeout=0.01)
                
                if success:
                    self.packets_sent += 1
                    import logging
                    logging.info(f"[PACKET_SENT] Frame {packet.frame_id}: "
                                f"{len(packet.tracks)} tracks, "
                                f"{len(packet.threat_assessments)} threats, "
                                f"confidence={packet.overall_confidence:.2f}")
                else:
                    self.packets_dropped += 1
                    import logging
                    logging.warning(f"[PACKET_DROPPED] Frame {packet.frame_id}: Event bus full")
                
                # Debug mode: print packet details
                if self.debug_packets:
                    self._print_packet_debug(packet)
            
            # ================================================================
            # 5. Legacy file-based export (backward compatibility)
            # ================================================================
            # Convert to legacy format for file export
            legacy_tracks = []
            legacy_threats = []
            
            for tr in tracks:
                legacy_track = Track(
                    track_id=tr['id'],
                    range_m=float(tr['estimated_range_m']),
                    azimuth_deg=self.scan_angle_deg,
                    radial_velocity_m_s=float(tr['estimated_velocity_ms']),
                    track_quality=float(tr.get('stability', 0.5)),
                    track_age_frames=int(tr.get('age', 0)),
                    last_update_timestamp=time.time(),
                    radial_acceleration_m_s2=float(tr.get('estimated_acceleration_ms2', 0.0)) if 'estimated_acceleration_ms2' in tr else None
                )
                legacy_tracks.append(legacy_track)
                
                threat_class = self._map_class_to_threat(tr.get('class_label', 'Unknown'))
                target_type = self._map_class_to_target_type(tr.get('class_label', 'Unknown'))
                confidence = float(tr.get('confidence', 0.5))
                
                legacy_threat = ThreatAssessment(
                    track_id=tr['id'],
                    threat_class=threat_class,
                    target_type=target_type,
                    classification_confidence=confidence,
                    threat_priority=self._calculate_threat_priority(tr, threat_class),
                    engagement_recommendation=self._get_engagement_recommendation(tr, threat_class),
                    classification_uncertainty=1.0 - confidence,
                    position_uncertainty_m=10.0 * (1.0 - legacy_track.track_quality),
                    velocity_uncertainty_m_s=5.0 * (1.0 - legacy_track.track_quality)
                )
                legacy_threats.append(legacy_threat)
            
            legacy_scene = SceneContext(
                scene_type=self._classify_scene_type(len(tracks), num_detections),
                clutter_ratio=self._calculate_clutter_ratio(len(tracks), num_detections),
                mean_snr_db=float(mean_snr_db),
                num_confirmed_tracks=len(tracks)
            )
            
            legacy_message = TacticalPictureMessage.create(
                frame_id=self.frame_count,
                sensor_id=self.sensor_id,
                tracks=legacy_tracks,
                threat_assessments=legacy_threats,
                scene_context=legacy_scene
            )
            
            # Publish to file (non-blocking)
            self.intelligence_publisher.publish(legacy_message)
            
        except Exception as e:
            # Never let export errors crash radar processing
            import logging
            logging.error(f"Intelligence export failed (non-fatal): {e}")
    
    def _map_class_to_threat(self, class_label: str) -> str:
        """Map AI class label to threat classification."""
        threat_map = {
            'Missile': ThreatClass.HOSTILE.value,
            'Aircraft': ThreatClass.UNKNOWN.value,
            'Drone': ThreatClass.UNKNOWN.value,
            'Bird': ThreatClass.NEUTRAL.value,
            'Noise': ThreatClass.NEUTRAL.value
        }
        return threat_map.get(class_label, ThreatClass.UNKNOWN.value)
    
    def _map_class_to_target_type(self, class_label: str) -> str:
        """Map AI class label to target type."""
        type_map = {
            'Missile': TargetType.MISSILE.value,
            'Aircraft': TargetType.AIRCRAFT.value,
            'Drone': TargetType.UAV.value,
            'Bird': TargetType.UNKNOWN.value,
            'Noise': TargetType.UNKNOWN.value
        }
        return type_map.get(class_label, TargetType.UNKNOWN.value)
    
    def _calculate_threat_priority(self, track: Dict, threat_class: str) -> int:
        """Calculate threat priority (1-10) based on track characteristics."""
        if threat_class == ThreatClass.HOSTILE.value:
            # High priority for hostile targets
            base_priority = 8
            # Increase priority for high-speed approaching targets
            velocity = abs(track.get('estimated_velocity_ms', 0))
            if velocity > 200:  # Fast moving (>200 m/s)
                base_priority = min(10, base_priority + 2)
            return base_priority
        elif threat_class == ThreatClass.UNKNOWN.value:
            return 5  # Medium priority
        else:
            return 2  # Low priority for neutral/friendly
    
    def _get_engagement_recommendation(self, track: Dict, threat_class: str) -> str:
        """Determine engagement recommendation."""
        if threat_class == ThreatClass.HOSTILE.value:
            return EngagementRecommendation.ENGAGE.value
        elif threat_class == ThreatClass.UNKNOWN.value:
            return EngagementRecommendation.MONITOR.value
        else:
            return EngagementRecommendation.IGNORE.value
    
    def _classify_scene_type(self, num_tracks: int, num_detections: int) -> str:
        """Classify scene type based on track/detection density."""
        if num_tracks == 0:
            return SceneType.SEARCH.value
        elif num_tracks <= 2:
            return SceneType.SPARSE.value
        elif num_tracks <= 5:
            return SceneType.TRACKING.value
        elif num_tracks <= 10:
            return SceneType.DENSE.value
        else:
            return SceneType.CLUTTERED.value
    
    def _calculate_clutter_ratio(self, num_tracks: int, num_detections: int) -> float:
        """Calculate ratio of clutter to valid tracks."""
        if num_detections == 0:
            return 0.0
        # Clutter = detections that didn't become tracks
        clutter_count = max(0, num_detections - num_tracks)
        return min(1.0, clutter_count / max(1, num_detections))
    
    def _print_packet_debug(self, packet: RadarIntelligencePacket):
        """Print detailed packet information for debugging."""
        print(f"\n{'='*80}")
        print(f"[RADAR_PACKET] Frame {packet.frame_id} @ {packet.timestamp:.3f}s")
        print(f"{'='*80}")
        print(f"Sensor: {packet.sensor_id}")
        print(f"Tracks: {len(packet.tracks)}")
        print(f"Threats: {len(packet.threat_assessments)}")
        print(f"Overall Confidence: {packet.overall_confidence:.2f}")
        print(f"Data Quality: {packet.data_quality:.2f}")
        print(f"Sensor Health: {packet.sensor_health:.2f}")
        print(f"Sensor Mode: {packet.sensor_mode}")
        
        if packet.scene_context:
            print(f"\nScene Context:")
            print(f"  Type: {packet.scene_context.scene_type}")
            print(f"  Clutter Ratio: {packet.scene_context.clutter_ratio:.2f}")
            print(f"  Mean SNR: {packet.scene_context.mean_snr_db:.1f} dB")
            print(f"  Confirmed Tracks: {packet.scene_context.num_confirmed_tracks}")
        
        for i, track in enumerate(packet.tracks):
            print(f"\n  Track {track.track_id}:")
            print(f"    Range: {track.range_m:.1f}m")
            print(f"    Azimuth: {track.azimuth_deg:.1f}°")
            print(f"    Velocity: {track.radial_velocity_m_s:.1f}m/s")
            print(f"    Quality: {track.track_quality:.2f}")
            print(f"    Age: {track.track_age_frames} frames")
            print(f"    Position Uncertainty: {track.position_uncertainty_m:.1f}m")
            print(f"    Velocity Uncertainty: {track.velocity_uncertainty_m_s:.1f}m/s")
        
        for i, threat in enumerate(packet.threat_assessments):
            print(f"\n  Threat {threat.track_id}:")
            print(f"    Class: {threat.threat_class}")
            print(f"    Type: {threat.target_type}")
            print(f"    Confidence: {threat.classification_confidence:.2f}")
            print(f"    Uncertainty: {threat.classification_uncertainty:.2f}")
            print(f"    Priority: {threat.threat_priority}/10")
            print(f"    Recommendation: {threat.engagement_recommendation}")
            print(f"    Model Confidence: {threat.model_confidence:.2f}")
            print(f"    Feature Quality: {threat.feature_quality:.2f}")
        
        print(f"\nPacket Statistics:")
        print(f"  Total Sent: {self.packets_sent}")
        print(f"  Total Dropped: {self.packets_dropped}")
        if self.packets_sent > 0:
            print(f"  Drop Rate: {self.packets_dropped / self.packets_sent * 100:.2f}%")
        print(f"{'='*80}\n")
