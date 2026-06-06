"""
AVCS FFmpeg Utilities
Wraps ffmpeg/ffprobe for media info and conversion.

TVO fix history:
  v1.1 - Capture full stderr for error reporting; multi-stage TVO fallback;
         correct flag placement; verbose error surfaced to UI log.
"""

import os
import re
import json
import shutil
import subprocess
from typing import Optional, Dict, Any, List, Tuple


def find_ffmpeg() -> Tuple[Optional[str], Optional[str]]:
    ffmpeg  = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    for base in ["/usr/bin", "/usr/local/bin", "/opt/ffmpeg/bin", "/snap/bin"]:
        if not ffmpeg  and os.path.isfile(f"{base}/ffmpeg"):  ffmpeg  = f"{base}/ffmpeg"
        if not ffprobe and os.path.isfile(f"{base}/ffprobe"): ffprobe = f"{base}/ffprobe"
    return ffmpeg, ffprobe


FFMPEG_PATH, FFPROBE_PATH = find_ffmpeg()


def ffmpeg_available()  -> bool: return FFMPEG_PATH  is not None
def ffprobe_available() -> bool: return FFPROBE_PATH is not None


# ── Probe ─────────────────────────────────────────────────────────

def probe_media(file_path: str) -> Optional[Dict[str, Any]]:
    if not ffprobe_available():
        return None
    try:
        cmd = [
            FFPROBE_PATH,
            "-v", "error",
            "-print_format", "json",
            "-show_format", "-show_streams",
            "-err_detect", "ignore_err",
            file_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
        # TVO files often make ffprobe return non-zero; try parsing anyway
        if result.stdout.strip():
            try:
                return json.loads(result.stdout)
            except Exception:
                pass
    except Exception:
        pass
    return None


def get_media_info(file_path: str) -> Dict[str, Any]:
    info = {
        "path":         file_path,
        "filename":     os.path.basename(file_path),
        "size_bytes":   0,
        "duration_sec": 0.0,
        "duration_str": "Unknown",
        "format_name":  "Unknown",
        "bit_rate":     "Unknown",
        "video":        None,
        "audio":        None,
        "is_tvo":       file_path.lower().endswith(".tvo"),
    }
    try:
        info["size_bytes"] = os.path.getsize(file_path)
    except OSError:
        pass

    probe = probe_media(file_path)
    if not probe:
        info["format_name"] = "TVO/Legacy" if info["is_tvo"] else "Unknown"
        return info

    fmt = probe.get("format", {})
    info["format_name"] = fmt.get("format_long_name", fmt.get("format_name", "Unknown"))

    try:
        dur = float(fmt.get("duration", 0))
        info["duration_sec"] = dur
        info["duration_str"] = _fmt_duration(dur)
    except (ValueError, TypeError):
        pass

    try:
        br = int(fmt.get("bit_rate", 0))
        info["bit_rate"] = f"{br // 1000} kbps" if br else "Unknown"
    except (ValueError, TypeError):
        pass

    for stream in probe.get("streams", []):
        ct = stream.get("codec_type", "")
        if ct == "video" and info["video"] is None:
            info["video"] = {
                "codec":    stream.get("codec_name", "Unknown"),
                "width":    stream.get("width", 0),
                "height":   stream.get("height", 0),
                "fps":      _parse_fps(stream.get("r_frame_rate", "0/1")),
                "pix_fmt":  stream.get("pix_fmt", "Unknown"),
            }
        elif ct == "audio" and info["audio"] is None:
            info["audio"] = {
                "codec":       stream.get("codec_name", "Unknown"),
                "channels":    stream.get("channels", 0),
                "sample_rate": stream.get("sample_rate", "Unknown"),
                "bit_rate":    stream.get("bit_rate", "Unknown"),
            }
    return info


# ── Command builders ──────────────────────────────────────────────

def _encode_args(vcodec: str, acodec: Optional[str],
                 crf: str, preset: str, resolution: Optional[str]) -> List[str]:
    """Return the codec/quality portion of an ffmpeg command (no -i / output)."""
    args: List[str] = []

    if vcodec == "copy" and acodec == "copy":
        return ["-c", "copy"]

    if vcodec == "gif":
        args += ["-vf", "fps=15,scale=480:-1:flags=lanczos", "-c:v", "gif"]
    else:
        args += ["-c:v", vcodec]
        if vcodec in ("libx264", "libx265"):
            args += ["-crf", crf, "-preset", preset]
        elif vcodec == "libvpx-vp9":
            args += ["-crf", crf, "-b:v", "0", "-quality", preset]

    if acodec:
        args += ["-c:a", acodec]
        if acodec in ("aac",):
            args += ["-b:a", "192k"]
        elif acodec == "libmp3lame":
            args += ["-b:a", "192k"]

    if resolution:
        # only add -vf scale if we haven't already added a -vf (gif case)
        if vcodec != "gif":
            args += ["-vf", f"scale={resolution}"]

    return args


def build_video_convert_cmd(
    input_path: str,
    output_path: str,
    vcodec: str,
    acodec: Optional[str],
    crf: str = "23",
    preset: str = "medium",
    resolution: Optional[str] = None,
    extra_args: Optional[List[str]] = None,
    is_tvo: bool = False,
) -> List[str]:
    """Standard single-attempt command.  TVO uses build_tvo_cmd_stages instead."""
    cmd = [FFMPEG_PATH, "-y", "-i", input_path]
    cmd += _encode_args(vcodec, acodec, crf, preset, resolution)
    if extra_args:
        cmd += extra_args
    cmd.append(output_path)
    return cmd


def build_tvo_cmd_stages(
    input_path: str,
    output_path: str,
    vcodec: str = "libx264",
    acodec: str  = "aac",
    crf: str     = "23",
    preset: str  = "medium",
) -> List[List[str]]:
    """
    Return an ordered list of ffmpeg commands to try for a .tvo file,
    from most to least likely to succeed.

    Stage 1 – AVI demuxer (TVO is RIFF-based, closest match)
    Stage 2 – auto-detect + all error-tolerance flags
    Stage 3 – force-AVI with extra timestamp repair
    Stage 4 – video-only stream extract (drop audio entirely)
    Stage 5 – raw MJPEG probe (last resort for MJPEG-encoded TVO)
    """
    enc = _encode_args(vcodec, acodec, crf, preset, None)
    enc_noaudio = _encode_args(vcodec, None, crf, preset, None) + ["-an"]

    base  = FFMPEG_PATH
    y     = "-y"

    stages = [
        # ── Stage 1: force AVI demuxer (TVO is RIFF/AVI-like)
        [base, y,
         "-f", "avi",
         "-err_detect", "ignore_err",
         "-fflags", "+genpts+igndts+discardcorrupt",
         "-i", input_path]
        + enc + [output_path],

        # ── Stage 2: auto-detect + full error tolerance
        [base, y,
         "-err_detect", "ignore_err",
         "-fflags", "+genpts+igndts+discardcorrupt",
         "-flags", "low_delay",
         "-i", input_path]
        + enc + [output_path],

        # ── Stage 3: force AVI + re-mux timestamps aggressively
        [base, y,
         "-f", "avi",
         "-err_detect", "ignore_err",
         "-fflags", "+genpts+igndts+discardcorrupt",
         "-avoid_negative_ts", "make_zero",
         "-i", input_path]
        + enc + [output_path],

        # ── Stage 4: drop audio (some TVO files have corrupt audio track)
        [base, y,
         "-f", "avi",
         "-err_detect", "ignore_err",
         "-fflags", "+genpts+igndts+discardcorrupt",
         "-i", input_path]
        + enc_noaudio + [output_path],

        # ── Stage 5: raw MJPEG fallback (video-only)
        [base, y,
         "-f", "mjpeg",
         "-err_detect", "ignore_err",
         "-i", input_path,
         "-c:v", vcodec,
         "-crf", crf, "-preset", preset,
         "-an",
         output_path],
    ]
    return stages


def build_audio_convert_cmd(
    input_path: str,
    output_path: str,
    acodec: str,
    bitrate: Optional[str] = "192k",
    extra_args: Optional[List[str]] = None,
) -> List[str]:
    cmd = [FFMPEG_PATH, "-y", "-i", input_path, "-c:a", acodec]
    if bitrate and acodec not in ("flac", "pcm_s16le", "pcm_s24le"):
        cmd += ["-b:a", bitrate]
    if extra_args:
        cmd += extra_args
    cmd.append(output_path)
    return cmd


# ── Execution ─────────────────────────────────────────────────────

def run_conversion(
    cmd: List[str],
    progress_callback=None,
    cancel_check=None,
    duration_sec: float = 0.0,
    log_callback=None,
) -> Tuple[bool, str]:
    """
    Run a single ffmpeg command.
    Returns (success, full_stderr_on_failure).
    """
    if not cmd:
        return False, "Empty command"

    stderr_lines: List[str] = []

    try:
        proc = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            universal_newlines=True,
            bufsize=1,
        )

        time_re = re.compile(r"time=(\d+):(\d+):(\d+)[\.:](\d+)")

        for line in proc.stderr:
            line = line.rstrip()
            stderr_lines.append(line)
            if log_callback:
                log_callback(line)

            if cancel_check and cancel_check():
                proc.terminate()
                proc.wait(timeout=5)
                return False, "Cancelled"

            if progress_callback and duration_sec > 0:
                m = time_re.search(line)
                if m:
                    h  = int(m.group(1))
                    mi = int(m.group(2))
                    s  = int(m.group(3))
                    cs = int(m.group(4))
                    current = h * 3600 + mi * 60 + s + cs / 100.0
                    pct = min(int(current / duration_sec * 100), 99)
                    progress_callback(pct)

        proc.wait()

        if proc.returncode == 0:
            if progress_callback:
                progress_callback(100)
            return True, ""

        # Collect the most relevant error lines (last 20 non-empty)
        error_lines = [l for l in stderr_lines if l.strip()][-20:]
        return False, "\n".join(error_lines)

    except FileNotFoundError:
        return False, "ffmpeg not found. Install with: sudo apt install ffmpeg"
    except Exception as e:
        return False, str(e)


def run_tvo_conversion(
    input_path: str,
    output_path: str,
    vcodec: str = "libx264",
    acodec: str = "aac",
    crf: str    = "23",
    preset: str = "medium",
    progress_callback=None,
    cancel_check=None,
    log_callback=None,
) -> Tuple[bool, str]:
    """
    Try each TVO decode stage in order; return on first success.
    Logs every attempt to log_callback so the user sees what's happening.
    """
    stages = build_tvo_cmd_stages(input_path, output_path, vcodec, acodec, crf, preset)
    stage_names = [
        "Stage 1: AVI demuxer + error tolerance",
        "Stage 2: Auto-detect + full error tolerance",
        "Stage 3: AVI demuxer + timestamp repair",
        "Stage 4: AVI demuxer, audio dropped",
        "Stage 5: Raw MJPEG fallback (video only)",
    ]

    last_error = "All decode stages failed."

    for i, cmd in enumerate(stages):
        if cancel_check and cancel_check():
            return False, "Cancelled"

        label = stage_names[i]
        if log_callback:
            log_callback(f"   TVO {label}")
            log_callback(f"   CMD: {' '.join(cmd)}")

        # Remove stale output from a previous failed stage
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass

        success, error = run_conversion(
            cmd,
            progress_callback=progress_callback,
            cancel_check=cancel_check,
            duration_sec=0.0,       # TVO duration usually unknown
            log_callback=log_callback,
        )

        if success and os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
            if log_callback:
                log_callback(f"   ✓ {label} succeeded.")
            return True, ""

        last_error = error
        if log_callback:
            log_callback(f"   ✗ {label} failed.")
            # Show the most relevant ffmpeg error line
            for line in error.splitlines()[-5:]:
                if line.strip():
                    log_callback(f"     {line}")

    return False, last_error


# ── Helpers ───────────────────────────────────────────────────────

def _fmt_duration(seconds: float) -> str:
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _parse_fps(r_frame_rate: str) -> str:
    try:
        num, den = r_frame_rate.split("/")
        return f"{float(num)/float(den):.2f}"
    except Exception:
        return r_frame_rate


def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:         return f"{size_bytes} B"
    if size_bytes < 1024**2:      return f"{size_bytes/1024:.1f} KB"
    if size_bytes < 1024**3:      return f"{size_bytes/1024**2:.1f} MB"
    return f"{size_bytes/1024**3:.2f} GB"
