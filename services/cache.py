"""TTL cache for delivery status."""

import time
from typing import Any, Optional


class DeliveryCache:
    """Simple TTL cache with stats tracking."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 60) -> None:
        """Initialize cache.

        Args:
            max_size: Maximum number of entries.
            ttl_seconds: Default time-to-live in seconds.
        """
        self._cache: dict[str, dict[str, Any]] = {}
        self._timestamps: dict[str, float] = {}
        self._ttls: dict[str, int] = {}
        self.max_size = max_size
        self.default_ttl_seconds = ttl_seconds
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[dict[str, Any]]:
        """Get value from cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if expired/missing.
        """
        if key not in self._cache:
            self._misses += 1
            return None

        timestamp = self._timestamps.get(key, 0)
        ttl = self._ttls.get(key, self.default_ttl_seconds)
        if time.time() - timestamp > ttl:
            del self._cache[key]
            del self._timestamps[key]
            del self._ttls[key]
            self._misses += 1
            return None

        self._hits += 1
        return self._cache[key]

    def set(
        self, key: str, value: dict[str, Any], ttl_seconds: Optional[int] = None
    ) -> None:
        """Set value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl_seconds: Optional TTL override (defaults to self.default_ttl_seconds).
        """
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._timestamps.keys(), key=lambda k: self._timestamps[k])
            del self._cache[oldest_key]
            del self._timestamps[oldest_key]
            del self._ttls[oldest_key]

        self._cache[key] = value
        self._timestamps[key] = time.time()
        self._ttls[key] = ttl_seconds or self.default_ttl_seconds

    def invalidate(self, key: str) -> None:
        """Invalidate a cache entry.

        Args:
            key: Cache key to invalidate.
        """
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        self._ttls.pop(key, None)

    def get_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Stats dict with hits, misses, size, hit_rate.
        """
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": len(self._cache),
            "hit_rate": hit_rate,
        }

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._timestamps.clear()
        self._ttls.clear()
        self._hits = 0
        self._misses = 0
