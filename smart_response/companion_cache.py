"""
Companion Cache
===============
Lightweight TTL cache for life companion module results.
Avoids repeated DB reads for data that changes slowly
(profile, life stage, pattern reports).

Thread-safe via threading.Lock.
"""

import threading
import time
from typing import Any, Optional, Dict, Tuple


class CompanionCache:
    """
    Simple in-memory TTL cache keyed by (user_id, namespace).

    Usage::

        cache = CompanionCache(default_ttl=300)  # 5 min
        cache.set(42, 'profile', profile_obj)
        hit = cache.get(42, 'profile')  # returns profile_obj or None
    """

    def __init__(self, default_ttl: int = 300):
        self._store: Dict[Tuple[int, str], Tuple[float, Any]] = {}
        self._ttls: Dict[str, int] = {}
        self._default_ttl = default_ttl
        self._lock = threading.Lock()

    def configure_ttl(self, namespace: str, ttl_seconds: int):
        self._ttls[namespace] = ttl_seconds

    def get(self, user_id: int, namespace: str) -> Optional[Any]:
        key = (user_id, namespace)
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if time.time() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, user_id: int, namespace: str, value: Any, ttl: int = None):
        key = (user_id, namespace)
        ttl = ttl or self._ttls.get(namespace, self._default_ttl)
        with self._lock:
            self._store[key] = (time.time() + ttl, value)

    def invalidate(self, user_id: int, namespace: str = None):
        with self._lock:
            if namespace:
                self._store.pop((user_id, namespace), None)
            else:
                keys_to_remove = [k for k in self._store if k[0] == user_id]
                for k in keys_to_remove:
                    del self._store[k]

    def invalidate_all(self):
        with self._lock:
            self._store.clear()

    def stats(self) -> Dict[str, int]:
        with self._lock:
            now = time.time()
            total = len(self._store)
            expired = sum(1 for _, (exp, _) in self._store.items() if now > exp)
            return {'total': total, 'active': total - expired, 'expired': expired}


# Module-level singleton
_cache = CompanionCache(default_ttl=300)

# Configure per-namespace TTLs
_cache.configure_ttl('life_stage', 600)       # 10 min — changes very rarely
_cache.configure_ttl('companion_profile', 120) # 2 min — updates each message but reads are expensive
_cache.configure_ttl('pattern_report', 300)    # 5 min — regenerated periodically
_cache.configure_ttl('habit_summary', 60)      # 1 min — changes when habits are completed
_cache.configure_ttl('emotional_state', 0)     # no cache — changes every message
_cache.configure_ttl('crisis', 0)              # no cache — safety critical


def get_companion_cache() -> CompanionCache:
    return _cache
