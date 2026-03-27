"""Pydantic models for OmniStream intermediate data format.

Each parser converts platform-specific data into these unified models
before normalization and loading into SQLite.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class Platform(str, Enum):
    SPOTIFY = "spotify"
    DEEZER = "deezer"
    AMAZON = "amazon"
    YOUTUBE = "youtube"
    SOUNDCLOUD = "soundcloud"


class Category(str, Enum):
    MUSIC = "music"
    PODCAST = "podcast"
    VIDEO = "video"


class RawStream(BaseModel):
    """A single listening event, as parsed from a platform export."""

    title: str
    artist: str
    album: str | None = None
    timestamp: datetime
    ms_played: int | None = None
    platform: Platform
    account_id: str
    source_file: str
    category: Category = Category.MUSIC


class RawPlaylistTrack(BaseModel):
    """A track within a playlist."""

    title: str
    artist: str
    album: str | None = None
    position: int | None = None
    added_at: datetime | None = None


class RawPlaylist(BaseModel):
    """A playlist as fetched from an API or parsed from an export."""

    name: str
    platform: Platform
    account_id: str
    description: str | None = None
    is_liked_songs: bool = False
    tracks: list[RawPlaylistTrack] = []
    source: str = "api"  # "api" or "rgpd"
