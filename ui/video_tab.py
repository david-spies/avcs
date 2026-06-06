"""
AVCS Video Conversion Tab
"""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QGroupBox, QFileDialog, QListWidget, QListWidgetItem,
    QCheckBox, QLineEdit, QScrollArea, QSizePolicy, QSplitter,
    QFrame, QMessageBox,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont

from ui.widgets import (
    SectionHeader, HDivider, DropZone, FileQueueItem,
    LogPanel, StatCard, StatusPill,
)
from utils.formats import (
    VIDEO_OUTPUT_FORMATS, VIDEO_QUALITY_PRESETS,
    RESOLUTION_PRESETS, build_video_filter, is_tvo, TVO_INFO,
)
from converters.workers import VideoConversionWorker, ConversionJob, ProbeWorker
from utils.ffmpeg_utils import ffmpeg_available, get_media_info


class VideoConversionTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._jobs = []          # list of ConversionJob
        self._file_items = {}    # path -> FileQueueItem
        self._worker = None
        self._probe_worker = None
        self._output_dir = ""
        self._pending_probe = []
        self._stats = {"queued": 0, "done": 0, "error": 0}
        self._setup_ui()

    # ── UI Setup ────────────────────────────────────────────────
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 12)
        root.setSpacing(12)

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setHandleWidth(1)

        # LEFT: File queue
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(8)

        left_layout.addWidget(SectionHeader("Input Files"))

        # Drop zone
        self._drop_zone = DropZone(accept_video=True, accept_audio=False)
        self._drop_zone.files_dropped.connect(self._on_drop_zone_activated)
        left_layout.addWidget(self._drop_zone)

        # Queue toolbar
        toolbar = QHBoxLayout()
        add_btn = QPushButton("+ Add Files")
        add_btn.clicked.connect(self._browse_files)
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._clear_queue)
        toolbar.addWidget(add_btn)
        toolbar.addWidget(clear_btn)
        toolbar.addStretch()

        queue_count_label = QLabel("0 files")
        queue_count_label.setObjectName("dim_label")
        self._queue_count_label = queue_count_label
        toolbar.addWidget(queue_count_label)
        left_layout.addLayout(toolbar)

        # Queue scroll area
        queue_scroll = QScrollArea()
        queue_scroll.setWidgetResizable(True)
        queue_scroll.setFrameShape(QFrame.NoFrame)
        queue_scroll.setStyleSheet("QScrollArea { border: 1px solid #1e2028; border-radius: 4px; }")
        self._queue_container = QWidget()
        self._queue_layout = QVBoxLayout(self._queue_container)
        self._queue_layout.setContentsMargins(4, 4, 4, 4)
        self._queue_layout.setSpacing(2)
        self._queue_layout.addStretch()
        queue_scroll.setWidget(self._queue_container)
        left_layout.addWidget(queue_scroll, 1)

        splitter.addWidget(left)

        # RIGHT: Settings + controls
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(10)
        right.setMaximumWidth(300)

        right_layout.addWidget(SectionHeader("Output Settings"))

        # Output format
        fmt_group = QGroupBox("Format")
        fmt_group_layout = QVBoxLayout(fmt_group)
        self._format_combo = QComboBox()
        self._format_combo.addItems(list(VIDEO_OUTPUT_FORMATS.keys()))
        fmt_group_layout.addWidget(self._format_combo)
        right_layout.addWidget(fmt_group)

        # Quality
        qual_group = QGroupBox("Quality")
        qual_layout = QVBoxLayout(qual_group)
        self._quality_combo = QComboBox()
        self._quality_combo.addItems(list(VIDEO_QUALITY_PRESETS.keys()))
        self._quality_combo.setCurrentText("Medium (CRF 23)")
        qual_layout.addWidget(self._quality_combo)
        right_layout.addWidget(qual_group)

        # Resolution
        res_group = QGroupBox("Resolution")
        res_layout = QVBoxLayout(res_group)
        self._resolution_combo = QComboBox()
        self._resolution_combo.addItems(list(RESOLUTION_PRESETS.keys()))
        res_layout.addWidget(self._resolution_combo)
        right_layout.addWidget(res_group)

        # Output folder
        out_group = QGroupBox("Output Folder")
        out_layout = QHBoxLayout(out_group)
        self._output_path_edit = QLineEdit()
        self._output_path_edit.setPlaceholderText("Same folder as input…")
        self._output_path_edit.setReadOnly(True)
        out_btn = QPushButton("Browse…")
        out_btn.setFixedWidth(70)
        out_btn.clicked.connect(self._browse_output)
        out_layout.addWidget(self._output_path_edit)
        out_layout.addWidget(out_btn)
        right_layout.addWidget(out_group)

        # TVO info banner
        self._tvo_banner = QLabel(
            "⚠  TVO file detected — Legacy TeVeo format.\nUsing extended compatibility mode.",
            self,
        )
        self._tvo_banner.setStyleSheet(
            "background:#2a1a3a; color:#a060e0; border:1px solid #4a2a6a; "
            "border-radius:4px; padding:6px 10px; font-size:8pt;"
        )
        self._tvo_banner.setWordWrap(True)
        self._tvo_banner.setVisible(False)
        right_layout.addWidget(self._tvo_banner)

        right_layout.addStretch()

        # Stats row
        stats_row = QHBoxLayout()
        self._stat_queued = StatCard("Queued", "0")
        self._stat_done = StatCard("Done", "0")
        self._stat_error = StatCard("Errors", "0")
        stats_row.addWidget(self._stat_queued)
        stats_row.addWidget(self._stat_done)
        stats_row.addWidget(self._stat_error)
        right_layout.addLayout(stats_row)

        # Action buttons
        self._convert_btn = QPushButton("▶  Start Conversion")
        self._convert_btn.setObjectName("primary_button")
        self._convert_btn.setMinimumHeight(36)
        self._convert_btn.clicked.connect(self._start_conversion)

        self._cancel_btn = QPushButton("✕  Cancel")
        self._cancel_btn.setObjectName("danger_button")
        self._cancel_btn.setMinimumHeight(36)
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self._cancel_conversion)

        right_layout.addWidget(self._convert_btn)
        right_layout.addWidget(self._cancel_btn)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        root.addWidget(splitter, 1)

        # Log panel
        self._log = LogPanel(self)
        root.addWidget(self._log)

        # ffmpeg warning
        if not ffmpeg_available():
            warn = QLabel(
                "⚠  ffmpeg not found. Please install ffmpeg to enable conversion.",
                self,
            )
            warn.setObjectName("warning_label")
            warn.setAlignment(Qt.AlignCenter)
            root.addWidget(warn)

    # ── File Management ──────────────────────────────────────────
    def _on_drop_zone_activated(self, paths):
        if not paths:
            self._browse_files()
        else:
            self._add_files(paths)

    def _browse_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Video Files", "", build_video_filter()
        )
        if paths:
            self._add_files(paths)

    def _add_files(self, paths):
        new_paths = [p for p in paths if p not in self._file_items]
        if not new_paths:
            return

        for path in new_paths:
            item = FileQueueItem(path, {})
            item.remove_requested.connect(self._remove_file)
            self._file_items[path] = item
            # Insert before the stretch
            self._queue_layout.insertWidget(self._queue_layout.count() - 1, item)

        self._pending_probe = new_paths[:]
        self._start_probe(new_paths)
        self._update_counts()
        self._check_tvo()

    def _remove_file(self, path):
        if path in self._file_items:
            item = self._file_items.pop(path)
            item.deleteLater()
        self._update_counts()
        self._check_tvo()

    def _clear_queue(self):
        for item in list(self._file_items.values()):
            item.deleteLater()
        self._file_items.clear()
        self._update_counts()
        self._check_tvo()
        self._reset_stats()

    def _update_counts(self):
        n = len(self._file_items)
        self._queue_count_label.setText(f"{n} file{'s' if n != 1 else ''}")
        self._stat_queued.set_value(str(n))

    def _check_tvo(self):
        has_tvo = any(is_tvo(p) for p in self._file_items)
        self._tvo_banner.setVisible(has_tvo)

    # ── Probing ──────────────────────────────────────────────────
    def _start_probe(self, paths):
        self._probe_worker = ProbeWorker(paths)
        self._probe_worker.file_probed.connect(self._on_file_probed)
        self._probe_worker.start()

    def _on_file_probed(self, path, info):
        if path in self._file_items:
            item = self._file_items[path]
            # Rebuild with info
            item.info = info
            # Quick update: just refresh status
            item.set_status("queued")

    # ── Output Folder ─────────────────────────────────────────────
    def _browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self._output_dir = folder
            self._output_path_edit.setText(folder)

    # ── Conversion ───────────────────────────────────────────────
    def _start_conversion(self):
        if not self._file_items:
            QMessageBox.warning(self, "No Files", "Please add video files to convert.")
            return
        if not ffmpeg_available():
            QMessageBox.critical(
                self, "ffmpeg Missing",
                "ffmpeg is required for conversion.\n\nInstall with:\n  sudo apt install ffmpeg"
            )
            return

        fmt_name = self._format_combo.currentText()
        fmt = VIDEO_OUTPUT_FORMATS[fmt_name]
        quality_name = self._quality_combo.currentText()
        quality = VIDEO_QUALITY_PRESETS[quality_name]
        res_name = self._resolution_combo.currentText()
        resolution = RESOLUTION_PRESETS[res_name]

        settings = {
            "vcodec": fmt["vcodec"],
            "acodec": fmt["acodec"],
            "crf": quality["crf"],
            "preset": quality["preset"],
            "resolution": resolution,
        }

        jobs = []
        for path in self._file_items:
            out_dir = self._output_dir or os.path.dirname(path)
            base, _ = os.path.splitext(os.path.basename(path))
            out_path = os.path.join(out_dir, f"{base}.{fmt['ext']}")
            jobs.append(ConversionJob(path, out_path, settings))
            self._file_items[path].set_status("queued")
            self._file_items[path].set_progress(0)

        self._reset_stats()
        self._stats["queued"] = len(jobs)
        self._stat_queued.set_value(str(len(jobs)))

        self._worker = VideoConversionWorker(jobs)
        self._worker.job_started.connect(self._on_job_started)
        self._worker.progress.connect(self._on_job_progress)
        self._worker.job_done.connect(self._on_job_done)
        self._worker.batch_done.connect(self._on_batch_done)
        self._worker.log_line.connect(self._log.append)

        self._convert_btn.setEnabled(False)
        self._cancel_btn.setEnabled(True)
        self._worker.start()

    def _cancel_conversion(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(5000)
        self._convert_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        self._log.append(">> Conversion cancelled by user.")

    def _on_job_started(self, idx, filename):
        paths = list(self._file_items.keys())
        if idx < len(paths):
            self._file_items[paths[idx]].set_status("converting")
        self._log.append(f">> Converting: {filename}")

    def _on_job_progress(self, idx, pct):
        paths = list(self._file_items.keys())
        if idx < len(paths):
            self._file_items[paths[idx]].set_progress(pct)

    def _on_job_done(self, idx, success, error):
        paths = list(self._file_items.keys())
        if idx < len(paths):
            status = "done" if success else "error"
            self._file_items[paths[idx]].set_status(status)
            if success:
                self._file_items[paths[idx]].set_progress(100)
                self._stats["done"] += 1
                self._stat_done.set_value(str(self._stats["done"]))
            else:
                self._stats["error"] += 1
                self._stat_error.set_value(str(self._stats["error"]))
                self._log.append(f"   ERROR: {error}")

    def _on_batch_done(self, succeeded, total):
        self._convert_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        self._log.append(f">> Batch complete: {succeeded}/{total} succeeded.")
        if succeeded == total:
            QMessageBox.information(
                self, "Conversion Complete",
                f"All {total} file(s) converted successfully."
            )
        else:
            QMessageBox.warning(
                self, "Conversion Finished",
                f"{succeeded}/{total} files converted.\n"
                f"{total - succeeded} error(s) — check the console log for details."
            )

    def _reset_stats(self):
        self._stats = {"queued": 0, "done": 0, "error": 0}
        self._stat_queued.set_value("0")
        self._stat_done.set_value("0")
        self._stat_error.set_value("0")
