"""Parser for Deezer GDPR data export.

Deezer exports typically include a CSV or JSON file with listening history.
Format can vary — this parser handles the most common structures:
- CSV with columns: Song Title, Artist, Album, Listening Date, ...
- JSON array format
"""

import csv
import json
from datetime import datetime
from pathlib import Path

from ..models import Category, Platform, RawStream


def _parse_csv(filepath: Path, account_id: str) -> list[RawStream]:
    """Parse Deezer CSV export."""
    streams = []
    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Deezer CSV column names vary by language
            title = (
                row.get("Song Title")
                or row.get("Titre")
                or row.get("Title")
                or row.get("Song")
            )
            artist = (
                row.get("Artist")
                or row.get("Artiste")
            )
            album = (
                row.get("Album")
                or row.get("Album Title")
            )
            timestamp_str = (
                row.get("Listening Date")
                or row.get("Date d'écoute")
                or row.get("Date")
                or row.get("Timestamp")
            )

            if not title or not artist or not timestamp_str:
                continue

            # Try multiple date formats
            timestamp = None
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y %H:%M"]:
                try:
                    timestamp = datetime.strptime(timestamp_str.strip(), fmt)
                    break
                except ValueError:
                    continue
            if not timestamp:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.strip())
                except ValueError:
                    continue

            # Duration if available
            ms_played = None
            duration_str = row.get("Duration") or row.get("Durée")
            if duration_str:
                try:
                    ms_played = int(float(duration_str) * 1000)
                except (ValueError, TypeError):
                    pass

            streams.append(
                RawStream(
                    title=title.strip(),
                    artist=artist.strip(),
                    album=album.strip() if album else None,
                    timestamp=timestamp,
                    ms_played=ms_played,
                    platform=Platform.DEEZER,
                    account_id=account_id,
                    source_file=filepath.name,
                    category=Category.MUSIC,
                )
            )
    return streams


def _parse_json(filepath: Path, account_id: str) -> list[RawStream]:
    """Parse Deezer JSON export."""
    streams = []
    with open(filepath, encoding="utf-8") as f:
        entries = json.load(f)

    if isinstance(entries, dict):
        entries = entries.get("data", entries.get("history", []))

    for entry in entries:
        title = entry.get("title") or entry.get("SNG_TITLE")
        artist = entry.get("artist") or entry.get("ART_NAME")
        album = entry.get("album") or entry.get("ALB_TITLE")
        timestamp_str = entry.get("timestamp") or entry.get("date") or entry.get("listened_at")

        if not title or not artist or not timestamp_str:
            continue

        if isinstance(timestamp_str, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp_str)
        else:
            timestamp = datetime.fromisoformat(str(timestamp_str).replace("Z", "+00:00"))

        duration = entry.get("duration") or entry.get("DURATION")
        ms_played = int(float(duration) * 1000) if duration else None

        streams.append(
            RawStream(
                title=str(title).strip(),
                artist=str(artist).strip(),
                album=str(album).strip() if album else None,
                timestamp=timestamp,
                ms_played=ms_played,
                platform=Platform.DEEZER,
                account_id=account_id,
                source_file=filepath.name,
                category=Category.MUSIC,
            )
        )
    return streams


def parse_deezer_export(
    export_dir: Path,
    account_id: str,
) -> list[RawStream]:
    """Parse Deezer GDPR export files.

    Args:
        export_dir: Directory containing Deezer export files
        account_id: Account identifier (e.g. "deezer_perso")

    Returns:
        List of RawStream objects
    """
    streams = []

    # Try CSV files
    for csv_file in export_dir.glob("*.csv"):
        streams.extend(_parse_csv(csv_file, account_id))

    # Try JSON files if no CSV found
    if not streams:
        for json_file in export_dir.glob("*.json"):
            streams.extend(_parse_json(json_file, account_id))

    return streams
