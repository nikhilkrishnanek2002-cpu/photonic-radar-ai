
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication
from desktop_app.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Set Fusion Style for uniform look
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    print("PHOENIX-RADAR Desktop Launched.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
