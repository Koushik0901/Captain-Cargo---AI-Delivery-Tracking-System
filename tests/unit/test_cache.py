"""Tests for TTL cache behavior."""

import time
import pytest
from services.cache import DeliveryCache


class TestDeliveryCache:
    """Test cases for DeliveryCache."""

    @pytest.fixture
    def cache(self) -> DeliveryCache:
        """Create a fresh cache instance."""
        return DeliveryCache(max_size=10, ttl_seconds=2)

    def test_set_and_get(self, cache: DeliveryCache) -> None:
        """Test basic set and get."""
        cache.set("key1", {"data": "value1"})
        result = cache.get("key1")
        assert result == {"data": "value1"}

    def test_get_nonexistent(self, cache: DeliveryCache) -> None:
        """Test getting nonexistent key returns None."""
        result = cache.get("nonexistent")
        assert result is None

    def test_ttl_expiration(self, cache: DeliveryCache) -> None:
        """Test that entries expire after TTL."""
        # Set with 1 second TTL override
        cache.set("expiring", {"data": "value"}, ttl_seconds=1)

        # Should be available immediately
        result = cache.get("expiring")
        assert result is not None

        # Wait for expiration
        import time

        time.sleep(1.5)

        # Should be expired now
        result = cache.get("expiring")
        assert result is None

    def test_invalidate(self, cache: DeliveryCache) -> None:
        """Test explicit cache invalidation."""
        cache.set("key1", {"data": "value1"})
        cache.invalidate("key1")
        result = cache.get("key1")
        assert result is None

    def test_max_size_eviction(self, cache: DeliveryCache) -> None:
        """Test that oldest entry is evicted when max size reached."""
        for i in range(15):
            cache.set(f"key{i}", {"data": f"value{i}"})

        assert cache.get("key0") is None
        assert cache.get("key14") is not None

    def test_get_stats(self, cache: DeliveryCache) -> None:
        """Test cache statistics."""
        cache.set("key1", {"data": "value1"})
        cache.set("key2", {"data": "value2"})
        cache.get("key1")
        cache.get("key3")

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 2
        assert 0.0 <= stats["hit_rate"] <= 1.0

    def test_clear(self, cache: DeliveryCache) -> None:
        """Test cache clear."""
        cache.set("key1", {"data": "value1"})
        cache.set("key2", {"data": "value2"})

        # Get stats BEFORE get calls
        stats_before = cache.get_stats()
        assert stats_before["size"] == 2

        cache.clear()

        # Stats should be reset after clear
        stats = cache.get_stats()
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
