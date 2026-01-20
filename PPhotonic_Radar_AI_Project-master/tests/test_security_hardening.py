"""
Test Suite: Security Hardening (RBAC, Tamper Detection, Deployment)

Tests for:
- Role-Based Access Control (RBAC)
- Tamper Detection and Integrity Verification
- Edge-Node and Command-Node Deployment
"""

import pytest
import tempfile
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

from src.security_core import (
    Role, Permission, AccessContext, RBACSystem, SecurityContextManager,
    SecurityEvent, get_rbac_system, get_security_context_manager
)
from src.tamper_detection import (
    ChecksumManager, TamperDetector, FileChecksum, TamperSeverity,
    get_tamper_detector
)
from src.deployment import (
    NodeConfig, NodeType, NodeStatus, NodeInfo, Message, EdgeNode, CommandNode,
    DeploymentOrchestrator, get_deployment_orchestrator
)


# ============================================================================
# RBAC TESTS
# ============================================================================

class TestRBACSystem:
    """Test Role-Based Access Control system."""
    
    def test_rbac_initialization(self):
        """Test RBAC system initializes with proper permissions."""
        rbac = RBACSystem()
        
        # Admin should have all permissions
        admin_perms = rbac.get_role_permissions(Role.ADMIN)
        assert Permission.MODIFY_SECURITY_CONFIG.value in admin_perms
        assert Permission.SHUTDOWN_SYSTEM.value in admin_perms
        
        # Guest should have minimal permissions
        guest_perms = rbac.get_role_permissions(Role.GUEST)
        assert Permission.RUN_INFERENCE.value in guest_perms
        assert Permission.MODIFY_CONFIG.value not in guest_perms
    
    def test_permission_check_allowed(self):
        """Test permission check when permission is granted."""
        rbac = RBACSystem()
        context = AccessContext(
            user_id="user1",
            role=Role.OPERATOR,
            username="operator1",
            session_id="sess1"
        )
        
        # Operator should have RUN_INFERENCE permission
        allowed, reason = rbac.check_permission(context, Permission.RUN_INFERENCE)
        assert allowed is True
        assert "has" in reason.lower()
    
    def test_permission_check_denied(self):
        """Test permission check when permission is denied (fail-safe)."""
        rbac = RBACSystem()
        context = AccessContext(
            user_id="user2",
            role=Role.GUEST,
            username="guest1",
            session_id="sess2"
        )
        
        # Guest should NOT have MODIFY_CONFIG permission
        allowed, reason = rbac.check_permission(context, Permission.MODIFY_CONFIG)
        assert allowed is False
        assert "lacks" in reason.lower()
    
    def test_require_permission_allowed(self):
        """Test require_permission raises no exception when allowed."""
        rbac = RBACSystem()
        context = AccessContext(
            user_id="user3",
            role=Role.COMMANDER,
            username="commander1",
            session_id="sess3"
        )
        
        # Should not raise (commander can run inference)
        rbac.require_permission(context, Permission.RUN_INFERENCE)
    
    def test_require_permission_denied(self):
        """Test require_permission raises exception when denied (fail-safe)."""
        rbac = RBACSystem()
        context = AccessContext(
            user_id="user4",
            role=Role.OPERATOR,
            username="operator2",
            session_id="sess4"
        )
        
        # Should raise (operator cannot modify config)
        with pytest.raises(PermissionError):
            rbac.require_permission(context, Permission.MODIFY_CONFIG)
    
    def test_grant_revoke_permission(self):
        """Test granting and revoking permissions."""
        rbac = RBACSystem()
        
        # Initially, GUEST cannot load models
        assert Permission.LOAD_MODEL.value not in rbac.get_role_permissions(Role.GUEST)
        
        # Grant permission
        rbac.grant_permission(Role.GUEST, Permission.LOAD_MODEL)
        assert Permission.LOAD_MODEL.value in rbac.get_role_permissions(Role.GUEST)
        
        # Revoke permission
        rbac.revoke_permission(Role.GUEST, Permission.LOAD_MODEL)
        assert Permission.LOAD_MODEL.value not in rbac.get_role_permissions(Role.GUEST)
    
    def test_audit_log_creation(self):
        """Test that permission checks are logged to audit trail."""
        rbac = RBACSystem()
        context = AccessContext(
            user_id="user5",
            role=Role.ANALYST,
            username="analyst1",
            session_id="sess5"
        )
        
        # Clear audit log
        rbac.audit_log.clear()
        
        # Make permission checks
        rbac.check_permission(context, Permission.VIEW_ANALYTICS, "test_resource")
        
        # Verify audit log entry
        assert len(rbac.audit_log) > 0
        event = rbac.audit_log[0]
        assert event.username == "analyst1"
        assert "view_analytics" in event.action.lower()
    
    def test_audit_log_filtering(self):
        """Test filtering audit log."""
        rbac = RBACSystem()
        rbac.audit_log.clear()
        
        ctx_admin = AccessContext("u1", Role.ADMIN, "admin1", "s1")
        ctx_op = AccessContext("u2", Role.OPERATOR, "op1", "s2")
        
        rbac.check_permission(ctx_admin, Permission.SHUTDOWN_SYSTEM)
        rbac.check_permission(ctx_op, Permission.RUN_INFERENCE)
        rbac.check_permission(ctx_op, Permission.MODIFY_CONFIG)  # Will be denied
        
        # Filter by user
        admin_events = rbac.get_audit_log(user_id="u1")
        assert len(admin_events) > 0
        
        # Filter by result
        denied_events = rbac.get_audit_log(result="DENIED")
        assert any("DENIED" == e.result for e in denied_events)


class TestSecurityContextManager:
    """Test security context management."""
    
    def test_create_context(self):
        """Test creating security context."""
        mgr = SecurityContextManager()
        
        ctx = mgr.create_context(
            user_id="user1",
            username="testuser",
            role=Role.OPERATOR,
            session_id="sess1",
            ip_address="192.168.1.100"
        )
        
        assert ctx.username == "testuser"
        assert ctx.role == Role.OPERATOR
        assert ctx.ip_address == "192.168.1.100"
    
    def test_get_context(self):
        """Test retrieving active context."""
        mgr = SecurityContextManager()
        
        ctx_orig = mgr.create_context(
            user_id="u1",
            username="user1",
            role=Role.COMMANDER,
            session_id="s1"
        )
        
        ctx_retrieved = mgr.get_context("s1")
        assert ctx_retrieved.username == "user1"
        assert ctx_retrieved.session_id == "s1"
    
    def test_destroy_context(self):
        """Test destroying security context (logout)."""
        mgr = SecurityContextManager()
        
        mgr.create_context("u1", "user1", Role.OPERATOR, "s1")
        assert mgr.get_context("s1") is not None
        
        mgr.destroy_context("s1")
        assert mgr.get_context("s1") is None
    
    def test_list_active_sessions(self):
        """Test listing all active sessions."""
        mgr = SecurityContextManager()
        
        mgr.create_context("u1", "user1", Role.OPERATOR, "s1")
        mgr.create_context("u2", "user2", Role.COMMANDER, "s2")
        
        sessions = mgr.list_active_sessions()
        assert len(sessions) == 2
        usernames = {s.username for s in sessions}
        assert "user1" in usernames
        assert "user2" in usernames


# ============================================================================
# TAMPER DETECTION TESTS
# ============================================================================

class TestChecksumManager:
    """Test checksum computation and verification."""
    
    def test_compute_sha256(self):
        """Test SHA256 checksum computation."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            f.flush()
            
            try:
                sha256 = ChecksumManager.compute_sha256(f.name)
                assert isinstance(sha256, str)
                assert len(sha256) == 64  # SHA256 hex is 64 chars
            finally:
                os.unlink(f.name)
    
    def test_compute_md5(self):
        """Test MD5 checksum computation."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            f.flush()
            
            try:
                md5 = ChecksumManager.compute_md5(f.name)
                assert isinstance(md5, str)
                assert len(md5) == 32  # MD5 hex is 32 chars
            finally:
                os.unlink(f.name)
    
    def test_compute_checksums(self):
        """Test computing both SHA256 and MD5."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            content = b"radar system model weights"
            f.write(content)
            f.flush()
            
            try:
                cs = ChecksumManager.compute_checksums(f.name)
                assert isinstance(cs, FileChecksum)
                assert len(cs.sha256) == 64
                assert len(cs.md5) == 32
                assert cs.filesize == len(content)
            finally:
                os.unlink(f.name)
    
    def test_verify_checksum_success(self):
        """Test successful checksum verification."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"original content")
            f.flush()
            
            try:
                expected = ChecksumManager.compute_sha256(f.name)
                is_valid, msg = ChecksumManager.verify_checksum(f.name, expected)
                assert is_valid is True
                assert "verified" in msg.lower()
            finally:
                os.unlink(f.name)
    
    def test_verify_checksum_failure(self):
        """Test checksum verification failure (fail-safe)."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"original content")
            f.flush()
            
            try:
                wrong_checksum = "00" * 32  # Invalid checksum
                is_valid, msg = ChecksumManager.verify_checksum(f.name, wrong_checksum)
                assert is_valid is False
                assert "mismatch" in msg.lower()
            finally:
                os.unlink(f.name)


class TestTamperDetector:
    """Test tampering detection."""
    
    def test_add_critical_file(self):
        """Test marking file as critical."""
        detector = TamperDetector()
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"critical file")
            f.flush()
            
            try:
                detector.add_critical_file(f.name)
                assert f.name in detector.critical_files
            finally:
                os.unlink(f.name)
    
    def test_establish_baseline(self):
        """Test establishing baseline for a file."""
        detector = TamperDetector()
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"baseline content")
            f.flush()
            
            try:
                cs = detector.establish_baseline(f.name)
                assert isinstance(cs, FileChecksum)
                assert f.name in detector.baseline
            finally:
                os.unlink(f.name)
    
    def test_verify_integrity_unmodified(self):
        """Test integrity check on unmodified file."""
        detector = TamperDetector()
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"stable content")
            f.flush()
            
            try:
                detector.establish_baseline(f.name)
                is_valid, msg = detector.verify_integrity(f.name)
                assert is_valid is True
            finally:
                os.unlink(f.name)
    
    def test_verify_integrity_modified(self):
        """Test tampering detection on modified file (fail-safe)."""
        detector = TamperDetector()
        
        with tempfile.NamedTemporaryFile(delete=False, mode='w+b') as f:
            f.write(b"original content")
            f.flush()
            filepath = f.name
        
        try:
            # Establish baseline
            detector.establish_baseline(filepath)
            
            # Modify file
            with open(filepath, 'w+b') as f:
                f.write(b"tampered content")
            
            # Verify should detect tampering
            is_valid, msg = detector.verify_integrity(filepath)
            assert is_valid is False
            assert "mismatch" in msg.lower()
            
            # Check tampering was logged
            assert len(detector.get_unresolved_events()) > 0
        finally:
            os.unlink(filepath)
    
    def test_verify_integrity_missing_file(self):
        """Test tampering detection on missing file (fail-safe)."""
        detector = TamperDetector()
        
        # Establish baseline for a file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"content")
            f.flush()
            filepath = f.name
        
        detector.establish_baseline(filepath)
        os.unlink(filepath)
        
        # Verify should fail-safe on missing file
        is_valid, msg = detector.verify_integrity(filepath)
        assert is_valid is False
        assert "not found" in msg.lower()
    
    def test_get_tamper_statistics(self):
        """Test tampering statistics."""
        detector = TamperDetector()
        
        with tempfile.NamedTemporaryFile(delete=False, mode='w+b') as f:
            f.write(b"content")
            filepath = f.name
        
        try:
            detector.establish_baseline(filepath)
            
            # Tamper file to create events
            with open(filepath, 'w+b') as f:
                f.write(b"modified")
            
            detector.verify_integrity(filepath)
            
            stats = detector.get_statistics()
            assert stats["total_events"] > 0
            assert stats["critical_files_monitored"] == 0  # Not added as critical
        finally:
            os.unlink(filepath)


# ============================================================================
# DEPLOYMENT TESTS
# ============================================================================

class TestNodeConfig:
    """Test deployment node configuration."""
    
    def test_valid_config(self):
        """Test valid configuration."""
        config = NodeConfig(
            node_id="edge1",
            node_type=NodeType.EDGE,
            hostname="192.168.1.100",
            port=5000,
            secure=False,
        )
        
        is_valid, msg = config.validate()
        assert is_valid is True
    
    def test_invalid_port(self):
        """Test invalid port validation."""
        config = NodeConfig(
            node_id="edge1",
            node_type=NodeType.EDGE,
            hostname="localhost",
            port=99999,  # Invalid
            secure=False,
        )
        
        is_valid, msg = config.validate()
        assert is_valid is False
    
    def test_secure_without_cert(self):
        """Test secure mode requires certificate."""
        config = NodeConfig(
            node_id="edge1",
            node_type=NodeType.EDGE,
            hostname="localhost",
            port=5000,
            secure=True,
            tls_cert_path=None,  # Missing
        )
        
        is_valid, msg = config.validate()
        assert is_valid is False


class TestEdgeNode:
    """Test edge node operations."""
    
    def test_edge_node_creation(self):
        """Test edge node creation."""
        config = NodeConfig(
            node_id="edge1",
            node_type=NodeType.EDGE,
            hostname="localhost",
            port=5000,
            secure=False,
        )
        
        edge = EdgeNode(config)
        assert edge.node_id == "edge1"
        assert edge.status == NodeStatus.ONLINE
    
    def test_edge_node_startup(self):
        """Test edge node startup."""
        config = NodeConfig(
            node_id="edge1",
            node_type=NodeType.EDGE,
            hostname="localhost",
            port=5000,
            secure=False,
        )
        
        edge = EdgeNode(config)
        edge.start()
        
        assert edge.is_running is True
        assert edge.status == NodeStatus.ONLINE
    
    def test_edge_node_inference(self):
        """Test edge node inference."""
        config = NodeConfig(
            node_id="edge1",
            node_type=NodeType.EDGE,
            hostname="localhost",
            port=5000,
            secure=False,
        )
        
        edge = EdgeNode(config)
        edge.start()
        
        result = edge.run_inference(b"signal data")
        assert result["inferences_run"] == 1
    
    def test_edge_node_local_state(self):
        """Test edge node local state."""
        config = NodeConfig(
            node_id="edge1",
            node_type=NodeType.EDGE,
            hostname="localhost",
            port=5000,
            secure=False,
        )
        
        edge = EdgeNode(config)
        edge.start()
        
        state = edge.get_local_state()
        assert state["node_id"] == "edge1"
        assert state["status"] == "online"
        assert state["inferences_run"] >= 0


class TestCommandNode:
    """Test command node operations."""
    
    def test_command_node_creation(self):
        """Test command node creation."""
        config = NodeConfig(
            node_id="cmd1",
            node_type=NodeType.COMMAND,
            hostname="192.168.1.1",
            port=6000,
            secure=False,
        )
        
        cmd = CommandNode(config)
        assert cmd.node_id == "cmd1"
        assert cmd.status == NodeStatus.ONLINE
    
    def test_command_node_startup(self):
        """Test command node startup."""
        config = NodeConfig(
            node_id="cmd1",
            node_type=NodeType.COMMAND,
            hostname="192.168.1.1",
            port=6000,
            secure=False,
        )
        
        cmd = CommandNode(config)
        cmd.start()
        
        assert cmd.is_running is True
    
    def test_register_edge_node(self):
        """Test registering edge node with command node."""
        config = NodeConfig(
            node_id="cmd1",
            node_type=NodeType.COMMAND,
            hostname="localhost",
            port=6000,
            secure=False,
        )
        
        cmd = CommandNode(config)
        cmd.start()
        
        # Register edge node
        edge_info = NodeInfo(
            node_id="edge1",
            node_type=NodeType.EDGE,
            status=NodeStatus.ONLINE,
            hostname="localhost",
            port=5000,
            last_heartbeat=datetime.utcnow(),
        )
        
        cmd.register_edge_node(edge_info)
        assert "edge1" in cmd.connected_edges


class TestMessage:
    """Test inter-node message communication."""
    
    def test_message_creation(self):
        """Test creating a message."""
        msg = Message(
            sender_id="edge1",
            recipient_id="cmd1",
            message_type="heartbeat",
            payload={"status": "online"},
        )
        
        assert msg.sender_id == "edge1"
        assert msg.recipient_id == "cmd1"
        assert msg.message_type == "heartbeat"
    
    def test_message_signature(self):
        """Test message signing."""
        msg = Message(
            sender_id="edge1",
            recipient_id="cmd1",
            message_type="heartbeat",
            payload={"status": "online"},
            message_id="msg1",
        )
        
        secret = "shared_secret"
        sig = msg.compute_signature(secret)
        assert isinstance(sig, str)
        assert len(sig) > 0
    
    def test_message_serialization(self):
        """Test message serialization."""
        msg = Message(
            sender_id="edge1",
            recipient_id="cmd1",
            message_type="heartbeat",
            payload={"status": "online"},
        )
        msg.signature = "test_sig"
        
        json_str = msg.to_json()
        assert isinstance(json_str, str)
        
        # Deserialize
        msg2 = Message.from_json(json_str)
        assert msg2.sender_id == "edge1"
        assert msg2.recipient_id == "cmd1"


class TestDeploymentOrchestrator:
    """Test deployment orchestration."""
    
    def test_register_edge_node(self):
        """Test registering edge node with orchestrator."""
        orch = DeploymentOrchestrator()
        
        config = NodeConfig(
            node_id="edge1",
            node_type=NodeType.EDGE,
            hostname="localhost",
            port=5000,
            secure=False,
        )
        
        edge = orch.register_edge_node(config)
        assert "edge1" in orch.edge_nodes
    
    def test_register_command_node(self):
        """Test registering command node with orchestrator."""
        orch = DeploymentOrchestrator()
        
        config = NodeConfig(
            node_id="cmd1",
            node_type=NodeType.COMMAND,
            hostname="localhost",
            port=6000,
            secure=False,
        )
        
        cmd = orch.register_command_node(config)
        assert "cmd1" in orch.command_nodes
    
    def test_start_all_nodes(self):
        """Test starting all nodes."""
        orch = DeploymentOrchestrator()
        
        edge_config = NodeConfig(
            node_id="edge1",
            node_type=NodeType.EDGE,
            hostname="localhost",
            port=5000,
            secure=False,
        )
        cmd_config = NodeConfig(
            node_id="cmd1",
            node_type=NodeType.COMMAND,
            hostname="localhost",
            port=6000,
            secure=False,
        )
        
        orch.register_edge_node(edge_config)
        orch.register_command_node(cmd_config)
        
        orch.start_all_nodes()
        
        assert orch.edge_nodes["edge1"].is_running is True
        assert orch.command_nodes["cmd1"].is_running is True
    
    def test_system_status(self):
        """Test getting system status."""
        orch = DeploymentOrchestrator()
        
        config = NodeConfig(
            node_id="edge1",
            node_type=NodeType.EDGE,
            hostname="localhost",
            port=5000,
            secure=False,
        )
        
        orch.register_edge_node(config)
        orch.start_all_nodes()
        
        status = orch.get_system_status()
        assert "edge_nodes" in status
        assert "command_nodes" in status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
