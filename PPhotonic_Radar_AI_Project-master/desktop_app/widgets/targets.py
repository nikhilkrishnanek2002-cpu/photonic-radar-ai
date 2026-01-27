
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QWidget, QVBoxLayout, QLabel, QPushButton

class TargetTable(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        layout.addWidget(QLabel("Tracked Targets"))
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Class", "Range (m)", "Vel (m/s)", "Azimuth"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("gridline-color: #444; color: #eee; background-color: #222;")
        layout.addWidget(self.table)
        
        # Export Button
        self.btn_export = QPushButton("EXPORT TARGET DATA (CSV)")
        self.btn_export.setStyleSheet("background-color: #444; color: #66fcf1; font-weight: bold; padding: 8px;")
        self.btn_export.clicked.connect(self._export_data)
        layout.addWidget(self.btn_export)
        
        self.current_tracks = []
        
    def update_table(self, frame_data):
        self.current_tracks = frame_data.get('tracks', [])
        # Store for export
        tracks = self.current_tracks
        
        self.table.setRowCount(len(tracks))
        
        illuminated_ids = set(frame_data.get('illuminated_ids', []))
        scan_angle = frame_data.get('scan_angle', 0.0)
        
        for row, track in enumerate(tracks):
            tid = track['id']
            rng = track['range_m']
            vel = track['velocity_m_s']
            cls = track.get('class_label', 'Scanning...')
            
            # Estimate Azimuth: if illuminated, use scan_angle. Else use '---'
            # Note: A real tracker would estimate Azimuth.
            az_str = f"{scan_angle:.1f}°" if tid in illuminated_ids else "---"
            
            self.table.setItem(row, 0, QTableWidgetItem(str(tid)))
            self.table.setItem(row, 1, QTableWidgetItem(str(cls)))
            self.table.setItem(row, 2, QTableWidgetItem(f"{rng:.1f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{vel:.1f}"))
            self.table.setItem(row, 4, QTableWidgetItem(az_str))

    def _export_data(self):
        if not self.current_tracks:
            return
            
        import csv
        import datetime
        from PySide6.QtWidgets import QFileDialog
        
        # Generate filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename, _ = QFileDialog.getSaveFileName(self, "Save Target Report", f"targets_{timestamp}.csv", "CSV Files (*.csv)")
        
        if filename:
            try:
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    # Header
                    writer.writerow(["Track ID", "Classification", "Range (m)", "Velocity (m/s)", "Confidence"])
                    # Rows
                    for tr in self.current_tracks:
                        writer.writerow([
                            tr['id'],
                            tr.get('class_label', 'Unknown'),
                            f"{tr['range_m']:.2f}",
                            f"{tr['velocity_m_s']:.2f}",
                            f"{tr.get('confidence', 0.0):.2f}"
                        ])
                print(f"Exported to {filename}")
            except Exception as e:
                print(f"Export failed: {e}")
