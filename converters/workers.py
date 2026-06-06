"""
AVCS Conversion Workers  v1.1
QThread workers for video and audio conversion.

TVO fix: use run_tvo_conversion() multi-stage path; pipe all ffmpeg
stderr lines to the UI log in real time.
"""

import os
from PyQt5.QtCore import QThread, pyqtSignal

from utils.ffmpeg_utils import (
    run_conversion,
    run_tvo_conversion,
    build_video_convert_cmd,
    build_audio_convert_cmd,
    get_media_info,
    FFMPEG_PATH,
)
from utils.formats import is_tvo


class ConversionJob:
    def __init__(self, input_path: str, output_path: str, settings: dict):
        self.input_path  = input_path
        self.output_path = output_path
        self.settings    = settings
        self.success     = False
        self.error       = ""


class VideoConversionWorker(QThread):
    job_started = pyqtSignal(int, str)      # (index, filename)
    progress    = pyqtSignal(int, int)       # (job_index, 0-100)
    job_done    = pyqtSignal(int, bool, str) # (index, success, message)
    batch_done  = pyqtSignal(int, int)       # (succeeded, total)
    log_line    = pyqtSignal(str)

    def __init__(self, jobs: list, parent=None):
        super().__init__(parent)
        self.jobs    = jobs
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        succeeded = 0
        total     = len(self.jobs)

        for idx, job in enumerate(self.jobs):
            if self._cancel:
                break

            fname = os.path.basename(job.input_path)
            self.job_started.emit(idx, fname)
            self.log_line.emit(f">> [{idx+1}/{total}] {fname}")

            # Probe duration for progress (best-effort; 0 = indeterminate)
            info     = get_media_info(job.input_path)
            duration = info.get("duration_sec", 0.0)

            s      = job.settings
            vcodec = s.get("vcodec", "libx264")
            acodec = s.get("acodec", "aac")
            crf    = s.get("crf",    "23")
            preset = s.get("preset", "medium")

            def _log(line, i=idx):
                self.log_line.emit(line)

            def _prog(pct, i=idx):
                self.progress.emit(i, pct)

            def _cancel():
                return self._cancel

            if is_tvo(job.input_path):
                # ── Multi-stage TVO path ──────────────────────────
                self.log_line.emit(f"   TVO legacy file detected — running multi-stage decode")
                success, error = run_tvo_conversion(
                    input_path        = job.input_path,
                    output_path       = job.output_path,
                    vcodec            = vcodec,
                    acodec            = acodec,
                    crf               = crf,
                    preset            = preset,
                    progress_callback = _prog,
                    cancel_check      = _cancel,
                    log_callback      = _log,
                )
            else:
                # ── Standard path ─────────────────────────────────
                cmd = build_video_convert_cmd(
                    input_path  = job.input_path,
                    output_path = job.output_path,
                    vcodec      = vcodec,
                    acodec      = acodec,
                    crf         = crf,
                    preset      = preset,
                    resolution  = s.get("resolution"),
                )
                self.log_line.emit(f"   CMD: {' '.join(cmd)}")
                success, error = run_conversion(
                    cmd               = cmd,
                    progress_callback = _prog,
                    cancel_check      = _cancel,
                    duration_sec      = duration,
                    log_callback      = _log,
                )

            job.success = success
            job.error   = error

            if success:
                succeeded += 1
                self.job_done.emit(idx, True, "")
                self.log_line.emit(f"   ✓ Done → {job.output_path}")
            else:
                self.job_done.emit(idx, False, error)
                # Surface the actual ffmpeg error to the UI
                self.log_line.emit(f"   ✗ FAILED: {fname}")
                for line in error.splitlines()[-8:]:
                    if line.strip():
                        self.log_line.emit(f"     {line}")

        self.batch_done.emit(succeeded, total)


class AudioConversionWorker(QThread):
    job_started = pyqtSignal(int, str)
    progress    = pyqtSignal(int, int)
    job_done    = pyqtSignal(int, bool, str)
    batch_done  = pyqtSignal(int, int)
    log_line    = pyqtSignal(str)

    def __init__(self, jobs: list, parent=None):
        super().__init__(parent)
        self.jobs    = jobs
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        succeeded = 0
        total     = len(self.jobs)

        for idx, job in enumerate(self.jobs):
            if self._cancel:
                break

            fname = os.path.basename(job.input_path)
            self.job_started.emit(idx, fname)
            self.log_line.emit(f">> [{idx+1}/{total}] {fname}")

            info     = get_media_info(job.input_path)
            duration = info.get("duration_sec", 0.0)

            s   = job.settings
            cmd = build_audio_convert_cmd(
                input_path  = job.input_path,
                output_path = job.output_path,
                acodec      = s.get("acodec", "libmp3lame"),
                bitrate     = s.get("bitrate", "192k"),
            )
            self.log_line.emit(f"   CMD: {' '.join(cmd)}")

            success, error = run_conversion(
                cmd               = cmd,
                progress_callback = lambda pct, i=idx: self.progress.emit(i, pct),
                cancel_check      = lambda: self._cancel,
                duration_sec      = duration,
                log_callback      = lambda line: self.log_line.emit(line),
            )

            job.success = success
            job.error   = error

            if success:
                succeeded += 1
                self.job_done.emit(idx, True, "")
            else:
                self.job_done.emit(idx, False, error)
                self.log_line.emit(f"   ✗ FAILED: {fname}")
                for line in error.splitlines()[-8:]:
                    if line.strip():
                        self.log_line.emit(f"     {line}")

        self.batch_done.emit(succeeded, total)


class ProbeWorker(QThread):
    file_probed = pyqtSignal(str, dict)
    all_done    = pyqtSignal()

    def __init__(self, paths: list, parent=None):
        super().__init__(parent)
        self.paths = paths

    def run(self):
        for path in self.paths:
            info = get_media_info(path)
            self.file_probed.emit(path, info)
        self.all_done.emit()
