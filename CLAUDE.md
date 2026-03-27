# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OmniStream aggregates music listening history from 5 platforms (Spotify, Deezer, Amazon Music, YouTube Music, SoundCloud) with multi-account support into a unified SQLite database and interactive dashboard.

## Commands

```bash
# Run all ETL tests
cd etl && python -m pytest tests/ -v

# Run a single test class/method
cd etl && python -m pytest tests/test_parsers.py::TestSpotifyParser -v
cd etl && python -m pytest tests/test_load.py::TestLoadStreams::test_idempotent_reinsert -v

# Lint
cd etl && ruff check src/ tests/

# Run the full ETL pipeline
cd etl && python -m src.pipeline config.json
```

## Architecture

### Data Flow

```
GDPR exports (JSON/CSV per platform)
  → Parsers (one per platform) → list[RawStream]
    → Normalization (accents, feat., remaster removal)
      → Loader (idempotent upserts) → SQLite star schema
```

### ETL Pipeline (`etl/src/`)

- **`models.py`** — Pydantic schemas: `RawStream`, `RawPlaylist`, `RawPlaylistTrack`. Enums: `Platform`, `Category` (music|podcast|video).
- **`parsers/*.py`** — One parser per platform. All follow the same signature: `parse_<platform>_export(export_dir: Path, account_id: str) -> list[RawStream]`. Handles platform-specific file formats, column name variations, and multi-format date parsing.
- **`normalize.py`** — Strips accents (unidecode), removes `(feat. X)` / `(Official Audio)` / `(Remastered)` patterns, collapses whitespace. Used for deduplication matching.
- **`load.py`** — `load_streams()` and `load_playlist()` insert data idempotently. Dedup key: `(track_id, timestamp, account_id)`. Dimension upserts via `get_or_create_artist/track`.
- **`db.py`** — SQLite connection with WAL mode and foreign keys enabled.
- **`pipeline.py`** — Orchestrator: reads JSON config, dispatches to parsers, calls loader. Runnable as `python -m src.pipeline config.json`.
- **`api/`** — Planned: OAuth clients for live playlist retrieval (Spotify, Deezer, YouTube).

### Database Schema (`etl/src/schema.sql`)

Star schema: `dim_artists`, `dim_tracks`, `dim_genres`, `dim_accounts`, `dim_playlists` (dimensions) + `fact_streams` (one row = one listen). Junction tables: `track_genres`, `playlist_tracks`, `track_features`. Dedup support: `dedup_overrides` for manual fuzzy match resolution. Matching relies on `name_normalized`/`title_normalized` columns.

### Dashboard (`dashboard/`)

Not yet initialized. Planned stack: Next.js 14+ (App Router), Tailwind, Shadcn/ui, Tremor, Recharts, better-sqlite3.

## Conventions

- Code language: English (variables, functions, docstrings)
- Conversation language: French
- Use Polars, not Pandas, for data processing
- Every parser produces `RawStream` or `RawPlaylist` (Pydantic models)
- The loader is idempotent: re-running on the same data produces no duplicates
- Tests use fixtures in `etl/tests/fixtures/` named to match platform file conventions (e.g., `Streaming_History_Audio_0.json`, `watch-history.json`)
- Database tests use in-memory SQLite (`:memory:`)
