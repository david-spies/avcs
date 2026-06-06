"""
AVCS UI Widgets
Reusable custom widgets used across the application.
"""

import os
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QFrame, QProgressBar, QSizePolicy, QAbstractItemView,
    QListWidget, QListWidgetItem, QStyle,
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QMimeData
from PyQt5.QtGui import QColor, QFont, QIcon, QPainter, QPen, QBrush, QDragEnterEvent, QDropEvent

from utils.ffmpeg_utils import format_size
from utils.formats import is_video, is_audio, is_tvo


# ── Section Header ────────────────────────────────────────────────
class SectionHeader(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text.upper(), parent)
        self.setObjectName("section_label")
        font = QFont()
        font.setPointSize(9)
        font.setWeight(QFont.Bold)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 1.0)
        self.setFont(font)


# ── Horizontal Divider ────────────────────────────────────────────
class HDivider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
        self.setFixedHeight(1)
        self.setStyleSheet("background-color: #1e2028; border: none;")


# ── Status Pill ───────────────────────────────────────────────────
class StatusPill(QLabel):
    STATUS_COLORS = {
        "pending":    ("#4a4d55", "#9a9da5"),
        "probing":    ("#2a3a5a", "#6090e0"),
        "queued":     ("#2a3a2a", "#60a060"),
        "converting": ("#3a2a10", "#e8a020"),
        "done":       ("#1a3a1a", "#50c850"),
        "error":      ("#3a1a1a", "#e05050"),
        "cancelled":  ("#2a2a2a", "#707070"),
        "tvo":        ("#2a1a3a", "#a060e0"),
    }

    def __init__(self, status: str = "pending", parent=None):
        super().__init__(parent)
        self.setStatus(status)
        self.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(7)
        font.setWeight(QFont.Bold)
        self.setFont(font)
        self.setFixedSize(80, 20)

    def setStatus(self, status: str):
        bg, fg = self.STATUS_COLORS.get(status, self.STATUS_COLORS["pending"])
        self.setText(status.upper())
        self.setStyleSheet(
            f"background-color: {bg}; color: {fg}; "
            f"border-radius: 10px; padding: 0 6px; font-weight: 700; font-size: 7pt;"
        )


# ── Drop Zone ────────────────────────────────────────────────────
class DropZone(QWidget):
    """A widget that accepts drag-and-drop of media files."""

    files_dropped = pyqtSignal(list)

    def __init__(self, accept_video: bool = True, accept_audio: bool = True, parent=None):
        super().__init__(parent)
        self.accept_video = accept_video
        self.accept_audio = accept_audio
        self.setAcceptDrops(True)
        self._hover = False
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self._icon_label = QLabel("⬇", self)
        self._icon_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(18)
        self._icon_label.setFont(font)
        self._icon_label.setStyleSheet("color: #3a3d45;")

        self._text_label = QLabel("Drop files here or click to browse", self)
        self._text_label.setAlignment(Qt.AlignCenter)
        self._text_label.setStyleSheet("color: #5a5d65; font-size: 9pt;")

        layout.addWidget(self._icon_label)
        layout.addWidget(self._text_label)

        self._update_style(False)

    def _update_style(self, hover: bool):
        if hover:
            self.setStyleSheet(
                "border: 2px dashed #e8a020; border-radius: 8px; background-color: #1e2010;"
            )
            self._icon_label.setStyleSheet("color: #e8a020;")
            self._text_label.setStyleSheet("color: #e8a020; font-size: 9pt;")
        else:
            self.setStyleSheet(
                "border: 2px dashed #2e3138; border-radius: 8px; background-color: #0c0e12;"
            )
            self._icon_label.setStyleSheet("color: #3a3d45;")
            self._text_label.setStyleSheet("color: #5a5d65; font-size: 9pt;")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._hover = True
            self._update_style(True)

    def dragLeaveEvent(self, event):
        self._hover = False
        self._update_style(False)

    def dropEvent(self, event: QDropEvent):
        self._hover = False
        self._update_style(False)
        paths = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path):
                ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
                if (self.accept_video and is_video(path)) or (self.accept_audio and is_audio(path)):
                    paths.append(path)
        if paths:
            self.files_dropped.emit(paths)
        event.acceptProposedAction()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.files_dropped.emit([])   # signal with empty = trigger browse dialog


# ── File Queue Item ───────────────────────────────────────────────
class FileQueueItem(QWidget):
    """One row in the file queue list."""

    remove_requested = pyqtSignal(str)

    def __init__(self, path: str, info: dict = None, parent=None):
        super().__init__(parent)
        self.path = path
        self.info = info or {}

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # TVO badge
        if is_tvo(path):
            tvo_badge = QLabel("TVO", self)
            tvo_badge.setFixedSize(32, 18)
            tvo_badge.setAlignment(Qt.AlignCenter)
            tvo_badge.setStyleSheet(
                "background:#2a1a3a; color:#a060e0; border-radius:9px; "
                "font-size:7pt; font-weight:700;"
            )
            layout.addWidget(tvo_badge)

        # Filename
        name_label = QLabel(os.path.basename(path), self)
        name_label.setStyleSheet("color: #d4d4d8; font-size: 9pt;")
        name_label.setMinimumWidth(160)
        name_label.setMaximumWidth(260)
        layout.addWidget(name_label)

        # Media info (if available)
        if info:
            details = []
            vid = info.get("video")
            aud = info.get("audio")
            if vid:
                details.append(f"{vid['width']}×{vid['height']}")
                details.append(f"{vid['fps']} fps")
            if aud:
                details.append(aud.get("codec", ""))
            dur = info.get("duration_str", "")
            if dur and dur != "Unknown":
                details.append(dur)
            size = info.get("size_bytes", 0)
            if size:
                details.append(format_size(size))

            detail_label = QLabel("  ·  ".join(d for d in details if d), self)
            detail_label.setStyleSheet("color: #5a5d65; font-size: 8pt;")
            layout.addWidget(detail_label)

        layout.addStretch()

        # Status pill
        self.status_pill = StatusPill("queued", self)
        layout.addWidget(self.status_pill)

        # Progress
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedWidth(100)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        # Remove button
        remove_btn = QPushButton("✕", self)
        remove_btn.setFixedSize(20, 20)
        remove_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #4a4d55; border: none; font-size: 10pt; }"
            "QPushButton:hover { color: #e05050; }"
        )
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.path))
        layout.addWidget(remove_btn)

    def set_status(self, status: str):
        self.status_pill.setStatus(status)

    def set_progress(self, value: int):
        self.progress_bar.setValue(value)


# ── Log Panel ────────────────────────────────────────────────────
class LogPanel(QWidget):
    """
    Console log panel — always visible, collapsible for space.
    Auto-expands and highlights red on error lines.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        from PyQt5.QtWidgets import QTextEdit
        self._expanded = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar
        header = QWidget(self)
        header.setStyleSheet("background: #0c0e14; border-top: 1px solid #1e2028;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 3, 8, 3)

        self._toggle_btn = QPushButton("▼  Console Log", header)
        self._toggle_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #5a6070; border: none; "
            "font-size: 8pt; text-align: left; font-family: monospace; }"
            "QPushButton:hover { color: #9aa0b0; }"
        )
        self._toggle_btn.clicked.connect(self._toggle)
        header_layout.addWidget(self._toggle_btn)
        header_layout.addStretch()

        copy_btn = QPushButton("Copy", header)
        copy_btn.setFixedHeight(20)
        copy_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #4a4d55; border: 1px solid #2e3138; "
            "border-radius: 3px; font-size: 7pt; padding: 0 8px; }"
            "QPushButton:hover { color: #7a7d85; }"
        )
        copy_btn.clicked.connect(self._copy)

        clear_btn = QPushButton("Clear", header)
        clear_btn.setFixedHeight(20)
        clear_btn.setStyleSheet(copy_btn.styleSheet())
        clear_btn.clicked.connect(self.clear)

        header_layout.addWidget(copy_btn)
        header_layout.addWidget(clear_btn)
        layout.addWidget(header)

        self._log_area = QTextEdit(self)
        self._log_area.setReadOnly(True)
        self._log_area.setMinimumHeight(150)
        self._log_area.setMaximumHeight(260)
        self._log_area.setStyleSheet(
            "QTextEdit { background-color: #07090c; color: #50b850; "
            "font-family: 'Consolas', 'Fira Code', 'Courier New', monospace; "
            "font-size: 8pt; border: none; padding: 4px 8px; }"
        )
        layout.addWidget(self._log_area)

    def _toggle(self):
        self._expanded = not self._expanded
        self._log_area.setVisible(self._expanded)
        self._toggle_btn.setText(
            f"{'▼' if self._expanded else '▶'}  Console Log"
        )

    def _copy(self):
        from PyQt5.QtWidgets import QApplication
        QApplication.clipboard().setText(self._log_area.toPlainText())

    def clear(self):
        self._log_area.clear()

    def append(self, text: str):
        """Append a line; color errors red and auto-expand."""
        from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor
        if not text.strip():
            return

        # Detect error / warning lines
        tl = text.lower()
        is_error   = any(k in tl for k in ("error", "✗", "failed", "invalid", "no such", "unable", "cannot"))
        is_warning = any(k in tl for k in ("warn", "stage", "✓"))
        is_cmd     = text.strip().startswith("CMD:")

        fmt = QTextCharFormat()
        if is_error:
            fmt.setForeground(QColor("#e05050"))
            # Auto-expand on errors so users see them immediately
            if not self._expanded:
                self._expanded = True
                self._log_area.setVisible(True)
                self._toggle_btn.setText("▼  Console Log")
        elif is_warning:
            fmt.setForeground(QColor("#e8a020"))
        elif is_cmd:
            fmt.setForeground(QColor("#3a6080"))
        else:
            fmt.setForeground(QColor("#50b850"))

        cursor = self._log_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text + "\n", fmt)
        self._log_area.setTextCursor(cursor)

        # Auto-scroll
        sb = self._log_area.verticalScrollBar()
        sb.setValue(sb.maximum())


# ── Stat Card ────────────────────────────────────────────────────
class StatCard(QWidget):
    def __init__(self, title: str, value: str = "—", parent=None):
        super().__init__(parent)
        self.setFixedHeight(54)
        self.setStyleSheet(
            "background-color: #12141a; border: 1px solid #1e2028; border-radius: 6px;"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(2)

        self._title_label = QLabel(title.upper(), self)
        self._title_label.setStyleSheet(
            "color: #4a4d55; font-size: 7pt; font-weight: 700; letter-spacing: 0.5px; background: transparent; border: none;"
        )

        self._value_label = QLabel(value, self)
        self._value_label.setStyleSheet(
            "color: #e8a020; font-size: 12pt; font-weight: 700; background: transparent; border: none;"
        )

        layout.addWidget(self._title_label)
        layout.addWidget(self._value_label)

    def set_value(self, value: str):
        self._value_label.setText(value)
