![AVCS](docs/avcs_banner.svg)
# AVCS — Audio Video Conversion Suite

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)
[![PyQt5](https://img.shields.io/badge/GUI-PyQt5-41CD52?logo=qt)](https://pypi.org/project/PyQt5/)
[![ffmpeg](https://img.shields.io/badge/Engine-ffmpeg-007808?logo=ffmpeg)](https://ffmpeg.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey)](https://github.com)

Enterprise-grade audio/video conversion application built with Python and PyQt5, powered by ffmpeg. Includes dedicated support for legacy **TeVeo VIDiO Suite `.tvo`** files.

---

## Features

### Video Conversion
- Convert between **MP4 (H.264/H.265), MKV, AVI, MOV, WebM, WMV, FLV, TS, VOB, OGV, 3GP, GIF**
- Adjustable quality presets (CRF 15–35, Lossless)
- Resolution scaling: 4K, 2K, 1080p, 720p, 480p, 360p, 240p
- Batch processing with live per-file progress bars
- Drag-and-drop file queue

### Audio Conversion
- Convert between **MP3, AAC, FLAC, WAV, OGG, M4A, WMA, OPUS, AC3**
- Bitrate control: 96 – 320 kbps, or Lossless
- Batch processing with cancel support

### TVO Legacy Converter *(Unique Feature)*
- Dedicated tab for **TeVeo VIDiO Suite `.tvo`** legacy format
- Extended ffmpeg compatibility mode (`-err_detect ignore_err`, `-fflags +genpts+igndts`)
- Handles the proprietary TeveoLive container from the late 1990s
- Converts to modern formats with full documentation on the TVO format

### Media Inspector
- Probe any media file with ffprobe
- Displays video stream (codec, resolution, fps, pixel format)
- Displays audio stream (codec, channels, sample rate, bitrate)
- Special TVO format recognition and metadata display

---

## The TVO Format — Research Notes

`.TVO` files are a **vintage proprietary video format** created by **TeveoLive**, an early internet webcam broadcasting application developed by **TeVeo Inc.** (also distributed as part of **WebCamDV by Orbisoft**).

| Property | Detail |
|----------|--------|
| Developer | TeVeo Inc. / Orbisoft |
| Era | Late 1990s – Early 2000s |
| Use case | Live webcam streaming, security recording |
| Compression | Indeo, Cinepak, or MJPEG (obsolete) |
| Resolution | Typically 160×120 or 320×240 |
| Status | **Orphaned** — software discontinued 20+ years ago |

Modern players (VLC, Windows Media Player) cannot natively decode TVO files because:
1. The original 16-bit/32-bit software won't run on 64-bit operating systems
2. The proprietary container structure is not supported by standard demuxers
3. The embedded codecs are decade-old and require explicit compatibility handling

**AVCS uses ffmpeg's extended error-tolerance flags** to extract and re-encode these files:
```
-err_detect ignore_err -fflags +genpts+igndts
```

---

## Installation

### Prerequisites

**System dependency** (required):
```bash
# Ubuntu / Debian / Linux Mint
sudo apt install ffmpeg

# Fedora / RHEL
sudo dnf install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html and add to PATH
```

# Create Virtual Environment

```
cd avcs
python3 -m venv venv
source venvbin/activate

**Python dependencies:**
```bash
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

---

## Architecture

```
avcs/
├── main.py                   # Entry point
├── requirements.txt
├── themes/
│   └── dark_theme.py         # Cinematic dark stylesheet + QPalette
├── ui/
│   ├── main_window.py        # QMainWindow, header, tab container
│   ├── widgets.py            # Reusable widgets (DropZone, FileQueueItem, LogPanel, ...)
│   ├── video_tab.py          # Video conversion tab
│   ├── audio_tab.py          # Audio conversion tab
│   ├── tvo_tab.py            # TVO legacy converter tab
│   └── inspector_tab.py      # Media file inspector
├── converters/
│   └── workers.py            # QThread workers: VideoConversionWorker, AudioConversionWorker
└── utils/
    ├── formats.py            # Format definitions, codec maps, extension lists
    └── ffmpeg_utils.py       # ffmpeg/ffprobe wrappers, probe, command builders
```

---

## Supported Formats

### Video Input
`mp4` `mkv` `avi` `mov` `wmv` `flv` `webm` `m4v` `mpg` `mpeg` `ts` `mts` `vob` `ogv` `3gp` `divx` `xvid` `rmvb` `rm` `mxf` `dv` `y4m` **`tvo`** *(+ more)*

### Audio Input
`mp3` `aac` `flac` `wav` `ogg` `m4a` `wma` `opus` `ac3` `dts` `mka` `ape` `alac` `aiff` *(+ more)*

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| GUI | PyQt5 |
| Conversion engine | ffmpeg / ffprobe |
| Threading | QThread |
| Language | Python 3.8+ |

---

## License

MIT License. See `LICENSE` for details.
