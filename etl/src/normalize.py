"""Text normalization utilities for deduplication and matching.

Handles accent stripping, case normalization, feat. extraction,
and common title cleaning patterns.
"""

import re

from unidecode import unidecode


# Patterns for extracting featured artists from titles
_FEAT_PATTERNS = [
    r"\s*\(feat\.?\s+[^)]+\)",
    r"\s*\(ft\.?\s+[^)]+\)",
    r"\s*\(with\s+[^)]+\)",
    r"\s*\(featuring\s+[^)]+\)",
    r"\s*feat\.?\s+.+$",
    r"\s*ft\.?\s+.+$",
]

# Patterns for removing common suffixes from titles
_TITLE_SUFFIX_PATTERNS = [
    r"\s*\(official\s*(audio|video|music\s*video|lyric\s*video)\)",
    r"\s*\(remaster(ed)?\s*\d*\)",
    r"\s*\(deluxe(\s*edition)?\)",
    r"\s*\[\s*official\s*(audio|video|music\s*video)\s*\]",
    r"\s*-\s*remaster(ed)?\s*\d*$",
]

_FEAT_RE = re.compile("|".join(_FEAT_PATTERNS), re.IGNORECASE)
_SUFFIX_RE = re.compile("|".join(_TITLE_SUFFIX_PATTERNS), re.IGNORECASE)


def normalize_text(text: str) -> str:
    """Normalize text for matching: lowercase, strip accents, collapse whitespace."""
    text = unidecode(text).lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_title(title: str) -> str:
    """Normalize a track title: remove feat., official video tags, etc."""
    title = _FEAT_RE.sub("", title)
    title = _SUFFIX_RE.sub("", title)
    return normalize_text(title)


def normalize_artist(artist: str) -> str:
    """Normalize an artist name."""
    return normalize_text(artist)


def extract_featured_artists(title: str) -> list[str]:
    """Extract featured artist names from a track title."""
    artists = []
    for match in _FEAT_RE.finditer(title):
        text = match.group()
        # Remove the pattern wrapper to get just the artist name(s)
        cleaned = re.sub(
            r"^\s*[\(\[]\s*(feat|ft|featuring|with)\.?\s+", "", text, flags=re.IGNORECASE
        )
        cleaned = re.sub(r"\s*[\)\]]$", "", cleaned)
        cleaned = re.sub(r"^\s*(feat|ft|featuring)\.?\s+", "", cleaned, flags=re.IGNORECASE)
        # Split on common separators (", ", " & ", " x ")
        for name in re.split(r"\s*[,&]\s*|\s+x\s+", cleaned, flags=re.IGNORECASE):
            name = name.strip()
            if name:
                artists.append(name)
    return artists
