"""
AVCS Format Definitions
Supported formats, codecs, and file type mappings.
"""

# ── Video Output Formats ──────────────────────────────────────────
VIDEO_OUTPUT_FORMATS = {
    "MP4 (H.264)":    {"ext": "mp4",  "vcodec": "libx264",   "acodec": "aac",        "container": "mp4"},
    "MP4 (H.265)":    {"ext": "mp4",  "vcodec": "libx265",   "acodec": "aac",        "container": "mp4"},
    "MKV":            {"ext": "mkv",  "vcodec": "libx264",   "acodec": "aac",        "container": "matroska"},
    "AVI":            {"ext": "avi",  "vcodec": "libx264",   "acodec": "mp3",        "container": "avi"},
    "MOV":            {"ext": "mov",  "vcodec": "libx264",   "acodec": "aac",        "container": "mov"},
    "WebM":           {"ext": "webm", "vcodec": "libvpx-vp9","acodec": "libopus",    "container": "webm"},
    "FLV":            {"ext": "flv",  "vcodec": "libx264",   "acodec": "aac",        "container": "flv"},
    "WMV":            {"ext": "wmv",  "vcodec": "wmv2",      "acodec": "wmav2",      "container": "asf"},
    "GIF (animated)": {"ext": "gif",  "vcodec": "gif",       "acodec": None,         "container": "gif"},
    "TS (Transport)": {"ext": "ts",   "vcodec": "libx264",   "acodec": "aac",        "container": "mpegts"},
    "VOB (DVD)":      {"ext": "vob",  "vcodec": "mpeg2video","acodec": "mp2",        "container": "vob"},
    "OGV":            {"ext": "ogv",  "vcodec": "libtheora", "acodec": "libvorbis",  "container": "ogg"},
    "3GP (Mobile)":   {"ext": "3gp",  "vcodec": "libx264",   "acodec": "aac",        "container": "3gp"},
    "MP4 (Copy)":     {"ext": "mp4",  "vcodec": "copy",      "acodec": "copy",       "container": "mp4"},
}

# ── Audio Output Formats ──────────────────────────────────────────
AUDIO_OUTPUT_FORMATS = {
    "MP3":  {"ext": "mp3",  "acodec": "libmp3lame"},
    "AAC":  {"ext": "aac",  "acodec": "aac"},
    "FLAC": {"ext": "flac", "acodec": "flac"},
    "WAV":  {"ext": "wav",  "acodec": "pcm_s16le"},
    "OGG":  {"ext": "ogg",  "acodec": "libvorbis"},
    "M4A":  {"ext": "m4a",  "acodec": "aac"},
    "WMA":  {"ext": "wma",  "acodec": "wmav2"},
    "OPUS": {"ext": "opus", "acodec": "libopus"},
    "AC3":  {"ext": "ac3",  "acodec": "ac3"},
}

# ── Quality Presets ───────────────────────────────────────────────
VIDEO_QUALITY_PRESETS = {
    "Ultra (CRF 15)":   {"crf": "15", "preset": "slow"},
    "High (CRF 20)":    {"crf": "20", "preset": "slow"},
    "Medium (CRF 23)":  {"crf": "23", "preset": "medium"},
    "Low (CRF 28)":     {"crf": "28", "preset": "fast"},
    "Draft (CRF 35)":   {"crf": "35", "preset": "veryfast"},
    "Lossless":         {"crf": "0",  "preset": "medium"},
}

AUDIO_BITRATE_PRESETS = {
    "320 kbps":  "320k",
    "256 kbps":  "256k",
    "192 kbps":  "192k",
    "128 kbps":  "128k",
    "96 kbps":   "96k",
    "Lossless":  None,
}

# ── Resolution Presets ────────────────────────────────────────────
RESOLUTION_PRESETS = {
    "Original":     None,
    "4K (3840×2160)": "3840:2160",
    "2K (2560×1440)": "2560:1440",
    "1080p":        "1920:1080",
    "720p":         "1280:720",
    "480p":         "854:480",
    "360p":         "640:360",
    "240p":         "426:240",
}

# ── Supported Input Extensions ────────────────────────────────────
VIDEO_INPUT_EXTENSIONS = [
    # Common modern
    "mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "m4v",
    "mpg", "mpeg", "ts", "mts", "m2ts", "vob", "ogv", "3gp",
    "3g2", "f4v", "asf", "divx", "xvid", "rmvb", "rm", "m2v",
    # Disc/capture
    "mxf", "dv", "dvr-ms", "wtv", "nuv", "rec",
    # Lossless / editing
    "y4m", "dnxhd", "prores", "huffyuv",
    # Legacy / vintage
    "tvo",   # TeVeo VIDiO Suite - legacy webcam streaming format
    "asf",   # Advanced Streaming Format
    "asx",   # Windows Media streaming
]

AUDIO_INPUT_EXTENSIONS = [
    "mp3", "aac", "flac", "wav", "ogg", "m4a", "wma", "opus",
    "ac3", "dts", "mka", "ape", "alac", "aiff", "aif", "ra",
    "amr", "mid", "midi", "caf", "spx",
]

# All input extensions combined for file dialogs
ALL_INPUT_EXTENSIONS = VIDEO_INPUT_EXTENSIONS + AUDIO_INPUT_EXTENSIONS

# ── TVO File Information ──────────────────────────────────────────
TVO_INFO = {
    "description": "TeVeo VIDiO Suite / TeveoLive Legacy Streaming Video",
    "developer": "TeVeo Inc. / Orbisoft (WebCamDV)",
    "era": "Late 1990s – Early 2000s",
    "type": "Proprietary container, webcam/streaming video",
    "codec_hint": "Indeo, Cinepak, or MJPEG (obsolete codecs)",
    "note": (
        "TVO files are orphaned legacy format from discontinued TeveoLive software. "
        "AVCS uses ffmpeg with fallback raw/force-demux strategies to extract the video stream."
    ),
    "recommended_output": "mp4",
}

# ── File Dialog Filters ───────────────────────────────────────────
def build_video_filter():
    exts = " ".join(f"*.{e}" for e in VIDEO_INPUT_EXTENSIONS)
    return f"Video Files ({exts});;All Files (*.*)"

def build_audio_filter():
    exts = " ".join(f"*.{e}" for e in AUDIO_INPUT_EXTENSIONS)
    return f"Audio Files ({exts});;All Files (*.*)"

def build_all_filter():
    vid_exts = " ".join(f"*.{e}" for e in VIDEO_INPUT_EXTENSIONS)
    aud_exts = " ".join(f"*.{e}" for e in AUDIO_INPUT_EXTENSIONS)
    all_exts = f"{vid_exts} {aud_exts}"
    return (
        f"All Media ({all_exts});;"
        f"Video Files ({vid_exts});;"
        f"Audio Files ({aud_exts});;"
        "All Files (*.*)"
    )

def is_video(path: str) -> bool:
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return ext in VIDEO_INPUT_EXTENSIONS

def is_audio(path: str) -> bool:
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return ext in AUDIO_INPUT_EXTENSIONS

def is_tvo(path: str) -> bool:
    return path.rsplit(".", 1)[-1].lower() == "tvo"
