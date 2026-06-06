#!/usr/bin/env python3
"""
AVCS - Audio Video Conversion Suite
Enterprise-grade audio/video conversion application.
Supports legacy formats including TeVeo VIDiO Suite .tvo files.
"""

import sys
import os

# Ensure the app directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QFont, QPalette, QColor

from ui.main_window import MainWindow
from themes.dark_theme import apply_dark_theme


def main():
    # Enable high-DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("AVCS")
    app.setApplicationDisplayName("AVCS - Audio Video Conversion Suite")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("AVCS")

    # Apply dark theme
    apply_dark_theme(app)

    # Set default font
    font = QFont("Segoe UI", 9)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
