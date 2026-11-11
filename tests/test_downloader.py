import sys
import types

import pytest
import yt_dlp

from ytaudio_downloader import downloader
from ytaudio_downloader.downloader import (
    DownloaderError,
    YtDlpLogger,
    check_ffmpeg,
    download_audio,
    progress_hook,
)

VIDEO_URL = "https://youtu.be/AbCdEf12345"


def test_default_download_dir_is_user_downloads():
    assert downloader.DOWNLOAD_DIR == downloader.Path.home() / "Downloads"


# ---------- check_ffmpeg ----------

def test_check_ffmpeg_ok_when_on_path(monkeypatch):
    monkeypatch.setattr(downloader.shutil, "which", lambda t: f"/bin/{t}")
    # static_ffmpeg must not be needed
    monkeypatch.setitem(sys.modules, "static_ffmpeg", None)
    check_ffmpeg()


def test_check_ffmpeg_uses_static_ffmpeg_when_missing(monkeypatch):
    available = {"ready": False}

    def fake_which(tool):
        return f"/bin/{tool}" if available["ready"] else None

    def fake_add_paths():
        available["ready"] = True

    fake = types.SimpleNamespace(add_paths=fake_add_paths)
    monkeypatch.setattr(downloader.shutil, "which", fake_which)
    monkeypatch.setitem(sys.modules, "static_ffmpeg", fake)

    check_ffmpeg()
    assert available["ready"]


def test_check_ffmpeg_raises_when_unavailable(monkeypatch):
    def boom():
        raise RuntimeError("offline")

    monkeypatch.setattr(downloader.shutil, "which", lambda t: None)
    monkeypatch.setitem(
        sys.modules, "static_ffmpeg", types.SimpleNamespace(add_paths=boom)
    )

    with pytest.raises(DownloaderError, match="ffmpeg and ffprobe not found"):
        check_ffmpeg()


def test_check_ffmpeg_reports_only_missing_tool(monkeypatch):
    monkeypatch.setattr(
        downloader.shutil,
        "which",
        lambda t: "/bin/ffmpeg" if t == "ffmpeg" else None,
    )
    monkeypatch.setitem(
        sys.modules,
        "static_ffmpeg",
        types.SimpleNamespace(add_paths=lambda: None),
    )

    with pytest.raises(DownloaderError) as exc:
        check_ffmpeg()
    assert "ffprobe not found" in str(exc.value)
    assert "ffmpeg and" not in str(exc.value)


# ---------- progress_hook ----------

def test_progress_hook_prints_percent(capsys):
    progress_hook(
        {"status": "downloading", "downloaded_bytes": 50, "total_bytes": 200}
    )
    assert "25.0%" in capsys.readouterr().out


def test_progress_hook_uses_estimate(capsys):
    progress_hook(
        {
            "status": "downloading",
            "downloaded_bytes": 10,
            "total_bytes_estimate": 100,
        }
    )
    assert "10.0%" in capsys.readouterr().out


def test_progress_hook_unknown_total_prints_nothing(capsys):
    progress_hook({"status": "downloading", "downloaded_bytes": 10})
    assert capsys.readouterr().out == ""


def test_format_progress_bounds():
    assert downloader.format_progress(0, 3).endswith("  0%")
    assert downloader.format_progress(3, 3).endswith("100%")
    assert "-" not in downloader.format_progress(5, 3)


def test_postprocessor_hook_shows_overall_progress(capsys):
    hook = downloader.make_postprocessor_hook(2)
    hook({"status": "started"})
    hook({"status": "finished"})
    hook({"status": "started"})
    hook({"status": "finished"})
    out = capsys.readouterr().out
    assert "  0%" in out and " 50%" in out and "100%" in out
    assert out.endswith("\n")


def test_progress_hook_finished(capsys):
    progress_hook({"status": "finished"})
    assert "Converting to MP3" in capsys.readouterr().out


# ---------- YtDlpLogger ----------

def test_logger_routes_levels(caplog):
    caplog.set_level("DEBUG", logger=downloader.LOGGER.name)
    log = YtDlpLogger()
    log.debug("[debug] detail")
    log.debug("plain")
    log.warning("warn")
    log.error("err")

    levels = {r.getMessage(): r.levelname for r in caplog.records}
    assert levels["[debug] detail"] == "DEBUG"
    assert levels["plain"] == "INFO"
    assert levels["warn"] == "WARNING"
    assert levels["err"] == "ERROR"


# ---------- download_audio ----------

class FakeYDL:
    """Stand-in for yt_dlp.YoutubeDL; behaviour set via class attributes."""

    info = {"id": "AbCdEf12345"}
    error = None
    created_options = None
    downloaded = False

    def __init__(self, options):
        type(self).created_options = options

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def extract_info(self, url, download=True):
        if type(self).error:
            raise type(self).error
        return type(self).info

    def process_ie_result(self, info, download=True):
        type(self).downloaded = download
        return info


@pytest.fixture
def env(monkeypatch, tmp_path):
    monkeypatch.setattr(downloader, "DOWNLOAD_DIR", tmp_path / "downloads")
    monkeypatch.setattr(downloader, "check_ffmpeg", lambda: None)
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", FakeYDL)
    FakeYDL.info = {"id": "AbCdEf12345"}
    FakeYDL.error = None
    FakeYDL.created_options = None
    FakeYDL.downloaded = False
    return tmp_path / "downloads"


def test_download_audio_returns_mp3(env):
    env.mkdir()
    expected = env / "Title [AbCdEf12345].mp3"
    expected.write_bytes(b"x")
    (env / "Other [ZZZZZZZZZZZ].mp3").write_bytes(b"x")

    assert download_audio(VIDEO_URL) == expected


def test_download_audio_creates_dir_and_sets_options(env):
    with pytest.raises(DownloaderError):  # no mp3 produced by fake
        download_audio(VIDEO_URL)

    assert env.is_dir()
    opts = FakeYDL.created_options
    assert opts["noplaylist"] is True
    assert opts["overwrites"] is False
    pp = opts["postprocessors"][0]
    assert pp["key"] == "FFmpegExtractAudio"
    assert pp["preferredcodec"] == "mp3"
    assert pp["preferredquality"] == "320"


def test_download_audio_missing_mp3(env):
    with pytest.raises(DownloaderError, match="MP3 file not found"):
        download_audio(VIDEO_URL)


def test_download_audio_no_info(env):
    FakeYDL.info = None
    with pytest.raises(DownloaderError, match="Could not identify"):
        download_audio(VIDEO_URL)


def test_download_audio_info_without_id(env):
    FakeYDL.info = {"title": "x"}
    with pytest.raises(DownloaderError, match="Could not identify"):
        download_audio(VIDEO_URL)


def test_download_audio_wraps_download_error(env):
    FakeYDL.error = yt_dlp.utils.DownloadError("private video")
    with pytest.raises(DownloaderError, match="yt-dlp download failed"):
        download_audio(VIDEO_URL)


def test_download_audio_wraps_unexpected_error(env):
    FakeYDL.error = OSError("disk full")
    with pytest.raises(DownloaderError, match="extraction/conversion failed"):
        download_audio(VIDEO_URL)


@pytest.mark.parametrize("status", ["is_live", "is_upcoming"])
def test_download_audio_refuses_live_streams(env, status):
    FakeYDL.info = {"id": "AbCdEf12345", "live_status": status}
    with pytest.raises(DownloaderError, match="live stream"):
        download_audio(VIDEO_URL)
    assert FakeYDL.downloaded is False


@pytest.mark.parametrize("status", ["not_live", "was_live", "post_live"])
def test_download_audio_allows_finished_videos(env, status):
    env.mkdir()
    expected = env / "Title [AbCdEf12345].mp3"
    expected.write_bytes(b"x")
    FakeYDL.info = {"id": "AbCdEf12345", "live_status": status}

    assert download_audio(VIDEO_URL) == expected
    assert FakeYDL.downloaded is True


def test_download_audio_custom_output_dir(env, tmp_path):
    custom = tmp_path / "custom" / "out"
    custom.mkdir(parents=True)
    expected = custom / "Title [AbCdEf12345].mp3"
    expected.write_bytes(b"x")

    assert download_audio(VIDEO_URL, custom) == expected
    template = FakeYDL.created_options["outtmpl"]["default"]
    assert template.startswith(str(custom))
    assert not env.exists()  # default folder untouched


def test_download_audio_creates_custom_output_dir(env, tmp_path):
    custom = tmp_path / "new" / "folder"
    with pytest.raises(DownloaderError):  # fake produces no mp3
        download_audio(VIDEO_URL, str(custom))
    assert custom.is_dir()


def test_download_audio_checks_ffmpeg_first(monkeypatch, env):
    def fail():
        raise DownloaderError("no ffmpeg")

    monkeypatch.setattr(downloader, "check_ffmpeg", fail)
    with pytest.raises(DownloaderError, match="no ffmpeg"):
        download_audio(VIDEO_URL)
    assert FakeYDL.created_options is None


def test_download_audio_prefers_reported_filepath(env):
    env.mkdir()
    reported = env / "Reported [AbCdEf12345].mp3"
    reported.write_bytes(b"x")
    (env / "Newer [AbCdEf12345].mp3").write_bytes(b"x")
    FakeYDL.info = {
        "id": "AbCdEf12345",
        "requested_downloads": [{"filepath": str(reported)}],
    }

    assert download_audio(VIDEO_URL) == reported


def test_download_audio_ignores_stale_reported_filepath(env):
    env.mkdir()
    real = env / "Title [AbCdEf12345].mp3"
    real.write_bytes(b"x")
    FakeYDL.info = {
        "id": "AbCdEf12345",
        "requested_downloads": [
            {"filepath": str(env / "gone [AbCdEf12345].webm")}
        ],
    }

    assert download_audio(VIDEO_URL) == real


def test_download_audio_fallback_picks_newest(env):
    import os

    env.mkdir()
    old = env / "Zzz [AbCdEf12345].mp3"
    new = env / "Aaa [AbCdEf12345].mp3"
    old.write_bytes(b"x")
    new.write_bytes(b"x")
    os.utime(old, (1, 1))

    assert download_audio(VIDEO_URL) == new


def test_download_audio_output_dir_is_a_file(env, tmp_path):
    blocker = tmp_path / "not_a_dir"
    blocker.write_text("x")

    with pytest.raises(DownloaderError, match="Cannot use output folder"):
        download_audio(VIDEO_URL, blocker)
    assert FakeYDL.created_options is None


def test_check_ffmpeg_warns_when_bundled_setup_fails(monkeypatch, caplog):
    def boom():
        raise RuntimeError("offline")

    monkeypatch.setattr(downloader.shutil, "which", lambda t: None)
    monkeypatch.setitem(
        sys.modules, "static_ffmpeg", types.SimpleNamespace(add_paths=boom)
    )

    with caplog.at_level("WARNING", logger=downloader.LOGGER.name):
        with pytest.raises(DownloaderError):
            check_ffmpeg()
    assert "offline" in caplog.text
