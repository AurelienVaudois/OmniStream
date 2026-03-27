"""Load normalized data into SQLite.

Handles upsert logic for dimensions and idempotent inserts for fact_streams.
"""

import sqlite3
from datetime import datetime

from .models import Category, RawPlaylist, RawStream
from .normalize import normalize_artist, normalize_title


def get_or_create_artist(conn: sqlite3.Connection, artist_name: str) -> int:
    """Find or create an artist, return artist_id."""
    name_norm = normalize_artist(artist_name)
    row = conn.execute(
        "SELECT artist_id FROM dim_artists WHERE name_normalized = ?", (name_norm,)
    ).fetchone()
    if row:
        return row["artist_id"]
    cursor = conn.execute(
        "INSERT INTO dim_artists (name, name_normalized, first_seen_date) VALUES (?, ?, ?)",
        (artist_name, name_norm, datetime.now().isoformat()[:10]),
    )
    return cursor.lastrowid


def get_or_create_track(
    conn: sqlite3.Connection,
    title: str,
    artist_id: int,
    album: str | None,
    category: Category,
    duration_ms: int | None = None,
) -> int:
    """Find or create a track, return track_id.

    Matching is done on normalized title + artist_id.
    """
    title_norm = normalize_title(title)
    row = conn.execute(
        "SELECT track_id FROM dim_tracks WHERE title_normalized = ? AND artist_id = ?",
        (title_norm, artist_id),
    ).fetchone()
    if row:
        return row["track_id"]
    cursor = conn.execute(
        """INSERT INTO dim_tracks (title, title_normalized, artist_id, album, category, duration_ms)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (title, title_norm, artist_id, album, category.value, duration_ms),
    )
    return cursor.lastrowid


def insert_stream(conn: sqlite3.Connection, stream: RawStream, track_id: int) -> int | None:
    """Insert a stream event. Returns stream_id or None if duplicate."""
    # Idempotency check: same track, same timestamp, same account = duplicate
    existing = conn.execute(
        """SELECT stream_id FROM fact_streams
        WHERE track_id = ? AND timestamp = ? AND account_id = ?""",
        (track_id, stream.timestamp.isoformat(), stream.account_id),
    ).fetchone()
    if existing:
        return None
    cursor = conn.execute(
        """INSERT INTO fact_streams (track_id, timestamp, ms_played, platform, account_id, source_file)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (
            track_id,
            stream.timestamp.isoformat(),
            stream.ms_played,
            stream.platform.value,
            stream.account_id,
            stream.source_file,
        ),
    )
    return cursor.lastrowid


def ensure_account(conn: sqlite3.Connection, account_id: str, platform: str) -> None:
    """Ensure an account exists in dim_accounts."""
    existing = conn.execute(
        "SELECT account_id FROM dim_accounts WHERE account_id = ?", (account_id,)
    ).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO dim_accounts (account_id, platform, label) VALUES (?, ?, ?)",
            (account_id, platform, account_id),
        )


def load_streams(conn: sqlite3.Connection, streams: list[RawStream]) -> dict:
    """Load a batch of RawStreams into the database.

    Returns stats: {inserted, skipped, tracks_created, artists_created}.
    """
    stats = {"inserted": 0, "skipped": 0, "tracks_created": 0, "artists_created": 0}
    artists_before = conn.execute("SELECT COUNT(*) FROM dim_artists").fetchone()[0]
    tracks_before = conn.execute("SELECT COUNT(*) FROM dim_tracks").fetchone()[0]

    for stream in streams:
        ensure_account(conn, stream.account_id, stream.platform.value)
        artist_id = get_or_create_artist(conn, stream.artist)
        track_id = get_or_create_track(
            conn, stream.title, artist_id, stream.album, stream.category
        )
        result = insert_stream(conn, stream, track_id)
        if result is not None:
            stats["inserted"] += 1
        else:
            stats["skipped"] += 1

    conn.commit()
    stats["artists_created"] = (
        conn.execute("SELECT COUNT(*) FROM dim_artists").fetchone()[0] - artists_before
    )
    stats["tracks_created"] = (
        conn.execute("SELECT COUNT(*) FROM dim_tracks").fetchone()[0] - tracks_before
    )
    return stats


def load_playlist(conn: sqlite3.Connection, playlist: RawPlaylist) -> int:
    """Load a playlist and its tracks into the database. Returns playlist_id."""
    ensure_account(conn, playlist.account_id, playlist.platform.value)
    snapshot_date = datetime.now().isoformat()[:10]
    cursor = conn.execute(
        """INSERT INTO dim_playlists
        (name, platform, account_id, description, is_liked_songs, track_count, snapshot_date, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            playlist.name,
            playlist.platform.value,
            playlist.account_id,
            playlist.description,
            1 if playlist.is_liked_songs else 0,
            len(playlist.tracks),
            snapshot_date,
            playlist.source,
        ),
    )
    playlist_id = cursor.lastrowid

    for pt in playlist.tracks:
        artist_id = get_or_create_artist(conn, pt.artist)
        track_id = get_or_create_track(conn, pt.title, artist_id, pt.album, Category.MUSIC)
        conn.execute(
            """INSERT OR IGNORE INTO playlist_tracks (playlist_id, track_id, position, added_at)
            VALUES (?, ?, ?, ?)""",
            (
                playlist_id,
                track_id,
                pt.position,
                pt.added_at.isoformat() if pt.added_at else None,
            ),
        )

    conn.commit()
    return playlist_id
