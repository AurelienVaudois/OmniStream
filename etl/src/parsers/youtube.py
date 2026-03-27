"""Parser for YouTube Music / Google Takeout export.

Expected formats:
- watch-history.json: Array of objects with title, titleUrl, subtitles, time
- watch-history.html: HTML file with watch history (fallback)

Note: Google Takeout does NOT provide ms_played (duration watched).
"""

import json
import re
from datetime import datetime
from pathlib import Path

from ..models import Category, Platform, RawStream


def _parse_watch_history_json(
    filepath: Path,
    account_id: str,
) -> list[RawStream]:
    """Parse watch-history.json from Google Takeout."""
    streams = []
    with open(filepath, encoding="utf-8") as f:
        entries = json.load(f)

    for entry in entries:
        title_raw = entry.get("title", "")
        # Google Takeout titles are prefixed with "Watched " or "Looked at "
        title = re.sub(r"^(Watched|Regardé)\s+", "", title_raw).strip()
        if not title:
            continue

        # Extract artist from subtitles
        subtitles = entry.get("subtitles", [])
        artist = "Unknown Artist"
        if subtitles:
            artist_raw = subtitles[0].get("name", "Unknown Artist")
            # YouTube channels often have " - Topic" suffix for music
            artist = re.sub(r"\s*-\s*Topic$", "", artist_raw)

        # Determine category
        # YouTube Music content from "Music" category or channels with "- Topic"
        header = entry.get("header", "")
        if header == "YouTube Music":
            category = Category.MUSIC
        elif "- Topic" in (subtitles[0].get("name", "") if subtitles else ""):
            category = Category.MUSIC
        else:
            category = Category.VIDEO

        timestamp_str = entry.get("time", "")
        if not timestamp_str:
            continue
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

        streams.append(
            RawStream(
                title=title,
                artist=artist,
                album=None,
                timestamp=timestamp,
                ms_played=None,  # Not available in Takeout
                platform=Platform.YOUTUBE,
                account_id=account_id,
                source_file=filepath.name,
                category=category,
            )
        )

    return streams


def parse_youtube_export(
    export_dir: Path,
    account_id: str,
) -> list[RawStream]:
    """Parse YouTube/YouTube Music data from Google Takeout.

    Args:
        export_dir: Directory containing Takeout export files
        account_id: Account identifier (e.g. "youtube_perso")

    Returns:
        List of RawStream objects
    """
    # Try JSON first
    json_path = export_dir / "watch-history.json"
    if json_path.exists():
        return _parse_watch_history_json(json_path, account_id)

    # Look in subdirectories (Takeout structure varies)
    for json_file in export_dir.rglob("watch-history.json"):
        return _parse_watch_history_json(json_file, account_id)

    return []
