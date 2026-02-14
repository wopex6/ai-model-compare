"""
Centralized SQLite connection helper.
Applies WAL journal mode and busy_timeout to prevent "database is locked" errors
under concurrent access (e.g. PythonAnywhere WSGI workers).
"""
import sqlite3


def connect_db(db_path, check_same_thread=True):
    """Open a SQLite connection with WAL mode and busy timeout.
    
    Args:
        db_path: Path to the database file (or ':memory:' for in-memory).
        check_same_thread: If False, allow cross-thread usage (for long-lived connections).
    
    Returns:
        sqlite3.Connection with WAL and busy_timeout configured.
    """
    conn = sqlite3.connect(db_path, check_same_thread=check_same_thread)
    if db_path != ':memory:':
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
    return conn
