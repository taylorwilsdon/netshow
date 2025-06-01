"""Tests for helper functions."""

from netshow.helpers import get_friendly_name


class TestGetFriendlyName:
    """Test friendly name generation."""

    def test_static_mapping(self):
        """Test static name mappings."""
        assert get_friendly_name("rapportd", 123, "") == "Handoff Sync Process"
        assert get_friendly_name("IPNExtension", 456, "") == "Tailscale"

    def test_plex_detection(self):
        """Test Plex process detection."""
        assert get_friendly_name("PlexMediaServer", 789, "") == "Plex Media Server"
        assert get_friendly_name("plex-something", 101112, "") == "Plex Media Server"

    def test_docker_detection(self):
        """Test Docker process detection."""
        assert "Docker Desktop" in get_friendly_name("com.docker.backend", 131415, "")

    def test_fallback_to_process_name(self):
        """Test fallback to original process name."""
        assert get_friendly_name("unknown_process", 161718, "") == "unknown_process"
