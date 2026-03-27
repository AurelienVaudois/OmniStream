"""Parser for Amazon Music GDPR data export.

Amazon exports are notoriously sparse. Common formats:
- CSV files in various structures
- JSON files with listening data

Fields may include: Title, Artist, Album, ASIN, timestamps (often imprecise).
ms_played is generally NOT available.
"""

import csv
import json
from datetime import datetime
from pathlib import Path

from ..models import Category, Platform, RawStream


def _try_parse_timestamp(value: str) -> datetime | None:
    """Try multiple date formats for Amazon's inconsistent timestamps."""
    for fmt in [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
    ]:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def _parse_csv(filepath: Path, account_id: str) -> list[RawStream]:
    """Parse an Amazon Music CSV export."""
    streams = []
    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = (
                row.get("Title")
                or row.get("title")
                or row.get("Track Name")
                or row.get("trackName")
            )
            artist = (
                row.get("Artist")
                or row.get("artist")
                or row.get("Artist Name")
                or row.get("artistName")
            )
            album = row.get("Album") or row.get("album") or row.get("Album Name")

            timestamp_str = (
                row.get("Date")
                or row.get("date")
                or row.get("Timestamp")
                or row.get("endTimestamp")
                or row.get("Start Date")
            )

            if not title or not timestamp_str:
                continue
            if not artist:
                artist = "Unknown Artist"

            timestamp = _try_parse_timestamp(timestamp_str)
            if not timestamp:
                continue

            streams.append(
                RawStream(
                    title=title.strip(),
                    artist=artist.strip(),
                    album=album.strip() if album else None,
                    timestamp=timestamp,
                    ms_played=None,  # Rarely available
                    platform=Platform.AMAZON,
                    account_id=account_id,
                    source_file=filepath.name,
                    category=Category.MUSIC,
                )
            )
    return streams


def _parse_json(filepath: Path, account_id: str) -> list[RawStream]:
    """Parse an Amazon Music JSON export."""
    streams = []
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    entries = data if isinstance(data, list) else data.get("data", data.get("history", []))

    for entry in entries:
        title = entry.get("title") or entry.get("trackName")
        artist = entry.get("artist") or entry.get("artistName") or "Unknown Artist"
        album = entry.get("album") or entry.get("albumName")
        timestamp_str = entry.get("timestamp") or entry.get("date") or entry.get("endTimestamp")

        if not title or not timestamp_str:
            continue

        if isinstance(timestamp_str, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp_str)
        else:
            timestamp = _try_parse_timestamp(str(timestamp_str))
        if not timestamp:
            continue

        streams.append(
            RawStream(
                title=str(title).strip(),
                artist=str(artist).strip(),
                album=str(album).strip() if album else None,
                timestamp=timestamp,
                ms_played=None,
                platform=Platform.AMAZON,
                account_id=account_id,
                source_file=filepath.name,
                category=Category.MUSIC,
            )
        )
    return streams


def parse_amazon_export(
    export_dir: Path,
    account_id: str,
) -> list[RawStream]:
    """Parse Amazon Music GDPR export files.

    Args:
        export_dir: Directory containing Amazon Music export files
        account_id: Account identifier (e.g. "amazon_perso")

    Returns:
        List of RawStream objects
    """
    streams = []
    for csv_file in export_dir.glob("*.csv"):
        streams.extend(_parse_csv(csv_file, account_id))
    if not streams:
        for json_file in export_dir.glob("*.json"):
            streams.extend(_parse_json(json_file, account_id))
    return streams
