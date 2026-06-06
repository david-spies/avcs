"""
AVCS Main Window
"""

import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QStatusBar, QMenuBar, QAction, QMessageBox, QSizeGrip,
    QFrame, QSplitter,
)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor, QPainter, QBrush, QPen, QLinearGradient

from ui.video_tab import VideoConversionTab
from ui.audio_tab import AudioConversionTab
from ui.tvo_tab import TvoConverterTab
from ui.inspector_tab import MediaInspectorTab
from ui.reference_tab import FormatReferenceTab
from ui.settings_tab import SettingsTab
from utils.ffmpeg_utils import ffmpeg_available, FFMPEG_PATH, FFPROBE_PATH


AVCS_VERSION = "1.0.0"

ABOUT_TEXT = f"""
AVCS — Audio Video Conversion Suite
Version {AVCS_VERSION}

Enterprise-grade media conversion application.
Built with Python + PyQt5 + ffmpeg.

Supports:
  • Video: MP4, MKV, AVI, MOV, WebM, WMV, FLV, TS, VOB, OGV, 3GP, GIF, and more
  • Audio: MP3, AAC, FLAC, WAV, OGG, M4A, WMA, OPUS, AC3
  • Legacy: TeVeo VIDiO Suite .TVO (late 1990s webcam format)

TVO Format Research:
  .TVO files are orphaned legacy recordings created by TeveoLive,
  an early internet webcam broadcasting application (TeVeo Inc. /
  Orbisoft). These use obsolete codecs (Indeo, Cinepak, MJPEG) and
  proprietary container structures. AVCS handles TVO files via
  ffmpeg's legacy compatibility mode with extended error tolerance.

ffmpeg:   {FFMPEG_PATH or 'Not found'}
ffprobe:  {FFPROBE_PATH or 'Not found'}
"""


def _make_logo_pixmap(size: int = 36) -> QPixmap:
    """Draw the AVCS logo programmatically (no image files required)."""
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)

    # Background circle
    p.setBrush(QBrush(QColor(30, 15, 50)))
    p.setPen(QPen(QColor(160, 96, 224), 1.5))
    p.drawEllipse(2, 2, size - 4, size - 4)

    # Play triangle in amber
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(QColor(232, 160, 32)))
    s = size
    pts_x = [s * 0.35, s * 0.35, s * 0.72]
    pts_y = [s * 0.28, s * 0.72, s * 0.50]
    from PyQt5.QtGui import QPolygon
    from PyQt5.QtCore import QPoint
    poly = QPolygon([QPoint(int(x), int(y)) for x, y in zip(pts_x, pts_y)])
    p.drawPolygon(poly)

    p.end()
    return pix


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AVCS — Audio Video Conversion Suite")
        self.setMinimumSize(900, 640)
        self.resize(1100, 720)
        self.setWindowIcon(QIcon(_make_logo_pixmap(64)))
        self._setup_menu()
        self._setup_ui()
        self._setup_statusbar()
        self._check_dependencies()

    # ── Menu ─────────────────────────────────────────────────────
    def _setup_menu(self):
        mb = self.menuBar()

        file_menu = mb.addMenu("File")
        file_menu.addAction("Exit", self.close, "Ctrl+Q")

        tools_menu = mb.addMenu("Tools")
        tools_menu.addAction("Video Converter",      lambda: self._tabs.setCurrentIndex(0))
        tools_menu.addAction("Audio Converter",      lambda: self._tabs.setCurrentIndex(1))
        tools_menu.addAction("TVO Legacy Converter", lambda: self._tabs.setCurrentIndex(2))
        tools_menu.addAction("Media Inspector",      lambda: self._tabs.setCurrentIndex(3))
        tools_menu.addSeparator()
        tools_menu.addAction("Format Reference",     lambda: self._tabs.setCurrentIndex(4))
        tools_menu.addAction("Settings",             lambda: self._tabs.setCurrentIndex(5))

        help_menu = mb.addMenu("Help")
        help_menu.addAction("About AVCS", self._show_about)
        help_menu.addAction("ffmpeg Setup", self._show_ffmpeg_help)

    # ── UI ───────────────────────────────────────────────────────
    def _setup_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QWidget(central)
        header.setObjectName("header_widget")
        header.setFixedHeight(52)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 0, 16, 0)
        hl.setSpacing(10)

        logo_label = QLabel(header)
        logo_label.setPixmap(_make_logo_pixmap(32))
        hl.addWidget(logo_label)

        title_label = QLabel("AVCS", header)
        title_font = QFont("Segoe UI", 16)
        title_font.setWeight(QFont.Black)
        title_font.setLetterSpacing(QFont.AbsoluteSpacing, 2.0)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #e8a020; background: transparent;")
        hl.addWidget(title_label)

        sub_label = QLabel("Audio Video Conversion Suite", header)
        sub_label.setStyleSheet("color: #3a3d45; font-size: 9pt; background: transparent;")
        hl.addWidget(sub_label)

        hl.addStretch()

        self._ffmpeg_status = QLabel(header)
        self._ffmpeg_status.setStyleSheet(
            "background: transparent; font-size: 8pt; padding: 3px 8px; border-radius: 10px;"
        )
        hl.addWidget(self._ffmpeg_status)

        ver_label = QLabel(f"v{AVCS_VERSION}", header)
        ver_label.setStyleSheet("color: #3a3d45; font-size: 8pt; background: transparent;")
        hl.addWidget(ver_label)

        root.addWidget(header)

        # Thin accent line
        accent = QFrame(central)
        accent.setFixedHeight(2)
        accent.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #0a0b0e, stop:0.3 #e8a020, stop:0.7 #e8a020, stop:1 #0a0b0e);"
        )
        root.addWidget(accent)

        # Tab widget
        self._tabs = QTabWidget(central)
        self._tabs.setDocumentMode(False)

        self._video_tab = VideoConversionTab()
        self._audio_tab = AudioConversionTab()
        self._tvo_tab = TvoConverterTab()
        self._inspector_tab = MediaInspectorTab()
        self._reference_tab = FormatReferenceTab()
        self._settings_tab = SettingsTab()

        self._tabs.addTab(self._video_tab,     "  🎬  Video  ")
        self._tabs.addTab(self._audio_tab,     "  🔊  Audio  ")
        self._tabs.addTab(self._tvo_tab,       "  📼  TVO Legacy  ")
        self._tabs.addTab(self._inspector_tab, "  🔍  Inspector  ")
        self._tabs.addTab(self._reference_tab, "  📋  Reference  ")
        self._tabs.addTab(self._settings_tab,  "  ⚙  Settings  ")

        root.addWidget(self._tabs, 1)

    # ── Status Bar ───────────────────────────────────────────────
    def _setup_statusbar(self):
        sb = self.statusBar()
        sb.showMessage("Ready")

        self._status_right = QLabel("AVCS v" + AVCS_VERSION)
        self._status_right.setStyleSheet("color: #3a3d45; font-size: 8pt; padding: 0 8px;")
        sb.addPermanentWidget(self._status_right)

    # ── Dependency Check ─────────────────────────────────────────
    def _check_dependencies(self):
        if ffmpeg_available():
            self._ffmpeg_status.setText("● ffmpeg ready")
            self._ffmpeg_status.setStyleSheet(
                "color: #50c850; background: #0a2010; border: 1px solid #204020; "
                "font-size: 8pt; padding: 3px 10px; border-radius: 10px;"
            )
            self.statusBar().showMessage(f"ffmpeg found: {FFMPEG_PATH}")
        else:
            self._ffmpeg_status.setText("⚠ ffmpeg not found")
            self._ffmpeg_status.setStyleSheet(
                "color: #e8a020; background: #1a1000; border: 1px solid #4a3000; "
                "font-size: 8pt; padding: 3px 10px; border-radius: 10px;"
            )
            self.statusBar().showMessage(
                "ffmpeg not found — install it to enable conversion"
            )

    # ── Dialogs ──────────────────────────────────────────────────
    def _show_about(self):
        mb = QMessageBox(self)
        mb.setWindowTitle("About AVCS")
        mb.setText("<b>AVCS — Audio Video Conversion Suite</b>")
        mb.setInformativeText(ABOUT_TEXT.strip())
        mb.setIcon(QMessageBox.Information)
        mb.exec_()

    def _show_ffmpeg_help(self):
        msg = (
            "<b>Installing ffmpeg</b><br><br>"
            "<b>Linux (Ubuntu/Debian):</b><br>"
            "<code>sudo apt install ffmpeg</code><br><br>"
            "<b>Linux (Fedora/RHEL):</b><br>"
            "<code>sudo dnf install ffmpeg</code><br><br>"
            "<b>macOS (Homebrew):</b><br>"
            "<code>brew install ffmpeg</code><br><br>"
            "<b>Windows:</b><br>"
            "Download from <a href='https://ffmpeg.org/download.html'>ffmpeg.org</a> "
            "and add to PATH.<br><br>"
            "After installing, restart AVCS."
        )
        mb = QMessageBox(self)
        mb.setWindowTitle("ffmpeg Setup")
        mb.setText("AVCS requires ffmpeg for all conversions.")
        mb.setInformativeText(msg)
        mb.setTextFormat(Qt.RichText)
        mb.exec_()
