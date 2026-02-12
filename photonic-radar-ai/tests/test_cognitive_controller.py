"""Unit tests for cognitive radar controller."""

import pytest
import numpy as np
import tempfile
import os
from src.cognitive_controller import (
    RadarState, WaveformAction, StateQuantizer, ActionSpace,
    RewardFunction, QLearningController, CognitiveRadarController
)


class TestStateQuantizer:
    """Tests for state discretization."""
    
    def test_quantize_perfect_state(self):
        """Test quantization of perfect detection state."""
        state = RadarState(
            detection_confidence=1.0,
            tracking_confidence=1.0,
            false_alarm_rate=0.0,
            energy_usage=0.0,
            num_active_tracks=5,
            time_step=0
        )
        quantizer = StateQuantizer(num_bins=3)
        bins = quantizer.quantize(state)
        assert bins[0] == 2  # max detection bin
        assert bins[1] == 2  # max tracking bin
        assert bins[2] == 0  # min false alarm bin
        assert bins[3] == 0  # min energy bin
    
    def test_quantize_poor_state(self):
        """Test quantization of poor detection state."""
        state = RadarState(
            detection_confidence=0.1,
            tracking_confidence=0.1,
            false_alarm_rate=0.9,
            energy_usage=0.9,
            num_active_tracks=0,
            time_step=0
        )
        quantizer = StateQuantizer(num_bins=3)
        bins = quantizer.quantize(state)
        assert bins[0] == 0  # min detection bin
        assert bins[1] == 0  # min tracking bin
        assert bins[2] == 2  # max false alarm bin
        assert bins[3] == 2  # max energy bin
    
    def test_quantize_clamps_bounds(self):
        """Test that quantizer clamps out-of-range values."""
        state = RadarState(
            detection_confidence=1.5,  # out of range
            tracking_confidence=-0.5,  # out of range
            false_alarm_rate=1.0,
            energy_usage=1.0,
            num_active_tracks=100,
            time_step=0
        )
        quantizer = StateQuantizer(num_bins=3)
        bins = quantizer.quantize(state)
        # Should clamp to valid bins without error
        assert all(0 <= b < 3 for b in bins[:4])


class TestActionSpace:
    """Tests for action space."""
    
    def test_action_count(self):
        """Test correct number of actions."""
        space = ActionSpace()
        # 4 gain levels x 4 distance levels x 6 targets = 96
        assert space.num_actions == 96
    
    def test_get_action(self):
        """Test action retrieval."""
        space = ActionSpace()
        gain, dist, target = space.get_action(0)
        assert gain == 5.0
        assert dist == 100.0
        assert target == "Drone"
    
    def test_get_default_action(self):
        """Test default action."""
        space = ActionSpace()
        gain, dist, target = space.get_default_action()
        assert gain == 15.0
        assert dist == 300.0
        assert target == "Drone"
    
    def test_action_out_of_bounds(self):
        """Test that out-of-bounds action index clamps correctly."""
        space = ActionSpace()
        gain, dist, target = space.get_action(1000)
        # Should not crash, return last valid action
        assert gain is not None
        assert dist is not None
        assert target is not None


class TestRewardFunction:
    """Tests for reward computation."""
    
    def test_reward_on_improvement(self):
        """Test positive reward for detection improvement."""
        prev_state = RadarState(0.3, 0.3, 0.1, 0.3, 1, 0)
        curr_state = RadarState(0.8, 0.8, 0.05, 0.3, 2, 1)
        
        reward_fn = RewardFunction()
        reward = reward_fn.compute(prev_state, curr_state)
        
        # Should receive positive reward for improvement
        assert reward > 0.0
    
    def test_reward_on_degradation(self):
        """Test negative reward for detection degradation."""
        prev_state = RadarState(0.8, 0.8, 0.05, 0.3, 2, 0)
        curr_state = RadarState(0.3, 0.3, 0.5, 0.8, 0, 1)
        
        reward_fn = RewardFunction()
        reward = reward_fn.compute(prev_state, curr_state)
        
        # Should receive negative reward for degradation
        assert reward < 0.0
    
    def test_reward_penalizes_false_alarms(self):
        """Test that false alarms are penalized."""
        state1 = RadarState(0.5, 0.5, 0.0, 0.5, 1, 0)
        state2 = RadarState(0.5, 0.5, 0.5, 0.5, 1, 1)
        
        reward_fn = RewardFunction()
        reward = reward_fn.compute(state1, state2)
        
        # High false alarm should result in negative reward
        assert reward < 0.0
    
    def test_reward_penalizes_energy(self):
        """Test that high energy usage is penalized."""
        state1 = RadarState(0.7, 0.7, 0.1, 0.2, 1, 0)
        state2 = RadarState(0.7, 0.7, 0.1, 0.95, 1, 1)
        
        reward_fn = RewardFunction()
        reward = reward_fn.compute(state1, state2)
        
        # High energy should be penalized
        assert reward < 0.0


class TestQLearningController:
    """Tests for Q-learning controller."""
    
    def test_controller_initialization(self):
        """Test Q-learning controller creation."""
        cfg = {'learning_rate': 0.1, 'discount_factor': 0.9}
        controller = QLearningController(cfg)
        
        assert controller.learning_rate == 0.1
        assert controller.discount_factor == 0.9
        assert len(controller.Q) == 0  # Q-table initially empty
    
    def test_action_selection(self):
        """Test action selection (epsilon-greedy)."""
        controller = QLearningController()
        state = RadarState(0.5, 0.5, 0.1, 0.3, 1, 0)
        
        action = controller.select_action(state)
        
        assert isinstance(action, WaveformAction)
        assert 1 <= action.gain_db <= 40
        assert 10 <= action.distance_m <= 1000
        assert action.target_type in ActionSpace.TARGETS
        assert action.is_adaptive == True
    
    def test_manual_override(self):
        """Test manual override of learned policy."""
        controller = QLearningController()
        state = RadarState(0.5, 0.5, 0.1, 0.3, 1, 0)
        
        override = WaveformAction(20.0, 500.0, "Aircraft", is_adaptive=False)
        action = controller.select_action(state, manual_override=override)
        
        assert action.gain_db == 20.0
        assert action.distance_m == 500.0
        assert action.target_type == "Aircraft"
        assert action.is_adaptive == False
    
    def test_q_learning_update(self):
        """Test Q-learning value update."""
        controller = QLearningController({'learning_rate': 0.1})
        
        prev_state = RadarState(0.3, 0.3, 0.1, 0.3, 1, 0)
        curr_state = RadarState(0.7, 0.7, 0.05, 0.3, 2, 1)
        
        reward = controller.update(prev_state, action_idx=5, curr_state=curr_state)
        
        assert isinstance(reward, float)
        assert len(controller.Q) > 0  # Q-table updated
    
    def test_epsilon_decay(self):
        """Test that epsilon decays over time."""
        cfg = {'epsilon': 0.5, 'epsilon_decay': 0.99, 'min_epsilon': 0.01}
        controller = QLearningController(cfg)
        
        initial_epsilon = controller.epsilon
        
        # Perform many updates to trigger decay
        for i in range(150):
            state1 = RadarState(0.5, 0.5, 0.1, 0.3, 1, i)
            state2 = RadarState(0.6, 0.6, 0.05, 0.3, 1, i + 1)
            controller.update(state1, 0, state2)
        
        # Epsilon should have decayed
        assert controller.epsilon < initial_epsilon
        assert controller.epsilon >= cfg['min_epsilon']
    
    def test_policy_save_load(self):
        """Test saving and loading learned policy."""
        controller1 = QLearningController()
        
        # Add some learning
        for i in range(10):
            state1 = RadarState(0.5, 0.5, 0.1, 0.3, 1, i)
            state2 = RadarState(0.6, 0.6, 0.05, 0.3, 1, i + 1)
            controller1.update(state1, i % 10, state2)
        
        # Save policy
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, 'policy.json')
            controller1.save_policy(filepath)
            
            # Load into new controller
            controller2 = QLearningController()
            controller2.load_policy(filepath)
            
            # Q-tables should match
            assert len(controller2.Q) == len(controller1.Q)


class TestCognitiveRadarController:
    """Tests for top-level cognitive controller."""
    
    def test_controller_initialization(self):
        """Test cognitive controller creation."""
        cfg = {'learning_rate': 0.1}
        controller = CognitiveRadarController(cfg)
        
        assert controller.learner is not None
        assert controller.manual_override_mode == False
    
    def test_observe_and_decide(self):
        """Test observation and decision workflow."""
        controller = CognitiveRadarController()
        
        # Observe state
        state = controller.observe(
            detection_confidence=0.7,
            tracking_confidence=0.6,
            num_active_tracks=2,
            total_detections=10,
            false_positives=1,
            current_gain=15.0,
            max_gain=40.0
        )
        
        assert state.detection_confidence == 0.7
        assert state.false_alarm_rate == 0.1  # 1/10
        
        # Decide action
        action = controller.decide(state)
        assert isinstance(action, WaveformAction)
    
    def test_full_cycle_with_learning(self):
        """Test full observe-decide-learn cycle."""
        controller = CognitiveRadarController()
        
        # First observation
        state1 = controller.observe(0.5, 0.5, 1, 10, 2, 15.0)
        controller.decide(state1)
        reward1 = controller.learn(state1)
        assert reward1 is None  # First cycle has no prior state
        
        # Second observation
        state2 = controller.observe(0.7, 0.7, 2, 12, 1, 20.0)
        controller.decide(state2)
        reward2 = controller.learn(state2)
        assert reward2 is not None  # Should have reward from state transition
    
    def test_manual_override_single_use(self):
        """Test that manual override is single-use."""
        controller = CognitiveRadarController()
        
        # Set manual override
        controller.set_manual_override(25.0, 400.0, "Missile")
        assert controller.manual_override_mode == True
        
        state = controller.observe(0.5, 0.5, 1, 10, 0, 15.0)
        action = controller.decide(state)
        
        # Should use override
        assert action.gain_db == 25.0
        assert action.distance_m == 400.0
        assert action.target_type == "Missile"
        
        # Override should be consumed
        assert controller.manual_override_mode == False
    
    def test_disable_manual_override(self):
        """Test disabling manual override."""
        controller = CognitiveRadarController()
        controller.set_manual_override(25.0, 400.0, "Missile")
        controller.disable_manual_override()
        
        assert controller.manual_override_mode == False
    
    def test_get_status(self):
        """Test status reporting."""
        controller = CognitiveRadarController()
        
        status = controller.get_status()
        
        assert 'step_count' in status
        assert 'epsilon' in status
        assert 'avg_reward' in status
        assert 'manual_override' in status
        assert 'q_table_size' in status
        assert status['manual_override'] == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
