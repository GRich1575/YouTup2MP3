import pytest

from ytaudio_downloader.validation import validate_youtube_url


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=AbCdEf12345",
        "https://youtu.be/AbCdEf12345",
        "https://www.youtube.com/shorts/AbCdEf12345",
        "https://www.youtube.com/live/AbCdEf12345",
        "https://www.youtube.com/embed/AbCdEf12345",
    ],
)
def test_valid_urls(url):
    assert validate_youtube_url(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "",
        "not a url",
        "https://example.com/watch?v=AbCdEf12345",
        "https://www.youtube.com/playlist?list=PL123456789",
        "ftp://youtube.com/watch?v=AbCdEf12345",
        "https://youtube.com.evil.example/watch?v=AbCdEf12345",
    ],
)
def test_invalid_urls(url):
    with pytest.raises(ValueError):
        validate_youtube_url(url)


def test_strips_whitespace():
    url = "  https://youtu.be/AbCdEf12345  "
    assert validate_youtube_url(url) == url.strip()
