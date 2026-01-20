"""
Cognitive Radar Controller - Closed-Loop Adaptive System.

Implements:
- State observation (detection/tracking confidence, false alarms, energy)
- Waveform parameter adaptation (gain, distance, target selection)
- Q-learning for reinforcement learning
- Reward function penalizing false alarms and high energy usage
- Manual override support
"""

import numpy as np
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
from collections import defaultdict
import json
import os


@dataclass
class RadarState:
    """Radar observation state for RL."""
    detection_confidence: float      # [0, 1]
    tracking_confidence: float       # [0, 1]
    false_alarm_rate: float          # [0, 1]
    energy_usage: float              # [0, 1] normalized
    num_active_tracks: int           # number of confirmed tracks
    time_step: int


@dataclass
class WaveformAction:
    """Waveform control action."""
    gain_db: float              # [1, 40] dB
    distance_m: float           # [10, 1000] m
    target_type: str            # which target to prioritize
    is_adaptive: bool           # whether controller issued this


class StateQuantizer:
    """Quantize continuous state to discrete bins for Q-learning."""
    
    def __init__(self, num_bins: int = 3):
        self.num_bins = num_bins
    
    def quantize(self, state: RadarState) -> Tuple[int, int, int, int, int]:
        """Quantize state to discrete bins."""
        det_conf_bin = min(max(int(state.detection_confidence * self.num_bins), 0), self.num_bins - 1)
        trk_conf_bin = min(max(int(state.tracking_confidence * self.num_bins), 0), self.num_bins - 1)
        fa_rate_bin = min(max(int(state.false_alarm_rate * self.num_bins), 0), self.num_bins - 1)
        energy_bin = min(max(int(state.energy_usage * self.num_bins), 0), self.num_bins - 1)
        num_tracks_bin = min(max(state.num_active_tracks, 0), 2)  # clamp to [0, 1, 2]
        
        return (det_conf_bin, trk_conf_bin, fa_rate_bin, energy_bin, num_tracks_bin)


class ActionSpace:
    """Discrete action space for waveform control."""
    
    GAIN_LEVELS = [5, 15, 25, 35]      # dB
    DISTANCE_LEVELS = [100, 300, 500, 800]  # meters
    TARGETS = ["Drone", "Aircraft", "Bird", "Helicopter", "Missile", "Clutter"]
    
    def __init__(self):
        # Generate all action combinations
        self.actions = []
        for gain in self.GAIN_LEVELS:
            for dist in self.DISTANCE_LEVELS:
                for target in self.TARGETS:
                    self.actions.append((gain, dist, target))
        self.num_actions = len(self.actions)
    
    def get_action(self, action_idx: int) -> Tuple[float, float, str]:
        """Get waveform parameters for action index."""
        if action_idx >= self.num_actions:
            action_idx = self.num_actions - 1
        return self.actions[action_idx]
    
    def get_default_action(self) -> Tuple[float, float, str]:
        """Return default/neutral action."""
        return (15.0, 300.0, "Drone")


class RewardFunction:
    """Compute reward for RL based on radar metrics."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.w_det = self.config.get('weight_detection', 0.4)      # detection confidence
        self.w_trk = self.config.get('weight_tracking', 0.3)       # tracking confidence
        self.w_fa = self.config.get('weight_false_alarm', -0.5)    # penalize false alarms
        self.w_energy = self.config.get('weight_energy', -0.2)     # penalize energy
        self.w_tracks = self.config.get('weight_tracks', 0.1)      # encourage tracking
    
    def compute(self, prev_state: RadarState, curr_state: RadarState) -> float:
        """Compute reward for state transition."""
        # Detection improvement
        det_delta = curr_state.detection_confidence - prev_state.detection_confidence
        
        # Tracking confidence
        trk_delta = curr_state.tracking_confidence - prev_state.tracking_confidence
        
        # False alarm penalty (stronger)
        fa_penalty = np.clip(curr_state.false_alarm_rate, 0, 1)
        
        # Energy penalty (stronger)
        energy_penalty = curr_state.energy_usage
        
        # Track count bonus
        track_bonus = curr_state.num_active_tracks * 0.1
        
        reward = (
            self.w_det * np.tanh(det_delta * 2) +
            self.w_trk * np.tanh(trk_delta * 2) +
            self.w_fa * fa_penalty +
            self.w_energy * energy_penalty +
            self.w_tracks * track_bonus
        )
        
        return float(reward)


class QLearningController:
    """Q-learning based cognitive radar controller."""
    
    def __init__(self, config: Dict = None):
        """
        Initialize Q-learning controller.
        
        Args:
            config: dict with keys:
                - 'learning_rate': alpha for Q-learning (default 0.1)
                - 'discount_factor': gamma for Q-learning (default 0.9)
                - 'epsilon': exploration rate (default 0.1)
                - 'epsilon_decay': epsilon decay rate (default 0.995)
                - 'min_epsilon': minimum epsilon (default 0.01)
                - 'max_memory': max history for learning (default 1000)
        """
        self.config = config or {}
        self.learning_rate = self.config.get('learning_rate', 0.1)
        self.discount_factor = self.config.get('discount_factor', 0.9)
        self.epsilon = self.config.get('epsilon', 0.1)
        self.epsilon_decay = self.config.get('epsilon_decay', 0.995)
        self.min_epsilon = self.config.get('min_epsilon', 0.01)
        self.max_memory = self.config.get('max_memory', 1000)
        
        # Q-table: state -> action -> Q-value
        self.Q = defaultdict(lambda: np.zeros(24))  # 4x4x6 = 96 actions max
        
        # Experience replay buffer
        self.memory = []
        self.episode_rewards = []
        
        # Action and reward functions
        self.action_space = ActionSpace()
        self.reward_fn = RewardFunction(self.config.get('reward', {}))
        self.quantizer = StateQuantizer(num_bins=3)
        
        self.step_count = 0
    
    def select_action(self, state: RadarState, manual_override: Optional[WaveformAction] = None) -> WaveformAction:
        """
        Select waveform action using epsilon-greedy Q-learning.
        
        Args:
            state: current radar state
            manual_override: if provided, use this instead of learned policy
        
        Returns:
            WaveformAction with recommended parameters
        """
        if manual_override is not None:
            return manual_override
        
        state_key = self.quantizer.quantize(state)
        
        # Epsilon-greedy action selection
        if np.random.random() < self.epsilon:
            # Explore: random action
            action_idx = np.random.randint(0, self.action_space.num_actions)
        else:
            # Exploit: greedy action
            Q_values = self.Q[state_key][:self.action_space.num_actions]
            action_idx = np.argmax(Q_values)
        
        gain, dist, target = self.action_space.get_action(action_idx)
        return WaveformAction(gain_db=gain, distance_m=dist, target_type=target, is_adaptive=True)
    
    def update(self, prev_state: RadarState, action_idx: int, curr_state: RadarState) -> float:
        """
        Q-learning update rule.
        
        Args:
            prev_state: state before action
            action_idx: action taken
            curr_state: state after action
        
        Returns:
            reward received
        """
        # Compute reward
        reward = self.reward_fn.compute(prev_state, curr_state)
        
        # Quantize states
        prev_state_key = self.quantizer.quantize(prev_state)
        curr_state_key = self.quantizer.quantize(curr_state)
        
        # Q-learning: Q(s,a) += alpha * (reward + gamma * max_a' Q(s',a') - Q(s,a))
        max_next_Q = np.max(self.Q[curr_state_key])
        Q_sa = self.Q[prev_state_key][action_idx]
        self.Q[prev_state_key][action_idx] = Q_sa + self.learning_rate * (
            reward + self.discount_factor * max_next_Q - Q_sa
        )
        
        # Store in memory
        self.memory.append((prev_state_key, action_idx, reward, curr_state_key))
        if len(self.memory) > self.max_memory:
            self.memory.pop(0)
        
        self.episode_rewards.append(reward)
        self.step_count += 1
        
        # Decay epsilon
        if self.step_count % 100 == 0:
            self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
        
        return reward
    
    def get_policy(self) -> Dict:
        """Get current learned policy (greedy Q-values)."""
        policy = {}
        for state_key in self.Q.keys():
            Q_values = self.Q[state_key][:self.action_space.num_actions]
            best_action = np.argmax(Q_values)
            policy[str(state_key)] = {
                'action_idx': int(best_action),
                'Q_value': float(Q_values[best_action])
            }
        return policy
    
    def save_policy(self, filepath: str):
        """Save learned policy to disk."""
        policy_data = {
            'Q': {str(k): v.tolist() for k, v in self.Q.items()},
            'step_count': self.step_count,
            'epsilon': self.epsilon
        }
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(policy_data, f, indent=2)
    
    def load_policy(self, filepath: str):
        """Load learned policy from disk."""
        if not os.path.exists(filepath):
            return
        with open(filepath, 'r') as f:
            policy_data = json.load(f)
        self.Q = defaultdict(lambda: np.zeros(24))
        for k_str, v in policy_data['Q'].items():
            k = eval(k_str)  # Convert string back to tuple
            self.Q[k] = np.array(v)
        self.step_count = policy_data.get('step_count', 0)
        self.epsilon = policy_data.get('epsilon', self.epsilon)
    
    def reset_episode(self):
        """Reset episodic statistics."""
        if self.episode_rewards:
            avg_reward = np.mean(self.episode_rewards)
            return avg_reward
        return 0.0


class CognitiveRadarController:
    """
    Top-level cognitive radar controller orchestrating adaptation.
    
    Workflow:
    1. Observe: gather detection, tracking, false alarm metrics
    2. Decide: Q-learning selects waveform parameters
    3. Act: apply parameters to radar (gain, distance, target type)
    4. Learn: compute reward and update Q-table
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize cognitive controller.
        
        Args:
            config: dict with 'rl', 'reward' sub-dicts for Q-learner config
        """
        self.config = config or {}
        self.learner = QLearningController(self.config)
        
        self.prev_state: Optional[RadarState] = None
        self.prev_action_idx: Optional[int] = None
        self.manual_override_mode = False
        self.manual_action: Optional[WaveformAction] = None
    
    def observe(self, 
                detection_confidence: float,
                tracking_confidence: float, 
                num_active_tracks: int,
                total_detections: int,
                false_positives: int,
                current_gain: float,
                max_gain: float = 40.0) -> RadarState:
        """
        Observe radar state metrics.
        
        Args:
            detection_confidence: [0, 1] quality of current detections
            tracking_confidence: [0, 1] quality of current tracks
            num_active_tracks: number of confirmed tracks
            total_detections: total detections this frame
            false_positives: estimated false alarms
            current_gain: current gain setting in dB
            max_gain: maximum gain for normalization
        
        Returns:
            RadarState observation
        """
        # Compute false alarm rate
        fa_rate = 0.0
        if total_detections > 0:
            fa_rate = false_positives / total_detections
        
        # Normalize energy usage (gain / max_gain)
        energy_usage = current_gain / max_gain
        
        state = RadarState(
            detection_confidence=np.clip(detection_confidence, 0, 1),
            tracking_confidence=np.clip(tracking_confidence, 0, 1),
            false_alarm_rate=np.clip(fa_rate, 0, 1),
            energy_usage=np.clip(energy_usage, 0, 1),
            num_active_tracks=num_active_tracks,
            time_step=self.learner.step_count
        )
        
        return state
    
    def decide(self, curr_state: RadarState) -> WaveformAction:
        """
        Decide next waveform parameters.
        
        Uses Q-learning if not in manual override mode.
        """
        manual_override = None
        if self.manual_override_mode and self.manual_action is not None:
            manual_override = self.manual_action
            self.manual_override_mode = False  # single-use override
        
        return self.learner.select_action(curr_state, manual_override)
    
    def learn(self, curr_state: RadarState) -> Optional[float]:
        """
        Update Q-learning with new state.
        
        Args:
            curr_state: observation after taking action
        
        Returns:
            reward received, or None if first observation
        """
        if self.prev_state is None:
            self.prev_state = curr_state
            return None
        
        # Find action index for the action taken
        # (simplified: use greedy action from prev_state)
        prev_state_key = self.learner.quantizer.quantize(self.prev_state)
        Q_values = self.learner.Q[prev_state_key][:self.learner.action_space.num_actions]
        action_idx = np.argmax(Q_values)
        
        # Update Q-learning
        reward = self.learner.update(self.prev_state, action_idx, curr_state)
        
        self.prev_state = curr_state
        self.prev_action_idx = action_idx
        
        return reward
    
    def set_manual_override(self, gain: float, distance: float, target_type: str):
        """
        Set manual override for next decision cycle.
        
        Args:
            gain: gain in dB
            distance: distance in meters
            target_type: target type string
        """
        self.manual_override_mode = True
        self.manual_action = WaveformAction(
            gain_db=gain, distance_m=distance, target_type=target_type, is_adaptive=False
        )
    
    def disable_manual_override(self):
        """Disable manual override mode."""
        self.manual_override_mode = False
        self.manual_action = None
    
    def get_status(self) -> Dict:
        """Get controller status and statistics."""
        avg_reward = self.learner.reset_episode()
        return {
            'step_count': self.learner.step_count,
            'epsilon': self.learner.epsilon,
            'avg_reward': avg_reward,
            'manual_override': self.manual_override_mode,
            'memory_size': len(self.learner.memory),
            'q_table_size': len(self.learner.Q)
        }


# Example usage / demo
if __name__ == "__main__":
    print("=== Cognitive Radar Controller Demo ===\n")
    
    cfg = {
        'learning_rate': 0.1,
        'discount_factor': 0.9,
        'epsilon': 0.15,
        'reward': {
            'weight_detection': 0.4,
            'weight_tracking': 0.3,
            'weight_false_alarm': -0.5,
            'weight_energy': -0.2,
            'weight_tracks': 0.1
        }
    }
    
    controller = CognitiveRadarController(cfg)
    
    # Simulate 20 radar frames
    for frame in range(20):
        print(f"Frame {frame}:")
        
        # Observe: simulate metrics
        det_conf = 0.5 + 0.3 * np.sin(frame * 0.3)
        trk_conf = 0.6 + 0.2 * np.cos(frame * 0.2)
        num_tracks = np.random.randint(0, 4)
        total_dets = np.random.randint(5, 20)
        false_pos = np.random.randint(0, 3)
        current_gain = 15.0
        
        curr_state = controller.observe(det_conf, trk_conf, num_tracks, total_dets, false_pos, current_gain)
        
        # Learn from previous step
        reward = controller.learn(curr_state)
        if reward is not None:
            print(f"  Reward: {reward:.3f}")
        
        # Decide next action
        action = controller.decide(curr_state)
        print(f"  Action: gain={action.gain_db}dB, dist={action.distance_m}m, target={action.target_type}, adaptive={action.is_adaptive}")
        
        # Status
        status = controller.get_status()
        print(f"  Status: epsilon={status['epsilon']:.3f}, Q-tables={status['q_table_size']}\n")
