"""
Rate Limiter and Security Module
Provides rate limiting, input validation, and CSRF protection.
"""
import time
import re
import secrets
import hashlib
from typing import Dict, Optional, Tuple, List
from functools import wraps
from collections import defaultdict
import threading


class RateLimiter:
    """
    Token bucket rate limiter with multiple limit tiers.
    
    Limits:
    - Per-user limits
    - Per-IP limits
    - Global limits
    - Endpoint-specific limits
    """
    
    # Default limits (requests per minute)
    LIMITS = {
        'default': (60, 60),          # 60 requests per 60 seconds
        'api': (100, 60),             # 100 requests per minute
        'auth': (10, 60),             # 10 login attempts per minute
        'ai': (20, 60),               # 20 AI calls per minute
        'export': (5, 60),            # 5 exports per minute
        'admin': (200, 60),           # Higher limit for admins
    }
    
    def __init__(self):
        self._buckets: Dict[str, Dict] = defaultdict(lambda: {'tokens': 0, 'last_update': 0})
        self._lock = threading.RLock()
        self._blocked: Dict[str, float] = {}  # Temporarily blocked keys
    
    def _get_bucket_key(self, identifier: str, limit_type: str) -> str:
        """Create bucket key from identifier and type"""
        return f"{limit_type}:{identifier}"
    
    def check_limit(self, identifier: str, limit_type: str = 'default') -> Tuple[bool, Dict]:
        """
        Check if request is within rate limit.
        
        Returns:
            (allowed: bool, info: dict with remaining, reset_time, etc.)
        """
        max_requests, window_seconds = self.LIMITS.get(limit_type, self.LIMITS['default'])
        bucket_key = self._get_bucket_key(identifier, limit_type)
        
        with self._lock:
            # Check if blocked
            if bucket_key in self._blocked:
                if time.time() < self._blocked[bucket_key]:
                    return False, {
                        'remaining': 0,
                        'blocked_until': self._blocked[bucket_key],
                        'reason': 'temporarily_blocked'
                    }
                else:
                    del self._blocked[bucket_key]
            
            now = time.time()
            bucket = self._buckets[bucket_key]
            
            # Refill tokens based on time elapsed
            elapsed = now - bucket['last_update']
            refill_rate = max_requests / window_seconds
            bucket['tokens'] = min(max_requests, bucket['tokens'] + elapsed * refill_rate)
            bucket['last_update'] = now
            
            # Check if we have tokens
            if bucket['tokens'] >= 1:
                bucket['tokens'] -= 1
                return True, {
                    'remaining': int(bucket['tokens']),
                    'limit': max_requests,
                    'reset_in': int(window_seconds - elapsed % window_seconds)
                }
            else:
                return False, {
                    'remaining': 0,
                    'limit': max_requests,
                    'reset_in': int((1 - bucket['tokens']) / refill_rate),
                    'reason': 'rate_limit_exceeded'
                }
    
    def block_temporarily(self, identifier: str, limit_type: str, duration_seconds: int = 300) -> None:
        """Temporarily block an identifier (e.g., after too many failed logins)"""
        bucket_key = self._get_bucket_key(identifier, limit_type)
        with self._lock:
            self._blocked[bucket_key] = time.time() + duration_seconds
    
    def reset(self, identifier: str, limit_type: str) -> None:
        """Reset rate limit for identifier"""
        bucket_key = self._get_bucket_key(identifier, limit_type)
        with self._lock:
            if bucket_key in self._buckets:
                del self._buckets[bucket_key]
            if bucket_key in self._blocked:
                del self._blocked[bucket_key]


class InputValidator:
    """
    Input validation and sanitization.
    
    Validates:
    - User inputs
    - API parameters
    - File uploads
    """
    
    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',                  # JavaScript URLs
        r'on\w+\s*=',                   # Event handlers
        r'data:text/html',              # Data URLs
        r'vbscript:',                   # VBScript
    ]
    
    # SQL injection patterns
    SQL_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b)",
        r"(--|#|/\*)",                  # SQL comments
        r"(\bOR\b\s+\d+\s*=\s*\d+)",   # OR 1=1 style
    ]
    
    MAX_INPUT_LENGTH = 10000  # Maximum input length
    MAX_MESSAGE_LENGTH = 5000  # Maximum message length
    
    @classmethod
    def sanitize_html(cls, text: str) -> str:
        """Remove potentially dangerous HTML"""
        if not text:
            return text
        
        # Remove script tags and event handlers
        for pattern in cls.DANGEROUS_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        return text
    
    @classmethod
    def validate_message(cls, message: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validate user message.
        
        Returns:
            (valid: bool, sanitized_message: str, error: Optional[str])
        """
        if not message:
            return False, '', 'Message cannot be empty'
        
        if len(message) > cls.MAX_MESSAGE_LENGTH:
            return False, '', f'Message too long (max {cls.MAX_MESSAGE_LENGTH} characters)'
        
        # Sanitize
        sanitized = cls.sanitize_html(message.strip())
        
        return True, sanitized, None
    
    @classmethod
    def validate_username(cls, username: str) -> Tuple[bool, Optional[str]]:
        """Validate username format"""
        if not username:
            return False, 'Username required'
        
        if len(username) < 2:
            return False, 'Username too short'
        
        if len(username) > 50:
            return False, 'Username too long'
        
        # Allow alphanumeric, spaces, and some special chars
        if not re.match(r'^[\w\s\-\.]+$', username):
            return False, 'Username contains invalid characters'
        
        return True, None
    
    @classmethod
    def validate_email(cls, email: str) -> Tuple[bool, Optional[str]]:
        """Validate email format"""
        if not email:
            return True, None  # Email optional
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, 'Invalid email format'
        
        return True, None
    
    @classmethod
    def check_sql_injection(cls, value: str) -> bool:
        """Check for potential SQL injection (returns True if suspicious)"""
        if not value:
            return False
        
        for pattern in cls.SQL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        
        return False


class CSRFProtection:
    """
    CSRF token management.
    
    Generates and validates CSRF tokens for form submissions.
    """
    
    TOKEN_LENGTH = 32
    TOKEN_EXPIRY = 3600  # 1 hour
    
    def __init__(self):
        self._tokens: Dict[str, Tuple[str, float]] = {}  # session_id -> (token, expires_at)
        self._lock = threading.RLock()
    
    def generate_token(self, session_id: str) -> str:
        """Generate new CSRF token for session"""
        token = secrets.token_hex(self.TOKEN_LENGTH)
        expires_at = time.time() + self.TOKEN_EXPIRY
        
        with self._lock:
            self._tokens[session_id] = (token, expires_at)
        
        return token
    
    def validate_token(self, session_id: str, token: str) -> bool:
        """Validate CSRF token"""
        with self._lock:
            stored = self._tokens.get(session_id)
            
            if not stored:
                return False
            
            stored_token, expires_at = stored
            
            if time.time() > expires_at:
                del self._tokens[session_id]
                return False
            
            # Use constant-time comparison to prevent timing attacks
            return secrets.compare_digest(stored_token, token)
    
    def cleanup_expired(self) -> int:
        """Remove expired tokens"""
        now = time.time()
        count = 0
        
        with self._lock:
            expired = [k for k, (_, exp) in self._tokens.items() if now > exp]
            for key in expired:
                del self._tokens[key]
                count += 1
        
        return count


# Global instances
_rate_limiter = RateLimiter()
_csrf = CSRFProtection()


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter"""
    return _rate_limiter


def get_csrf() -> CSRFProtection:
    """Get global CSRF protection"""
    return _csrf


def rate_limit(limit_type: str = 'default', get_identifier=None):
    """
    Decorator for rate limiting endpoints.
    
    Usage:
        @rate_limit('api')
        def my_endpoint():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get identifier (default to IP from Flask request)
            try:
                from flask import request, jsonify
                identifier = get_identifier() if get_identifier else request.remote_addr
            except:
                identifier = 'unknown'
            
            allowed, info = _rate_limiter.check_limit(identifier, limit_type)
            
            if not allowed:
                from flask import jsonify
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': info.get('reset_in', 60)
                }), 429
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
