"""Command-line interface."""

import argparse
import logging
import sys
from pathlib import Path

from ytaudio_downloader import __version__
from ytaudio_downloader.downloader import (
    AUDIO_BITRATE_KBPS,
    DOWNLOAD_DIR,
    DownloaderError,
    download_audio,
)
from ytaudio_downloader.validation import validate_youtube_url


def build_parser():
    parser = argparse.ArgumentParser(
        prog="ytaudio",
        description=(
            f"Extract authorized YouTube audio to {AUDIO_BITRATE_KBPS} kbps "
            "MP3. Live streams are refused until they have ended."
        ),
    )

    parser.add_argument(
        "url",
        nargs="?",
        help="YouTube video URL (prompted for if omitted).",
    )

    parser.add_argument(
        "-o",
        "--output",
        metavar="DIR",
        help=f"Output folder (default: {DOWNLOAD_DIR}).",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable detailed logging.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    output_dir = (
        Path(args.output).expanduser() if args.output else DOWNLOAD_DIR
    )

    print("=" * 58)
    print("             YOUTUBE AUDIO DOWNLOADER")
    print("=" * 58)
    print(f"Output folder: {output_dir}")
    print(f"Format: MP3 | Target bitrate: {AUDIO_BITRATE_KBPS} kbps\n")

    try:
        url = args.url or input("Paste one YouTube video URL: ").strip()
        valid_url = validate_youtube_url(url)
        output_file = download_audio(valid_url, output_dir)

    except ValueError as exc:
        print(f"\nInput error: {exc}", file=sys.stderr)
        return 2

    except DownloaderError as exc:
        print(f"\nDownload error: {exc}", file=sys.stderr)
        return 1

    except EOFError:
        print("\nInput error: no URL provided.", file=sys.stderr)
        return 2

    except KeyboardInterrupt:
        print("\nCancelled.")
        return 130

    print("\nSuccess!")
    print(f"MP3 saved to: {output_file}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
