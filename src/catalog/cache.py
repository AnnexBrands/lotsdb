import logging

from django.core.cache import cache

logger = logging.getLogger(__name__)


def safe_cache_get(key, default=None):
    """Retrieve from cache. Returns *default* when key is missing or Redis is down."""
    try:
        return cache.get(key, default)
    except Exception:
        logger.warning("Cache read failed for key=%s", key)
        return default


def safe_cache_set(key, value, timeout=None):
    """Store in cache. No-op when Redis is down."""
    try:
        cache.set(key, value, timeout)
    except Exception:
        logger.warning("Cache write failed for key=%s", key)
