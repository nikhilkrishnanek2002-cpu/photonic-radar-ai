
import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout
from desktop_app.theme import TacticalTheme

class MetricsDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # 1. Plots Area
        # We need 3 small plots: Pd, PFA, RMSE
        
        self.plot_pd = self._create_plot("Detection Probability (Pd)", TacticalTheme.COLOR_SUCCESS, [0, 1])
        self.plot_pfa = self._create_plot("False Alarm Rate (PFA)", TacticalTheme.COLOR_WARNING, [0, 0.1])
        self.plot_rmse = self._create_plot("Range RMSE (m)", TacticalTheme.COLOR_DANGER, [0, 20])
        
        self.layout.addWidget(self.plot_pd)
        self.layout.addWidget(self.plot_pfa)
        self.layout.addWidget(self.plot_rmse)
        
        # Data Buffers
        self.history_len = 100
        self.data_pd = np.zeros(self.history_len)
        self.data_pfa = np.zeros(self.history_len)
        self.data_rmse = np.zeros(self.history_len)
        
        self.ptr = 0

    def _create_plot(self, title, color, y_range):
        plot = pg.PlotWidget(title=title)
        plot.setBackground(TacticalTheme.COLOR_BG_PANEL)
        plot.showGrid(x=True, y=True, alpha=0.3)
        plot.setYRange(y_range[0], y_range[1])
        plot.hideAxis('bottom') # Save space
        plot.getAxis('left').setPen(TacticalTheme.COLOR_TEXT_MAIN)
        
        # Curve
        curve = plot.plot(pen=pg.mkPen(color, width=2))
        plot.curve = curve # Store reference
        return plot

    def update_metrics(self, frame_data):
        eval_data = frame_data.get('evaluation', {})
        
        # Parse Metrics
        # Eval manager returns summary dict: 'pd', 'pfa', 'range_rmse', 'velocity_rmse'
        pd = eval_data.get('pd', 0.0)
        pfa = eval_data.get('pfa', 0.0)
        rmse = eval_data.get('range_rmse', 0.0)
        
        if rmse is None: rmse = 0.0 # Handle NoneType
        
        # Update Buffers
        self.data_pd = np.roll(self.data_pd, -1)
        self.data_pd[-1] = pd
        
        self.data_pfa = np.roll(self.data_pfa, -1)
        self.data_pfa[-1] = pfa
        
        self.data_rmse = np.roll(self.data_rmse, -1)
        self.data_rmse[-1] = rmse
        
        # Update Plots
        self.plot_pd.curve.setData(self.data_pd)
        self.plot_pfa.curve.setData(self.data_pfa)
        self.plot_rmse.curve.setData(self.data_rmse)
