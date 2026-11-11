"""Audio extraction and MP3 conversion using yt-dlp and FFmpeg."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

import yt_dlp

LOGGER = logging.getLogger(__name__)

# Default output: the current user's Downloads folder
# (e.g. C:\Users\<username>\Downloads on Windows).
DOWNLOAD_DIR = Path.home() / "Downloads"

# yt-dlp `live_status` values that must not be downloaded yet.
LIVE_STATUSES = {"is_live", "is_upcoming"}

AUDIO_FORMAT = "mp3"
AUDIO_BITRATE_KBPS = "320"


class DownloaderError(RuntimeError):
    """Raised when downloading or conversion fails."""


def _missing_tools() -> list[str]:
    return [
        tool
        for tool in ("ffmpeg", "ffprobe")
        if shutil.which(tool) is None
    ]


def check_ffmpeg() -> None:
    # Prefer a system FFmpeg; otherwise fetch bundled binaries on first use.
    if _missing_tools():
        try:
            import static_ffmpeg

            print("FFmpeg not found on PATH; preparing bundled copy "
                  "(first run downloads it)...")
            static_ffmpeg.add_paths()
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning(
                "Could not set up bundled FFmpeg (offline or blocked?): %s",
                exc,
            )

    missing = [
        tool
        for tool in ("ffmpeg", "ffprobe")
        if shutil.which(tool) is None
    ]

    if missing:
        raise DownloaderError(
            f"{' and '.join(missing)} not found. "
            "Install FFmpeg and add its bin directory to PATH."
        )


def progress_hook(data: dict[str, Any]) -> None:
    if data.get("status") == "downloading":
        total = data.get("total_bytes") or data.get(
            "total_bytes_estimate"
        )
        downloaded = data.get("downloaded_bytes", 0)

        if total:
            percent = downloaded * 100 / total
            print(
                f"\rDownloading: {percent:5.1f}%",
                end="",
                flush=True,
            )

    elif data.get("status") == "finished":
        print("\nDownload complete. Converting to MP3...")


BAR_WIDTH = 30


def format_progress(done: int, total: int) -> str:
    """Render a text progress bar with a percentage, e.g. ``[###---] 50%``."""
    total = max(total, 1)
    done = min(max(done, 0), total)
    filled = BAR_WIDTH * done // total
    bar = "#" * filled + "-" * (BAR_WIDTH - filled)
    return f"[{bar}] {done * 100 // total:3d}%"


def make_postprocessor_hook(total_steps: int):
    """Return a hook showing overall conversion progress.

    yt-dlp reports no byte-level progress for FFmpeg, so progress is the
    share of post-processing steps (convert, metadata, thumbnail) finished.
    """
    finished = 0

    def hook(data: dict[str, Any]) -> None:
        nonlocal finished
        status = data.get("status")
        if status == "started":
            print(
                f"\rConverting: {format_progress(finished, total_steps)}",
                end="",
                flush=True,
            )
        elif status == "finished":
            finished += 1
            end = "\n" if finished >= total_steps else ""
            print(
                f"\rConverting: {format_progress(finished, total_steps)}",
                end=end,
                flush=True,
            )

    return hook


class YtDlpLogger:

    def debug(self, message: str) -> None:
        if message.startswith("[debug]"):
            LOGGER.debug(message)
        else:
            LOGGER.info(message)

    def info(self, message: str) -> None:
        LOGGER.info(message)

    def warning(self, message: str) -> None:
        LOGGER.warning(message)

    def error(self, message: str) -> None:
        LOGGER.error(message)


def download_audio(url: str, output_dir: Path | str | None = None) -> Path:
    """Download one video's audio as MP3 and return the file path.

    ``output_dir`` defaults to ``DOWNLOAD_DIR`` (the user's Downloads).
    Live and upcoming streams are refused: they would record in real time
    and never finish until the broadcast ends.
    """
    check_ffmpeg()
    target_dir = (
        Path(output_dir).expanduser() if output_dir else DOWNLOAD_DIR
    )
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DownloaderError(
            f"Cannot use output folder {target_dir}: {exc}"
        ) from exc

    postprocessors = [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": AUDIO_FORMAT,
            "preferredquality": AUDIO_BITRATE_KBPS,
        },
        {
            "key": "FFmpegMetadata",
            "add_metadata": True,
            "add_chapters": True,
        },
        {
            "key": "EmbedThumbnail",
        },
    ]

    options = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "outtmpl": {
            "default": str(
                target_dir / "%(title).180B [%(id)s].%(ext)s"
            )
        },
        "windowsfilenames": True,
        "overwrites": False,
        "continuedl": True,
        "writethumbnail": True,
        "progress_hooks": [progress_hook],
        "postprocessor_hooks": [
            make_postprocessor_hook(len(postprocessors))
        ],
        "postprocessors": postprocessors,
        "quiet": True,
        "no_warnings": False,
        "logger": YtDlpLogger(),
    }

    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(url, download=False)

            if info and info.get("live_status") in LIVE_STATUSES:
                raise DownloaderError(
                    "This video is a live stream (or a scheduled premiere) "
                    "that has not ended. Wait until the broadcast is over, "
                    "then run the tool again."
                )

            if info:
                info = downloader.process_ie_result(info, download=True)

    except DownloaderError:
        raise

    except yt_dlp.utils.DownloadError as exc:
        raise DownloaderError(
            f"yt-dlp download failed: {exc}"
        ) from exc

    except Exception as exc:
        raise DownloaderError(
            f"Audio extraction/conversion failed: {exc}"
        ) from exc

    if not info or not info.get("id"):
        raise DownloaderError("Could not identify the downloaded video.")

    return _locate_mp3(info, target_dir)


def _locate_mp3(info: dict[str, Any], target_dir: Path) -> Path:
    """Return the MP3 yt-dlp produced, preferring its reported path."""
    for item in info.get("requested_downloads") or []:
        reported = item.get("filepath")
        if reported and Path(reported).suffix == ".mp3":
            path = Path(reported)
            if path.is_file():
                return path

    # Fallback: newest MP3 in the folder carrying this video's ID.
    suffix = f"[{info['id']}].mp3"
    matches = sorted(
        (
            path
            for path in target_dir.glob("*.mp3")
            if path.name.endswith(suffix)
        ),
        key=lambda path: (path.stat().st_mtime, path.name),
    )

    if not matches:
        raise DownloaderError(f"MP3 file not found in {target_dir}")

    return matches[-1]
