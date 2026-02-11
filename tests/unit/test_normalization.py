"""Tests for tracking ID normalization."""

import pytest
from utils.normalization import normalize_tracking_id, validate_tracking_id


class TestNormalizeTrackingId:
    """Test cases for normalize_tracking_id function."""

    def test_valid_uppercase(self) -> None:
        """Test valid uppercase tracking ID."""
        result = normalize_tracking_id("ABC123")
        assert result == "ABC123"

    def test_valid_lowercase(self) -> None:
        """Test valid lowercase tracking ID gets uppercased."""
        result = normalize_tracking_id("abc123")
        assert result == "ABC123"

    def test_with_spaces(self) -> None:
        """Test tracking ID with spaces gets normalized."""
        result = normalize_tracking_id("ABC 123")
        assert result == "ABC123"

    def test_with_special_chars(self) -> None:
        """Test tracking ID with special characters gets normalized."""
        result = normalize_tracking_id("ABC-123!")
        assert result == "ABC123"

    def test_empty_after_normalization(self) -> None:
        """Test ValueError for empty string."""
        with pytest.raises(ValueError) as excinfo:
            normalize_tracking_id("")
        assert "cannot be empty" in str(excinfo.value).lower()

    def test_too_short(self) -> None:
        """Test ValueError for ID too short after normalization."""
        with pytest.raises(ValueError) as excinfo:
            normalize_tracking_id("A")
        assert "too short" in str(excinfo.value).lower()

    def test_too_long(self) -> None:
        """Test ValueError for ID too long."""
        with pytest.raises(ValueError) as excinfo:
            normalize_tracking_id("A" * 50)
        assert "too long" in str(excinfo.value).lower()

    def test_none_input(self) -> None:
        """Test ValueError for None input."""
        with pytest.raises(ValueError) as excinfo:
            normalize_tracking_id(None)  # type: ignore
        assert "cannot be empty" in str(excinfo.value).lower()


class TestValidateTrackingId:
    """Test cases for validate_tracking_id function."""

    def test_valid_id_returns_true(self) -> None:
        """Test that valid ID returns True."""
        assert validate_tracking_id("ABC123") is True

    def test_invalid_returns_false(self) -> None:
        """Test that invalid ID returns False."""
        assert validate_tracking_id("") is False
        assert validate_tracking_id("AB") is False
