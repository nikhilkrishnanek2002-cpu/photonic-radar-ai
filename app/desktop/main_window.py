"""
Main Desktop Application Window
PySide6-based desktop GUI for Photonic Radar AI
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QTextEdit, QGroupBox, QStatusBar, QProgressBar,
    QMessageBox, QTabWidget
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QSize
from PySide6.QtGui import QIcon, QColor, QFont, QTextCursor, QPixmap
from PySide6.QtWebEngineWidgets import QWebEngineView

from app.desktop.launcher import BackendLauncher, open_dashboard_in_browser, open_api_in_browser
from app.desktop.system_monitor import SystemMonitor, SystemMetrics, HealthStatus

logger = logging.getLogger(__name__)


class StatusIndicator(QLabel):
    """Visual status indicator"""
    
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.status_label = label
        self.status = False
        self.update_display()
    
    def set_status(self, status: bool):
        self.status = status
        self.update_display()
    
    def update_display(self):
        color = "🟢" if self.status else "🔴"
        self.setText(f"{color} {self.status_label}: {'Ready' if self.status else 'Offline'}")
        self.setStyleSheet(
            "QLabel { color: #00FF00 if self.status else #FF6B6B; font-weight: bold; }"
        )


class ConsoleWidget(QTextEdit):
    """Console output widget with auto-scroll"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                border: 1px solid #333;
            }
        """)
    
    def log(self, message: str):
        """Add message to console with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}"
        
        # Append text
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)
        self.insertPlainText(formatted + "\n")
        
        # Auto-scroll to bottom
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class MetricsWidget(QWidget):
    """System metrics display widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QGridLayout(self)
        layout.setSpacing(10)
        
        # CPU
        self.cpu_label = QLabel("CPU: --%")
        self.cpu_bar = QProgressBar()
        layout.addWidget(QLabel("CPU Usage:"), 0, 0)
        layout.addWidget(self.cpu_bar, 0, 1)
        layout.addWidget(self.cpu_label, 0, 2)
        
        # Memory
        self.memory_label = QLabel("- MB (--%)")
        self.memory_bar = QProgressBar()
        layout.addWidget(QLabel("Memory:"), 1, 0)
        layout.addWidget(self.memory_bar, 1, 1)
        layout.addWidget(self.memory_label, 1, 2)
        
        # Uptime
        self.uptime_label = QLabel("--:--:--")
        layout.addWidget(QLabel("Uptime:"), 2, 0)
        layout.addWidget(self.uptime_label, 2, 1, 1, 2)
    
    def update_metrics(self, metrics: SystemMetrics):
        """Update metrics display"""
        # CPU
        self.cpu_bar.setValue(int(metrics.cpu_percent))
        self.cpu_label.setText(f"{metrics.cpu_percent:.1f}%")
        
        # Memory
        self.memory_bar.setValue(int(metrics.memory_percent))
        self.memory_label.setText(f"{metrics.memory_mb:.0f} MB ({metrics.memory_percent:.1f}%)")
        
        # Uptime
        uptime_seconds = int(metrics.uptime_seconds)
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        self.uptime_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")


class StatusWidget(QWidget):
    """System status indicators"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Status indicators
        self.backend_indicator = StatusIndicator("Backend")
        self.api_indicator = StatusIndicator("API Server (5000)")
        self.dashboard_indicator = StatusIndicator("Dashboard (8501)")
        
        layout.addWidget(self.backend_indicator)
        layout.addWidget(self.api_indicator)
        layout.addWidget(self.dashboard_indicator)
        layout.addStretch()
    
    def update_status(self, metrics: SystemMetrics):
        """Update status indicators"""
        self.backend_indicator.set_status(metrics.backend_alive)
        self.api_indicator.set_status(metrics.api_ready)
        self.dashboard_indicator.set_status(metrics.dashboard_ready)


class MainWindow(QMainWindow):
    """Main desktop application window"""
    
    def __init__(self):
        super().__init__()
        
        # Setup
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.launcher: Optional[BackendLauncher] = None
        self.monitor: Optional[SystemMonitor] = None
        self.health = HealthStatus()
        self.startup_time = None
        
        # Initialize UI
        self.init_ui()
        self.setup_logging()
        self.apply_theme()
        
        # Initialize components
        self.launcher = BackendLauncher(self.project_root, self.console.log)
        self.monitor = SystemMonitor(update_interval=1.0)
        self.monitor.register_callback(self._on_metrics_update)
        
        # Timers
        self.health_check_timer = QTimer()
        self.health_check_timer.timeout.connect(self._check_health)
        
        self.setWindowTitle("Photonic Radar AI Defense Platform")
        self.setWindowIcon(self._create_icon())
        self.resize(1200, 800)
        self.show()
        
        self.console.log("Desktop application initialized")
    
    def init_ui(self):
        """Initialize UI components"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Left panel: Controls & Status
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(15)
        
        # Control buttons
        button_group = QGroupBox("System Control")
        button_layout = QVBoxLayout()
        
        self.start_button = QPushButton("▶ Start System")
        self.start_button.setMinimumHeight(40)
        self.start_button.clicked.connect(self.start_system)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover { background-color: #27ae60; }
            QPushButton:pressed { background-color: #229954; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)
        
        self.stop_button = QPushButton("⏹ Stop System")
        self.stop_button.setMinimumHeight(40)
        self.stop_button.clicked.connect(self.stop_system)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover { background-color: #c0392b; }
            QPushButton:pressed { background-color: #a93226; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)
        
        self.reload_button = QPushButton("🔄 Restart System")
        self.reload_button.setMinimumHeight(40)
        self.reload_button.clicked.connect(self.restart_system)
        self.reload_button.setEnabled(False)
        self.reload_button.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover { background-color: #d68910; }
            QPushButton:pressed { background-color: #b87519; }
        """)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.reload_button)
        button_group.setLayout(button_layout)
        left_layout.addWidget(button_group)
        
        # Dashboard/API buttons
        dashboard_group = QGroupBox("Access")
        dashboard_layout = QVBoxLayout()
        
        self.dashboard_button = QPushButton("📊 Open Dashboard")
        self.dashboard_button.setMinimumHeight(35)
        self.dashboard_button.clicked.connect(self.open_dashboard)
        self.dashboard_button.setEnabled(False)
        
        self.api_button = QPushButton("🔌 API Docs")
        self.api_button.setMinimumHeight(35)
        self.api_button.clicked.connect(self.open_api)
        self.api_button.setEnabled(False)
        
        dashboard_layout.addWidget(self.dashboard_button)
        dashboard_layout.addWidget(self.api_button)
        dashboard_group.setLayout(dashboard_layout)
        left_layout.addWidget(dashboard_group)
        
        # Status indicators
        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout()
        self.status_widget = StatusWidget()
        status_layout.addWidget(self.status_widget)
        status_group.setLayout(status_layout)
        left_layout.addWidget(status_group)
        
        # Metrics
        metrics_group = QGroupBox("System Metrics")
        metrics_layout = QVBoxLayout()
        self.metrics_widget = MetricsWidget()
        metrics_layout.addWidget(self.metrics_widget)
        metrics_group.setLayout(metrics_layout)
        left_layout.addWidget(metrics_group)
        
        # Health indicator
        health_group = QGroupBox("Health")
        health_layout = QVBoxLayout()
        self.health_label = QLabel("Stopped")
        health_layout.addWidget(self.health_label)
        health_group.setLayout(health_layout)
        left_layout.addWidget(health_group)
        
        left_layout.addStretch()
        left_panel.setMaximumWidth(320)
        
        # Right panel: Console
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        console_group = QGroupBox("System Console")
        console_layout = QVBoxLayout()
        self.console = ConsoleWidget()
        console_layout.addWidget(self.console)
        console_group.setLayout(console_layout)
        right_layout.addWidget(console_group)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)
        
        # Status bar
        self.statusBar().showMessage("Ready to start")
    
    def setup_logging(self):
        """Setup logging to console widget"""
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        logging.root.addHandler(handler)
        logging.root.setLevel(logging.INFO)
    
    def apply_theme(self):
        """Apply dark theme"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QGroupBox {
                color: #ecf0f1;
                border: 2px solid #34495e;
                border-radius: 5px;
                margin-top: 15px;
                padding-top: 15px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0px 3px 0px 3px;
            }
            QLabel {
                color: #ecf0f1;
            }
            QPushButton {
                color: white;
                border-radius: 3px;
                padding: 5px;
                font-weight: bold;
            }
            QProgressBar {
                border: 1px solid #34495e;
                border-radius: 3px;
                background-color: #2c3e50;
                color: #ecf0f1;
            }
            QProgressBar::chunk {
                background-color: #3498db;
            }
            QStatusBar {
                background-color: #2c3e50;
                color: #ecf0f1;
            }
        """)
    
    def start_system(self):
        """Start backend system"""
        self.console.log("Starting system...")
        self.health.set_starting()
        self.start_button.setEnabled(False)
        self.statusBar().showMessage("Starting system...")
        
        if self.launcher.start():
            self.startup_time = None
            self.health_check_timer.start(2000)  # Check every 2 seconds
            self.monitor.set_backend_pid(self.launcher.get_pid())
            self.monitor.start()
            self.console.log("System startup initiated")
        else:
            self.health.set_error("Failed to start backend")
            self.start_button.setEnabled(True)
            self.statusBar().showMessage("Failed to start system")
            QMessageBox.critical(self, "Startup Error", "Failed to start backend system")
    
    def stop_system(self):
        """Stop backend system"""
        self.console.log("Stopping system...")
        self.health.set_stopping()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.reload_button.setEnabled(False)
        self.statusBar().showMessage("Stopping system...")
        
        self.monitor.stop()
        self.health_check_timer.stop()
        
        if self.launcher.stop():
            self.health.set_stopped()
            self.console.log("System stopped successfully")
            self.statusBar().showMessage("System stopped")
        else:
            self.console.log("Error during shutdown")
            self.statusBar().showMessage("Error during shutdown")
    
    def restart_system(self):
        """Restart system"""
        self.console.log("Restarting system...")
        self.stop_system()
        import time
        time.sleep(2)
        self.start_system()
    
    def open_dashboard(self):
        """Open dashboard in browser"""
        self.console.log("Opening dashboard...")
        if open_dashboard_in_browser():
            self.console.log("Dashboard opened in browser")
        else:
            self.console.log("Dashboard not ready yet")
            QMessageBox.warning(self, "Dashboard", "Dashboard is not ready. Please try again.")
    
    def open_api(self):
        """Open API docs in browser"""
        self.console.log("Opening API documentation...")
        open_api_in_browser()
    
    def _on_metrics_update(self, metrics: SystemMetrics):
        """Handle metrics update"""
        self.metrics_widget.update_metrics(metrics)
        self.status_widget.update_status(metrics)
        
        # Update health status
        if metrics.backend_alive:
            if metrics.api_ready and metrics.dashboard_ready:
                self.health.set_running()
        
        self.health_label.setText(
            f"Status: {self.health.status.upper()}\n{self.health.message}"
        )
    
    def _check_health(self):
        """Check system health"""
        if self.launcher.is_running():
            # System is running
            self.stop_button.setEnabled(True)
            self.reload_button.setEnabled(True)
            self.dashboard_button.setEnabled(self.monitor.metrics and self.monitor.metrics.dashboard_ready)
            self.api_button.setEnabled(self.monitor.metrics and self.monitor.metrics.api_ready)
            
            if self.startup_time is None:
                self.startup_time = datetime.now()
                self.console.log("✓ System ready")
                self.statusBar().showMessage("System operational")
                self.health.set_running()
        else:
            # System crashed
            self.health_check_timer.stop()
            self.monitor.stop()
            self.console.log("✗ System crashed or stopped")
            self.health.set_error("System process terminated")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.reload_button.setEnabled(False)
            self.dashboard_button.setEnabled(False)
            self.api_button.setEnabled(False)
            self.statusBar().showMessage("System offline")
    
    def closeEvent(self, event):
        """Handle window close"""
        if self.launcher and self.launcher.is_running():
            reply = QMessageBox.warning(
                self,
                "Confirm Exit",
                "System is still running. Stop and exit?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.stop_system()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
    
    @staticmethod
    def _create_icon() -> QIcon:
        """Create application icon"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor("#2c3e50"))
        icon = QIcon(pixmap)
        return icon
