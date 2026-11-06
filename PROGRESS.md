# PROGRESS — YouTup2MP3 / ytaudio (read first when resuming)

Updated: 2026-11-06 | Branch: main | Version: 1.1.0 | Last commit: see `git log` | Remote: github.com/GRich1575/YouTup2MP3 (origin/main). Project files live at the repo root; venv is `.venv/` there.

## What it is
CLI (`ytaudio`, also `python -m ytaudio_downloader`) that extracts authorized YouTube audio to 320 kbps MP3 via yt-dlp. Code in `src/ytaudio_downloader/` (`cli.py`, `downloader.py`, `validation.py`, `__main__.py`). Default output: user's Downloads folder (`DOWNLOAD_DIR` in `downloader.py`); override with `-o/--output DIR`.

## Run / test
- `.venv\Scripts\Activate.ps1`, then `pip install -e ".[dev]"`.
- Tests: `python -m pytest -q` (54 passed; yt-dlp and ffmpeg mocked, offline).
- Real-network tests (opt-in): set `YTAUDIO_TEST_URL` to an authorized non-live video URL, then `python -m pytest -m network -q`. Skipped when unset. No video URLs are stored in the repo (only fake placeholder IDs).
- CI: `.github/workflows/tests.yml` (offline tests, Ubuntu + Windows, Py 3.10/3.13; also weekly cron and manual dispatch). Earlier runs green. Optional `network` job runs only if repo secret `YTAUDIO_TEST_URL` is set (informational; YouTube may block CI IPs). `.github/dependabot.yml` updates pip + actions weekly.

## FFmpeg
- `check_ffmpeg()` uses ffmpeg/ffprobe from PATH if present; otherwise `static-ffmpeg` downloads them on first run (needs internet; no checksum, noted in README). Setup failures are logged as warnings.
- Dev machine: system copy at `C:\Tools\ffmpeg\bin` (user PATH).

## Behaviour notes
- Live (`is_live`) and upcoming streams are refused with exit code 1. Unit-tested only.
- Exit codes: 0 ok, 1 download error (incl. unusable output folder), 2 bad input/EOF, 130 Ctrl+C.
- Result path comes from yt-dlp `requested_downloads[0].filepath`; falls back to newest `*[id].mp3` in the folder.
- yt-dlp warns about a missing JS runtime (Deno); optional fix: install to `C:\Tools\deno`.

## Done (2026-11-06)
- v1.1.0 features, tests, README, MIT LICENSE, CI, flattened repo, real links removed (see git history).
- QC pass: output-folder OSError now -> DownloaderError; ffmpeg setup failure logged; Dependabot + weekly/network CI; MP3 lookup uses yt-dlp's reported path. +5 tests.
- Remote history was rewritten earlier: origin/main is clean (single root commit).

## Open
1. Local branch `backup-before-rewrite` still holds the old history with a real video ID (never pushed). Delete when no longer needed: `git branch -D backup-before-rewrite`.
2. GitHub may still serve old commit SHAs by URL until it garbage-collects them (contact support to purge if it matters).
3. QC changes are committed locally; push status: see `git status -sb`.

## Next steps
Optionally set repo secret `YTAUDIO_TEST_URL`; install Deno; optional features (bitrate flag, batch URLs); ruff/mypy in CI.

## Update rule
Refresh this file at the end of every working session/milestone (date, branch, last commit, done, open, next). Keep ≤60 lines; no secrets.
