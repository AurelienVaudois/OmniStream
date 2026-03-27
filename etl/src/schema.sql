-- OmniStream - SQLite Schema
-- Star schema for unified music listening history

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ============================================================
-- DIMENSION TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_accounts (
    account_id   TEXT PRIMARY KEY,        -- e.g. "spotify_perso", "deezer_promo_2020"
    platform     TEXT NOT NULL,            -- spotify | deezer | amazon | youtube | soundcloud
    email        TEXT,
    label        TEXT,                     -- human-friendly label e.g. "Perso", "Promo 2020"
    is_active    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS dim_artists (
    artist_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    name_normalized TEXT NOT NULL,          -- lowercase, stripped accents, for matching
    musicbrainz_id TEXT,
    first_seen_date TEXT,                   -- ISO 8601 date
    UNIQUE(name_normalized)
);

CREATE TABLE IF NOT EXISTS dim_genres (
    genre_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_tracks (
    track_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    title_normalized TEXT NOT NULL,         -- lowercase, stripped accents/feat, for matching
    artist_id       INTEGER NOT NULL,
    album           TEXT,
    category        TEXT NOT NULL DEFAULT 'music',  -- music | podcast | video
    duration_ms     INTEGER,
    musicbrainz_id  TEXT,
    isrc            TEXT,                   -- International Standard Recording Code
    FOREIGN KEY (artist_id) REFERENCES dim_artists(artist_id)
);

CREATE TABLE IF NOT EXISTS track_genres (
    track_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,
    PRIMARY KEY (track_id, genre_id),
    FOREIGN KEY (track_id) REFERENCES dim_tracks(track_id),
    FOREIGN KEY (genre_id) REFERENCES dim_genres(genre_id)
);

CREATE TABLE IF NOT EXISTS track_features (
    track_id     INTEGER PRIMARY KEY,
    valence      REAL,                     -- 0.0 to 1.0
    energy       REAL,                     -- 0.0 to 1.0
    danceability REAL,                     -- 0.0 to 1.0
    tempo        REAL,                     -- BPM
    acousticness REAL,                     -- 0.0 to 1.0
    source       TEXT NOT NULL,            -- musicbrainz | essentia | spotify | lastfm
    FOREIGN KEY (track_id) REFERENCES dim_tracks(track_id)
);

-- ============================================================
-- PLAYLIST TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_playlists (
    playlist_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    platform       TEXT NOT NULL,
    account_id     TEXT NOT NULL,
    description    TEXT,
    is_liked_songs INTEGER NOT NULL DEFAULT 0,
    track_count    INTEGER,
    snapshot_date  TEXT NOT NULL,           -- ISO 8601 date of when we captured this
    source         TEXT NOT NULL DEFAULT 'api',  -- api | rgpd
    FOREIGN KEY (account_id) REFERENCES dim_accounts(account_id)
);

CREATE TABLE IF NOT EXISTS playlist_tracks (
    playlist_id INTEGER NOT NULL,
    track_id    INTEGER NOT NULL,
    position    INTEGER,                   -- order in playlist
    added_at    TEXT,                       -- ISO 8601 datetime, if available
    PRIMARY KEY (playlist_id, track_id),
    FOREIGN KEY (playlist_id) REFERENCES dim_playlists(playlist_id),
    FOREIGN KEY (track_id) REFERENCES dim_tracks(track_id)
);

-- ============================================================
-- FACT TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS fact_streams (
    stream_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id    INTEGER NOT NULL,
    timestamp   TEXT NOT NULL,              -- ISO 8601 datetime UTC
    ms_played   INTEGER,                    -- NULL if not available (e.g. YouTube)
    platform    TEXT NOT NULL,              -- spotify | deezer | amazon | youtube | soundcloud
    account_id  TEXT NOT NULL,
    source_file TEXT,                       -- which RGPD file this came from (for traceability)
    FOREIGN KEY (track_id) REFERENCES dim_tracks(track_id),
    FOREIGN KEY (account_id) REFERENCES dim_accounts(account_id)
);

-- ============================================================
-- DEDUPLICATION SUPPORT
-- ============================================================

-- Manual override table for fuzzy matching edge cases
CREATE TABLE IF NOT EXISTS dedup_overrides (
    override_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_title      TEXT NOT NULL,
    raw_artist     TEXT NOT NULL,
    platform       TEXT NOT NULL,
    resolved_track_id INTEGER NOT NULL,
    FOREIGN KEY (resolved_track_id) REFERENCES dim_tracks(track_id)
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_streams_timestamp ON fact_streams(timestamp);
CREATE INDEX IF NOT EXISTS idx_streams_platform ON fact_streams(platform);
CREATE INDEX IF NOT EXISTS idx_streams_account ON fact_streams(account_id);
CREATE INDEX IF NOT EXISTS idx_streams_track ON fact_streams(track_id);
CREATE INDEX IF NOT EXISTS idx_tracks_artist ON dim_tracks(artist_id);
CREATE INDEX IF NOT EXISTS idx_tracks_title_norm ON dim_tracks(title_normalized);
CREATE INDEX IF NOT EXISTS idx_artists_name_norm ON dim_artists(name_normalized);
CREATE INDEX IF NOT EXISTS idx_tracks_isrc ON dim_tracks(isrc);
CREATE INDEX IF NOT EXISTS idx_playlists_account ON dim_playlists(account_id);
