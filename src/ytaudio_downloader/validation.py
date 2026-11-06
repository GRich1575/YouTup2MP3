"""Validation for supported YouTube video URLs."""

from urllib.parse import parse_qs, urlparse
import re

ALLOWED_HOSTS = {"youtu.be"}

VIDEO_PATTERNS = (
    re.compile(r"^/shorts/([^/?#]+)"),
    re.compile(r"^/live/([^/?#]+)"),
    re.compile(r"^/embed/([^/?#]+)"),
)


def validate_youtube_url(url: str) -> str:
    candidate = (url or "").strip()

    if not candidate:
        raise ValueError("Please provide a YouTube video URL.")

    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower().rstrip(".")

    valid_host = (
        host in ALLOWED_HOSTS
        or host == "youtube.com"
        or host.endswith(".youtube.com")
    )

    if parsed.scheme not in {"http", "https"} or not valid_host:
        raise ValueError(
            "URL must be an HTTP(S) link from youtube.com or youtu.be."
        )

    video_id = None

    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/", 1)[0] or None

    elif parsed.path.rstrip("/") == "/watch":
        video_id = parse_qs(parsed.query).get("v", [None])[0]

    else:
        for pattern in VIDEO_PATTERNS:
            match = pattern.match(parsed.path)
            if match:
                video_id = match.group(1)
                break

    if not video_id:
        raise ValueError(
            "Could not find a video ID. Provide a video URL, not a playlist-only URL."
        )

    if not re.fullmatch(r"[A-Za-z0-9_-]{6,}", video_id):
        raise ValueError("Invalid-looking YouTube video ID.")

    return candidate
