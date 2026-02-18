"""
System Monitor Module
Monitors CPU, memory, and process health in real-time
"""

import psutil
import threading
import time
from typing import Callable, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """Container for system metrics"""
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    processes: int
    uptime_seconds: float
    backend_alive: bool
    api_ready: bool
    dashboard_ready: bool


class SystemMonitor:
    """Monitors system resources and application health"""
    
    def __init__(self, update_interval: float = 1.0):
        self.update_interval = update_interval
        self.running = False
        self.metrics: SystemMetrics = None
        self.thread = None
        self.callbacks: list = []
        self.start_time = time.time()
        self.backend_pid = None
        self.api_port = 5000
        self.dashboard_port = 8501
        
    def register_callback(self, callback: Callable[[SystemMetrics], None]):
        """Register callback for metrics updates"""
        self.callbacks.append(callback)
        
    def unregister_callback(self, callback: Callable):
        """Unregister callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def start(self):
        """Start monitoring thread"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("System monitor started")
    
    def stop(self):
        """Stop monitoring thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("System monitor stopped")
    
    def set_backend_pid(self, pid: int):
        """Set backend process ID for monitoring"""
        self.backend_pid = pid
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                self.metrics = self._collect_metrics()
                
                # Notify all callbacks
                for callback in self.callbacks:
                    try:
                        callback(self.metrics)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
                
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                time.sleep(self.update_interval)
    
    def _collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_info = psutil.virtual_memory()
            memory_mb = memory_info.used / 1024 / 1024
            memory_percent = memory_info.percent
            
            # Process count
            process_count = len(psutil.pids())
            
            # Uptime
            uptime = time.time() - self.start_time
            
            # Check backend alive
            backend_alive = self._check_backend_alive()
            
            # Check ports
            api_ready = self._check_port_open('127.0.0.1', self.api_port)
            dashboard_ready = self._check_port_open('127.0.0.1', self.dashboard_port)
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                processes=process_count,
                uptime_seconds=uptime,
                backend_alive=backend_alive,
                api_ready=api_ready,
                dashboard_ready=dashboard_ready
            )
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return SystemMetrics(0, 0, 0, 0, 0, False, False, False)
    
    def _check_backend_alive(self) -> bool:
        """Check if backend process is still running"""
        if self.backend_pid is None:
            return False
        try:
            process = psutil.Process(self.backend_pid)
            return process.is_running()
        except:
            return False
    
    @staticmethod
    def _check_port_open(host: str, port: int) -> bool:
        """Check if port is open/listening"""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False


class HealthStatus:
    """System health status tracker"""
    
    def __init__(self):
        self.status = "stopped"  # stopped, starting, running, stopping, error
        self.message = "System stopped"
        self.error = None
    
    def set_running(self):
        self.status = "running"
        self.message = "System operational"
        self.error = None
    
    def set_starting(self):
        self.status = "starting"
        self.message = "Initializing system..."
        self.error = None
    
    def set_stopping(self):
        self.status = "stopping"
        self.message = "Shutting down..."
        self.error = None
    
    def set_stopped(self):
        self.status = "stopped"
        self.message = "System stopped"
        self.error = None
    
    def set_error(self, error: str):
        self.status = "error"
        self.message = f"Error: {error}"
        self.error = error
    
    def is_healthy(self) -> bool:
        return self.status == "running"
