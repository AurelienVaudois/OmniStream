"""Tests for text normalization."""

from src.normalize import (
    extract_featured_artists,
    normalize_artist,
    normalize_text,
    normalize_title,
)


class TestNormalizeText:
    def test_lowercase(self):
        assert normalize_text("Daft Punk") == "daft punk"

    def test_strip_accents(self):
        assert normalize_text("Stromae") == "stromae"
        assert normalize_text("Édith Piaf") == "edith piaf"
        assert normalize_text("Beyoncé") == "beyonce"

    def test_collapse_whitespace(self):
        assert normalize_text("  Daft   Punk  ") == "daft punk"


class TestNormalizeTitle:
    def test_removes_feat(self):
        assert normalize_title("Get Lucky (feat. Pharrell Williams)") == "get lucky"
        assert normalize_title("Get Lucky (ft. Pharrell Williams)") == "get lucky"
        assert normalize_title("Get Lucky (featuring Pharrell)") == "get lucky"

    def test_removes_official_tags(self):
        assert normalize_title("Get Lucky (Official Audio)") == "get lucky"
        assert normalize_title("Get Lucky (Official Video)") == "get lucky"
        assert normalize_title("Get Lucky [Official Music Video]") == "get lucky"

    def test_removes_remaster(self):
        assert normalize_title("Bohemian Rhapsody (Remastered 2011)") == "bohemian rhapsody"
        assert normalize_title("Bohemian Rhapsody - Remastered") == "bohemian rhapsody"

    def test_combined_cleaning(self):
        result = normalize_title("Get Lucky (feat. Pharrell Williams) (Official Audio)")
        assert result == "get lucky"


class TestNormalizeArtist:
    def test_basic(self):
        assert normalize_artist("Daft Punk") == "daft punk"
        assert normalize_artist("Édith Piaf") == "edith piaf"


class TestExtractFeaturedArtists:
    def test_feat_parentheses(self):
        artists = extract_featured_artists("Song (feat. Artist1)")
        assert artists == ["Artist1"]

    def test_feat_multiple(self):
        artists = extract_featured_artists("Song (feat. Artist1 & Artist2)")
        assert "Artist1" in artists
        assert "Artist2" in artists

    def test_no_feat(self):
        artists = extract_featured_artists("Just a Song")
        assert artists == []
