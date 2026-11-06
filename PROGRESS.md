# PROGRESS — YouTup2MP3 / ytaudio (read first when resuming)

Updated: 2026-11-06 | Branch: main | Version: 1.1.0 | Last commit: see `git log` | Remote: github.com/GRich1575/YouTup2MP3 (origin/main). Project files live at the repo root; venv is `.venv/` there.

## What it is
CLI (`ytaudio`, also `python -m ytaudio_downloader`) that extracts authorized YouTube audio to 320 kbps MP3 via yt-dlp. Code in `src/ytaudio_downloader/` (`cli.py`, `downloader.py`, `validation.py`, `__main__.py`). Default output: user's Downloads folder (`DOWNLOAD_DIR` in `downloader.py`); override with `-o/--output DIR`.

## Run / test
- `.venv\Scripts\Activate.ps1`, then `pip install -e ".[dev]"`.
- Tests: `python -m pytest -q` (49 passed; yt-dlp and ffmpeg mocked, offline).
- Real-network tests (opt-in): set `YTAUDIO_TEST_URL` to an authorized non-live video URL, then `python -m pytest -m network -q`. Skipped when unset. No video URLs are stored in the repo (only fake placeholder IDs in unit tests/README).
- CI: `.github/workflows/tests.yml` (offline tests, Ubuntu + Windows, Python 3.10 and 3.13). Not yet confirmed green on GitHub: check the Actions tab.

## FFmpeg
- `check_ffmpeg()` uses ffmpeg/ffprobe from PATH if present; otherwise `static-ffmpeg` downloads them on first run (needs internet). Verified end to end with system ffmpeg hidden.
- Dev machine: system copy at `C:\Tools\ffmpeg\bin` (user PATH).

## Behaviour notes
- Live (`is_live`) and upcoming streams are refused with exit code 1 (they would record in real time forever). Unit-tested; not exercised against a real live stream.
- Exit codes: 0 ok, 1 download error, 2 bad input/EOF, 130 Ctrl+C.
- yt-dlp warns about a missing JS runtime (Deno); optional fix: install to `C:\Tools\deno`.

## Done (2026-11-06)
- Test investigation, bundled ffmpeg (static-ffmpeg), unit + integration tests, README rewrite, repo flattened to root, default output = Downloads, real video links removed.
- v1.1.0: live-stream guard, `--output`, `python -m` entry, EOF/Ctrl+C handling at the prompt, packaging metadata (dynamic version from `__version__`), CI workflow.
- MIT LICENSE added (copyright 2026 G.Rich); referenced in pyproject and README.
- Real downloads verified with `-o` custom folder (normal video and a finished former live stream).

## Open
1. Git history still contains the real video links removed from the files (rewrite needs a force-push; not done).
2. Empty leftover folder `youtube-audio-downloader/` in the working copy (untracked; delete it manually).

## Next steps
Check CI on GitHub; optionally install Deno; optional features (bitrate flag, batch URLs).

## Update rule
Refresh this file at the end of every working session/milestone (date, branch, last commit, done, open, next). Keep ≤60 lines; no secrets.
