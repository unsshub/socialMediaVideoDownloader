from smvd.downloader import _categorize
from smvd.jobs import Failure


def test_categorize_unsupported_url():
    error, _ = _categorize("Unsupported URL: example.com is not supported")
    assert error == Failure.UNSUPPORTED_URL


def test_categorize_private():
    error, _ = _categorize("ERROR: This video is private. Login required.")
    assert error == Failure.PRIVATE


def test_categorize_youtube_age_restricted_or_members_only():
    error, _ = _categorize("ERROR: [youtube] abc: Sign in to confirm your age. This video may be inappropriate.")
    assert error == Failure.PRIVATE
    error2, _ = _categorize("ERROR: [youtube] abc: Join this channel to get access to members-only content.")
    assert error2 == Failure.PRIVATE


def test_categorize_unavailable_deleted():
    error, _ = _categorize("ERROR: Video unavailable. This video has been removed.")
    assert error == Failure.UNAVAILABLE


def test_categorize_youtube_unavailable():
    error, _ = _categorize("ERROR: [youtube] abc: Video unavailable. This video is no longer available.")
    assert error == Failure.UNAVAILABLE


def test_categorize_unavailable_geo():
    error, _ = _categorize("ERROR: This video is geo-restricted and cannot be viewed.")
    assert error == Failure.UNAVAILABLE


def test_categorize_network_dns():
    error, _ = _categorize("ERROR: Unable to download webpage: Name or service not known")
    assert error == Failure.NETWORK


def test_categorize_network_connection():
    error, _ = _categorize("ERROR: Unable to connect to the server, connection timed out")
    assert error == Failure.NETWORK


def test_categorize_other():
    error, message = _categorize("ERROR: some bizarre yt-dlp internal failure")
    assert error == Failure.OTHER
    assert message  # message is retained


def test_extract_url_from_share_text():
    from smvd.downloader import extract_url

    text = "OMG check this out https://vm.tiktok.com/abc/xyz! more text"
    assert extract_url(text) == "https://vm.tiktok.com/abc/xyz"


def test_extract_url_none_when_missing():
    from smvd.downloader import extract_url

    assert extract_url("no url here") is None


def test_extract_url_first_url():
    from smvd.downloader import extract_url

    assert extract_url("https://a.com/1 and https://b.com/2") == "https://a.com/1"


def test_extract_youtube_urls():
    from smvd.downloader import extract_url

    assert (
        extract_url("Watch this: https://www.youtube.com/watch?v=dQw4w9WgXcQ.")
        == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    assert extract_url("https://youtu.be/dQw4w9WgXcQ?si=12345") == "https://youtu.be/dQw4w9WgXcQ?si=12345"
    assert (
        extract_url("Check out this short https://www.youtube.com/shorts/abc123xyz!")
        == "https://www.youtube.com/shorts/abc123xyz"
    )
