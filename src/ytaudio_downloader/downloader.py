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
            LOGGER.debug("static-ffmpeg setup failed: %s", exc)

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
    target_dir.mkdir(parents=True, exist_ok=True)

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
        "postprocessors": [
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
        ],
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

    video_id = info["id"]
    suffix = f"[{video_id}].mp3"

    matches = sorted(
        path
        for path in target_dir.glob("*.mp3")
        if path.name.endswith(suffix)
    )

    if not matches:
        raise DownloaderError(
            f"MP3 file not found in {target_dir}"
        )

    return matches[-1]
