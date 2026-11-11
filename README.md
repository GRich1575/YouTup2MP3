# YouTube Audio Downloader (`ytaudio`)

Command-line tool that extracts the audio of **one** authorized YouTube
video, converts it to **MP3 (320 kbps target)** and saves it in the
your user **Downloads** folder (`C:\Users\<username>\Downloads` on
Windows, `~/Downloads` elsewhere). Title, uploader and cover art are embedded
when available.

Use only for content you own or are authorized to download, and comply
with YouTube's terms and applicable law. This tool does not bypass DRM,
access controls, or paid-content restrictions.

## Quick start

Requires Python 3.10+ and an internet connection. FFmpeg is **not**
required: it is downloaded automatically on first run if missing.

**Windows (PowerShell)**

    git clone https://github.com/GRich1575/YouTup2MP3.git
    cd YouTup2MP3
    py -3 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install -e ".[dev]"
    ytaudio "https://www.youtube.com/watch?v=VIDEO_ID"

**macOS / Linux**

    git clone https://github.com/GRich1575/YouTup2MP3.git
    cd YouTup2MP3
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -e ".[dev]"
    ytaudio "https://www.youtube.com/watch?v=VIDEO_ID"

Run `ytaudio` with no argument to be prompted for the URL.
`python -m ytaudio_downloader <url>` works too.

Options:

    -o, --output DIR    save the MP3 in DIR instead of your Downloads folder
    --verbose           detailed logging
    --version           print the version
    -h, --help          show help

Example: `ytaudio -o "D:\Music" "<video url>"`

If PowerShell blocks activation, run this once in that window:

    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

## What a run looks like

    ==========================================================
                 YOUTUBE AUDIO DOWNLOADER
    ==========================================================
    Output folder: C:\Users\<username>\Downloads
    Format: MP3 | Target bitrate: 320 kbps

    Downloading: 100.0%
    Download complete. Converting to MP3...
    Converting: [##############################] 100%

    Success!
    MP3 saved to: C:\Users\<username>\Downloads\Artist - Title [VIDEO_ID].mp3

Exit codes: `0` success, `1` download/conversion error (including a
stream that has not ended), `2` invalid or missing input, `130` cancelled
with Ctrl+C.

## Features

- One video per run; playlist downloads are disabled. Extra link
  parameters such as `&list=...` are ignored.
- Embeds title, artist/uploader metadata and thumbnail artwork when the
  source provides them (nothing is invented when unavailable).
- Windows-friendly file names that include the video ID.
- Input validation (only `youtube.com` and `youtu.be` links) with clear
  error messages.
- Choose the output folder with `-o/--output`.
- Live streams and unstarted premieres are refused (see below).
- Automatic FFmpeg setup: a system FFmpeg/FFprobe on PATH is used if
  present; otherwise the `static-ffmpeg` dependency downloads them once
  (needs internet) and later runs reuse them. These binaries are fetched
  over the network without a checksum check; install FFmpeg yourself if
  that is a concern.

320 kbps is an encoding target; converting a lower-quality source does not
restore missing audio quality.

## Live streams

A stream that is still live, or a premiere that has not started, is
refused with a clear message instead of recording in real time and never
finishing. Wait until the broadcast has ended (YouTube then publishes it
as a normal video) and run the tool again.

To check a link yourself:

    python -m yt_dlp --skip-download --print live_status "URL"

`is_live` and `is_upcoming` are refused; `not_live`, `was_live` and
`post_live` are downloaded.

## Tests

    python -m pytest

The default run is offline (yt-dlp and FFmpeg are mocked). Opt-in tests
that download a real video and verify the MP3 with ffprobe need internet
and a video URL you are authorized to download (a normal, non-live
video). No URL is stored in the repo; pass it through the environment:

    # PowerShell
    $env:YTAUDIO_TEST_URL = "<video url>"
    python -m pytest -m network

    # macOS / Linux
    YTAUDIO_TEST_URL="<video url>" python -m pytest -m network

Without the variable these tests are skipped.

## Troubleshooting

- **FFmpeg or FFprobe not found** and automatic setup failed (for example,
  no internet on first run): reconnect and rerun, or install FFmpeg
  yourself, add its `bin` folder to PATH and restart the terminal.
  On Windows: `winget install --id Gyan.FFmpeg`.
- **Downloads fail:** update yt-dlp:

      python -m pip install --upgrade "yt-dlp[default]"

- **"This video is a live stream ... that has not ended":** wait for the
  broadcast to finish, then rerun (see Live streams above).
- **"No JavaScript runtime" warning from yt-dlp:** downloads usually still
  work; installing Deno silences it.
- Some videos expose no thumbnail or artist metadata.
- Make sure the video is available and you have permission to download it.

## Project layout

    src/ytaudio_downloader/   application code
        cli.py                command-line entry point (`ytaudio`)
        __main__.py           enables `python -m ytaudio_downloader`
        downloader.py         yt-dlp download + MP3 conversion, FFmpeg setup
        validation.py         URL validation
    tests/                    unit tests and opt-in network tests
    .github/workflows/        CI: offline tests on Linux and Windows
    pyproject.toml            package metadata, dependencies, pytest config
    requirements.txt          runtime dependencies
    PROGRESS.md               development status notes
    LICENSE                   MIT license

## License

MIT, see [LICENSE](LICENSE). The license covers this tool's code only; it
does not grant any right to download content you are not authorized to
download.
