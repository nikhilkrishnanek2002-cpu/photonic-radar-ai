
from PySide6.QtGui import QColor, QPalette

class TacticalTheme:
    # Color Palette (Cyberpunk / Military HUD)
    COLOR_BG_MAIN = "#0b0c10"      # Deep Black/Blue
    COLOR_BG_PANEL = "#1f2833"     # Dark Gunmetal
    COLOR_ACCENT_1 = "#66fcf1"     # Neon Cyan
    COLOR_ACCENT_2 = "#45a29e"     # Muted Cyan
    COLOR_TEXT_MAIN = "#c5c6c7"    # Off-white
    COLOR_DANGER = "#ff003c"       # Cyber Red
    COLOR_WARNING = "#f2a900"      # Amber
    COLOR_SUCCESS = "#00ff9d"      # Neon Green

    @staticmethod
    def get_stylesheet():
        return f"""
        QMainWindow {{
            background-color: {TacticalTheme.COLOR_BG_MAIN};
        }}
        
        QDockWidget {{
            color: {TacticalTheme.COLOR_ACCENT_1};
            background-color: {TacticalTheme.COLOR_BG_PANEL};
            border: 1px solid {TacticalTheme.COLOR_ACCENT_2};
            titlebar-close-icon: url(close.png);
            titlebar-normal-icon: url(undock.png);
            font-family: 'Segoe UI', 'Roboto', 'Helvetica';
            font-weight: bold;
        }}
        
        QDockWidget::title {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {TacticalTheme.COLOR_BG_PANEL}, stop:1 {TacticalTheme.COLOR_BG_MAIN});
            padding: 8px;
            border-bottom: 1px solid {TacticalTheme.COLOR_ACCENT_2};
        }}

        QWidget {{
            color: {TacticalTheme.COLOR_TEXT_MAIN};
            font-size: 14px;
        }}
        
        /* Tactical Buttons */
        QPushButton {{
            background-color: rgba(69, 162, 158, 0.2);
            border: 1px solid {TacticalTheme.COLOR_ACCENT_2};
            color: {TacticalTheme.COLOR_ACCENT_1};
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
            letter-spacing: 1px;
        }}
        
        QPushButton:hover {{
            background-color: rgba(102, 252, 241, 0.3);
            border: 1px solid {TacticalTheme.COLOR_ACCENT_1};
            color: #ffffff;
        }}
        
        QPushButton:pressed {{
            background-color: {TacticalTheme.COLOR_ACCENT_1};
            color: {TacticalTheme.COLOR_BG_MAIN};
        }}
        
        QPushButton:checked {{
            background-color: {TacticalTheme.COLOR_DANGER};
            border-color: {TacticalTheme.COLOR_DANGER};
            color: white;
        }}

        /* Data Tables */
        QTableWidget {{
            background-color: rgba(31, 40, 51, 0.8);
            alternate-background-color: rgba(45, 55, 65, 0.8);
            gridline-color: {TacticalTheme.COLOR_ACCENT_2};
            border: none;
            selection-background-color: {TacticalTheme.COLOR_ACCENT_2};
        }}
        
        QHeaderView::section {{
            background-color: {TacticalTheme.COLOR_BG_PANEL};
            color: {TacticalTheme.COLOR_ACCENT_1};
            padding: 5px;
            border: 1px solid {TacticalTheme.COLOR_ACCENT_2};
            font-weight: bold;
            text-transform: uppercase;
        }}
        
        /* Combo Box */
        QComboBox {{
            background-color: {TacticalTheme.COLOR_BG_PANEL};
            border: 1px solid {TacticalTheme.COLOR_ACCENT_2};
            color: {TacticalTheme.COLOR_ACCENT_1};
            padding: 5px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {TacticalTheme.COLOR_BG_PANEL};
            color: {TacticalTheme.COLOR_TEXT_MAIN};
            selection-background-color: {TacticalTheme.COLOR_ACCENT_2};
        }}
        
        /* Group Box */
        QGroupBox {{
            border: 1px solid {TacticalTheme.COLOR_ACCENT_2};
            margin-top: 20px;
            font-weight: bold;
            color: {TacticalTheme.COLOR_ACCENT_1};
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 5px;
            background-color: {TacticalTheme.COLOR_BG_MAIN};
        }}
        """
