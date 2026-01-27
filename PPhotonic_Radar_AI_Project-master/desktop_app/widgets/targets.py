
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QWidget, QVBoxLayout, QLabel

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
        
    def update_table(self, frame_data):
        tracks = frame_data.get('tracks', [])
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
