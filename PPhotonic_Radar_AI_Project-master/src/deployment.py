"""
DEPLOYMENT ARCHITECTURE: Edge-Node + Command-Node System

Distributed military-grade radar with:
- EDGE NODES: Deploy radar processing at the sensor (distributed inference)
- COMMAND NODES: Central command and control (orchestration, decisions)
- SECURE COMMUNICATION: Encrypted, authenticated inter-node communication
- FAIL-SAFE: Loss of command node doesn't compromise edge operations

Design Principles:
1. Edge nodes are independent and can operate autonomously
2. Command nodes orchestrate and aggregate
3. All communication is encrypted and authenticated
4. System fails secure (defaults to deny/shutdown)
5. No single point of failure
"""

import logging
import json
import ssl
import socket
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
import hashlib
import hmac

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Deployment node types."""
    EDGE = "edge"              # Sensor-level radar processing
    COMMAND = "command"        # Central command and control
    RELAY = "relay"            # Secure relay/gateway


class NodeStatus(Enum):
    """Node operational status."""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    COMPROMISED = "compromised"
    SHUTDOWN = "shutdown"


@dataclass
class NodeConfig:
    """Configuration for a deployment node."""
    node_id: str
    node_type: NodeType
    hostname: str
    port: int
    secure: bool = True
    tls_cert_path: Optional[str] = None
    tls_key_path: Optional[str] = None
    shared_secret: Optional[str] = None
    max_reconnect_attempts: int = 3
    reconnect_delay_s: int = 5
    heartbeat_interval_s: int = 30
    timeout_s: int = 60
    
    def validate(self) -> Tuple[bool, str]:
        """Validate configuration."""
        if not self.node_id or not self.hostname or not self.port:
            return False, "Missing required fields: node_id, hostname, port"
        
        if self.secure and not self.tls_cert_path:
            return False, "TLS enabled but no certificate path provided"
        
        if self.port < 1024 or self.port > 65535:
            return False, f"Invalid port: {self.port}"
        
        return True, "Configuration valid"


@dataclass
class NodeInfo:
    """Information about a connected node."""
    node_id: str
    node_type: NodeType
    status: NodeStatus
    hostname: str
    port: int
    last_heartbeat: datetime
    last_update: datetime = field(default_factory=datetime.utcnow)
    capabilities: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0"
    
    def is_healthy(self, timeout_s: int = 120) -> bool:
        """Check if node is healthy (recent heartbeat)."""
        elapsed = (datetime.utcnow() - self.last_heartbeat).total_seconds()
        return elapsed < timeout_s and self.status != NodeStatus.OFFLINE


@dataclass
class Message:
    """Inter-node communication message."""
    sender_id: str
    recipient_id: str
    message_type: str  # "command", "response", "heartbeat", "alert", "status"
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message_id: str = ""
    signature: str = ""
    
    def compute_signature(self, shared_secret: str) -> str:
        """Compute HMAC signature for message integrity."""
        msg_str = json.dumps({
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "message_type": self.message_type,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id,
        }, sort_keys=True)
        
        signature = hmac.new(
            shared_secret.encode(),
            msg_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_signature(self, shared_secret: str) -> bool:
        """Verify message signature."""
        expected_sig = self.compute_signature(shared_secret)
        return hmac.compare_digest(expected_sig, self.signature)
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps({
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "message_type": self.message_type,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id,
            "signature": self.signature,
        })
    
    @staticmethod
    def from_json(data: str) -> "Message":
        """Deserialize from JSON."""
        d = json.loads(data)
        msg = Message(
            sender_id=d["sender_id"],
            recipient_id=d["recipient_id"],
            message_type=d["message_type"],
            payload=d["payload"],
            timestamp=datetime.fromisoformat(d["timestamp"]),
            message_id=d["message_id"],
            signature=d["signature"],
        )
        return msg


class EdgeNode:
    """
    Edge Node: Radar processing at the sensor
    
    Responsibilities:
    - Run inference on raw signals
    - Detect targets
    - Track locally
    - Send alerts and status to command node
    - Operate autonomously if command node unavailable
    """
    
    def __init__(self, config: NodeConfig):
        """Initialize edge node."""
        is_valid, msg = config.validate()
        if not is_valid:
            raise ValueError(f"Invalid configuration: {msg}")
        
        self.config = config
        self.node_id = config.node_id
        self.status = NodeStatus.ONLINE
        self.is_running = False
        self.connected_to_command = False
        self.lock = threading.Lock()
        
        # Local state (survives command node loss)
        self.local_detections = []
        self.local_tracks = []
        self.local_alerts = []
        self.max_local_buffer = 1000
        
        # Statistics
        self.inferences_run = 0
        self.detections_logged = 0
        self.heartbeats_sent = 0
        self.startup_time = datetime.utcnow()
        
        logger.info(f"EdgeNode {config.node_id} initialized")
    
    def start(self) -> None:
        """Start edge node operations."""
        if self.is_running:
            logger.warning(f"EdgeNode {self.node_id} already running")
            return
        
        self.is_running = True
        self.status = NodeStatus.ONLINE
        logger.info(f"EdgeNode {self.node_id} started")
    
    def stop(self) -> None:
        """Stop edge node operations."""
        self.is_running = False
        self.status = NodeStatus.SHUTDOWN
        logger.info(f"EdgeNode {self.node_id} stopped")
    
    def run_inference(self, signal_data: bytes) -> Dict[str, Any]:
        """Run local inference on signal data."""
        if not self.is_running:
            raise RuntimeError(f"EdgeNode {self.node_id} not running")
        
        with self.lock:
            self.inferences_run += 1
        
        # Placeholder: real implementation would run ML model
        result = {
            "inferences_run": self.inferences_run,
            "timestamp": datetime.utcnow().isoformat(),
            "detections": [],
        }
        
        logger.debug(f"EdgeNode {self.node_id} inference #{self.inferences_run} complete")
        return result
    
    def log_detection(self, detection: Dict[str, Any]) -> None:
        """Log local detection."""
        with self.lock:
            self.local_detections.append({
                "detection": detection,
                "timestamp": datetime.utcnow().isoformat(),
            })
            self.detections_logged += 1
            
            # Trim buffer
            if len(self.local_detections) > self.max_local_buffer:
                self.local_detections = self.local_detections[-self.max_local_buffer:]
    
    def get_local_state(self) -> Dict[str, Any]:
        """Get current local state (for status reports)."""
        with self.lock:
            return {
                "node_id": self.node_id,
                "status": self.status.value,
                "uptime_seconds": (datetime.utcnow() - self.startup_time).total_seconds(),
                "inferences_run": self.inferences_run,
                "detections_logged": self.detections_logged,
                "heartbeats_sent": self.heartbeats_sent,
                "connected_to_command": self.connected_to_command,
                "local_detection_count": len(self.local_detections),
            }
    
    def create_heartbeat_message(self, command_node_id: str) -> Message:
        """Create heartbeat message for command node."""
        state = self.get_local_state()
        
        msg = Message(
            sender_id=self.node_id,
            recipient_id=command_node_id,
            message_type="heartbeat",
            payload=state,
        )
        
        with self.lock:
            self.heartbeats_sent += 1
        
        return msg


class CommandNode:
    """
    Command Node: Central command and control
    
    Responsibilities:
    - Receive status from all edge nodes
    - Aggregate detections and tracks
    - Make strategic decisions
    - Send commands to edge nodes
    - Maintain operational picture
    - Fail-safe: alert operators if edge nodes become unreachable
    """
    
    def __init__(self, config: NodeConfig):
        """Initialize command node."""
        is_valid, msg = config.validate()
        if not is_valid:
            raise ValueError(f"Invalid configuration: {msg}")
        
        self.config = config
        self.node_id = config.node_id
        self.status = NodeStatus.ONLINE
        self.is_running = False
        self.lock = threading.Lock()
        
        # Connected nodes
        self.connected_edges: Dict[str, NodeInfo] = {}
        self.last_command_update = datetime.utcnow()
        
        # Aggregated state
        self.aggregated_detections = []
        self.aggregated_tracks = []
        self.critical_alerts = []
        self.max_buffer = 5000
        
        # Statistics
        self.commands_issued = 0
        self.heartbeats_received = 0
        self.startup_time = datetime.utcnow()
        
        logger.info(f"CommandNode {config.node_id} initialized")
    
    def start(self) -> None:
        """Start command node."""
        if self.is_running:
            logger.warning(f"CommandNode {self.node_id} already running")
            return
        
        self.is_running = True
        self.status = NodeStatus.ONLINE
        logger.info(f"CommandNode {self.node_id} started")
    
    def stop(self) -> None:
        """Stop command node."""
        self.is_running = False
        self.status = NodeStatus.SHUTDOWN
        logger.info(f"CommandNode {self.node_id} stopped")
    
    def register_edge_node(self, node_info: NodeInfo) -> None:
        """Register or update edge node."""
        with self.lock:
            self.connected_edges[node_info.node_id] = node_info
        logger.info(f"Edge node registered: {node_info.node_id}")
    
    def process_heartbeat(self, message: Message) -> bool:
        """Process heartbeat from edge node."""
        if not self.is_running:
            return False
        
        edge_id = message.sender_id
        payload = message.payload
        
        with self.lock:
            if edge_id in self.connected_edges:
                self.connected_edges[edge_id].last_heartbeat = datetime.utcnow()
                self.heartbeats_received += 1
            
            # Check for failures (fail-safe: alert if node has many detections)
            if payload.get("status") == "degraded":
                logger.warning(f"Edge node {edge_id} reported degraded status")
            elif payload.get("status") == "compromised":
                logger.critical(f"SECURITY: Edge node {edge_id} reported compromised status")
        
        return True
    
    def issue_command(self, edge_node_id: str, command: str, params: Dict[str, Any]) -> Message:
        """Issue command to edge node."""
        if not self.is_running:
            raise RuntimeError(f"CommandNode {self.node_id} not running")
        
        with self.lock:
            if edge_node_id not in self.connected_edges:
                raise ValueError(f"Edge node {edge_node_id} not connected")
            
            self.commands_issued += 1
        
        msg = Message(
            sender_id=self.node_id,
            recipient_id=edge_node_id,
            message_type="command",
            payload={
                "command": command,
                "parameters": params,
            },
        )
        
        logger.info(f"Command issued to {edge_node_id}: {command}")
        return msg
    
    def aggregate_detection(self, detection: Dict[str, Any], source_node: str) -> None:
        """Aggregate detection from edge node."""
        with self.lock:
            self.aggregated_detections.append({
                "detection": detection,
                "source": source_node,
                "timestamp": datetime.utcnow().isoformat(),
            })
            
            # Trim buffer
            if len(self.aggregated_detections) > self.max_buffer:
                self.aggregated_detections = self.aggregated_detections[-self.max_buffer:]
    
    def get_operational_picture(self) -> Dict[str, Any]:
        """Get current operational picture."""
        with self.lock:
            healthy_edges = sum(
                1 for n in self.connected_edges.values()
                if n.is_healthy()
            )
            
            return {
                "command_node": self.node_id,
                "status": self.status.value,
                "uptime_seconds": (datetime.utcnow() - self.startup_time).total_seconds(),
                "connected_edge_nodes": len(self.connected_edges),
                "healthy_edge_nodes": healthy_edges,
                "commands_issued": self.commands_issued,
                "heartbeats_received": self.heartbeats_received,
                "aggregated_detections": len(self.aggregated_detections),
                "aggregated_tracks": len(self.aggregated_tracks),
                "critical_alerts": len(self.critical_alerts),
            }
    
    def check_edge_node_health(self) -> Dict[str, Tuple[bool, str]]:
        """Check health of all connected edge nodes."""
        health = {}
        
        with self.lock:
            for node_id, node_info in self.connected_edges.items():
                is_healthy = node_info.is_healthy()
                status_msg = f"{node_info.status.value}"
                
                if not is_healthy:
                    logger.warning(f"FAILSAFE ALERT: Edge node {node_id} unhealthy")
                    # Fail-safe: report to operators
                    self.critical_alerts.append({
                        "severity": "critical",
                        "message": f"Edge node {node_id} unhealthy",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                
                health[node_id] = (is_healthy, status_msg)
        
        return health


class DeploymentOrchestrator:
    """
    Orchestrate edge-node and command-node deployments.
    Manages secure communication, authentication, and fail-safety.
    """
    
    def __init__(self):
        """Initialize deployment orchestrator."""
        self.edge_nodes: Dict[str, EdgeNode] = {}
        self.command_nodes: Dict[str, CommandNode] = {}
        self.message_queue: List[Message] = []
        self.lock = threading.Lock()
        logger.info("DeploymentOrchestrator initialized")
    
    def register_edge_node(self, config: NodeConfig) -> EdgeNode:
        """Register and initialize an edge node."""
        is_valid, msg = config.validate()
        if not is_valid:
            raise ValueError(f"Invalid edge node config: {msg}")
        
        edge_node = EdgeNode(config)
        
        with self.lock:
            if config.node_id in self.edge_nodes:
                raise ValueError(f"Edge node {config.node_id} already registered")
            
            self.edge_nodes[config.node_id] = edge_node
        
        logger.info(f"Edge node registered: {config.node_id}")
        return edge_node
    
    def register_command_node(self, config: NodeConfig) -> CommandNode:
        """Register and initialize a command node."""
        is_valid, msg = config.validate()
        if not is_valid:
            raise ValueError(f"Invalid command node config: {msg}")
        
        command_node = CommandNode(config)
        
        with self.lock:
            if config.node_id in self.command_nodes:
                raise ValueError(f"Command node {config.node_id} already registered")
            
            self.command_nodes[config.node_id] = command_node
        
        logger.info(f"Command node registered: {config.node_id}")
        return command_node
    
    def start_all_nodes(self) -> None:
        """Start all registered nodes."""
        with self.lock:
            for edge in self.edge_nodes.values():
                edge.start()
            
            for command in self.command_nodes.values():
                command.start()
        
        logger.info("All nodes started")
    
    def stop_all_nodes(self) -> None:
        """Stop all registered nodes (graceful shutdown)."""
        with self.lock:
            for edge in self.edge_nodes.values():
                edge.stop()
            
            for command in self.command_nodes.values():
                command.stop()
        
        logger.info("All nodes stopped (graceful shutdown)")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of entire deployment system."""
        with self.lock:
            edge_states = {
                node_id: node.get_local_state()
                for node_id, node in self.edge_nodes.items()
            }
            
            command_states = {
                node_id: node.get_operational_picture()
                for node_id, node in self.command_nodes.items()
            }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "edge_nodes": edge_states,
            "command_nodes": command_states,
            "message_queue_size": len(self.message_queue),
        }
    
    def send_message(self, message: Message, shared_secret: str) -> None:
        """Send message through system (with authentication)."""
        # Sign message
        message.signature = message.compute_signature(shared_secret)
        
        with self.lock:
            self.message_queue.append(message)
        
        logger.debug(f"Message queued: {message.message_type} from {message.sender_id} to {message.recipient_id}")


# Global instance
_orchestrator = DeploymentOrchestrator()


def get_deployment_orchestrator() -> DeploymentOrchestrator:
    """Get global deployment orchestrator instance."""
    return _orchestrator
