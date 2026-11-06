"""Real-network end-to-end tests. Deselected by default.

No video URL is stored in the repository. Provide one you are authorized
to download (a normal, non-live video) through the environment:

    PowerShell:  $env:YTAUDIO_TEST_URL = "<video url>"
    bash:        export YTAUDIO_TEST_URL="<video url>"

then run:  python -m pytest -m network -q

The URL may carry extra parameters (e.g. `&list=...`); only the single
video must be downloaded. Tests are skipped when the variable is unset.
"""

import json
import os
import shutil
import subprocess
from urllib.parse import parse_qs, urlparse

import pytest

from ytaudio_downloader import cli, downloader
from ytaudio_downloader.validation import validate_youtube_url

REAL_URL = os.environ.get("YTAUDIO_TEST_URL", "").strip()

pytestmark = [
    pytest.mark.network,
    pytest.mark.skipif(
        not REAL_URL, reason="set YTAUDIO_TEST_URL to run network tests"
    ),
]


def _video_id(url: str) -> str:
    parsed = urlparse(url)
    if parsed.hostname == "youtu.be":
        return parsed.path.strip("/")
    return parse_qs(parsed.query)["v"][0]


@pytest.fixture
def out_dir(monkeypatch, tmp_path):
    target = tmp_path / "downloads"
    monkeypatch.setattr(downloader, "DOWNLOAD_DIR", target)
    monkeypatch.setattr(cli, "DOWNLOAD_DIR", target)
    return target


def test_real_url_is_valid():
    assert validate_youtube_url(REAL_URL) == REAL_URL


def test_download_real_video_to_mp3(out_dir):
    video_id = _video_id(REAL_URL)
    result = downloader.download_audio(REAL_URL)

    assert result.exists()
    assert result.suffix == ".mp3"
    assert result.name.endswith(f"[{video_id}].mp3")
    assert result.parent == out_dir
    # Playlist/mix parameter must not trigger extra downloads.
    assert len(list(out_dir.glob("*.mp3"))) == 1

    probe = subprocess.run(
        [
            shutil.which("ffprobe"),
            "-v", "error",
            "-show_entries", "format=duration,format_name",
            "-of", "json",
            str(result),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    fmt = json.loads(probe.stdout)["format"]
    assert "mp3" in fmt["format_name"]
    assert float(fmt["duration"]) > 1


def test_cli_real_url_exit_code(monkeypatch, out_dir, capsys):
    video_id = _video_id(REAL_URL)
    monkeypatch.setattr("sys.argv", ["ytaudio", REAL_URL])
    assert cli.main() == 0
    assert "Success!" in capsys.readouterr().out
    assert list(out_dir.glob(f"*[[]{video_id}[]].mp3"))
