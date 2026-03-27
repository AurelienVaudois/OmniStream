"""Main ETL pipeline orchestrator.

Reads a configuration of accounts and export directories,
parses all exports, and loads them into SQLite.
"""

import json
import sqlite3
from pathlib import Path

from .db import init_db
from .load import load_streams
from .models import RawStream
from .parsers.amazon import parse_amazon_export
from .parsers.deezer import parse_deezer_export
from .parsers.soundcloud import parse_soundcloud_export
from .parsers.spotify import parse_spotify_export
from .parsers.youtube import parse_youtube_export

PARSERS = {
    "spotify": parse_spotify_export,
    "deezer": parse_deezer_export,
    "youtube": parse_youtube_export,
    "amazon": parse_amazon_export,
    "soundcloud": parse_soundcloud_export,
}


def load_config(config_path: Path) -> list[dict]:
    """Load pipeline config. Expected format:
    [
        {"platform": "spotify", "account_id": "spotify_perso", "export_dir": "data/exports/spotify_perso"},
        ...
    ]
    """
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def run_pipeline(
    config_path: Path,
    db_path: Path | None = None,
) -> dict:
    """Run the full ETL pipeline.

    Args:
        config_path: Path to the JSON config file
        db_path: Path to SQLite database (uses default if None)

    Returns:
        Dict with total stats
    """
    config = load_config(config_path)
    conn = init_db(db_path)

    total_stats = {"total_parsed": 0, "total_inserted": 0, "total_skipped": 0}

    for source in config:
        platform = source["platform"]
        account_id = source["account_id"]
        export_dir = Path(source["export_dir"])

        parser = PARSERS.get(platform)
        if not parser:
            print(f"[WARN] No parser for platform: {platform}")
            continue

        if not export_dir.exists():
            print(f"[WARN] Export directory not found: {export_dir}")
            continue

        print(f"[INFO] Parsing {platform} ({account_id}) from {export_dir}...")
        streams: list[RawStream] = parser(export_dir, account_id)
        print(f"[INFO]   → {len(streams)} streams parsed")
        total_stats["total_parsed"] += len(streams)

        if streams:
            stats = load_streams(conn, streams)
            print(f"[INFO]   → {stats['inserted']} inserted, {stats['skipped']} skipped")
            total_stats["total_inserted"] += stats["inserted"]
            total_stats["total_skipped"] += stats["skipped"]

    conn.close()
    return total_stats


if __name__ == "__main__":
    import sys

    config_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("config.json")
    stats = run_pipeline(config_file)
    print(f"\n[DONE] Total: {stats['total_parsed']} parsed, "
          f"{stats['total_inserted']} inserted, {stats['total_skipped']} skipped")
