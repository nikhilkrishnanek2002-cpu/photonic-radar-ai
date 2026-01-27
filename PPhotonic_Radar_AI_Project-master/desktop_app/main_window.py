
from PySide6.QtWidgets import QMainWindow, QDockWidget, QWidget, QMessageBox
from PySide6.QtCore import Qt, Slot, QThread, Signal

from desktop_app.bridge import RadarWorker
from desktop_app.widgets.ppi import PPIDisplay
from desktop_app.widgets.waterfall import DopplerWaterfall
from desktop_app.widgets.controls import ControlPanel
from desktop_app.widgets.targets import TargetTable
from desktop_app.widgets.metrics import MetricsDashboard
from desktop_app.theme import TacticalTheme

class MainWindow(QMainWindow):
    # Signal to start worker initialization in its thread
    start_init = Signal()
    request_start = Signal()
    request_stop = Signal()
    request_scenario = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PHOENIX-RADAR: Strategic Command Console")
        self.resize(1600, 900)
        self.setStyleSheet(TacticalTheme.get_stylesheet())
        
        # 1. Setup Backend Thread
        self.worker_thread = QThread()
        self.worker = RadarWorker()
        self.worker.moveToThread(self.worker_thread)
        
        # 2. Connect Signals
        # Control Flow
        self.start_init.connect(self.worker.initialize)
        self.request_start.connect(self.worker.start_sim)
        self.request_stop.connect(self.worker.stop_sim)
        self.request_scenario.connect(self.worker.switch_scenario)
        
        # Data Flow
        self.worker.frame_ready.connect(self.on_frame_ready)
        self.worker.error_occurred.connect(self.on_worker_error)
        
        # Thread Lifecycle
        self.worker_thread.start()
        self.start_init.emit() # Trigger init in thread
        
        # 3. Setup GUI
        self._setup_ui()
        
        # Auto-start simulation
        self.request_start.emit()

    def _setup_ui(self):
        # Central Widget (PPI)
        self.ppi = PPIDisplay()
        self.setCentralWidget(self.ppi)
        
        # Dock Widgets
        # Left: Controls + Targets
        self.dock_controls = QDockWidget("Mission Control", self)
        self.controls = ControlPanel()
        self.controls.scenario_changed.connect(self.request_scenario)
        self.controls.stop_resume.connect(self.toggle_simulation)
        self.dock_controls.setWidget(self.controls)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_controls)
        
        self.dock_targets = QDockWidget("Track List", self)
        self.target_list = TargetTable()
        self.dock_targets.setWidget(self.target_list)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_targets)
        
        # Right: Waterfall + Metrics
        self.dock_waterfall = QDockWidget("Doppler Analytics", self)
        self.waterfall = DopplerWaterfall()
        self.dock_waterfall.setWidget(self.waterfall)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_waterfall)
        
        self.dock_metrics = QDockWidget("Live Performance", self)
        self.metrics = MetricsDashboard()
        self.dock_metrics.setWidget(self.metrics)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_metrics)

    @Slot(dict)
    def on_frame_ready(self, frame_data):
        self.ppi.update_display(frame_data)
        self.waterfall.update_display(frame_data)
        self.target_list.update_table(frame_data)
        self.controls.update_telemetry(frame_data)
        self.metrics.update_metrics(frame_data)
        
    @Slot(str)
    def on_worker_error(self, msg):
        QMessageBox.critical(self, "Simulation Error", f"Backend Error: {msg}")

    @Slot(bool)
    def toggle_simulation(self, stop):
        if stop:
            self.request_stop.emit()
        else:
            self.request_start.emit()

    def closeEvent(self, event):
        # Graceful Shutdown
        self.request_stop.emit()
        self.worker_thread.quit()
        self.worker_thread.wait(2000) # Wait up to 2s
        event.accept()
