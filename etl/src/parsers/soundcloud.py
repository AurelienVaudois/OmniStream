"""Parser for SoundCloud GDPR data export.

SoundCloud exports typically contain JSON files with listening history.
ms_played is generally NOT available.
"""

import json
from datetime import datetime
from pathlib import Path

from ..models import Category, Platform, RawStream


def parse_soundcloud_export(
    export_dir: Path,
    account_id: str,
) -> list[RawStream]:
    """Parse SoundCloud GDPR export files.

    Args:
        export_dir: Directory containing SoundCloud export files
        account_id: Account identifier (e.g. "soundcloud_perso")

    Returns:
        List of RawStream objects
    """
    streams = []

    # SoundCloud exports vary in structure — look for listening history files
    candidate_files = (
        list(export_dir.glob("*listen*"))
        + list(export_dir.glob("*history*"))
        + list(export_dir.glob("*plays*"))
        + list(export_dir.glob("*.json"))
    )
    # Deduplicate
    seen = set()
    json_files = []
    for f in candidate_files:
        if f.suffix == ".json" and f not in seen:
            seen.add(f)
            json_files.append(f)

    for filepath in json_files:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        entries = data if isinstance(data, list) else data.get("collection", data.get("data", []))

        for entry in entries:
            # SoundCloud entries can have various structures
            title = (
                entry.get("title")
                or entry.get("track", {}).get("title")
                if isinstance(entry.get("track"), dict)
                else entry.get("track_title")
            )
            artist = (
                entry.get("artist")
                or (
                    entry.get("track", {}).get("user", {}).get("username")
                    if isinstance(entry.get("track"), dict)
                    else None
                )
                or entry.get("user", {}).get("username")
                if isinstance(entry.get("user"), dict)
                else "Unknown Artist"
            )

            if not title:
                continue
            if not artist:
                artist = "Unknown Artist"

            timestamp_str = (
                entry.get("created_at")
                or entry.get("timestamp")
                or entry.get("played_at")
                or entry.get("date")
            )
            if not timestamp_str:
                continue

            if isinstance(timestamp_str, (int, float)):
                timestamp = datetime.fromtimestamp(timestamp_str)
            else:
                try:
                    timestamp = datetime.fromisoformat(
                        str(timestamp_str).replace("Z", "+00:00").replace("/", "-")
                    )
                except ValueError:
                    continue

            streams.append(
                RawStream(
                    title=str(title).strip(),
                    artist=str(artist).strip(),
                    album=None,
                    timestamp=timestamp,
                    ms_played=None,
                    platform=Platform.SOUNDCLOUD,
                    account_id=account_id,
                    source_file=filepath.name,
                    category=Category.MUSIC,
                )
            )

    return streams
