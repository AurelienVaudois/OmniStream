"""Tests for platform parsers."""

from pathlib import Path

from src.models import Category, Platform
from src.parsers.spotify import parse_spotify_export
from src.parsers.youtube import parse_youtube_export

FIXTURES = Path(__file__).parent / "fixtures"


class TestSpotifyParser:
    def test_parses_music_tracks(self):
        streams = parse_spotify_export(FIXTURES, "spotify_test")
        # Fixture has 5 entries: 2 music (>30s), 1 skipped (<30s), 1 podcast, 1 music
        music = [s for s in streams if s.category == Category.MUSIC]
        assert len(music) == 3  # Get Lucky, Instant Crush, Bohemian Rhapsody

    def test_parses_podcasts(self):
        streams = parse_spotify_export(FIXTURES, "spotify_test")
        podcasts = [s for s in streams if s.category == Category.PODCAST]
        assert len(podcasts) == 1
        assert podcasts[0].title == "Episode 42 - La tech en 2023"
        assert podcasts[0].artist == "Tech Café"

    def test_skips_short_listens(self):
        streams = parse_spotify_export(FIXTURES, "spotify_test")
        titles = [s.title for s in streams]
        assert "Skipped Song" not in titles

    def test_metadata_correctness(self):
        streams = parse_spotify_export(FIXTURES, "spotify_test")
        get_lucky = next(s for s in streams if s.title == "Get Lucky")
        assert get_lucky.artist == "Daft Punk"
        assert get_lucky.album == "Random Access Memories"
        assert get_lucky.ms_played == 245000
        assert get_lucky.platform == Platform.SPOTIFY
        assert get_lucky.account_id == "spotify_test"

    def test_custom_min_ms_played(self):
        streams = parse_spotify_export(FIXTURES, "spotify_test", min_ms_played=0)
        assert len(streams) == 5  # All entries including the skipped one


class TestYouTubeParser:
    def test_parses_music(self):
        # Create a temp dir with watch-history.json
        streams = parse_youtube_export(FIXTURES, "youtube_test")
        music = [s for s in streams if s.category == Category.MUSIC]
        assert len(music) == 2  # Daft Punk (Topic) and Queen (YT Music header)

    def test_parses_videos(self):
        streams = parse_youtube_export(FIXTURES, "youtube_test")
        videos = [s for s in streams if s.category == Category.VIDEO]
        assert len(videos) == 1
        assert "Dashboard" in videos[0].title

    def test_strips_watched_prefix(self):
        streams = parse_youtube_export(FIXTURES, "youtube_test")
        for s in streams:
            assert not s.title.startswith("Watched")

    def test_strips_topic_from_artist(self):
        streams = parse_youtube_export(FIXTURES, "youtube_test")
        daft_punk = next(s for s in streams if "Daft Punk" in s.title)
        assert daft_punk.artist == "Daft Punk"

    def test_ms_played_is_none(self):
        streams = parse_youtube_export(FIXTURES, "youtube_test")
        for s in streams:
            assert s.ms_played is None
