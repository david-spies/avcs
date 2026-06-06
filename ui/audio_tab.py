"""
AVCS Audio Conversion Tab
"""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QGroupBox, QFileDialog, QScrollArea,
    QLineEdit, QFrame, QMessageBox, QSplitter,
)
from PyQt5.QtCore import Qt

from ui.widgets import (
    SectionHeader, DropZone, FileQueueItem, LogPanel, StatCard,
)
from utils.formats import (
    AUDIO_OUTPUT_FORMATS, AUDIO_BITRATE_PRESETS,
    build_audio_filter,
)
from converters.workers import AudioConversionWorker, ConversionJob, ProbeWorker
from utils.ffmpeg_utils import ffmpeg_available


class AudioConversionTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._file_items = {}
        self._worker = None
        self._output_dir = ""
        self._stats = {"queued": 0, "done": 0, "error": 0}
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 12)
        root.setSpacing(12)

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setHandleWidth(1)

        # LEFT
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(8)

        left_layout.addWidget(SectionHeader("Input Audio Files"))

        drop = DropZone(accept_video=False, accept_audio=True)
        drop.files_dropped.connect(self._on_drop)
        left_layout.addWidget(drop)

        toolbar = QHBoxLayout()
        add_btn = QPushButton("+ Add Files")
        add_btn.clicked.connect(self._browse)
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._clear)
        toolbar.addWidget(add_btn)
        toolbar.addWidget(clear_btn)
        toolbar.addStretch()
        self._count_label = QLabel("0 files")
        self._count_label.setObjectName("dim_label")
        toolbar.addWidget(self._count_label)
        left_layout.addLayout(toolbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #1e2028; border-radius: 4px; }")
        self._queue_container = QWidget()
        self._queue_layout = QVBoxLayout(self._queue_container)
        self._queue_layout.setContentsMargins(4, 4, 4, 4)
        self._queue_layout.setSpacing(2)
        self._queue_layout.addStretch()
        scroll.setWidget(self._queue_container)
        left_layout.addWidget(scroll, 1)
        splitter.addWidget(left)

        # RIGHT
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(10)
        right.setMaximumWidth(300)

        right_layout.addWidget(SectionHeader("Output Settings"))

        fmt_group = QGroupBox("Format")
        fmt_layout = QVBoxLayout(fmt_group)
        self._format_combo = QComboBox()
        self._format_combo.addItems(list(AUDIO_OUTPUT_FORMATS.keys()))
        fmt_layout.addWidget(self._format_combo)
        right_layout.addWidget(fmt_group)

        br_group = QGroupBox("Bitrate / Quality")
        br_layout = QVBoxLayout(br_group)
        self._bitrate_combo = QComboBox()
        self._bitrate_combo.addItems(list(AUDIO_BITRATE_PRESETS.keys()))
        br_layout.addWidget(self._bitrate_combo)
        right_layout.addWidget(br_group)

        out_group = QGroupBox("Output Folder")
        out_layout = QHBoxLayout(out_group)
        self._out_edit = QLineEdit()
        self._out_edit.setPlaceholderText("Same folder as input…")
        self._out_edit.setReadOnly(True)
        out_btn = QPushButton("Browse…")
        out_btn.setFixedWidth(70)
        out_btn.clicked.connect(self._browse_output)
        out_layout.addWidget(self._out_edit)
        out_layout.addWidget(out_btn)
        right_layout.addWidget(out_group)

        right_layout.addStretch()

        stats_row = QHBoxLayout()
        self._stat_q = StatCard("Queued", "0")
        self._stat_d = StatCard("Done", "0")
        self._stat_e = StatCard("Errors", "0")
        stats_row.addWidget(self._stat_q)
        stats_row.addWidget(self._stat_d)
        stats_row.addWidget(self._stat_e)
        right_layout.addLayout(stats_row)

        self._convert_btn = QPushButton("▶  Start Conversion")
        self._convert_btn.setObjectName("primary_button")
        self._convert_btn.setMinimumHeight(36)
        self._convert_btn.clicked.connect(self._start)

        self._cancel_btn = QPushButton("✕  Cancel")
        self._cancel_btn.setObjectName("danger_button")
        self._cancel_btn.setMinimumHeight(36)
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self._cancel)

        right_layout.addWidget(self._convert_btn)
        right_layout.addWidget(self._cancel_btn)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter, 1)

        self._log = LogPanel(self)
        root.addWidget(self._log)

        if not ffmpeg_available():
            warn = QLabel("⚠  ffmpeg not found. Please install ffmpeg.", self)
            warn.setObjectName("warning_label")
            warn.setAlignment(Qt.AlignCenter)
            root.addWidget(warn)

    def _on_drop(self, paths):
        if not paths:
            self._browse()
        else:
            self._add_files(paths)

    def _browse(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Audio Files", "", build_audio_filter())
        if paths:
            self._add_files(paths)

    def _add_files(self, paths):
        new = [p for p in paths if p not in self._file_items]
        for p in new:
            item = FileQueueItem(p, {})
            item.remove_requested.connect(self._remove)
            self._file_items[p] = item
            self._queue_layout.insertWidget(self._queue_layout.count() - 1, item)
        self._update_count()

    def _remove(self, path):
        if path in self._file_items:
            self._file_items.pop(path).deleteLater()
        self._update_count()

    def _clear(self):
        for item in list(self._file_items.values()):
            item.deleteLater()
        self._file_items.clear()
        self._update_count()

    def _update_count(self):
        n = len(self._file_items)
        self._count_label.setText(f"{n} file{'s' if n != 1 else ''}")
        self._stat_q.set_value(str(n))

    def _browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self._output_dir = folder
            self._out_edit.setText(folder)

    def _start(self):
        if not self._file_items:
            QMessageBox.warning(self, "No Files", "Please add audio files.")
            return
        if not ffmpeg_available():
            QMessageBox.critical(self, "ffmpeg Missing", "ffmpeg is required.")
            return

        fmt_name = self._format_combo.currentText()
        fmt = AUDIO_OUTPUT_FORMATS[fmt_name]
        br_name = self._bitrate_combo.currentText()
        bitrate = AUDIO_BITRATE_PRESETS[br_name]

        settings = {"acodec": fmt["acodec"], "bitrate": bitrate}

        jobs = []
        for path in self._file_items:
            out_dir = self._output_dir or os.path.dirname(path)
            base, _ = os.path.splitext(os.path.basename(path))
            out_path = os.path.join(out_dir, f"{base}.{fmt['ext']}")
            jobs.append(ConversionJob(path, out_path, settings))
            self._file_items[path].set_status("queued")
            self._file_items[path].set_progress(0)

        self._stats = {"queued": len(jobs), "done": 0, "error": 0}
        self._stat_q.set_value(str(len(jobs)))
        self._stat_d.set_value("0")
        self._stat_e.set_value("0")

        self._worker = AudioConversionWorker(jobs)
        self._worker.job_started.connect(lambda i, f: (
            self._file_items[list(self._file_items.keys())[i]].set_status("converting")
            if i < len(self._file_items) else None
        ))
        self._worker.progress.connect(lambda i, p: (
            self._file_items[list(self._file_items.keys())[i]].set_progress(p)
            if i < len(self._file_items) else None
        ))
        self._worker.job_done.connect(self._on_job_done)
        self._worker.batch_done.connect(self._on_batch_done)
        self._worker.log_line.connect(self._log.append)

        self._convert_btn.setEnabled(False)
        self._cancel_btn.setEnabled(True)
        self._worker.start()

    def _cancel(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(5000)
        self._convert_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)

    def _on_job_done(self, idx, success, error):
        paths = list(self._file_items.keys())
        if idx < len(paths):
            self._file_items[paths[idx]].set_status("done" if success else "error")
            if success:
                self._file_items[paths[idx]].set_progress(100)
                self._stats["done"] += 1
                self._stat_d.set_value(str(self._stats["done"]))
            else:
                self._stats["error"] += 1
                self._stat_e.set_value(str(self._stats["error"]))
                self._log.append(f"ERROR: {error}")

    def _on_batch_done(self, succeeded, total):
        self._convert_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        self._log.append(f">> Audio batch complete: {succeeded}/{total}")
        if succeeded == total:
            QMessageBox.information(self, "Done", f"All {total} audio file(s) converted.")
        else:
            QMessageBox.warning(
                self, "Finished With Errors",
                f"{succeeded}/{total} files converted.\nCheck log for details."
            )
