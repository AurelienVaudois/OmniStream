"""Parser for Spotify Extended Streaming History (GDPR export).

Expected file format: JSON array of objects with fields like:
- ts: timestamp (ISO 8601)
- ms_played: milliseconds played
- master_metadata_track_name: track title (null for podcasts)
- master_metadata_album_artist_name: artist name
- master_metadata_album_album_name: album name
- episode_name: podcast episode name (null for music)
- episode_show_name: podcast show name (null for music)
- reason_start, reason_end: why playback started/ended
"""

import json
from datetime import datetime
from pathlib import Path

from ..models import Category, Platform, RawStream


def parse_spotify_export(
    export_dir: Path,
    account_id: str,
    min_ms_played: int = 30000,
) -> list[RawStream]:
    """Parse all Spotify Extended Streaming History JSON files in a directory.

    Args:
        export_dir: Directory containing StreamingHistory_music_*.json files
        account_id: Account identifier (e.g. "spotify_perso")
        min_ms_played: Minimum ms to consider a valid listen (default 30s)

    Returns:
        List of RawStream objects
    """
    streams = []
    json_files = sorted(export_dir.glob("Streaming_History_Audio_*.json"))
    if not json_files:
        # Try older file naming convention
        json_files = sorted(export_dir.glob("StreamingHistory_music_*.json"))
    if not json_files:
        json_files = sorted(export_dir.glob("StreamingHistory*.json"))

    for filepath in json_files:
        with open(filepath, encoding="utf-8") as f:
            entries = json.load(f)

        for entry in entries:
            ms_played = entry.get("ms_played", 0)
            if ms_played < min_ms_played:
                continue

            # Determine category
            episode_name = entry.get("episode_name")
            track_name = entry.get("master_metadata_track_name")

            if episode_name and not track_name:
                category = Category.PODCAST
                title = episode_name
                artist = entry.get("episode_show_name", "Unknown Podcast")
                album = None
            elif track_name:
                category = Category.MUSIC
                title = track_name
                artist = entry.get("master_metadata_album_artist_name", "Unknown Artist")
                album = entry.get("master_metadata_album_album_name")
            else:
                continue  # Skip entries with no identifiable content

            timestamp = datetime.fromisoformat(entry["ts"].replace("Z", "+00:00"))

            streams.append(
                RawStream(
                    title=title,
                    artist=artist,
                    album=album,
                    timestamp=timestamp,
                    ms_played=ms_played,
                    platform=Platform.SPOTIFY,
                    account_id=account_id,
                    source_file=filepath.name,
                    category=category,
                )
            )

    return streams
