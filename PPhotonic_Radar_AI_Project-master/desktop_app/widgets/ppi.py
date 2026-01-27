
import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Slot, Qt

class PPIDisplay(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Configure Plot
        self.plot_widget = pg.PlotWidget(title="Plan Position Indicator (PPI)")
        self.plot_widget.setAspectLocked(True)
        self.plot_widget.setXRange(-1000, 1000)
        self.plot_widget.setYRange(-1000, 1000)
        self.plot_widget.showGrid(x=False, y=False) # Custom grid
        self.plot_widget.setBackground('#0b0c10')
        self.layout.addWidget(self.plot_widget)
        
        # Add Circular Grid (Range Rings)
        self._add_radar_grid()
        
        # Sweep Line (Glowing)
        self.sweep_line = pg.PlotCurveItem(pen=pg.mkPen('#66fcf1', width=3, style=Qt.SolidLine))
        self.plot_widget.addItem(self.sweep_line)
        
        # Ground Truth Targets (Red Glow)
        self.scatter_targets = pg.ScatterPlotItem(
            size=12, 
            pen=pg.mkPen(None), 
            brush=pg.mkBrush(255, 0, 60, 200),
            name="Targets"
        )
        self.plot_widget.addItem(self.scatter_targets)
        
        # Detections (Amber Glow)
        self.scatter_detections = pg.ScatterPlotItem(
            size=14, 
            symbol='+',
            pen=pg.mkPen('#f2a900', width=2),
            brush=pg.mkBrush('#f2a900'),
            name="Detections"
        )
        self.plot_widget.addItem(self.scatter_detections)
        
        self.track_azimuths = {} # ID -> Azimuth (deg)
        self.track_labels = {}   # ID -> pg.TextItem

    def _add_radar_grid(self):
        # Range Rings
        for r in [250, 500, 750, 1000]:
            circle = pg.QtWidgets.QGraphicsEllipseItem(-r, -r, r*2, r*2)
            circle.setPen(pg.mkPen('#1f2833', width=1))
            self.plot_widget.addItem(circle)
            
        # Crosshairs
        line_pen = pg.mkPen('#1f2833', width=1)
        self.plot_widget.addItem(pg.InfiniteLine(angle=0, pen=line_pen))
        self.plot_widget.addItem(pg.InfiniteLine(angle=90, pen=line_pen))


    @Slot(dict)
    def update_display(self, frame_data):
        angle_deg = frame_data['scan_angle']
        angle_rad = np.radians(angle_deg)
        
        # 1. Update Sweep Line
        r_max = 1000
        x_line = [0, r_max * np.cos(angle_rad)]
        y_line = [0, r_max * np.sin(angle_rad)]
        self.sweep_line.setData(x_line, y_line)
        
        # 2. Update Ground Truth Targets
        targets = frame_data.get('targets', [])
        tx = [t['pos_x'] for t in targets]
        ty = [t['pos_y'] for t in targets]
        self.scatter_targets.setData(tx, ty)
        
        # 3. Visualize Detections/Tracks at Current Scan Angle
        tracks = frame_data.get('tracks', [])
        dx = []
        dy = []
        
        illuminated = set(frame_data.get('illuminated_ids', []))
        active_ids = set()
        
        for tr in tracks:
            tid = tr['id']
            r = tr['range_m']
            
            # Update known azimuth if illuminated
            if tid in illuminated:
                self.track_azimuths[tid] = angle_rad
            
            # Plot if we have an azimuth
            if tid in self.track_azimuths:
                active_ids.add(tid)
                az = self.track_azimuths[tid]
                x = r * np.cos(az)
                y = r * np.sin(az)
                dx.append(x)
                dy.append(y)
                
                # Update Label
                if tid not in self.track_labels:
                    # Create new label
                    label = pg.TextItem(text=f"T{tid}", color='#f2a900', anchor=(0, 1))
                    self.plot_widget.addItem(label)
                    self.track_labels[tid] = label
                
                # Update label position and text
                # We can also add class info if available: tr.get('class_label', '')
                self.track_labels[tid].setPos(x, y)
                self.track_labels[tid].setText(f"T{tid}")

        self.scatter_detections.setData(dx, dy)
        
        # 4. Cleanup Stale Labels
        # Remove labels for tracks that are no longer in the list
        for tid in list(self.track_labels.keys()):
            if tid not in active_ids:
                self.plot_widget.removeItem(self.track_labels[tid])
                del self.track_labels[tid]
