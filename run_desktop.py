#!/usr/bin/env python3
"""
Photonic Radar AI - Desktop Application Entry Point

Usage:
    python run_desktop.py
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    try:
        # Import PySide6
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        
        # Add project root to path
        project_root = Path(__file__).resolve().parent
        sys.path.insert(0, str(project_root))
        
        # Import main window
        from app.desktop.main_window import MainWindow
        
        # Create application
        app = QApplication(sys.argv)
        
        # Set application properties
        app.setApplicationName("Photonic Radar AI Defense Platform")
        app.setApplicationVersion("1.0.0")
        
        # Create and show main window
        window = MainWindow()
        
        # Log startup
        logger.info("=" * 70)
        logger.info("PHOTONIC RADAR AI - DESKTOP APPLICATION")
        logger.info("=" * 70)
        logger.info("Application started successfully")
        
        # Run event loop
        sys.exit(app.exec())
    
    except ImportError as e:
        logger.error(f"Failed to import required packages: {e}")
        logger.error("Please install: pip install PySide6")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
