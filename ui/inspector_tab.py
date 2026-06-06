"""
AVCS Media Inspector Tab
Displays detailed media file information.
"""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QTreeWidget, QTreeWidgetItem, QFrame,
    QTextEdit, QSplitter,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.widgets import SectionHeader, DropZone
from utils.ffmpeg_utils import get_media_info, ffprobe_available, format_size
from utils.formats import build_all_filter, is_tvo


class MediaInspectorTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 12)
        root.setSpacing(12)

        root.addWidget(SectionHeader("Media File Inspector"))

        if not ffprobe_available():
            warn = QLabel(
                "⚠  ffprobe not found. Install ffmpeg to enable media inspection.",
                self,
            )
            warn.setObjectName("warning_label")
            warn.setAlignment(Qt.AlignCenter)
            root.addWidget(warn)

        # Drop / browse
        drop_row = QHBoxLayout()
        drop = DropZone(accept_video=True, accept_audio=True)
        drop._text_label.setText("Drop any media file to inspect")
        drop.files_dropped.connect(self._on_drop)
        drop.setFixedHeight(60)

        browse_btn = QPushButton("Browse…")
        browse_btn.setFixedWidth(100)
        browse_btn.setMinimumHeight(60)
        browse_btn.clicked.connect(self._browse)

        drop_row.addWidget(drop)
        drop_row.addWidget(browse_btn)
        root.addLayout(drop_row)

        # Splitter: tree left, raw JSON right
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        # Left: formatted tree
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Property", "Value"])
        self._tree.setColumnWidth(0, 200)
        self._tree.setAlternatingRowColors(True)
        self._tree.setRootIsDecorated(True)
        self._tree.setStyleSheet(
            "QTreeWidget { border: 1px solid #1e2028; border-radius: 4px; }"
        )
        splitter.addWidget(self._tree)

        # Right: raw output
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(6)

        right_layout.addWidget(SectionHeader("Raw Info"))

        self._raw_text = QTextEdit()
        self._raw_text.setReadOnly(True)
        self._raw_text.setStyleSheet(
            "QTextEdit { background: #080a0d; color: #8080a0; "
            "font-family: 'Consolas', monospace; font-size: 8pt; "
            "border: 1px solid #1e2028; border-radius: 4px; }"
        )
        right_layout.addWidget(self._raw_text)
        splitter.addWidget(right_widget)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        root.addWidget(splitter, 1)

    def _on_drop(self, paths):
        if not paths:
            self._browse()
        elif paths:
            self._inspect(paths[0])

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Media File", "", build_all_filter())
        if path:
            self._inspect(path)

    def _inspect(self, path: str):
        self._tree.clear()
        self._raw_text.clear()

        info = get_media_info(path)
        self._populate_tree(info)
        self._populate_raw(info)

    def _populate_tree(self, info: dict):
        tree = self._tree

        def add(parent, key, val):
            item = QTreeWidgetItem(parent, [key, str(val)])
            item.setForeground(0, tree.palette().link())
            return item

        # File
        file_item = QTreeWidgetItem(tree, ["📁 File", ""])
        file_item.setExpanded(True)
        add(file_item, "Name", info.get("filename", ""))
        add(file_item, "Size", format_size(info.get("size_bytes", 0)))
        add(file_item, "Duration", info.get("duration_str", "Unknown"))
        add(file_item, "Format", info.get("format_name", "Unknown"))
        add(file_item, "Bit Rate", info.get("bit_rate", "Unknown"))

        if info.get("is_tvo"):
            tvo_item = QTreeWidgetItem(tree, ["📼 TVO Legacy", ""])
            tvo_item.setExpanded(True)
            tvo_item.setForeground(0, tree.palette().brightText())
            add(tvo_item, "Format", "TeVeo VIDiO Suite / TeveoLive")
            add(tvo_item, "Era", "Late 1990s – Early 2000s")
            add(tvo_item, "Compatibility", "Legacy — requires extended decode")
            add(tvo_item, "Recommendation", "Convert to MP4 (H.264)")

        # Video stream
        vid = info.get("video")
        if vid:
            v_item = QTreeWidgetItem(tree, ["🎬 Video Stream", ""])
            v_item.setExpanded(True)
            add(v_item, "Codec", vid.get("codec", "Unknown"))
            add(v_item, "Resolution", f"{vid.get('width', 0)} × {vid.get('height', 0)}")
            add(v_item, "Frame Rate", f"{vid.get('fps', 'Unknown')} fps")
            add(v_item, "Pixel Format", vid.get("pix_fmt", "Unknown"))
        else:
            QTreeWidgetItem(tree, ["🎬 Video Stream", "None / Not detected"])

        # Audio stream
        aud = info.get("audio")
        if aud:
            a_item = QTreeWidgetItem(tree, ["🔊 Audio Stream", ""])
            a_item.setExpanded(True)
            add(a_item, "Codec", aud.get("codec", "Unknown"))
            add(a_item, "Channels", str(aud.get("channels", 0)))
            add(a_item, "Sample Rate", f"{aud.get('sample_rate', 'Unknown')} Hz")
            add(a_item, "Bit Rate", aud.get("bit_rate", "Unknown"))
        else:
            QTreeWidgetItem(tree, ["🔊 Audio Stream", "None / Not detected"])

    def _populate_raw(self, info: dict):
        lines = []
        lines.append(f"File: {info.get('path', '')}")
        lines.append(f"Size: {format_size(info.get('size_bytes', 0))}")
        lines.append(f"Duration: {info.get('duration_str', 'Unknown')}")
        lines.append(f"Format: {info.get('format_name', 'Unknown')}")
        lines.append(f"Bit Rate: {info.get('bit_rate', 'Unknown')}")
        lines.append("")

        if info.get("is_tvo"):
            lines.append("═" * 40)
            lines.append("LEGACY TVO FORMAT DETECTED")
            lines.append("Developer: TeVeo Inc. (TeveoLive)")
            lines.append("Era: Late 1990s – Early 2000s")
            lines.append("Use the TVO tab for best conversion results.")
            lines.append("═" * 40)
            lines.append("")

        vid = info.get("video")
        if vid:
            lines.append("[Video Stream]")
            for k, v in vid.items():
                lines.append(f"  {k}: {v}")
            lines.append("")

        aud = info.get("audio")
        if aud:
            lines.append("[Audio Stream]")
            for k, v in aud.items():
                lines.append(f"  {k}: {v}")

        self._raw_text.setPlainText("\n".join(lines))
