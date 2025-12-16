#!/usr/bin/env python3
"""Production Database Migration - Latest Schema

Safely updates the SQLite database schema to match the current application.

Goals:
- Idempotent (safe to run multiple times)
- No data loss (only CREATE TABLE/INDEX and ALTER TABLE ADD COLUMN)
- Optional automatic backup

Usage:
    python migrate_production_latest_schema.py --db integrated_users.db --backup
    python migrate_production_latest_schema.py --db /path/to/db --no-backup --yes

Notes:
- This script is designed for production environments (e.g. PythonAnywhere).
- It does NOT drop or rewrite tables.
"""

import argparse
import os
import shutil
import sqlite3
from datetime import datetime
from typing import Any, List, Optional


def _now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def backup_database(db_path: str) -> str:
    """Create a file-level backup before migration."""
    backup_path = f"{db_path}.backup_{_now_stamp()}"
    print(f"📦 Creating backup: {backup_path}")

    # Copy database file (fast + compatible everywhere)
    shutil.copy2(db_path, backup_path)

    size_mb = os.path.getsize(backup_path) / (1024 * 1024)
    print(f"✅ Backup created ({size_mb:.2f} MB)")
    return backup_path


def table_exists(cursor: sqlite3.Cursor, table: str) -> bool:
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    return cursor.fetchone() is not None


def column_exists(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cursor.fetchall()]
    return column in cols


def _sql_default_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    # Strings
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def ensure_column(
    cursor: sqlite3.Cursor,
    table: str,
    column: str,
    col_type: str,
    default: Any = None,
) -> bool:
    """Ensure a column exists; returns True if it was added."""
    if not table_exists(cursor, table):
        raise RuntimeError(f"Table '{table}' does not exist (cannot add column '{column}').")

    if column_exists(cursor, table, column):
        return False

    sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
    if default is not None:
        sql += f" DEFAULT {_sql_default_literal(default)}"

    cursor.execute(sql)
    return True


def ensure_index(cursor: sqlite3.Cursor, index_sql: str) -> None:
    cursor.execute(index_sql)


def apply_migration(conn: sqlite3.Connection) -> List[str]:
    cursor = conn.cursor()
    changes: List[str] = []

    # Be explicit in production
    cursor.execute("PRAGMA foreign_keys=ON")

    # ------------------------------------------------------------------
    # Core user/auth schema safety (roles / soft delete / verification)
    # ------------------------------------------------------------------

    # If the users table doesn't exist, we create it with the *minimal* fields
    # and then add any new columns below.
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Role-based access
    if ensure_column(cursor, "users", "user_role", "TEXT", default="guest"):
        changes.append("Added users.user_role")

    # Soft-delete support
    if ensure_column(cursor, "users", "is_deleted", "INTEGER", default=0):
        changes.append("Added users.is_deleted")

    # Email verification support (IntegratedDatabase.add_email_verification_columns)
    if ensure_column(cursor, "users", "email_verified", "INTEGER", default=0):
        changes.append("Added users.email_verified")
    if ensure_column(cursor, "users", "verification_code", "TEXT", default=None):
        changes.append("Added users.verification_code")
    if ensure_column(cursor, "users", "verification_expires", "DATETIME", default=None):
        changes.append("Added users.verification_expires")

    # ------------------------------------------------------------------
    # Conversations: character_id support (IntegratedDatabase.migrate_add_character_id)
    # ------------------------------------------------------------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id TEXT UNIQUE NOT NULL,
            title TEXT,
            conversation_data TEXT,
            personality_data TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """
    )

    # Some older DBs may not have character_id
    try:
        if ensure_column(cursor, "ai_conversations", "character_id", "TEXT", default=None):
            changes.append("Added ai_conversations.character_id")
    except RuntimeError:
        # If the table truly doesn't exist, the CREATE TABLE above should have created it.
        # This is here defensively.
        pass

    ensure_index(
        cursor,
        "CREATE INDEX IF NOT EXISTS idx_conversations_user_character ON ai_conversations(user_id, character_id)",
    )
    ensure_index(
        cursor,
        "CREATE INDEX IF NOT EXISTS idx_conversations_session ON ai_conversations(session_id)",
    )

    # ------------------------------------------------------------------
    # Message usage (roles/limits)
    # ------------------------------------------------------------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS message_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date DATE NOT NULL,
            message_count INTEGER DEFAULT 0,
            UNIQUE(user_id, date),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )
    ensure_index(cursor, "CREATE INDEX IF NOT EXISTS idx_message_usage_user ON message_usage(user_id)")
    ensure_index(cursor, "CREATE INDEX IF NOT EXISTS idx_message_usage_date ON message_usage(date)")

    # ------------------------------------------------------------------
    # User Context Manager tables
    # ------------------------------------------------------------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            fact_type TEXT NOT NULL,
            content TEXT NOT NULL,
            priority TEXT DEFAULT 'normal',
            confidence REAL DEFAULT 0.8,
            source_phrase TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME,
            is_active INTEGER DEFAULT 1,
            UNIQUE(user_id, fact_type, content)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_language_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            pattern_type TEXT NOT NULL,
            user_phrase TEXT NOT NULL,
            frequency INTEGER DEFAULT 1,
            first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, pattern_type, user_phrase)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS conversation_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            character_id TEXT NOT NULL,
            summary TEXT NOT NULL,
            topics TEXT,
            goals_mentioned TEXT,
            emotional_arc TEXT,
            message_count INTEGER,
            last_message_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_stale INTEGER DEFAULT 0,
            UNIQUE(user_id, character_id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_engagement (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            character_id TEXT NOT NULL,
            session_date DATE DEFAULT CURRENT_DATE,
            message_count INTEGER DEFAULT 0,
            avg_response_length REAL,
            positive_signals INTEGER DEFAULT 0,
            negative_signals INTEGER DEFAULT 0,
            topics_discussed TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, character_id, session_date)
        )
        """
    )

    ensure_index(cursor, "CREATE INDEX IF NOT EXISTS idx_user_context_user ON user_context(user_id)")
    ensure_index(cursor, "CREATE INDEX IF NOT EXISTS idx_user_context_active ON user_context(user_id, is_active)")
    ensure_index(cursor, "CREATE INDEX IF NOT EXISTS idx_user_language_user ON user_language_patterns(user_id)")
    ensure_index(cursor, "CREATE INDEX IF NOT EXISTS idx_conv_summary_user ON conversation_summaries(user_id, character_id)")

    # ------------------------------------------------------------------
    # Proactive Clarification System tables
    # ------------------------------------------------------------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS clarification_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            character_id TEXT NOT NULL,
            question_asked TEXT NOT NULL,
            reason TEXT NOT NULL,
            context_gap TEXT,
            user_response TEXT,
            was_helpful BOOLEAN,
            asked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            responded_at DATETIME
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS context_gaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            character_id TEXT NOT NULL,
            gap_type TEXT NOT NULL,
            gap_description TEXT,
            resolved BOOLEAN DEFAULT 0,
            detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved_at DATETIME
        )
        """
    )

    ensure_index(cursor, "CREATE INDEX IF NOT EXISTS idx_clarification_user ON clarification_history(user_id)")
    ensure_index(cursor, "CREATE INDEX IF NOT EXISTS idx_context_gaps_user ON context_gaps(user_id)")

    # ------------------------------------------------------------------
    # Character Trait System tables
    # ------------------------------------------------------------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS character_library (
            character_id TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            traits_json TEXT NOT NULL,
            domain TEXT DEFAULT 'general',
            description TEXT,
            philosophical_lens TEXT,
            effectiveness_score REAL DEFAULT 0.5,
            usage_count INTEGER DEFAULT 0,
            is_base BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS character_usage_outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            character_id TEXT NOT NULL,
            situation_json TEXT,
            conversation_length INTEGER,
            user_satisfaction REAL,
            goal_achieved BOOLEAN,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS situation_analysis_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            character_id TEXT NOT NULL,
            analysis_json TEXT NOT NULL,
            matched_character TEXT,
            match_score REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    ensure_index(cursor, "CREATE INDEX IF NOT EXISTS idx_char_outcomes_user ON character_usage_outcomes(user_id)")
    ensure_index(cursor, "CREATE INDEX IF NOT EXISTS idx_char_outcomes_char ON character_usage_outcomes(character_id)")

    # ------------------------------------------------------------------
    # Developer Analytics tables
    # ------------------------------------------------------------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS developer_access_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            endpoint TEXT,
            parameters TEXT,
            result_summary TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS system_health_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metrics_json TEXT NOT NULL,
            snapshot_time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    ensure_index(cursor, "CREATE INDEX IF NOT EXISTS idx_dev_access_user ON developer_access_log(user_id)")
    ensure_index(cursor, "CREATE INDEX IF NOT EXISTS idx_dev_access_time ON developer_access_log(timestamp)")

    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description="Production-safe SQLite schema migration")
    parser.add_argument(
        "--db",
        dest="db_path",
        default=os.environ.get("INTEGRATED_DB_PATH")
        or os.environ.get("DB_PATH")
        or "integrated_users.db",
        help="Path to SQLite DB (default: INTEGRATED_DB_PATH/DB_PATH env var or integrated_users.db)",
    )
    parser.add_argument("--backup", dest="backup", action="store_true", help="Create a backup")
    parser.add_argument("--no-backup", dest="backup", action="store_false", help="Do not create a backup")
    parser.set_defaults(backup=True)
    args = parser.parse_args()

    db_path = args.db_path

    print("🚀 Production Migration: Latest Schema")
    print("=" * 70)
    print(f"DB: {db_path}")

    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return 1

    backup_path: Optional[str] = None
    if args.backup:
        backup_path = backup_database(db_path)

    conn = sqlite3.connect(db_path)

    try:
        print("\n🔍 Applying schema updates...")

        conn.execute("BEGIN")
        changes = apply_migration(conn)
        conn.commit()

        print("\n" + "=" * 70)
        print("Migration Summary")
        print("=" * 70)

        if changes:
            print("✅ Columns added:")
            for c in changes:
                print(f"- {c}")
        else:
            print("✅ No column additions were necessary")

        if backup_path:
            print(f"\n📦 Backup saved at: {backup_path}")

        print("\n✅ Migration completed successfully")
        return 0

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        try:
            conn.rollback()
        except Exception:
            pass

        if backup_path:
            print(f"\n📦 You can restore from backup: {backup_path}")
        return 2

    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
