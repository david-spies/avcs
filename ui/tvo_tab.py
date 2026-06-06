"""
AVCS TVO Legacy Converter Tab
Dedicated interface for converting legacy TeVeo VIDiO Suite .tvo files.
"""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QFileDialog, QScrollArea, QLineEdit, QFrame,
    QMessageBox, QComboBox, QTextEdit, QSplitter,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.widgets import SectionHeader, DropZone, FileQueueItem, LogPanel, StatCard
from utils.formats import VIDEO_OUTPUT_FORMATS, VIDEO_QUALITY_PRESETS, TVO_INFO
from converters.workers import VideoConversionWorker, ConversionJob
from utils.ffmpeg_utils import ffmpeg_available


TVO_ABOUT_TEXT = """
TeVeo VIDiO Suite — Legacy Format Overview
═══════════════════════════════════════════

Developer:     TeVeo Inc. / Orbisoft (WebCamDV)
Era:           Late 1990s – Early 2000s
Format type:   Proprietary container, legacy webcam/streaming

What are .TVO files?
─────────────────────
TVO files are video recordings created by TeveoLive, an early
internet webcam broadcasting application developed by Teveo Inc.
These files were used to capture and store live webcam streams,
often for personal broadcasts or security monitoring.

Why are they hard to open?
──────────────────────────
• TeveoLive software has been discontinued for over 20 years
• The original 16-bit / 32-bit software won't run on modern 64-bit OS
• They use obsolete compression (Indeo, Cinepak, or MJPEG variants)
• No native support in modern players (VLC, Windows Media Player, etc.)

How AVCS converts TVO files
─────────────────────────────
AVCS uses ffmpeg with extended legacy compatibility flags:
  -err_detect ignore_err   → tolerates container errors
  -fflags +genpts+igndts   → regenerates timestamps
  
This extracts the embedded video stream and re-encodes it to a
modern format (MP4/H.264 recommended for best compatibility).

Quality note:  Original TVO recordings were low-resolution webcam
footage (typically 160×120 or 320×240). Upscaling is not recommended.

Recommended output:  MP4 (H.264), Medium quality (CRF 23)
"""


class TvoConverterTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._file_items = {}
        self._worker = None
        self._output_dir = ""
        self._stats = {"queued": 0, "done": 0, "error": 0}
        self._failed_errors = {}   # filename -> full ffmpeg stderr
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 12)
        root.setSpacing(12)

        # Header banner
        banner = QWidget(self)
        banner.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #1a0a2a, stop:1 #0e0a1a); "
            "border: 1px solid #4a2a6a; border-radius: 6px;"
        )
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(16, 10, 16, 10)

        tvo_icon = QLabel("📼", banner)
        tvo_icon.setFont(QFont("", 24))
        tvo_icon.setStyleSheet("background: transparent; border: none;")
        banner_layout.addWidget(tvo_icon)

        banner_text_layout = QVBoxLayout()
        title_lbl = QLabel("TeVeo VIDiO Suite — Legacy TVO Converter", banner)
        title_lbl.setStyleSheet(
            "color: #c080f0; font-weight: 700; font-size: 11pt; background: transparent; border: none;"
        )
        sub_lbl = QLabel(
            "Convert obsolete .TVO webcam recordings to modern formats (MP4, MKV, AVI, MOV)",
            banner,
        )
        sub_lbl.setStyleSheet(
            "color: #7a5a9a; font-size: 8pt; background: transparent; border: none;"
        )
        banner_text_layout.addWidget(title_lbl)
        banner_text_layout.addWidget(sub_lbl)
        banner_layout.addLayout(banner_text_layout)
        banner_layout.addStretch()

        root.addWidget(banner)

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setHandleWidth(1)

        # LEFT: file list
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(8)

        left_layout.addWidget(SectionHeader("TVO Input Files"))

        drop = DropZone(accept_video=True, accept_audio=False)
        drop._text_label.setText("Drop .TVO files here or click to browse")
        drop.files_dropped.connect(self._on_drop)
        left_layout.addWidget(drop)

        toolbar = QHBoxLayout()
        add_btn = QPushButton("+ Add TVO Files")
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

        # RIGHT: settings + info
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(10)
        right.setMaximumWidth(320)

        right_layout.addWidget(SectionHeader("Conversion Settings"))

        fmt_group = QGroupBox("Output Format")
        fmt_layout = QVBoxLayout(fmt_group)
        self._format_combo = QComboBox()
        # Show only widely compatible formats for TVO
        tvo_formats = ["MP4 (H.264)", "MKV", "AVI", "MOV", "MP4 (H.265)"]
        self._format_combo.addItems(tvo_formats)
        fmt_hint = QLabel("MP4 (H.264) recommended for TVO files")
        fmt_hint.setStyleSheet("color: #5a5d65; font-size: 8pt;")
        fmt_layout.addWidget(self._format_combo)
        fmt_layout.addWidget(fmt_hint)
        right_layout.addWidget(fmt_group)

        qual_group = QGroupBox("Quality")
        qual_layout = QVBoxLayout(qual_group)
        self._quality_combo = QComboBox()
        self._quality_combo.addItems(list(VIDEO_QUALITY_PRESETS.keys()))
        self._quality_combo.setCurrentText("Medium (CRF 23)")
        qual_hint = QLabel("TVO source is low-res; medium quality is optimal")
        qual_hint.setStyleSheet("color: #5a5d65; font-size: 8pt;")
        qual_layout.addWidget(self._quality_combo)
        qual_layout.addWidget(qual_hint)
        right_layout.addWidget(qual_group)

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

        # About panel
        about_group = QGroupBox("About TVO Format")
        about_layout = QVBoxLayout(about_group)
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setPlainText(TVO_ABOUT_TEXT)
        about_text.setStyleSheet(
            "QTextEdit { background: #0a0a10; color: #7a7d90; font-family: 'Consolas', monospace; "
            "font-size: 8pt; border: none; }"
        )
        about_text.setFixedHeight(200)
        about_layout.addWidget(about_text)
        right_layout.addWidget(about_group)

        right_layout.addStretch()

        stats_row = QHBoxLayout()
        self._stat_q = StatCard("Queued", "0")
        self._stat_d = StatCard("Done", "0")
        self._stat_e = StatCard("Errors", "0")
        stats_row.addWidget(self._stat_q)
        stats_row.addWidget(self._stat_d)
        stats_row.addWidget(self._stat_e)
        right_layout.addLayout(stats_row)

        self._convert_btn = QPushButton("▶  Convert TVO → MP4")
        self._convert_btn.setObjectName("primary_button")
        self._convert_btn.setMinimumHeight(36)
        self._convert_btn.clicked.connect(self._start)
        self._convert_btn.setStyleSheet(
            "QPushButton#primary_button { background-color: #7030c0; color: #ffffff; } "
            "QPushButton#primary_button:hover { background-color: #8040d0; }"
        )

        self._cancel_btn = QPushButton("✕  Cancel")
        self._cancel_btn.setObjectName("danger_button")
        self._cancel_btn.setMinimumHeight(36)
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self._cancel)

        right_layout.addWidget(self._convert_btn)
        right_layout.addWidget(self._cancel_btn)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        root.addWidget(splitter, 1)

        self._log = LogPanel(self)
        root.addWidget(self._log)

    def _on_drop(self, paths):
        if not paths:
            self._browse()
        else:
            tvo_paths = [p for p in paths if p.lower().endswith(".tvo")]
            non_tvo = [p for p in paths if not p.lower().endswith(".tvo")]
            if non_tvo:
                self._log.append(
                    f"Note: {len(non_tvo)} non-TVO file(s) skipped on this tab. "
                    "Use the Video tab for other formats."
                )
            if tvo_paths:
                self._add_files(tvo_paths)

    def _browse(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select TVO Files", "",
            "TVO Files (*.tvo);;All Video Files (*.tvo *.mp4 *.avi *.mkv);;All Files (*.*)"
        )
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
            QMessageBox.warning(self, "No Files", "Please add TVO files to convert.")
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

        settings = {
            "vcodec": fmt["vcodec"],
            "acodec": fmt["acodec"],
            "crf": quality["crf"],
            "preset": quality["preset"],
            "resolution": None,
        }

        jobs = []
        for path in self._file_items:
            out_dir = self._output_dir or os.path.dirname(path)
            base, _ = os.path.splitext(os.path.basename(path))
            out_path = os.path.join(out_dir, f"{base}_converted.{fmt['ext']}")
            jobs.append(ConversionJob(path, out_path, settings))
            self._file_items[path].set_status("queued")
            self._file_items[path].set_progress(0)

        self._stats = {"queued": len(jobs), "done": 0, "error": 0}
        self._failed_errors = {}
        self._stat_q.set_value(str(len(jobs)))
        self._stat_d.set_value("0")
        self._stat_e.set_value("0")

        self._worker = VideoConversionWorker(jobs)
        self._worker.job_started.connect(self._on_start)
        self._worker.progress.connect(self._on_progress)
        self._worker.job_done.connect(self._on_done)
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

    def _on_start(self, idx, fname):
        paths = list(self._file_items.keys())
        if idx < len(paths):
            self._file_items[paths[idx]].set_status("converting")
        self._log.append(f">> TVO Converting: {fname}")

    def _on_progress(self, idx, pct):
        paths = list(self._file_items.keys())
        if idx < len(paths):
            self._file_items[paths[idx]].set_progress(pct)

    def _on_done(self, idx, success, error):
        paths = list(self._file_items.keys())
        if idx < len(paths):
            path = paths[idx]
            self._file_items[path].set_status("done" if success else "error")
            if success:
                self._file_items[path].set_progress(100)
                self._stats["done"] += 1
                self._stat_d.set_value(str(self._stats["done"]))
            else:
                self._stats["error"] += 1
                self._stat_e.set_value(str(self._stats["error"]))
                # Store full error keyed by filename for the diagnostic dialog
                self._failed_errors[os.path.basename(path)] = error

    def _on_batch_done(self, succeeded, total):
        self._convert_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        self._log.append(f">> TVO batch complete: {succeeded}/{total}")

        if succeeded == total:
            QMessageBox.information(
                self, "TVO Conversion Complete",
                f"All {total} TVO file(s) converted successfully!"
            )
        else:
            self._show_tvo_diagnostic(succeeded, total)

    def _show_tvo_diagnostic(self, succeeded: int, total: int):
        """Show a detailed diagnostic dialog with ffmpeg output and fix suggestions."""
        from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QTabWidget, QTextEdit

        dlg = QDialog(self)
        dlg.setWindowTitle("TVO Conversion — Diagnostic Report")
        dlg.setMinimumSize(680, 480)
        dlg.setStyleSheet(self.styleSheet())

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(10)

        # Summary header
        errors = total - succeeded
        summary_color = "#e05050" if succeeded == 0 else "#e8a020"
        summary = QLabel(
            f"<b style='color:{summary_color}'>{errors} of {total} TVO file(s) failed to convert.</b>"
            + (f"  <span style='color:#50b850'>{succeeded} succeeded.</span>" if succeeded else ""),
            dlg
        )
        summary.setTextFormat(Qt.RichText)
        layout.addWidget(summary)

        tabs = QTabWidget(dlg)

        # ── Tab 1: What went wrong ──
        why_text = QTextEdit()
        why_text.setReadOnly(True)
        why_text.setStyleSheet(
            "QTextEdit { background:#07090c; color:#c0c8d8; font-family:'Consolas',monospace; "
            "font-size:8.5pt; border:none; padding:8px; }"
        )
        why_lines = []
        for fname, err in self._failed_errors.items():
            why_lines.append(f"FILE: {fname}")
            why_lines.append("─" * 60)
            # Show last 30 meaningful lines from ffmpeg output
            relevant = [l for l in err.splitlines() if l.strip()][-30:]
            why_lines.extend(relevant)
            why_lines.append("")
        why_text.setPlainText("\n".join(why_lines) if why_lines else "No error detail captured.")
        tabs.addTab(why_text, "  ffmpeg Output  ")

        # ── Tab 2: Likely causes & fixes ──
        fix_text = QTextEdit()
        fix_text.setReadOnly(True)
        fix_text.setStyleSheet(why_text.styleSheet())

        # Analyse the error text to give targeted advice
        all_errors = "\n".join(self._failed_errors.values()).lower()
        causes = []

        if "invalid data" in all_errors or "moov atom not found" in all_errors:
            causes.append((
                "Container corruption / truncated file",
                "The TVO file's container header is damaged. "
                "This sometimes happens with recordings that were interrupted.\n"
                "→ Try opening the file in a hex editor to verify it starts with 'RIFF'.\n"
                "→ If it does NOT start with RIFF, the file may not be a valid TVO at all."
            ))
        if "no such decoder" in all_errors or "decoder" in all_errors or "codec not" in all_errors:
            causes.append((
                "Missing codec — ffmpeg not built with Indeo/Cinepak support",
                "Some Linux ffmpeg packages omit proprietary/patent-encumbered codecs.\n"
                "→ Install the full ffmpeg from the official builds:\n"
                "     sudo apt install ffmpeg   (Ubuntu/Debian)\n"
                "  or download a static build from https://johnvansickle.com/ffmpeg/\n"
                "→ Verify Indeo support:  ffmpeg -codecs | grep -i indeo"
            ))
        if "permission" in all_errors or "access" in all_errors:
            causes.append((
                "File permission error",
                "AVCS cannot read the input file or write to the output folder.\n"
                "→ Check file permissions:  ls -l /path/to/file.tvo\n"
                "→ Try copying the TVO file to your home folder first."
            ))
        if "pipe" in all_errors or "broken" in all_errors:
            causes.append((
                "Process terminated unexpectedly",
                "ffmpeg crashed mid-conversion. This can happen with deeply corrupted files.\n"
                "→ Check available disk space: df -h\n"
                "→ Try converting to a different output format (e.g. MKV instead of MP4)."
            ))
        if not causes:
            causes.append((
                "Unrecognised container / truly proprietary variant",
                "None of AVCS's 5 decode stages could extract a video stream.\n"
                "This TVO file may use an unusual codec or container variant.\n"
                "→ Run ffprobe directly and paste the output in the console log:\n"
                "     ffprobe -v error -show_streams yourfile.tvo\n"
                "→ Try MediaInfo (GUI tool) to inspect what codec is embedded.\n"
                "→ If the file plays in VLC: File → Convert → MP4, then re-add to AVCS."
            ))

        fix_lines = ["LIKELY CAUSES & SUGGESTED FIXES\n" + "═"*50 + "\n"]
        for i, (title, detail) in enumerate(causes, 1):
            fix_lines.append(f"{i}. {title}")
            fix_lines.append("-" * 40)
            fix_lines.append(detail)
            fix_lines.append("")

        fix_lines += [
            "═" * 50,
            "GENERAL TIPS FOR STUBBORN TVO FILES",
            "─" * 40,
            "• Verify ffmpeg has Indeo support:",
            "    ffmpeg -codecs 2>&1 | grep -i 'indeo\\|iv3\\|iv4\\|iv5'",
            "",
            "• Try a full static ffmpeg build (includes more codecs):",
            "    https://johnvansickle.com/ffmpeg/",
            "",
            "• If VLC plays the file, use VLC's built-in converter:",
            "    Media → Convert/Save → Add file → Convert",
            "",
            "• Last resort — screen-record while VLC plays the file.",
        ]
        fix_text.setPlainText("\n".join(fix_lines))
        tabs.addTab(fix_text, "  Causes & Fixes  ")

        layout.addWidget(tabs, 1)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
        btn_box.accepted.connect(dlg.accept)
        layout.addWidget(btn_box)

        dlg.exec_()
