"""
AVCS Format Reference Tab
A scrollable compatibility matrix and codec reference guide.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QTableWidget, QTableWidgetItem, QScrollArea, QFrame,
    QTextEdit, QHeaderView, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QBrush

from ui.widgets import SectionHeader


# ── Data ─────────────────────────────────────────────────────────

VIDEO_COMPAT = [
    # (Format, Extension, Container, Video Codec, Audio Codec, Use Case, Notes)
    ("MP4 (H.264)",  ".mp4",  "MPEG-4",     "H.264/AVC",  "AAC",       "Universal",        "Best all-around compatibility"),
    ("MP4 (H.265)",  ".mp4",  "MPEG-4",     "H.265/HEVC", "AAC",       "4K/HDR",           "50% smaller than H.264"),
    ("MKV",          ".mkv",  "Matroska",   "H.264/H.265","AAC/FLAC",  "Archival",         "Supports multiple audio/sub tracks"),
    ("AVI",          ".avi",  "AVI",        "H.264",      "MP3",       "Legacy",           "Older Windows software compat"),
    ("MOV",          ".mov",  "QuickTime",  "H.264/ProRes","AAC",      "Apple / Editing",  "Native macOS/iOS format"),
    ("WebM",         ".webm", "WebM",       "VP9",        "Opus",      "Web / HTML5",      "Open-source, browser native"),
    ("FLV",          ".flv",  "Flash Video","H.264",      "AAC",       "Legacy Web",       "Deprecated; Flash is EOL"),
    ("WMV",          ".wmv",  "ASF",        "WMV2",       "WMA",       "Windows Legacy",   "Windows Media compatibility"),
    ("GIF",          ".gif",  "GIF",        "GIF",        "None",      "Animation/Meme",   "No audio; 256 colors max"),
    ("TS",           ".ts",   "MPEG-TS",    "H.264",      "AAC",       "Broadcast/DVR",    "Used by OTA/DVR recordings"),
    ("VOB",          ".vob",  "MPEG-PS",    "MPEG-2",     "AC3/MP2",   "DVD",              "DVD video object files"),
    ("OGV",          ".ogv",  "Ogg",        "Theora",     "Vorbis",    "Open Web",         "Fully open-source codecs"),
    ("3GP",          ".3gp",  "3GPP",       "H.264",      "AAC",       "Mobile",           "Old mobile phone format"),
    ("TVO (Legacy)", ".tvo",  "Proprietary","Indeo/MJPEG","PCM/ADPCM", "Vintage Webcam",   "TeVeo VIDiO Suite 1990s–2000s"),
]

AUDIO_COMPAT = [
    # (Format, Extension, Lossy/Lossless, Bitrate Range, Use Case, Notes)
    ("MP3",   ".mp3",  "Lossy",    "32–320 kbps",  "Universal",       "Most widely supported audio format"),
    ("AAC",   ".aac",  "Lossy",    "32–320 kbps",  "Apple / Streaming","Better quality than MP3 at same bitrate"),
    ("FLAC",  ".flac", "Lossless", "~600–1200 kbps","Archival/Hi-Fi",  "Perfect copy, no quality loss"),
    ("WAV",   ".wav",  "Lossless", "~1411 kbps",   "Studio/Editing",  "Uncompressed PCM; very large files"),
    ("OGG",   ".ogg",  "Lossy",    "45–500 kbps",  "Open/Gaming",     "Open-source; used by many games"),
    ("M4A",   ".m4a",  "Lossy",    "32–320 kbps",  "iTunes/Apple",    "AAC in MPEG-4 container"),
    ("WMA",   ".wma",  "Lossy",    "48–320 kbps",  "Windows Legacy",  "Windows Media Audio"),
    ("OPUS",  ".opus", "Lossy",    "6–510 kbps",   "VoIP / Modern",   "Best quality at low bitrates"),
    ("AC3",   ".ac3",  "Lossy",    "32–640 kbps",  "Surround / DVD",  "Dolby Digital; up to 5.1 surround"),
]

TVO_DEEP_DIVE = """
TeVeo VIDiO Suite — Deep Dive Reference
════════════════════════════════════════════════════════════════

HISTORICAL CONTEXT
──────────────────
The TeVeo VIDiO Suite (also shipped as part of WebCamDV by Orbisoft)
was an early internet webcam application targeting consumer use in
the late 1990s and early 2000s. The software allowed users to:

  • Broadcast live webcam streams over early broadband connections
  • Record streams locally in the proprietary .TVO container
  • Share short video clips using the TeveoLive platform

The associated executable "TeVeo VIDiO Suite.exe" ran under
Windows 95/98/ME/2000 (32-bit). Version 1.0 and 1.1 are the only
documented releases.

FILE STRUCTURE
──────────────
TVO files use a proprietary container derived loosely from
AVI/RIFF structures. Key characteristics:

  Container:   Proprietary RIFF-like wrapper
  Video:       Typically Indeo 3/4/5, Cinepak, or Motion JPEG
  Audio:       PCM (uncompressed) or ADPCM (compressed)
  Resolution:  160×120, 320×240 (rare: 640×480)
  Frame rate:  10–15 fps (typical for late-90s webcam hardware)
  Color depth: 8-bit or 16-bit

DECODING STRATEGY IN AVCS
──────────────────────────
Since TVO files are not natively supported by any modern demuxer,
AVCS uses a multi-stage fallback approach via ffmpeg:

  Stage 1: Standard probe with extended error tolerance
    ffmpeg -err_detect ignore_err -fflags +genpts+igndts -i <input>

  Stage 2: Force-demux as AVI if Stage 1 yields no streams
    ffmpeg -f avi -err_detect ignore_err -i <input>

  Stage 3: Raw video stream extraction as last resort
    ffmpeg -f rawvideo -i <input>

The most commonly successful is Stage 1, which handles the
malformed timestamps and container errors typical of TVO files.

CONVERSION RECOMMENDATIONS
───────────────────────────
  Output format:  MP4 (H.264) — universally playable
  Quality:        Medium (CRF 23) — TVO source is low-res;
                  high quality wastes space without benefit
  Resolution:     Original (do NOT upscale; no quality benefit)
  Audio:          AAC 128k — matches original quality ceiling

KNOWN LIMITATIONS
─────────────────
  • Some TVO files recorded with very early (alpha) TeveoLive
    versions may have completely unrecoverable video streams.
  • Files > 2 GB are unlikely (original OS had 2 GB file limits).
  • Indeo codec decoding may fail on modern ffmpeg builds if
    Indeo support was not compiled in (rare on major distros).
  • Corrupted files from aged storage media may fail entirely.

ALTERNATIVE TOOLS
─────────────────
  • VLC (attempt with All Codecs → Force Demux)
  • MediaInfo (for file analysis only)
  • Handbrake (limited legacy format support)
  • AVCS TVO Tab (recommended — purpose-built)
"""

CODEC_NOTES = """
VIDEO CODEC QUICK REFERENCE
════════════════════════════

H.264 / AVC  ──────────────────────────────────────────────────
  Standard:    ISO/IEC 14496-10, ITU-T H.264
  Released:    2003
  Profile:     Baseline, Main, High
  Best for:    Universal compatibility, streaming, web delivery
  ffmpeg enc:  libx264  |  CRF: 18 (visually lossless) to 28 (low)

H.265 / HEVC ──────────────────────────────────────────────────
  Standard:    ISO/IEC 23008-2, ITU-T H.265
  Released:    2013
  Profile:     Main, Main 10 (HDR), Main Still Picture
  Best for:    4K/HDR content, ~50% smaller than H.264
  ffmpeg enc:  libx265  |  CRF: 24–28 typical

VP9           ─────────────────────────────────────────────────
  Developer:   Google (open-source)
  Released:    2013
  Best for:    Web/browser delivery (YouTube default)
  ffmpeg enc:  libvpx-vp9  |  CRF: 31–35 typical

MPEG-2        ─────────────────────────────────────────────────
  Standard:    ISO/IEC 13818-2
  Released:    1996
  Best for:    DVD compatibility, broadcast legacy
  ffmpeg enc:  mpeg2video

INDEO         ─────────────────────────────────────────────────
  Developer:   Intel → Ligos Corporation
  Released:    1992 (v3), 1994 (v4), 1996 (v5)
  Used in:     .TVO, early AVI files, CD-ROM multimedia
  Status:      Obsolete — decoder-only in modern ffmpeg builds
  Note:        Proprietary; some builds exclude it entirely

CINEPAK       ─────────────────────────────────────────────────
  Developer:   SuperMac Technologies / Radius
  Released:    1991
  Used in:     .TVO, QuickTime, early AVI, Sega/PlayStation FMV
  Status:      Obsolete but widely decodable

MJPEG         ─────────────────────────────────────────────────
  Type:        Intra-frame only (no temporal compression)
  Used in:     Webcams, surveillance, .TVO variants
  Best for:    Editing (every frame is a keyframe)
  ffmpeg dec:  mjpeg

───────────────────────────────────────────────────────────────
AUDIO CODEC QUICK REFERENCE

AAC    Advanced Audio Coding — successor to MP3, better quality
       at same bitrate. Profile: LC (most common), HE-AAC (VoIP)

MP3    MPEG Layer III — most universally supported audio format.
       Psychoacoustic masking. Royalty-free since ~2017.

FLAC   Free Lossless Audio Codec — perfect reconstruction.
       ~50–60% of raw PCM size. Metadata rich.

OPUS   Open, royalty-free. Lowest latency. Best quality at
       low bitrates (≤64 kbps). Preferred for VoIP and real-time.

AC3    Dolby Digital — 5.1 surround, used in DVD/Blu-ray.
       Bitrate 192–448 kbps typical.
"""


class FormatReferenceTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 12)
        root.setSpacing(12)

        root.addWidget(SectionHeader("Format & Codec Reference"))

        inner_tabs = QTabWidget(self)
        inner_tabs.setStyleSheet(
            "QTabBar::tab { min-width: 120px; padding: 6px 12px; }"
        )

        inner_tabs.addTab(self._build_video_table(), "Video Formats")
        inner_tabs.addTab(self._build_audio_table(), "Audio Formats")
        inner_tabs.addTab(self._build_text_panel(TVO_DEEP_DIVE), "TVO Deep Dive")
        inner_tabs.addTab(self._build_text_panel(CODEC_NOTES), "Codec Notes")

        root.addWidget(inner_tabs, 1)

    def _build_video_table(self) -> QWidget:
        headers = ["Format", "Ext", "Container", "Video Codec", "Audio Codec", "Use Case", "Notes"]
        table = _make_table(headers, len(VIDEO_COMPAT))

        for row, entry in enumerate(VIDEO_COMPAT):
            for col, val in enumerate(entry):
                item = QTableWidgetItem(val)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

                # Highlight TVO row
                if entry[0].startswith("TVO"):
                    item.setBackground(QBrush(QColor(42, 26, 58)))
                    item.setForeground(QBrush(QColor(192, 128, 240)))

                table.setItem(row, col, item)

        table.resizeColumnsToContents()
        table.setColumnWidth(6, 260)
        return table

    def _build_audio_table(self) -> QWidget:
        headers = ["Format", "Ext", "Lossy/Lossless", "Bitrate Range", "Use Case", "Notes"]
        table = _make_table(headers, len(AUDIO_COMPAT))

        for row, entry in enumerate(AUDIO_COMPAT):
            for col, val in enumerate(entry):
                item = QTableWidgetItem(val)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                if val == "Lossless":
                    item.setForeground(QBrush(QColor(80, 200, 80)))
                elif val == "Lossy":
                    item.setForeground(QBrush(QColor(200, 160, 60)))
                table.setItem(row, col, item)

        table.resizeColumnsToContents()
        table.setColumnWidth(5, 280)
        return table

    def _build_text_panel(self, text: str) -> QWidget:
        te = QTextEdit()
        te.setReadOnly(True)
        te.setPlainText(text.strip())
        te.setStyleSheet(
            "QTextEdit { background: #080a0d; color: #8a90a8; "
            "font-family: 'Consolas', 'Fira Code', 'Courier New', monospace; "
            "font-size: 8.5pt; border: none; padding: 12px; }"
        )
        return te


def _make_table(headers: list, rows: int) -> QTableWidget:
    t = QTableWidget(rows, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.verticalHeader().setVisible(False)
    t.setAlternatingRowColors(True)
    t.setSelectionBehavior(QTableWidget.SelectRows)
    t.setEditTriggers(QTableWidget.NoEditTriggers)
    t.setShowGrid(False)
    t.horizontalHeader().setStretchLastSection(True)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
    t.setStyleSheet(
        "QTableWidget { border: 1px solid #1e2028; border-radius: 4px; gridline-color: #1a1d24; }"
    )
    return t
