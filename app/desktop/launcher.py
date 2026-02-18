"""
Backend Launcher and Process Manager
Manages backend (main.py) lifecycle and monitoring
"""

import subprocess
import time
import os
import signal
import logging
import sys
from pathlib import Path
from typing import Optional, Callable
import threading
import webbrowser

logger = logging.getLogger(__name__)


class BackendLauncher:
    """Manages backend process lifecycle"""
    
    def __init__(self, project_root: Path, log_callback: Optional[Callable[[str], None]] = None):
        self.project_root = project_root
        self.process: Optional[subprocess.Popen] = None
        self.running = False
        self.log_callback = log_callback
        self.venv_python = project_root / "photonic-radar-ai" / "venv" / "bin" / "python"
        self.main_script = project_root / "main.py"
        self.log_file = project_root / "photonic-radar-ai" / "runtime" / "desktop_backend.log"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
    def _log(self, message: str):
        """Log message through callback"""
        if self.log_callback:
            self.log_callback(message)
        logger.info(message)
    
    def start(self) -> bool:
        """Start backend process"""
        if self.running:
            self._log("Backend already running")
            return False
        
        try:
            self._log(f"Starting backend: {self.main_script}")
            
            # Prepare command
            python_exe = str(self.venv_python) if self.venv_python.exists() else sys.executable
            cmd = [python_exe, str(self.main_script), "--ui"]
            
            # Start process
            self.process = subprocess.Popen(
                cmd,
                cwd=str(self.project_root),
                stdout=open(self.log_file, 'a'),
                stderr=subprocess.STDOUT,
                env={**os.environ, 'PYTHONUNBUFFERED': '1'}
            )
            
            self.running = True
            self._log(f"Backend started (PID: {self.process.pid})")
            
            # Monitor process
            threading.Thread(target=self._monitor_process, daemon=True).start()
            
            # Wait for API to be ready
            if self._wait_for_api(timeout=30):
                self._log("API server ready")
                return True
            else:
                self._log("Warning: API not ready within timeout")
                return True  # Still started, but API not responding
        
        except Exception as e:
            self._log(f"Failed to start backend: {e}")
            self.running = False
            return False
    
    def stop(self) -> bool:
        """Stop backend process gracefully"""
        if not self.running or not self.process:
            return True
        
        try:
            self._log("Stopping backend...")
            
            # Try graceful shutdown first
            if sys.platform == "win32":
                self.process.send_signal(signal.CTRL_C_EVENT)
            else:
                self.process.send_signal(signal.SIGTERM)
            
            # Wait for graceful shutdown
            try:
                self.process.wait(timeout=10)
                self._log("Backend stopped gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if graceful didn't work
                self._log("Force killing backend...")
                self.process.kill()
                self.process.wait()
                self._log("Backend force killed")
            
            self.running = False
            self.process = None
            return True
        
        except Exception as e:
            self._log(f"Error stopping backend: {e}")
            return False
    
    def restart(self) -> bool:
        """Restart backend"""
        self.stop()
        time.sleep(1)
        return self.start()
    
    def is_running(self) -> bool:
        """Check if backend is running"""
        if not self.process:
            return False
        return self.process.poll() is None
    
    def get_pid(self) -> Optional[int]:
        """Get backend process ID"""
        return self.process.pid if self.process else None
    
    def _monitor_process(self):
        """Monitor process and handle unexpected termination"""
        while self.running and self.process:
            if self.process.poll() is not None:
                self._log("Backend process terminated unexpectedly")
                self.running = False
                break
            time.sleep(1)
    
    @staticmethod
    def _wait_for_api(timeout: int = 30) -> bool:
        """Wait for API server to be ready"""
        import socket
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', 5000))
                sock.close()
                if result == 0:
                    return True
            except:
                pass
            time.sleep(0.5)
        
        return False
    
    @staticmethod
    def wait_for_dashboard(timeout: int = 30) -> bool:
        """Wait for Streamlit dashboard to be ready"""
        import socket
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', 8501))
                sock.close()
                if result == 0:
                    return True
            except:
                pass
            time.sleep(0.5)
        
        return False


def open_dashboard_in_browser():
    """Open dashboard in default browser"""
    if BackendLauncher.wait_for_dashboard(timeout=10):
        webbrowser.open('http://localhost:8501')
        return True
    return False


def open_api_in_browser():
    """Open API docs in default browser"""
    webbrowser.open('http://localhost:5000/docs')
