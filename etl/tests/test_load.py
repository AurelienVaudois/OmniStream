"""Tests for data loading into SQLite."""

from datetime import datetime

from src.db import init_db
from src.load import load_streams
from src.models import Category, Platform, RawStream


def _make_stream(**overrides) -> RawStream:
    defaults = {
        "title": "Get Lucky",
        "artist": "Daft Punk",
        "album": "Random Access Memories",
        "timestamp": datetime(2023, 6, 15, 14, 32, 10),
        "ms_played": 245000,
        "platform": Platform.SPOTIFY,
        "account_id": "spotify_test",
        "source_file": "test.json",
        "category": Category.MUSIC,
    }
    defaults.update(overrides)
    return RawStream(**defaults)


class TestLoadStreams:
    def setup_method(self):
        self.conn = init_db(db_path=None)  # In-memory won't work with file path
        # Use :memory: via direct connection
        import sqlite3
        from pathlib import Path
        from src.db import SCHEMA_PATH
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        self.conn.executescript(schema)

    def teardown_method(self):
        self.conn.close()

    def test_insert_single_stream(self):
        streams = [_make_stream()]
        stats = load_streams(self.conn, streams)
        assert stats["inserted"] == 1
        assert stats["skipped"] == 0

    def test_creates_artist_and_track(self):
        streams = [_make_stream()]
        stats = load_streams(self.conn, streams)
        assert stats["artists_created"] == 1
        assert stats["tracks_created"] == 1

        # Verify in DB
        artist = self.conn.execute("SELECT * FROM dim_artists").fetchone()
        assert artist["name"] == "Daft Punk"
        track = self.conn.execute("SELECT * FROM dim_tracks").fetchone()
        assert track["title"] == "Get Lucky"

    def test_idempotent_reinsert(self):
        streams = [_make_stream()]
        stats1 = load_streams(self.conn, streams)
        stats2 = load_streams(self.conn, streams)
        assert stats1["inserted"] == 1
        assert stats2["inserted"] == 0
        assert stats2["skipped"] == 1

        count = self.conn.execute("SELECT COUNT(*) FROM fact_streams").fetchone()[0]
        assert count == 1

    def test_deduplicates_artists_across_tracks(self):
        streams = [
            _make_stream(title="Get Lucky"),
            _make_stream(title="Instant Crush", timestamp=datetime(2023, 6, 15, 14, 40)),
        ]
        stats = load_streams(self.conn, streams)
        assert stats["artists_created"] == 1  # Same artist
        assert stats["tracks_created"] == 2
        assert stats["inserted"] == 2

    def test_creates_account(self):
        streams = [_make_stream()]
        load_streams(self.conn, streams)
        account = self.conn.execute("SELECT * FROM dim_accounts").fetchone()
        assert account["account_id"] == "spotify_test"
        assert account["platform"] == "spotify"

    def test_multiple_platforms(self):
        streams = [
            _make_stream(platform=Platform.SPOTIFY, account_id="spotify_test"),
            _make_stream(
                platform=Platform.YOUTUBE,
                account_id="youtube_test",
                timestamp=datetime(2023, 6, 16, 10, 0),
                ms_played=None,
            ),
        ]
        stats = load_streams(self.conn, streams)
        assert stats["inserted"] == 2
        accounts = self.conn.execute("SELECT COUNT(*) FROM dim_accounts").fetchone()[0]
        assert accounts == 2
