"""
SECURITY CORE: Role-Based Access Control (RBAC) & Fail-Safe Authorization

Implements military-grade RBAC for defense radar system with fail-safe defaults.
All authorization checks default to DENY unless explicitly granted.

Security Principles:
- Fail-Safe (default DENY)
- Least Privilege
- Defense in Depth
- Audit Trail
"""

import logging
from enum import Enum
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class Role(Enum):
    """Military radar system roles with hierarchical privilege levels."""
    ADMIN = "admin"              # Full system access, security configuration
    COMMANDER = "commander"      # Strategic decisions, mission authority
    OPERATOR = "operator"        # Tactical operations, real-time monitoring
    ENGINEER = "engineer"        # System maintenance, diagnostics
    ANALYST = "analyst"          # Data analysis, read-only access
    GUEST = "guest"              # Minimal access for demonstrations


class Permission(Enum):
    """Granular permissions for all system operations."""
    
    # Model & Inference
    LOAD_MODEL = "load_model"
    UNLOAD_MODEL = "unload_model"
    RUN_INFERENCE = "run_inference"
    TRAIN_MODEL = "train_model"
    
    # Data & Signals
    CAPTURE_SIGNALS = "capture_signals"
    PROCESS_SIGNALS = "process_signals"
    EXPORT_SIGNALS = "export_signals"
    
    # Tracking & Detection
    ENABLE_DETECTION = "enable_detection"
    ENABLE_TRACKING = "enable_tracking"
    MODIFY_TRACKING_PARAMS = "modify_tracking_params"
    
    # Alerts & Incidents
    ACKNOWLEDGE_ALERTS = "acknowledge_alerts"
    DISMISS_ALERTS = "dismiss_alerts"
    CREATE_INCIDENTS = "create_incidents"
    
    # Replay & Analysis
    ACCESS_REPLAY = "access_replay"
    EXPORT_INCIDENTS = "export_incidents"
    VIEW_ANALYTICS = "view_analytics"
    
    # Configuration
    VIEW_CONFIG = "view_config"
    MODIFY_CONFIG = "modify_config"
    MODIFY_SECURITY_CONFIG = "modify_security_config"
    
    # System Management
    VIEW_SYSTEM_HEALTH = "view_system_health"
    RESTART_SYSTEM = "restart_system"
    SHUTDOWN_SYSTEM = "shutdown_system"
    
    # User Management
    VIEW_USERS = "view_users"
    CREATE_USERS = "create_users"
    MODIFY_USERS = "modify_users"
    DELETE_USERS = "delete_users"
    
    # Security & Audit
    VIEW_AUDIT_LOG = "view_audit_log"
    EXPORT_AUDIT_LOG = "export_audit_log"
    CONFIGURE_RBAC = "configure_rbac"
    MANAGE_SECRETS = "manage_secrets"


@dataclass
class AccessContext:
    """Security context for an operation."""
    user_id: str
    role: Role
    username: str
    session_id: str
    ip_address: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    clearance_level: int = 0  # 0=public, 1=unclass, 2=confidential, 3=secret
    
    def __repr__(self) -> str:
        return f"AccessContext(user={self.username}, role={self.role.value}, session={self.session_id[:8]}...)"


@dataclass
class SecurityEvent:
    """Audit trail entry."""
    timestamp: datetime
    user_id: str
    username: str
    action: str
    resource: str
    result: str  # "ALLOWED" or "DENIED"
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action,
            "resource": self.resource,
            "result": self.result,
            "reason": self.reason,
            "ip_address": self.ip_address,
            "session_id": self.session_id,
        }


class RBACSystem:
    """
    Role-Based Access Control (RBAC) with fail-safe defaults.
    
    All authorization checks default to DENY unless explicitly granted.
    """
    
    def __init__(self):
        """Initialize RBAC with default permissions."""
        self.role_permissions: Dict[Role, Set[Permission]] = self._initialize_permissions()
        self.audit_log: List[SecurityEvent] = []
        self.max_audit_entries = 10000
        
    def _initialize_permissions(self) -> Dict[Role, Set[Permission]]:
        """Initialize permission matrix for all roles."""
        permissions = {
            # ADMIN: Full access except some dangerous operations require dual approval
            Role.ADMIN: {
                Permission.LOAD_MODEL,
                Permission.UNLOAD_MODEL,
                Permission.RUN_INFERENCE,
                Permission.TRAIN_MODEL,
                Permission.CAPTURE_SIGNALS,
                Permission.PROCESS_SIGNALS,
                Permission.EXPORT_SIGNALS,
                Permission.ENABLE_DETECTION,
                Permission.ENABLE_TRACKING,
                Permission.MODIFY_TRACKING_PARAMS,
                Permission.ACKNOWLEDGE_ALERTS,
                Permission.DISMISS_ALERTS,
                Permission.CREATE_INCIDENTS,
                Permission.ACCESS_REPLAY,
                Permission.EXPORT_INCIDENTS,
                Permission.VIEW_ANALYTICS,
                Permission.VIEW_CONFIG,
                Permission.MODIFY_CONFIG,
                Permission.MODIFY_SECURITY_CONFIG,
                Permission.VIEW_SYSTEM_HEALTH,
                Permission.RESTART_SYSTEM,
                Permission.SHUTDOWN_SYSTEM,
                Permission.VIEW_USERS,
                Permission.CREATE_USERS,
                Permission.MODIFY_USERS,
                Permission.DELETE_USERS,
                Permission.VIEW_AUDIT_LOG,
                Permission.EXPORT_AUDIT_LOG,
                Permission.CONFIGURE_RBAC,
                Permission.MANAGE_SECRETS,
            },
            
            # COMMANDER: Strategic operations, can modify mission-critical settings
            Role.COMMANDER: {
                Permission.RUN_INFERENCE,
                Permission.PROCESS_SIGNALS,
                Permission.EXPORT_SIGNALS,
                Permission.ENABLE_DETECTION,
                Permission.ENABLE_TRACKING,
                Permission.ACKNOWLEDGE_ALERTS,
                Permission.DISMISS_ALERTS,
                Permission.CREATE_INCIDENTS,
                Permission.ACCESS_REPLAY,
                Permission.EXPORT_INCIDENTS,
                Permission.VIEW_ANALYTICS,
                Permission.VIEW_CONFIG,
                Permission.MODIFY_TRACKING_PARAMS,
                Permission.VIEW_SYSTEM_HEALTH,
                Permission.VIEW_AUDIT_LOG,
            },
            
            # OPERATOR: Real-time operations, cannot modify configuration
            Role.OPERATOR: {
                Permission.RUN_INFERENCE,
                Permission.PROCESS_SIGNALS,
                Permission.ENABLE_DETECTION,
                Permission.ENABLE_TRACKING,
                Permission.ACKNOWLEDGE_ALERTS,
                Permission.DISMISS_ALERTS,
                Permission.CREATE_INCIDENTS,
                Permission.ACCESS_REPLAY,
                Permission.VIEW_ANALYTICS,
                Permission.VIEW_CONFIG,
                Permission.VIEW_SYSTEM_HEALTH,
            },
            
            # ENGINEER: System maintenance and diagnostics
            Role.ENGINEER: {
                Permission.LOAD_MODEL,
                Permission.UNLOAD_MODEL,
                Permission.CAPTURE_SIGNALS,
                Permission.PROCESS_SIGNALS,
                Permission.EXPORT_SIGNALS,
                Permission.VIEW_CONFIG,
                Permission.MODIFY_CONFIG,
                Permission.VIEW_SYSTEM_HEALTH,
                Permission.RESTART_SYSTEM,
                Permission.VIEW_AUDIT_LOG,
                Permission.EXPORT_AUDIT_LOG,
            },
            
            # ANALYST: Data analysis and reporting, read-only
            Role.ANALYST: {
                Permission.RUN_INFERENCE,
                Permission.PROCESS_SIGNALS,
                Permission.EXPORT_SIGNALS,
                Permission.ACCESS_REPLAY,
                Permission.EXPORT_INCIDENTS,
                Permission.VIEW_ANALYTICS,
                Permission.VIEW_CONFIG,
                Permission.VIEW_AUDIT_LOG,
                Permission.EXPORT_AUDIT_LOG,
            },
            
            # GUEST: Minimal access for demos
            Role.GUEST: {
                Permission.RUN_INFERENCE,
                Permission.VIEW_ANALYTICS,
                Permission.ACCESS_REPLAY,
            },
        }
        return permissions
    
    def check_permission(
        self,
        context: AccessContext,
        permission: Permission,
        resource: str = "system"
    ) -> Tuple[bool, str]:
        """
        Check if user has permission. Fails safe (returns False if uncertain).
        
        Args:
            context: User's access context
            permission: Required permission
            resource: Resource being accessed (for audit trail)
            
        Returns:
            (allowed: bool, reason: str)
        """
        # Get permissions for user's role
        allowed_perms = self.role_permissions.get(context.role, set())
        
        # Fail-safe: default to DENY
        has_permission = permission in allowed_perms
        result = "ALLOWED" if has_permission else "DENIED"
        reason = f"Role '{context.role.value}' {'has' if has_permission else 'lacks'} permission '{permission.value}'"
        
        # Log to audit trail
        self._log_security_event(
            user_id=context.user_id,
            username=context.username,
            action=f"CHECK_{permission.value}",
            resource=resource,
            result=result,
            reason=reason,
            ip_address=context.ip_address,
            session_id=context.session_id,
        )
        
        logger.info(
            f"Permission check: user={context.username} role={context.role.value} "
            f"permission={permission.value} result={result}"
        )
        
        return has_permission, reason
    
    def require_permission(
        self,
        context: AccessContext,
        permission: Permission,
        resource: str = "system"
    ) -> None:
        """
        Require permission, raise exception if denied.
        
        Args:
            context: User's access context
            permission: Required permission
            resource: Resource being accessed
            
        Raises:
            PermissionError: If permission denied
        """
        has_permission, reason = self.check_permission(context, permission, resource)
        if not has_permission:
            logger.error(f"Permission denied: {reason}")
            raise PermissionError(f"Access denied: {reason}")
    
    def grant_permission(self, role: Role, permission: Permission) -> None:
        """Grant permission to a role."""
        if role not in self.role_permissions:
            self.role_permissions[role] = set()
        self.role_permissions[role].add(permission)
        logger.warning(f"Permission granted: {role.value} <- {permission.value}")
    
    def revoke_permission(self, role: Role, permission: Permission) -> None:
        """Revoke permission from a role."""
        if role in self.role_permissions:
            self.role_permissions[role].discard(permission)
        logger.warning(f"Permission revoked: {role.value} -> {permission.value}")
    
    def get_role_permissions(self, role: Role) -> Set[str]:
        """Get all permissions for a role."""
        perms = self.role_permissions.get(role, set())
        return {p.value for p in perms}
    
    def _log_security_event(
        self,
        user_id: str,
        username: str,
        action: str,
        resource: str,
        result: str,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Log security event to audit trail."""
        event = SecurityEvent(
            timestamp=datetime.utcnow(),
            user_id=user_id,
            username=username,
            action=action,
            resource=resource,
            result=result,
            reason=reason,
            ip_address=ip_address,
            session_id=session_id,
        )
        
        self.audit_log.append(event)
        
        # Trim audit log if too large (keep most recent entries)
        if len(self.audit_log) > self.max_audit_entries:
            self.audit_log = self.audit_log[-self.max_audit_entries:]
    
    def get_audit_log(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        result: Optional[str] = None,
        limit: int = 100,
    ) -> List[SecurityEvent]:
        """Query audit log with optional filters."""
        events = self.audit_log
        
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        if action:
            events = [e for e in events if e.action == action]
        if result:
            events = [e for e in events if e.result == result]
        
        return events[-limit:]  # Return most recent
    
    def export_audit_log(self, filepath: str) -> None:
        """Export audit log to JSON file."""
        audit_data = [e.to_dict() for e in self.audit_log]
        with open(filepath, 'w') as f:
            json.dump(audit_data, f, indent=2)
        logger.info(f"Audit log exported to {filepath}")


class SecurityContextManager:
    """Manage security contexts for sessions."""
    
    def __init__(self):
        self.active_contexts: Dict[str, AccessContext] = {}
        self.rbac = RBACSystem()
    
    def create_context(
        self,
        user_id: str,
        username: str,
        role: Role,
        session_id: str,
        ip_address: Optional[str] = None,
        clearance_level: int = 0,
    ) -> AccessContext:
        """Create and store a new security context."""
        context = AccessContext(
            user_id=user_id,
            role=role,
            username=username,
            session_id=session_id,
            ip_address=ip_address,
            clearance_level=clearance_level,
        )
        self.active_contexts[session_id] = context
        logger.info(f"Security context created: {context}")
        return context
    
    def get_context(self, session_id: str) -> Optional[AccessContext]:
        """Get active security context by session ID."""
        return self.active_contexts.get(session_id)
    
    def destroy_context(self, session_id: str) -> None:
        """Destroy security context (logout)."""
        if session_id in self.active_contexts:
            context = self.active_contexts.pop(session_id)
            logger.info(f"Security context destroyed: {context.username}")
    
    def list_active_sessions(self) -> List[AccessContext]:
        """List all active security contexts."""
        return list(self.active_contexts.values())


# Global instances
_rbac_system = RBACSystem()
_security_context_manager = SecurityContextManager()


def get_rbac_system() -> RBACSystem:
    """Get global RBAC system instance."""
    return _rbac_system


def get_security_context_manager() -> SecurityContextManager:
    """Get global security context manager instance."""
    return _security_context_manager
