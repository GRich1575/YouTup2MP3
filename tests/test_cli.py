from pathlib import Path

import pytest

from ytaudio_downloader import __version__, cli
from ytaudio_downloader.downloader import DownloaderError

URL = "https://www.youtube.com/watch?v=AbCdEf12345"


def run(monkeypatch, *argv):
    monkeypatch.setattr("sys.argv", ["ytaudio", *argv])
    return cli.main()


def test_success(monkeypatch, capsys):
    monkeypatch.setattr(cli, "download_audio", lambda u, d: Path("out.mp3"))
    assert run(monkeypatch, URL) == 0
    out = capsys.readouterr().out
    assert "Success!" in out
    assert "out.mp3" in out


def test_passes_validated_url(monkeypatch):
    seen = {}

    def fake(url, output_dir):
        seen["url"] = url
        seen["dir"] = output_dir
        return Path("x.mp3")

    monkeypatch.setattr(cli, "download_audio", fake)
    run(monkeypatch, f"  {URL}  ")
    assert seen["url"] == URL
    assert seen["dir"] == cli.DOWNLOAD_DIR


def test_output_option(monkeypatch, tmp_path, capsys):
    seen = {}

    def fake(url, output_dir):
        seen["dir"] = output_dir
        return Path("x.mp3")

    monkeypatch.setattr(cli, "download_audio", fake)
    assert run(monkeypatch, "-o", str(tmp_path), URL) == 0
    assert seen["dir"] == tmp_path
    assert str(tmp_path) in capsys.readouterr().out


def test_invalid_url_returns_2(monkeypatch, capsys):
    called = []
    monkeypatch.setattr(
        cli, "download_audio", lambda u, d: called.append(u)
    )
    assert run(monkeypatch, "https://example.com/watch?v=AbCdEf12345") == 2
    assert "Input error" in capsys.readouterr().err
    assert not called


def test_prompts_when_no_url(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: f" {URL} ")
    monkeypatch.setattr(cli, "download_audio", lambda u, d: Path("x.mp3"))
    assert run(monkeypatch) == 0


def test_closed_stdin_returns_2(monkeypatch, capsys):
    def eof(prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", eof)
    assert run(monkeypatch) == 2
    assert "no URL provided" in capsys.readouterr().err


def test_ctrl_c_at_prompt_returns_130(monkeypatch, capsys):
    def interrupt(prompt):
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", interrupt)
    assert run(monkeypatch) == 130
    assert "Cancelled" in capsys.readouterr().out


def test_empty_prompt_returns_2(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "")
    assert run(monkeypatch) == 2


def test_download_error_returns_1(monkeypatch, capsys):
    def fail(url, output_dir):
        raise DownloaderError("boom")

    monkeypatch.setattr(cli, "download_audio", fail)
    assert run(monkeypatch, URL) == 1
    assert "Download error: boom" in capsys.readouterr().err


def test_keyboard_interrupt_returns_130(monkeypatch, capsys):
    def interrupt(url, output_dir):
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "download_audio", interrupt)
    assert run(monkeypatch, URL) == 130
    assert "Cancelled" in capsys.readouterr().out


def test_version_flag(monkeypatch, capsys):
    with pytest.raises(SystemExit) as exc:
        run(monkeypatch, "--version")
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_parser_accepts_verbose():
    args = cli.build_parser().parse_args(["--verbose", URL])
    assert args.verbose is True
    assert args.url == URL
