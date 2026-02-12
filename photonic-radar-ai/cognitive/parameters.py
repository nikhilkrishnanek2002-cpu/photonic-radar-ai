"""
Adaptive Waveform Parameter Manager
===================================

Manages the translation of cognitive adaptation commands into actual radar 
waveform parameters. Handles parameter caching, bounded scaling, and integration
with the signal generation pipeline.

Key Functions:
1. Parameter caching across frames (feedforward adaptation)
2. Bounded scaling enforcement
3. Hardware constraint checking
4. Legacy parameter conversion (old config → adaptive config)

Author: Adaptive Waveform Systems
"""

import numpy as np
from dataclasses import dataclass, asdict
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class RadarWaveformParameters:
    """
    Complete radar waveform parameter set.
    These are the physical parameters used by photonic signal generation.
    """
    # Chirp/FMCW parameters
    bandwidth: float = 1e9                  # Hz, typical 1 GHz
    chirp_duration: float = 10e-6           # seconds, typical 10 µs
    center_frequency: float = 10e9          # Hz, typically 10 GHz (X-band)
    
    # Pulse repetition
    prf: float = 20e3                       # Hz, typical 20 kHz
    num_pulses: int = 64                    # Number of coherent pulses per CPI
    
    # Power
    tx_power_watts: float = 10.0             # Transmit power in watts
    
    # Detection parameters
    cfar_pfa: float = 1e-6                   # Target probability of false alarm
    cfar_alpha: float = None                 # Computed from pfa (set later)
    cfar_guard: int = 2                      # Guard cells for CFAR
    cfar_train: int = 8                      # Training cells for CFAR
    
    # Processing
    dwell_frames: int = 1                    # Number of coherent frames to integrate
    integration_time_ms: float = 50.0        # Total integration time
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        d = asdict(self)
        return d


@dataclass
class AdaptiveParameterCache:
    """
    Persistent cache of adaptive parameters across frames.
    Allows cognitive decisions from frame N to be applied to frame N+1 TX.
    """
    current_frame_id: int = 0
    
    # Current waveform parameters
    waveform_params: RadarWaveformParameters = None
    
    # Pending adaptations (to be applied next frame)
    pending_adaptations: Dict = None
    
    # Historical tracking
    parameter_history: list = None
    
    def __post_init__(self):
        if self.waveform_params is None:
            self.waveform_params = RadarWaveformParameters()
        if self.pending_adaptations is None:
            self.pending_adaptations = {}
        if self.parameter_history is None:
            self.parameter_history = []


class AdaptiveParameterManager:
    """
    Manages adaptive radar waveform parameters.
    
    Responsibilities:
    1. Convert cognitive adaptation commands to parameter deltas
    2. Enforce hardware constraints and bounds
    3. Cache parameters for feedforward application
    4. Maintain parameter history for analysis
    """
    
    # Hardware constraints (realistic)
    HARDWARE_LIMITS = {
        'bandwidth': (100e6, 2e9),              # 100 MHz to 2 GHz
        'chirp_duration': (1e-6, 100e-6),       # 1 µs to 100 µs
        'prf': (4e3, 50e3),                     # 4 kHz to 50 kHz
        'tx_power_watts': (1.0, 100.0),         # 1 W to 100 W
        'dwell_frames': (1, 20),                # 1 to 20 coherent frames
    }
    
    def __init__(self):
        """Initialize parameter manager."""
        self.cache = AdaptiveParameterCache()
        self.nominal_params = RadarWaveformParameters()
        self.logger = logging.getLogger(__name__)
    
    def apply_adaptation_command(self, 
                                 cmd,  # AdaptationCommand from cognitive engine
                                 current_params: RadarWaveformParameters) \
            -> RadarWaveformParameters:
        """
        Convert cognitive adaptation command to new waveform parameters.
        
        Args:
            cmd: AdaptationCommand with scaling factors
            current_params: Current waveform parameters as reference
            
        Returns:
            New RadarWaveformParameters with adapted values
        """
        new_params = RadarWaveformParameters(
            bandwidth=current_params.bandwidth * cmd.bandwidth_scaling,
            chirp_duration=current_params.chirp_duration,  # Keep fixed for now
            center_frequency=current_params.center_frequency,
            
            prf=current_params.prf * cmd.prf_scale,
            num_pulses=current_params.num_pulses,  # Coherent pulses per CPI
            
            tx_power_watts=current_params.tx_power_watts * cmd.tx_power_scaling,
            
            cfar_pfa=current_params.cfar_pfa,  # Keep target Pfa
            cfar_alpha=current_params.cfar_alpha * cmd.cfar_alpha_scale if current_params.cfar_alpha else None,
            cfar_guard=current_params.cfar_guard,
            cfar_train=current_params.cfar_train,
            
            dwell_frames=int(np.round(current_params.dwell_frames * cmd.dwell_time_scale)),
            integration_time_ms=current_params.integration_time_ms * cmd.dwell_time_scale,
        )
        
        # Enforce hardware constraints
        new_params = self._enforce_hardware_limits(new_params)
        
        # Recompute CFAR alpha if needed
        if new_params.cfar_alpha is None:
            new_params.cfar_alpha = self._compute_cfar_alpha(new_params.cfar_pfa, 
                                                             new_params.cfar_guard,
                                                             new_params.cfar_train)
        
        # Cache the adaptation
        self.cache.pending_adaptations = {
            'bandwidth_scaling': cmd.bandwidth_scaling,
            'prf_scale': cmd.prf_scale,
            'tx_power_scaling': cmd.tx_power_scaling,
            'cfar_alpha_scale': cmd.cfar_alpha_scale,
            'dwell_time_scale': cmd.dwell_time_scale,
        }
        
        # Log adaptation
        self.logger.info(
            f"Cognitive Adaptation [Frame {cmd.frame_id}]: "
            f"BW×{cmd.bandwidth_scaling:.2f}, "
            f"PRF×{cmd.prf_scale:.2f}, "
            f"TxPower×{cmd.tx_power_scaling:.2f}"
        )
        
        return new_params
    
    def _enforce_hardware_limits(self, params: RadarWaveformParameters) -> RadarWaveformParameters:
        """
        Clip all parameters to hardware limits.
        Ensures physical realizability.
        """
        for param_name, (min_val, max_val) in self.HARDWARE_LIMITS.items():
            if hasattr(params, param_name):
                current_val = getattr(params, param_name)
                clipped_val = np.clip(current_val, min_val, max_val)
                
                if clipped_val != current_val:
                    self.logger.warning(
                        f"Parameter {param_name} clipped: "
                        f"{current_val:.2e} → {clipped_val:.2e} "
                        f"(bounds: {min_val:.2e}–{max_val:.2e})"
                    )
                
                setattr(params, param_name, clipped_val)
        
        return params
    
    def _compute_cfar_alpha(self, pfa: float, guard: int, train: int) -> float:
        """
        Compute CA-CFAR alpha threshold from target Pfa.
        
        Formula for square-law detector:
        alpha = num_train * (Pfa^(-1/num_train) - 1)
        
        Args:
            pfa: Target probability of false alarm
            guard: Number of guard cells
            train: Number of training cells per side
            
        Returns:
            CFAR alpha threshold
        """
        num_train = (2*train + 2*guard + 1)**2 - (2*guard + 1)**2
        if num_train <= 0:
            num_train = 16  # Default fallback
        
        alpha = num_train * (pfa**(-1.0 / num_train) - 1.0)
        return float(np.clip(alpha, 1.0, 1e6))
    
    def update_cache(self, frame_id: int, params: RadarWaveformParameters):
        """
        Update cached parameters for feedforward to next frame.
        """
        self.cache.current_frame_id = frame_id
        self.cache.waveform_params = params
        self.cache.parameter_history.append({
            'frame_id': frame_id,
            'params': asdict(params),
            'timestamp': None,
        })
        
        # Keep history bounded
        if len(self.cache.parameter_history) > 1000:
            self.cache.parameter_history.pop(0)
    
    def get_current_parameters(self) -> RadarWaveformParameters:
        """
        Get current waveform parameters from cache.
        """
        return self.cache.waveform_params if self.cache.waveform_params else self.nominal_params
    
    def compute_derived_parameters(self, params: RadarWaveformParameters) -> Dict:
        """
        Compute derived radar parameters (for reference/analysis).
        
        Args:
            params: Waveform parameters
            
        Returns:
            Dict of derived quantities
        """
        c = 3e8  # Speed of light
        
        # Resolution
        range_res = c / (2 * params.bandwidth)
        velocity_res = c / (2 * params.center_frequency * params.chirp_duration * params.num_pulses)
        
        # Unambiguous ranges
        r_unambiguous = c / (2 * params.prf)
        
        # Unambiguous velocity
        wavelength = c / params.center_frequency
        v_unambiguous = (wavelength * params.prf) / 4
        
        # Processing gain
        processing_gain_db = 10 * np.log10(params.num_pulses * params.dwell_frames)
        
        # SNR improvement from integration
        snr_improvement_db = 10 * np.log10(params.dwell_frames) + \
                            10 * np.log10(params.num_pulses)
        
        return {
            'range_resolution_m': range_res,
            'velocity_resolution_m_s': velocity_res,
            'unambiguous_range_m': r_unambiguous,
            'unambiguous_velocity_m_s': v_unambiguous,
            'processing_gain_db': processing_gain_db,
            'snr_improvement_db': snr_improvement_db,
            'integration_time_ms': params.integration_time_ms,
        }
    
    def get_parameter_impact_summary(self, 
                                     old_params: RadarWaveformParameters,
                                     new_params: RadarWaveformParameters) -> Dict:
        """
        Summarize impact of parameter changes on performance.
        """
        old_derived = self.compute_derived_parameters(old_params)
        new_derived = self.compute_derived_parameters(new_params)
        
        impact = {}
        for key in old_derived:
            old_val = old_derived[key]
            new_val = new_derived[key]
            if old_val != 0:
                pct_change = 100 * (new_val - old_val) / old_val
                impact[key] = {
                    'old': old_val,
                    'new': new_val,
                    'percent_change': pct_change,
                }
            else:
                impact[key] = {'old': old_val, 'new': new_val}
        
        return impact
    
    def validate_parameters(self, params: RadarWaveformParameters) -> Tuple[bool, List[str]]:
        """
        Validate that parameters are physically realizable.
        
        Returns:
            (is_valid, list_of_warnings_or_errors)
        """
        issues = []
        
        # Check ranges
        for param_name, (min_val, max_val) in self.HARDWARE_LIMITS.items():
            if hasattr(params, param_name):
                val = getattr(params, param_name)
                if val < min_val or val > max_val:
                    issues.append(f"{param_name}: {val:.2e} out of bounds [{min_val:.2e}, {max_val:.2e}]")
        
        # Check consistency
        if params.chirp_duration * params.prf > 0.8:
            issues.append("Duty cycle high: chirp_duration * PRF > 0.8 (may cause ambiguity)")
        
        if params.dwell_frames < 1:
            issues.append("dwell_frames must be >= 1")
        
        # Warnings (non-fatal)
        if params.bandwidth > 1.8e9:
            issues.append(f"WARNING: Very wide bandwidth ({params.bandwidth/1e9:.1f} GHz) may exceed component specs")
        
        if params.tx_power_watts > 50:
            issues.append(f"WARNING: Very high power ({params.tx_power_watts:.1f} W) may stress amplifier")
        
        is_valid = len([i for i in issues if not i.startswith("WARNING")]) == 0
        return is_valid, issues


# ============================================================================
# Integration Helpers
# ============================================================================

def convert_config_to_waveform_params(config_dict: Dict) -> RadarWaveformParameters:
    """
    Convert YAML config dict to RadarWaveformParameters.
    
    Args:
        config_dict: Configuration dictionary (e.g., from config.yaml)
        
    Returns:
        RadarWaveformParameters
    """
    # Extract nested config paths
    photonic_cfg = config_dict.get('photonic', {})
    detection_cfg = config_dict.get('detection', {})
    
    params = RadarWaveformParameters(
        bandwidth=photonic_cfg.get('bandwidth', 1e9),
        chirp_duration=photonic_cfg.get('duration', 10e-6),
        center_frequency=photonic_cfg.get('carrier_freq', 10e9),
        
        prf=photonic_cfg.get('prf', 20e3),
        num_pulses=detection_cfg.get('n_chirps', 64),
        
        tx_power_watts=photonic_cfg.get('optical_power_dbm_to_watts', 10.0),
        
        cfar_pfa=detection_cfg.get('pfa', 1e-6),
        cfar_guard=detection_cfg.get('guard', 2),
        cfar_train=detection_cfg.get('train', 8),
        
        dwell_frames=1,
    )
    
    # Compute CFAR alpha
    manager = AdaptiveParameterManager()
    params.cfar_alpha = manager._compute_cfar_alpha(params.cfar_pfa, 
                                                    params.cfar_guard,
                                                    params.cfar_train)
    
    return params


def waveform_params_to_photonic_config(params: RadarWaveformParameters) -> Dict:
    """
    Convert RadarWaveformParameters back to photonic config format.
    Used for passing adapted parameters to signal generation.
    
    Args:
        params: RadarWaveformParameters
        
    Returns:
        Dict compatible with photonic.signals.PhotonicConfig
    """
    return {
        'bandwidth': params.bandwidth,
        'duration': params.chirp_duration,
        'carrier_freq': params.center_frequency,
        'prf': params.prf,
        'num_pulses': params.num_pulses,
        'tx_power': params.tx_power_watts,
    }
