"""
AVCS Settings Tab
Persistent user preferences and application configuration.
"""

import os
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QCheckBox, QSpinBox, QComboBox, QLineEdit,
    QFileDialog, QMessageBox, QFormLayout, QFrame, QScrollArea,
)
from PyQt5.QtCore import Qt, QSettings

from ui.widgets import SectionHeader, HDivider


SETTINGS_ORG = "AVCS"
SETTINGS_APP = "AudioVideoConversionSuite"

DEFAULTS = {
    "output_same_folder":      True,
    "output_folder":           "",
    "default_video_format":    "MP4 (H.264)",
    "default_video_quality":   "Medium (CRF 23)",
    "default_audio_format":    "MP3",
    "default_audio_bitrate":   "320 kbps",
    "overwrite_existing":      False,
    "max_concurrent_jobs":     1,
    "show_log_on_start":       False,
    "confirm_on_overwrite":    True,
    "suffix_on_same_folder":   True,
    "output_suffix":           "_converted",
    "ffmpeg_path_override":    "",
    "ffprobe_path_override":   "",
    "theme":                   "Dark (Default)",
}


def load_settings() -> dict:
    qs = QSettings(SETTINGS_ORG, SETTINGS_APP)
    result = {}
    for key, default in DEFAULTS.items():
        val = qs.value(key, default)
        # QSettings stores booleans as strings on some platforms
        if isinstance(default, bool):
            if isinstance(val, str):
                val = val.lower() in ("true", "1", "yes")
            else:
                val = bool(val)
        elif isinstance(default, int):
            try:
                val = int(val)
            except (ValueError, TypeError):
                val = default
        result[key] = val
    return result


def save_settings(settings: dict):
    qs = QSettings(SETTINGS_ORG, SETTINGS_APP)
    for key, val in settings.items():
        qs.setValue(key, val)
    qs.sync()


class SettingsTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = load_settings()
        self._setup_ui()
        self._load_to_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        root.addWidget(scroll)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        scroll.setWidget(content)

        # ── Output ───────────────────────────────────────────
        out_group = QGroupBox("Output")
        out_form = QFormLayout(out_group)
        out_form.setLabelAlignment(Qt.AlignRight)
        out_form.setSpacing(10)

        self._same_folder_cb = QCheckBox("Save output in same folder as input")
        out_form.addRow("Default Location:", self._same_folder_cb)
        self._same_folder_cb.toggled.connect(self._toggle_output_folder)

        out_folder_row = QHBoxLayout()
        self._output_folder_edit = QLineEdit()
        self._output_folder_edit.setPlaceholderText("No folder selected…")
        self._output_folder_edit.setReadOnly(True)
        browse_btn = QPushButton("Browse…")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_output_folder)
        out_folder_row.addWidget(self._output_folder_edit)
        out_folder_row.addWidget(browse_btn)
        self._out_folder_widget = QWidget()
        self._out_folder_widget.setLayout(out_folder_row)
        out_form.addRow("Output Folder:", self._out_folder_widget)

        self._overwrite_cb = QCheckBox("Overwrite existing files without asking")
        out_form.addRow("Overwrite:", self._overwrite_cb)

        self._confirm_overwrite_cb = QCheckBox("Confirm before overwriting")
        out_form.addRow("Confirm:", self._confirm_overwrite_cb)

        self._suffix_cb = QCheckBox("Add suffix when output would overwrite input")
        out_form.addRow("Collision Safety:", self._suffix_cb)

        self._suffix_edit = QLineEdit()
        self._suffix_edit.setMaximumWidth(160)
        out_form.addRow("Suffix:", self._suffix_edit)

        layout.addWidget(out_group)

        # ── Defaults ─────────────────────────────────────────
        def_group = QGroupBox("Default Conversion Settings")
        def_form = QFormLayout(def_group)
        def_form.setLabelAlignment(Qt.AlignRight)
        def_form.setSpacing(10)

        from utils.formats import VIDEO_OUTPUT_FORMATS, VIDEO_QUALITY_PRESETS, AUDIO_OUTPUT_FORMATS, AUDIO_BITRATE_PRESETS
        self._default_video_fmt = QComboBox()
        self._default_video_fmt.addItems(list(VIDEO_OUTPUT_FORMATS.keys()))
        def_form.addRow("Default Video Format:", self._default_video_fmt)

        self._default_video_quality = QComboBox()
        self._default_video_quality.addItems(list(VIDEO_QUALITY_PRESETS.keys()))
        def_form.addRow("Default Video Quality:", self._default_video_quality)

        self._default_audio_fmt = QComboBox()
        self._default_audio_fmt.addItems(list(AUDIO_OUTPUT_FORMATS.keys()))
        def_form.addRow("Default Audio Format:", self._default_audio_fmt)

        self._default_audio_bitrate = QComboBox()
        self._default_audio_bitrate.addItems(list(AUDIO_BITRATE_PRESETS.keys()))
        def_form.addRow("Default Audio Bitrate:", self._default_audio_bitrate)

        layout.addWidget(def_group)

        # ── Performance ──────────────────────────────────────
        perf_group = QGroupBox("Performance")
        perf_form = QFormLayout(perf_group)
        perf_form.setLabelAlignment(Qt.AlignRight)
        perf_form.setSpacing(10)

        self._concurrent_spin = QSpinBox()
        self._concurrent_spin.setRange(1, 8)
        self._concurrent_spin.setFixedWidth(80)
        perf_note = QLabel("(1 recommended — ffmpeg already uses multiple cores)")
        perf_note.setObjectName("dim_label")
        perf_row = QHBoxLayout()
        perf_row.addWidget(self._concurrent_spin)
        perf_row.addWidget(perf_note)
        perf_row.addStretch()
        perf_widget = QWidget()
        perf_widget.setLayout(perf_row)
        perf_form.addRow("Concurrent Jobs:", perf_widget)

        layout.addWidget(perf_group)

        # ── Appearance ───────────────────────────────────────
        app_group = QGroupBox("Appearance")
        app_form = QFormLayout(app_group)
        app_form.setLabelAlignment(Qt.AlignRight)
        app_form.setSpacing(10)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Dark (Default)"])
        self._theme_combo.setEnabled(False)
        theme_note = QLabel("More themes coming in a future release")
        theme_note.setObjectName("dim_label")
        theme_row = QHBoxLayout()
        theme_row.addWidget(self._theme_combo)
        theme_row.addWidget(theme_note)
        theme_row.addStretch()
        theme_widget = QWidget()
        theme_widget.setLayout(theme_row)
        app_form.addRow("Theme:", theme_widget)

        self._show_log_cb = QCheckBox("Expand console log on startup")
        app_form.addRow("Log Panel:", self._show_log_cb)

        layout.addWidget(app_group)

        # ── Advanced / ffmpeg paths ───────────────────────────
        adv_group = QGroupBox("Advanced — ffmpeg Paths")
        adv_form = QFormLayout(adv_group)
        adv_form.setLabelAlignment(Qt.AlignRight)
        adv_form.setSpacing(10)

        adv_note = QLabel(
            "Leave blank to use system PATH. Specify only if you have a custom ffmpeg install."
        )
        adv_note.setObjectName("dim_label")
        adv_note.setWordWrap(True)
        adv_form.addRow("", adv_note)

        ffmpeg_row = QHBoxLayout()
        self._ffmpeg_path_edit = QLineEdit()
        self._ffmpeg_path_edit.setPlaceholderText("Detected automatically from PATH…")
        ffmpeg_browse = QPushButton("Browse…")
        ffmpeg_browse.setFixedWidth(80)
        ffmpeg_browse.clicked.connect(
            lambda: self._browse_binary(self._ffmpeg_path_edit, "ffmpeg")
        )
        ffmpeg_row.addWidget(self._ffmpeg_path_edit)
        ffmpeg_row.addWidget(ffmpeg_browse)
        ffmpeg_widget = QWidget()
        ffmpeg_widget.setLayout(ffmpeg_row)
        adv_form.addRow("ffmpeg Binary:", ffmpeg_widget)

        ffprobe_row = QHBoxLayout()
        self._ffprobe_path_edit = QLineEdit()
        self._ffprobe_path_edit.setPlaceholderText("Detected automatically from PATH…")
        ffprobe_browse = QPushButton("Browse…")
        ffprobe_browse.setFixedWidth(80)
        ffprobe_browse.clicked.connect(
            lambda: self._browse_binary(self._ffprobe_path_edit, "ffprobe")
        )
        ffprobe_row.addWidget(self._ffprobe_path_edit)
        ffprobe_row.addWidget(ffprobe_browse)
        ffprobe_widget = QWidget()
        ffprobe_widget.setLayout(ffprobe_row)
        adv_form.addRow("ffprobe Binary:", ffprobe_widget)

        layout.addWidget(adv_group)

        layout.addStretch()

        # ── Action buttons ────────────────────────────────────
        btn_row = QHBoxLayout()
        save_btn = QPushButton("  Save Settings")
        save_btn.setObjectName("primary_button")
        save_btn.setMinimumHeight(34)
        save_btn.setMinimumWidth(140)
        save_btn.clicked.connect(self._save)

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setMinimumHeight(34)
        reset_btn.clicked.connect(self._reset)

        btn_row.addStretch()
        btn_row.addWidget(reset_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    # ── Load / Save ──────────────────────────────────────────
    def _load_to_ui(self):
        s = self._settings
        self._same_folder_cb.setChecked(s["output_same_folder"])
        self._output_folder_edit.setText(s["output_folder"])
        self._out_folder_widget.setEnabled(not s["output_same_folder"])
        self._overwrite_cb.setChecked(s["overwrite_existing"])
        self._confirm_overwrite_cb.setChecked(s["confirm_on_overwrite"])
        self._suffix_cb.setChecked(s["suffix_on_same_folder"])
        self._suffix_edit.setText(s["output_suffix"])
        self._concurrent_spin.setValue(s["max_concurrent_jobs"])
        self._show_log_cb.setChecked(s["show_log_on_start"])
        self._ffmpeg_path_edit.setText(s["ffmpeg_path_override"])
        self._ffprobe_path_edit.setText(s["ffprobe_path_override"])

        # Combo boxes — safe set
        _set_combo(self._default_video_fmt, s["default_video_format"])
        _set_combo(self._default_video_quality, s["default_video_quality"])
        _set_combo(self._default_audio_fmt, s["default_audio_format"])
        _set_combo(self._default_audio_bitrate, s["default_audio_bitrate"])

    def _save(self):
        s = {
            "output_same_folder":    self._same_folder_cb.isChecked(),
            "output_folder":         self._output_folder_edit.text(),
            "default_video_format":  self._default_video_fmt.currentText(),
            "default_video_quality": self._default_video_quality.currentText(),
            "default_audio_format":  self._default_audio_fmt.currentText(),
            "default_audio_bitrate": self._default_audio_bitrate.currentText(),
            "overwrite_existing":    self._overwrite_cb.isChecked(),
            "max_concurrent_jobs":   self._concurrent_spin.value(),
            "show_log_on_start":     self._show_log_cb.isChecked(),
            "confirm_on_overwrite":  self._confirm_overwrite_cb.isChecked(),
            "suffix_on_same_folder": self._suffix_cb.isChecked(),
            "output_suffix":         self._suffix_edit.text(),
            "ffmpeg_path_override":  self._ffmpeg_path_edit.text(),
            "ffprobe_path_override": self._ffprobe_path_edit.text(),
            "theme":                 self._theme_combo.currentText(),
        }
        save_settings(s)
        self._settings = s
        QMessageBox.information(self, "Settings Saved", "Your preferences have been saved.")

    def _reset(self):
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Reset all settings to their default values?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._settings = dict(DEFAULTS)
            self._load_to_ui()
            save_settings(self._settings)

    # ── Helpers ──────────────────────────────────────────────
    def _toggle_output_folder(self, checked: bool):
        self._out_folder_widget.setEnabled(not checked)

    def _browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Default Output Folder")
        if folder:
            self._output_folder_edit.setText(folder)

    def _browse_binary(self, edit: QLineEdit, name: str):
        path, _ = QFileDialog.getOpenFileName(self, f"Select {name} Binary", "", "All Files (*)")
        if path:
            edit.setText(path)


def _set_combo(combo: QComboBox, value: str):
    idx = combo.findText(value)
    if idx >= 0:
        combo.setCurrentIndex(idx)
