"""
EW Feedback Publisher
=====================

Publishes EW feedback messages from Cognitive EW-AI to radar sensor.
Generates countermeasure and engagement status messages.

Author: Cognitive EW Systems Team
"""

import logging
import time
import json
from pathlib import Path
from typing import List, Optional
import threading
import queue
import numpy as np

from interfaces.message_schema import (
    EWFeedbackMessage, Countermeasure, EngagementStatus,
    CountermeasureType, EngagementState
)

logger = logging.getLogger(__name__)


class EWFeedbackPublisher:
    """
    Publishes EW feedback messages to radar.
    
    Generates countermeasures based on threat assessments.
    """
    
    def __init__(self,
                 effector_id: str = 'COGNITIVE_EW_01',
                 export_directory: str = 'runtime/ew_feedback',
                 enable_export: bool = True,
                 enable_event_bus: bool = False,
                 log_all_transmissions: bool = True):
        """
        Initialize EW feedback publisher.
        
        Args:
            effector_id: EW system identifier
            export_directory: Directory for feedback files
            enable_export: Enable/disable file export
            enable_event_bus: Enable/disable event bus publishing
            log_all_transmissions: Log every transmitted packet
        """
        self.effector_id = effector_id
        self.export_dir = Path(export_directory)
        self.enable_export = enable_export
        self.enable_event_bus = enable_event_bus
        self.log_all_transmissions = log_all_transmissions
        
        if self.enable_export:
            self.export_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize event bus if enabled
        self.defense_bus = None
        if self.enable_event_bus:
            from defense_core import get_defense_bus
            self.defense_bus = get_defense_bus()
            logger.info(f"[EW-FEEDBACK] Event bus publishing ENABLED for {self.effector_id}")
        
        self.cm_counter = 0
        self.messages_published = 0
        
        # Statistics
        self.packets_sent = 0
        self.packets_dropped = 0
        
        # Track active countermeasures
        self.active_cms: List[Countermeasure] = []
        self.active_engagements: List[EngagementStatus] = []
        
        logger.info(f"EW Feedback Publisher initialized: {self.effector_id}")
    
    def generate_countermeasures(self, threat_assessments: List) -> List[Countermeasure]:
        """
        Generate countermeasures based on threat assessments.
        
        Args:
            threat_assessments: List of ThreatAssessment objects
            
        Returns:
            List of Countermeasure objects
        """
        countermeasures = []
        
        for threat in threat_assessments:
            # Only engage hostile threats
            if threat.threat_class != "HOSTILE":
                continue
            
            # Select countermeasure type based on target type
            cm_type = self._select_cm_type(threat.target_type)
            
            # Calculate jammer power based on threat priority
            power_dbm = self._calculate_jammer_power(threat.threat_priority)
            
            # Estimate effectiveness
            effectiveness = 0.6 + 0.2 * (threat.threat_priority / 10.0)
            
            cm = Countermeasure(
                countermeasure_id=self.cm_counter,
                target_track_id=threat.track_id,
                cm_type=cm_type,
                start_time=time.time(),
                power_level_dbm=power_dbm,
                frequency_mhz=77000.0,  # Match radar frequency
                bandwidth_mhz=150.0,
                effectiveness_score=min(effectiveness, 0.9)
            )
            
            countermeasures.append(cm)
            self.cm_counter += 1
        
        return countermeasures
    
    def _select_cm_type(self, target_type: str) -> str:
        """Select appropriate countermeasure type for target."""
        if target_type == "MISSILE":
            return CountermeasureType.NOISE_JAM.value
        elif target_type == "AIRCRAFT":
            return CountermeasureType.DECEPTION_JAM.value
        elif target_type == "UAV":
            return CountermeasureType.NOISE_JAM.value
        else:
            return CountermeasureType.NOISE_JAM.value
    
    def _calculate_jammer_power(self, threat_priority: int) -> float:
        """Calculate jammer power based on threat priority."""
        # Higher priority = more power
        base_power_dbm = 30.0  # 1 Watt
        priority_boost_db = (threat_priority / 10.0) * 10.0  # Up to +10dB
        return base_power_dbm + priority_boost_db
    
    def generate_engagement_status(self, threat_assessments: List) -> List[EngagementStatus]:
        """
        Generate engagement status for threats.
        
        Args:
            threat_assessments: List of ThreatAssessment objects
            
        Returns:
            List of EngagementStatus objects
        """
        engagements = []
        
        for threat in threat_assessments:
            if threat.engagement_recommendation == "ENGAGE":
                state = EngagementState.ENGAGING.value
            elif threat.engagement_recommendation == "MONITOR":
                state = EngagementState.MONITORING.value
            else:
                continue  # Don't report ignored threats
            
            engagement = EngagementStatus(
                track_id=threat.track_id,
                engagement_state=state,
                time_to_threat_s=self._estimate_time_to_threat(threat),
                kill_probability=0.7 if state == EngagementState.ENGAGING.value else None
            )
            
            engagements.append(engagement)
        
        return engagements
    
    def _estimate_time_to_threat(self, threat) -> Optional[float]:
        """Estimate time until threat reaches critical range."""
        # Simplified calculation
        # Would use actual kinematics in production
        return 30.0  # 30 seconds placeholder
    
    def publish_feedback(self, 
                        threat_assessments: List,
                        tracks: List = None) -> bool:
        """
        Publish EW feedback message.
        
        Args:
            threat_assessments: Current threat assessments
            tracks: Optional track list
            
        Returns:
            True if published successfully
        """
        if not self.enable_export:
            return False
        
        # Generate countermeasures and engagements
        countermeasures = self.generate_countermeasures(threat_assessments)
        engagements = self.generate_engagement_status(threat_assessments)
        
        # Create message
        message = EWFeedbackMessage.create(
            effector_id=self.effector_id,
            countermeasures=countermeasures,
            engagements=engagements
        )
        
        # Export to file
        try:
            filename = f"ew_feedback_{int(time.time()*1000):016d}.json"
            filepath = self.export_dir / filename
            
            with open(filepath, 'w') as f:
                f.write(message.to_json(indent=2))
            
            self.messages_published += 1
            self.active_cms = countermeasures
            self.active_engagements = engagements
            
            logger.info(f"[EW-FEEDBACK-TX] Published: {len(countermeasures)} CMs, "
                       f"{len(engagements)} engagements")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish EW feedback: {e}")
            return False
    
    def publish_attack_packet(self,
                              threat_assessments: List,
                              adaptation_command,
                              tracks: List = None) -> bool:
        """
        Publish Electronic Attack Packet to event bus.
        
        Includes:
        - Action type (countermeasure type)
        - Jam power (power_level_dbm)
        - Expected effect (effectiveness_score, expected_impact)
        - Confidence (decision_confidence, overall_effectiveness)
        - Decision rationale (effector_metadata)
        
        Args:
            threat_assessments: List of ThreatAssessment objects
            adaptation_command: AdaptationCommand from cognitive engine
            tracks: Optional list of tracks
            
        Returns:
            True if published successfully
        """
        from defense_core import ElectronicAttackPacket
        
        # Generate countermeasures from threats and adaptation
        countermeasures = self._generate_countermeasures_with_adaptation(
            threat_assessments, adaptation_command
        )
        
        # Generate engagements
        engagements = self.generate_engagement_status(threat_assessments)
        
        # Calculate overall effectiveness from adaptation command
        overall_effectiveness = self._calculate_effectiveness(adaptation_command)
        
        # Calculate expected impact on sensor
        expected_impact = self._calculate_expected_impact(adaptation_command)
        
        # Convert to defense_core types for event bus
        from defense_core import Countermeasure as DCCountermeasure, EngagementStatus as DCEngagementStatus
        
        dc_countermeasures = []
        for cm in countermeasures:
            dc_cm = DCCountermeasure(
                countermeasure_id=cm.countermeasure_id,
                target_track_id=cm.target_track_id,
                cm_type=cm.cm_type,
                start_time=cm.start_time,
                power_level_dbm=cm.power_level_dbm,
                frequency_mhz=cm.frequency_mhz,
                bandwidth_mhz=cm.bandwidth_mhz,
                effectiveness_score=cm.effectiveness_score,
                confidence=adaptation_command.decision_confidence,
                predicted_snr_reduction_db=adaptation_command.predicted_snr_improvement_db
            )
            dc_countermeasures.append(dc_cm)
        
        dc_engagements = []
        for eng in engagements:
            dc_eng = DCEngagementStatus(
                track_id=eng.track_id,
                engagement_state=eng.engagement_state,
                time_to_threat_s=eng.time_to_threat_s,
                kill_probability=eng.kill_probability
            )
            dc_engagements.append(dc_eng)
        
        # Create packet
        packet = ElectronicAttackPacket.create(
            effector_id=self.effector_id,
            countermeasures=dc_countermeasures,
            engagements=dc_engagements,
            overall_effectiveness=overall_effectiveness,
            decision_confidence=adaptation_command.decision_confidence
        )
        
        # Add expected impact
        packet.expected_impact = expected_impact
        
        # Add decision rationale to metadata
        packet.effector_metadata = {
            'decision_rationale': adaptation_command.reasoning,
            'adaptation_command': {
                'bandwidth_scaling': adaptation_command.bandwidth_scaling,
                'tx_power_scaling': adaptation_command.tx_power_scaling,
                'cfar_alpha_scale': adaptation_command.cfar_alpha_scale,
                'prf_scale': adaptation_command.prf_scale,
                'dwell_time_scale': adaptation_command.dwell_time_scale,
                'predicted_snr_improvement_db': adaptation_command.predicted_snr_improvement_db,
                'predicted_pfa_change': adaptation_command.predicted_pfa_change,
                'predicted_range_resolution_m': adaptation_command.predicted_range_resolution_m
            }
        }
        
        success = False
        
        # Publish to event bus
        if self.enable_event_bus and self.defense_bus:
            success = self.defense_bus.publish_feedback(packet, timeout=0.01)
            
            if success:
                self.packets_sent += 1
                if self.log_all_transmissions:
                    logger.info(
                        f"[EW-ATTACK-TX] Frame {adaptation_command.frame_id}: "
                        f"{len(countermeasures)} CMs, "
                        f"{len(engagements)} engagements, "
                        f"effectiveness={overall_effectiveness:.2f}, "
                        f"confidence={adaptation_command.decision_confidence:.2f}, "
                        f"impact={expected_impact:.2f}"
                    )
            else:
                self.packets_dropped += 1
                logger.warning(
                    f"[EW-ATTACK-DROPPED] Frame {adaptation_command.frame_id}: "
                    f"Event bus full"
                )
        
        # Legacy file export
        if self.enable_export:
            self._export_attack_packet_to_file(packet)
            success = True  # File export succeeded
        
        # Update active state
        self.active_cms = countermeasures
        self.active_engagements = engagements
        
        return success
    
    def _generate_countermeasures_with_adaptation(self,
                                                   threat_assessments: List,
                                                   adaptation_command) -> List[Countermeasure]:
        """
        Generate countermeasures incorporating cognitive adaptation decisions.
        
        Maps adaptation command to countermeasure parameters.
        """
        countermeasures = []
        
        for threat in threat_assessments:
            # Only engage hostile threats
            if threat.threat_class != "HOSTILE":
                continue
            
            # Determine CM type from adaptation
            cm_type = self._map_adaptation_to_cm_type(adaptation_command)
            
            # Calculate jam power from adaptation
            jam_power_dbm = self._calculate_jam_power(
                adaptation_command,
                threat.threat_priority
            )
            
            # Calculate effectiveness
            effectiveness = self._calculate_cm_effectiveness(
                adaptation_command,
                threat.classification_confidence
            )
            
            cm = Countermeasure(
                countermeasure_id=self.cm_counter,
                target_track_id=threat.track_id,
                cm_type=cm_type,
                start_time=time.time(),
                power_level_dbm=jam_power_dbm,
                frequency_mhz=77000.0,  # Match radar frequency
                bandwidth_mhz=150.0 * adaptation_command.bandwidth_scaling,
                effectiveness_score=effectiveness,
            )
            
            countermeasures.append(cm)
            self.cm_counter += 1
        
        return countermeasures
    
    def _map_adaptation_to_cm_type(self, adaptation_command) -> str:
        """
        Map cognitive adaptation to countermeasure type.
        
        Action type selection based on adaptation strategy.
        """
        # If significantly increasing power → noise jamming
        if adaptation_command.tx_power_scaling > 1.2:
            return CountermeasureType.NOISE_JAM.value
        
        # If changing bandwidth → deception jamming
        elif adaptation_command.bandwidth_scaling > 1.1:
            return CountermeasureType.DECEPTION_JAM.value
        
        # If adjusting CFAR → deception jamming
        elif adaptation_command.cfar_alpha_scale < 0.95:
            return CountermeasureType.DECEPTION_JAM.value
        
        # Default: noise jamming
        else:
            return CountermeasureType.NOISE_JAM.value
    
    def _calculate_jam_power(self,
                            adaptation_command,
                            threat_priority: int) -> float:
        """
        Calculate jammer power from adaptation command.
        
        Jam power incorporates TX power scaling and threat priority.
        """
        # Base power
        base_power_dbm = 30.0  # 1 Watt
        
        # Scale based on TX power adaptation
        power_boost_db = 10 * np.log10(max(0.1, adaptation_command.tx_power_scaling))
        
        # Add predicted SNR improvement
        power_boost_db += adaptation_command.predicted_snr_improvement_db
        
        # Add threat priority boost
        priority_boost_db = (threat_priority / 10.0) * 5.0  # Up to +5dB
        
        total_power = base_power_dbm + power_boost_db + priority_boost_db
        
        # Clamp to realistic range
        return min(50.0, max(20.0, total_power))
    
    def _calculate_cm_effectiveness(self,
                                   adaptation_command,
                                   threat_confidence: float) -> float:
        """
        Calculate countermeasure effectiveness score.
        """
        # Base effectiveness from adaptation impact
        base_effectiveness = 0.5
        
        # Boost from power scaling
        power_factor = (adaptation_command.tx_power_scaling - 1.0) * 0.3
        
        # Boost from bandwidth scaling
        bandwidth_factor = (adaptation_command.bandwidth_scaling - 1.0) * 0.2
        
        # Reduce if threat has high confidence (harder to jam)
        confidence_penalty = threat_confidence * 0.1
        
        effectiveness = base_effectiveness + power_factor + bandwidth_factor - confidence_penalty
        
        return min(0.9, max(0.1, effectiveness))
    
    def _calculate_effectiveness(self, adaptation_command) -> float:
        """
        Calculate overall effectiveness from adaptation.
        
        Expected effect on sensor performance.
        """
        # Effectiveness based on predicted impact
        snr_impact = min(1.0, abs(adaptation_command.predicted_snr_improvement_db) / 10.0)
        pfa_impact = abs(adaptation_command.predicted_pfa_change)
        
        # Weighted combination
        effectiveness = 0.6 * snr_impact + 0.4 * pfa_impact
        
        return min(0.95, max(0.1, effectiveness))
    
    def _calculate_expected_impact(self, adaptation_command) -> float:
        """
        Calculate expected impact on sensor.
        
        How much we expect to degrade sensor performance.
        """
        # Impact from power changes
        power_impact = abs(adaptation_command.tx_power_scaling - 1.0) * 0.5
        
        # Impact from bandwidth changes
        bandwidth_impact = abs(adaptation_command.bandwidth_scaling - 1.0) * 0.3
        
        # Impact from CFAR changes
        cfar_impact = abs(1.0 - adaptation_command.cfar_alpha_scale) * 0.2
        
        total_impact = power_impact + bandwidth_impact + cfar_impact
        
        return min(0.9, max(0.0, total_impact))
    
    def _export_attack_packet_to_file(self, packet):
        """
        Export attack packet to file (legacy mode).
        """
        try:
            filename = f"ew_attack_{int(time.time()*1000):016d}.json"
            filepath = self.export_dir / filename
            
            with open(filepath, 'w') as f:
                f.write(packet.to_json(indent=2))
            
            self.messages_published += 1
            
        except Exception as e:
            logger.error(f"Failed to export attack packet to file: {e}")
    
    def get_statistics(self):
        """Get publisher statistics."""
        return {
            'messages_published': self.messages_published,
            'packets_sent': self.packets_sent,
            'packets_dropped': self.packets_dropped,
            'active_countermeasures': len(self.active_cms),
            'active_engagements': len(self.active_engagements),
            'drop_rate': self.packets_dropped / max(1, self.packets_sent) if self.packets_sent > 0 else 0.0
        }


class NullEWFeedbackPublisher:
    """Null publisher when feedback is disabled."""
    
    def publish_feedback(self, *args, **kwargs):
        return False
    
    def get_statistics(self):
        return {'enabled': False}
