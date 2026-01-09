"""
Cache Manager for Performance Optimization
Provides in-memory caching with TTL support for frequently accessed data.
"""
import time
from typing import Any, Optional, Dict, Callable
from functools import wraps
import threading
import hashlib
import json


class CacheEntry:
    """Single cache entry with TTL"""
    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.expires_at = time.time() + ttl_seconds
        self.created_at = time.time()
        self.hits = 0
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at
    
    def hit(self) -> Any:
        self.hits += 1
        return self.value


class CacheManager:
    """
    Thread-safe in-memory cache with TTL support.
    
    Features:
    - Automatic expiration
    - Hit tracking for analytics
    - Size limits with LRU eviction
    - Namespace support for different data types
    """
    
    # Default TTLs by data type (seconds)
    DEFAULT_TTLS = {
        'user': 300,           # 5 minutes
        'statistics': 60,      # 1 minute
        'ai_budget': 30,       # 30 seconds
        'character': 3600,     # 1 hour
        'session': 1800,       # 30 minutes
        'api_response': 120,   # 2 minutes
    }
    
    MAX_ENTRIES = 1000  # Maximum cache entries
    
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def _make_key(self, namespace: str, key: str) -> str:
        """Create namespaced cache key"""
        return f"{namespace}:{key}"
    
    def get(self, namespace: str, key: str) -> Optional[Any]:
        """Get value from cache, returns None if not found or expired"""
        cache_key = self._make_key(namespace, key)
        
        with self._lock:
            entry = self._cache.get(cache_key)
            
            if entry is None:
                self._stats['misses'] += 1
                return None
            
            if entry.is_expired():
                del self._cache[cache_key]
                self._stats['misses'] += 1
                return None
            
            self._stats['hits'] += 1
            return entry.hit()
    
    def set(self, namespace: str, key: str, value: Any, ttl: int = None) -> None:
        """Set value in cache with TTL"""
        cache_key = self._make_key(namespace, key)
        
        if ttl is None:
            ttl = self.DEFAULT_TTLS.get(namespace, 300)
        
        with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self.MAX_ENTRIES:
                self._evict_expired()
                if len(self._cache) >= self.MAX_ENTRIES:
                    self._evict_lru()
            
            self._cache[cache_key] = CacheEntry(value, ttl)
    
    def delete(self, namespace: str, key: str) -> bool:
        """Delete specific cache entry"""
        cache_key = self._make_key(namespace, key)
        
        with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
                return True
            return False
    
    def invalidate_namespace(self, namespace: str) -> int:
        """Invalidate all entries in a namespace"""
        prefix = f"{namespace}:"
        count = 0
        
        with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
            for key in keys_to_delete:
                del self._cache[key]
                count += 1
        
        return count
    
    def _evict_expired(self) -> int:
        """Remove all expired entries"""
        count = 0
        keys_to_delete = []
        
        for key, entry in self._cache.items():
            if entry.is_expired():
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self._cache[key]
            count += 1
            self._stats['evictions'] += 1
        
        return count
    
    def _evict_lru(self, count: int = 100) -> None:
        """Evict least recently used entries"""
        entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].created_at
        )
        
        for key, _ in entries[:count]:
            del self._cache[key]
            self._stats['evictions'] += 1
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        with self._lock:
            total = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total * 100) if total > 0 else 0
            
            return {
                'entries': len(self._cache),
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': f"{hit_rate:.1f}%",
                'evictions': self._stats['evictions'],
                'max_entries': self.MAX_ENTRIES
            }
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()


# Global cache instance
_cache = CacheManager()


def get_cache() -> CacheManager:
    """Get global cache instance"""
    return _cache


def cached(namespace: str, ttl: int = None, key_func: Callable = None):
    """
    Decorator to cache function results.
    
    Usage:
        @cached('user', ttl=300)
        def get_user(user_id):
            return db.query(...)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: hash of function name + args
                key_data = f"{func.__name__}:{args}:{sorted(kwargs.items())}"
                cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Try cache first
            result = _cache.get(namespace, cache_key)
            if result is not None:
                return result
            
            # Call function and cache result
            result = func(*args, **kwargs)
            if result is not None:
                _cache.set(namespace, cache_key, result, ttl)
            
            return result
        
        # Add cache control methods to the wrapper
        wrapper.cache_invalidate = lambda: _cache.invalidate_namespace(namespace)
        return wrapper
    
    return decorator


def cache_user_data(user_id: int, data: Dict) -> None:
    """Cache user data"""
    _cache.set('user', str(user_id), data)


def get_cached_user(user_id: int) -> Optional[Dict]:
    """Get cached user data"""
    return _cache.get('user', str(user_id))


def invalidate_user_cache(user_id: int) -> None:
    """Invalidate specific user's cache"""
    _cache.delete('user', str(user_id))
