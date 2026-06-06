"""
AVCS Dark Theme - Cinematic dark aesthetic with amber/gold accents.
"""

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt


DARK_STYLESHEET = """
/* ── Base ─────────────────────────────────────────────── */
QWidget {
    background-color: #0f1014;
    color: #d4d4d8;
    font-family: "Segoe UI", "SF Pro Display", Ubuntu, sans-serif;
    font-size: 9pt;
}

QMainWindow {
    background-color: #0a0b0e;
}

/* ── Header / Title Bar ───────────────────────────────── */
#header_widget {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0a0b0e, stop:0.5 #12141a, stop:1 #0a0b0e);
    border-bottom: 1px solid #e8a020;
}

/* ── Tab Widget ───────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #2a2d35;
    background-color: #0f1014;
    border-radius: 4px;
}

QTabWidget::tab-bar {
    left: 0px;
}

QTabBar::tab {
    background-color: #1a1d24;
    color: #7a7d85;
    border: 1px solid #2a2d35;
    border-bottom: none;
    padding: 8px 20px;
    min-width: 100px;
    font-weight: 500;
    letter-spacing: 0.5px;
}

QTabBar::tab:selected {
    background-color: #0f1014;
    color: #e8a020;
    border-top: 2px solid #e8a020;
    border-left: 1px solid #3a3d45;
    border-right: 1px solid #3a3d45;
}

QTabBar::tab:hover:!selected {
    background-color: #1e2128;
    color: #b0b3bb;
}

/* ── Buttons ──────────────────────────────────────────── */
QPushButton {
    background-color: #1e2128;
    color: #c4c7cf;
    border: 1px solid #3a3d45;
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: 500;
    min-height: 28px;
}

QPushButton:hover {
    background-color: #262930;
    border-color: #5a5d65;
    color: #e4e7ef;
}

QPushButton:pressed {
    background-color: #16181e;
    border-color: #e8a020;
}

QPushButton#primary_button {
    background-color: #e8a020;
    color: #0a0b0e;
    border: none;
    font-weight: 700;
    letter-spacing: 0.5px;
}

QPushButton#primary_button:hover {
    background-color: #f0b030;
}

QPushButton#primary_button:pressed {
    background-color: #c88010;
}

QPushButton#primary_button:disabled {
    background-color: #3a3010;
    color: #6a6050;
}

QPushButton#danger_button {
    background-color: #2a1515;
    color: #e05050;
    border: 1px solid #4a2020;
}

QPushButton#danger_button:hover {
    background-color: #351a1a;
    border-color: #e05050;
}

QPushButton:disabled {
    background-color: #14161a;
    color: #404348;
    border-color: #242628;
}

/* ── Input Fields ─────────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #14161c;
    color: #d4d4d8;
    border: 1px solid #2a2d35;
    border-radius: 4px;
    padding: 5px 8px;
    selection-background-color: #e8a02040;
}

QLineEdit:focus, QTextEdit:focus {
    border-color: #e8a020;
    background-color: #16181e;
}

QLineEdit:read-only {
    background-color: #0f1014;
    color: #7a7d85;
}

/* ── ComboBox ─────────────────────────────────────────── */
QComboBox {
    background-color: #1a1d24;
    color: #d4d4d8;
    border: 1px solid #2a2d35;
    border-radius: 4px;
    padding: 5px 8px;
    min-height: 28px;
}

QComboBox:hover {
    border-color: #5a5d65;
}

QComboBox:focus {
    border-color: #e8a020;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #7a7d85;
    margin-right: 6px;
}

QComboBox QAbstractItemView {
    background-color: #1a1d24;
    color: #d4d4d8;
    border: 1px solid #3a3d45;
    selection-background-color: #e8a02025;
    selection-color: #e8a020;
    outline: none;
}

/* ── Spin Box ─────────────────────────────────────────── */
QSpinBox, QDoubleSpinBox {
    background-color: #1a1d24;
    color: #d4d4d8;
    border: 1px solid #2a2d35;
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 26px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #e8a020;
}

/* ── Progress Bar ─────────────────────────────────────── */
QProgressBar {
    background-color: #1a1d24;
    border: 1px solid #2a2d35;
    border-radius: 4px;
    height: 10px;
    text-align: center;
    color: #d4d4d8;
    font-size: 8pt;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #c07010, stop:1 #e8a020);
    border-radius: 3px;
}

/* ── List/Tree Views ──────────────────────────────────── */
QListView, QTreeView, QTableView {
    background-color: #0f1014;
    color: #d4d4d8;
    border: 1px solid #2a2d35;
    border-radius: 4px;
    alternate-background-color: #12141a;
    gridline-color: #1e2128;
    outline: none;
}

QListView::item, QTreeView::item {
    padding: 4px 8px;
    border: none;
}

QListView::item:selected, QTreeView::item:selected {
    background-color: #e8a02020;
    color: #e8a020;
}

QListView::item:hover, QTreeView::item:hover {
    background-color: #1e2128;
}

QHeaderView::section {
    background-color: #1a1d24;
    color: #7a7d85;
    border: none;
    border-right: 1px solid #2a2d35;
    border-bottom: 1px solid #2a2d35;
    padding: 6px 10px;
    font-weight: 600;
    font-size: 8pt;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ── Group Box ────────────────────────────────────────── */
QGroupBox {
    border: 1px solid #2a2d35;
    border-radius: 6px;
    margin-top: 14px;
    padding-top: 8px;
    font-weight: 600;
    color: #7a7d85;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: #c4a050;
    font-size: 8pt;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

/* ── Slider ───────────────────────────────────────────── */
QSlider::groove:horizontal {
    background-color: #1e2128;
    height: 4px;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background-color: #e8a020;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}

QSlider::sub-page:horizontal {
    background-color: #e8a020;
    border-radius: 2px;
}

/* ── Checkboxes ───────────────────────────────────────── */
QCheckBox {
    spacing: 8px;
    color: #b4b7bf;
}

QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #4a4d55;
    border-radius: 3px;
    background-color: #1a1d24;
}

QCheckBox::indicator:checked {
    background-color: #e8a020;
    border-color: #e8a020;
}

QCheckBox::indicator:hover {
    border-color: #8a8d95;
}

/* ── Radio Buttons ────────────────────────────────────── */
QRadioButton {
    spacing: 8px;
    color: #b4b7bf;
}

QRadioButton::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #4a4d55;
    border-radius: 7px;
    background-color: #1a1d24;
}

QRadioButton::indicator:checked {
    background-color: #e8a020;
    border-color: #e8a020;
}

/* ── Scroll Bars ──────────────────────────────────────── */
QScrollBar:vertical {
    background-color: #0f1014;
    width: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #2e3138;
    border-radius: 4px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4a4d55;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #0f1014;
    height: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background-color: #2e3138;
    border-radius: 4px;
    min-width: 24px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #4a4d55;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ── Status Bar ───────────────────────────────────────── */
QStatusBar {
    background-color: #080a0d;
    color: #6a6d75;
    border-top: 1px solid #1e2028;
    font-size: 8pt;
}

QStatusBar::item {
    border: none;
}

/* ── Menu Bar ─────────────────────────────────────────── */
QMenuBar {
    background-color: #0a0c10;
    color: #c4c7cf;
    border-bottom: 1px solid #1e2028;
    padding: 2px 0;
}

QMenuBar::item {
    padding: 4px 12px;
    background: transparent;
}

QMenuBar::item:selected {
    background-color: #1e2128;
    color: #e8a020;
}

QMenu {
    background-color: #1a1d24;
    color: #c4c7cf;
    border: 1px solid #2e3138;
    border-radius: 4px;
    padding: 4px 0;
}

QMenu::item {
    padding: 6px 24px;
}

QMenu::item:selected {
    background-color: #e8a02020;
    color: #e8a020;
}

QMenu::separator {
    height: 1px;
    background-color: #2e3138;
    margin: 4px 12px;
}

/* ── Tool Tips ────────────────────────────────────────── */
QToolTip {
    background-color: #1a1d24;
    color: #e4e7ef;
    border: 1px solid #e8a020;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 8pt;
}

/* ── Splitter ─────────────────────────────────────────── */
QSplitter::handle {
    background-color: #2a2d35;
    width: 1px;
}

/* ── Frame ────────────────────────────────────────────── */
QFrame[frameShape="4"],  /* HLine */
QFrame[frameShape="5"]   /* VLine */
{
    color: #2a2d35;
    background-color: #2a2d35;
}

/* ── Label ────────────────────────────────────────────── */
QLabel#section_label {
    color: #e8a020;
    font-weight: 700;
    font-size: 10pt;
    letter-spacing: 0.5px;
}

QLabel#dim_label {
    color: #5a5d65;
    font-size: 8pt;
}

QLabel#success_label {
    color: #50c850;
}

QLabel#error_label {
    color: #e05050;
}

QLabel#warning_label {
    color: #e8a020;
}
"""


def apply_dark_theme(app: QApplication):
    """Apply the AVCS dark theme to the application."""
    app.setStyleSheet(DARK_STYLESHEET)

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(15, 16, 20))
    palette.setColor(QPalette.WindowText, QColor(212, 212, 216))
    palette.setColor(QPalette.Base, QColor(20, 22, 28))
    palette.setColor(QPalette.AlternateBase, QColor(18, 20, 26))
    palette.setColor(QPalette.ToolTipBase, QColor(26, 29, 36))
    palette.setColor(QPalette.ToolTipText, QColor(228, 231, 239))
    palette.setColor(QPalette.Text, QColor(212, 212, 216))
    palette.setColor(QPalette.Button, QColor(30, 33, 40))
    palette.setColor(QPalette.ButtonText, QColor(196, 199, 207))
    palette.setColor(QPalette.BrightText, QColor(232, 160, 32))
    palette.setColor(QPalette.Link, QColor(232, 160, 32))
    palette.setColor(QPalette.Highlight, QColor(232, 160, 32, 60))
    palette.setColor(QPalette.HighlightedText, QColor(232, 160, 32))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(90, 93, 101))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(64, 67, 72))
    app.setPalette(palette)
