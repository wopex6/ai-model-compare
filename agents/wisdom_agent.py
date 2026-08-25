"""
Wisdom Agent
============
Continuously learns from a user's conversation history and life situations to:

1. Detect recurring patterns — mistakes repeated, emotional triggers, decision styles
2. Build a personal wisdom profile — what this person struggles with and grows from
3. Cross-reference human/historical wisdom — philosophy, psychology, lived experience
4. Proactively generate nudges — timely, personalized advice before the mistake repeats
5. Track growth over time — is the person actually improving?

Philosophy: This is not just a chatbot. It's a patient mentor that watches quietly,
learns deeply, and speaks only when it has something genuinely useful to say.

Usage:
    # Analyze a single user and generate wisdom report
    python agents/wisdom_agent.py --user-id 23

    # Run continuously, monitoring all users every hour
    python agents/wisdom_agent.py --continuous --interval 60

    # Generate nudges for a user and print them
    python agents/wisdom_agent.py --user-id 23 --nudges

    # Dry run (no DB writes)
    python agents/wisdom_agent.py --user-id 23 --dry-run
"""

import os
import re
import sys
import json
import math
import time
import sqlite3
import hashlib
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.wisdom_knowledge_base import (
    build_wisdom_context_for_prompt,
    match_lessons_to_patterns,
    WISDOM_LESSONS,
)
from agents.wisdom_hypothesis import HypothesisEngine, Hypothesis


# ─────────────────────────────────────────────
# Module-level helpers
# ─────────────────────────────────────────────

def _merge_unique(existing: List[str], incoming: List[str], cap: int = 10) -> List[str]:
    """Merge two string lists, deduplicating and capped at `cap`.
    Incoming items are preferred (prepended) so the most recently observed
    strengths/growth areas are not crowded out by stale older ones.
    """
    seen = set()
    merged = []
    for item in list(incoming) + list(existing):  # incoming first = newest preferred
        if item not in seen:
            seen.add(item)
            merged.append(item)
    return merged[:cap]


# ─────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────

@dataclass
class LifePattern:
    """A recurring pattern detected in a user's conversations."""
    pattern_type: str           # 'mistake', 'trigger', 'avoidance', 'strength', 'growth'
    description: str
    evidence: List[str]         # Quotes or paraphrases from conversations
    frequency: int              # How many times observed
    first_seen: str
    last_seen: str
    resolved: bool = False      # Has the user shown improvement?
    confidence: float = 0.0     # 0–1

    _MAX_EVIDENCE = 5  # cap evidence snippets per pattern to prevent unbounded growth

    def to_dict(self):
        return {
            'pattern_type': self.pattern_type,
            'description': self.description,
            'evidence': self.evidence[-self._MAX_EVIDENCE:],  # keep most recent
            'frequency': self.frequency,
            'first_seen': self.first_seen,
            'last_seen': self.last_seen,
            'resolved': self.resolved,
            'confidence': max(0.0, min(1.0, self.confidence)),  # clamp to [0,1]
        }


@dataclass
class WisdomNudge:
    """A proactive piece of advice generated for a user."""
    user_id: str
    nudge_type: str             # 'warning', 'reflection', 'encouragement', 'lesson'
    title: str
    message: str
    pattern_reference: str      # Which pattern triggered this nudge
    historical_anchor: str      # Quote, story, or principle from human wisdom
    urgency: str                # 'high', 'medium', 'low'
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    delivered: bool = False

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'nudge_type': self.nudge_type,
            'title': self.title,
            'message': self.message,
            'pattern_reference': self.pattern_reference,
            'historical_anchor': self.historical_anchor,
            'urgency': self.urgency,
            'created_at': self.created_at,
            'delivered': self.delivered
        }


@dataclass
class WisdomProfile:
    """Complete wisdom profile for a single user."""
    user_id: str
    patterns: List[LifePattern] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    growth_areas: List[str] = field(default_factory=list)
    pending_nudges: List[WisdomNudge] = field(default_factory=list)
    conversation_count: int = 0
    last_analyzed: str = ''
    wisdom_score: float = 0.0   # 0–100: overall self-awareness / growth trajectory
    _data_hash: str = field(default='', repr=False)  # tracks last-analyzed data fingerprint
    score_history: List[Dict] = field(default_factory=list)  # [{score, date}] trend log

    def __post_init__(self):
        """Clamp wisdom_score to valid range at construction to prevent NaN/out-of-range."""
        if math.isnan(self.wisdom_score):
            self.wisdom_score = 0.0
        else:
            # min/max handles +inf → 100.0 and -inf → 0.0 correctly
            self.wisdom_score = max(0.0, min(100.0, self.wisdom_score))

    _MAX_PENDING_NUDGES = 20  # cap to prevent unbounded growth in JSON profile

    def to_dict(self):
        # Keep only valid, undelivered nudges — isinstance guard first to avoid AttributeError
        valid_nudges = [n for n in self.pending_nudges if isinstance(n, WisdomNudge)]
        nudges_to_save = [n for n in valid_nudges if not n.delivered]
        if len(nudges_to_save) > self._MAX_PENDING_NUDGES:
            nudges_to_save = nudges_to_save[-self._MAX_PENDING_NUDGES:]
        return {
            'user_id': self.user_id,
            'patterns': [p.to_dict() for p in self.patterns],
            'strengths': self.strengths,
            'growth_areas': self.growth_areas,
            'pending_nudges': [n.to_dict() for n in nudges_to_save],
            'conversation_count': self.conversation_count,
            'last_analyzed': self.last_analyzed,
            'wisdom_score': self.wisdom_score,
            '_data_hash': self._data_hash,
            'score_history': self.score_history[-100:],  # keep last 100 data points
        }


# ─────────────────────────────────────────────
# The Wisdom Agent
# ─────────────────────────────────────────────

class WisdomAgent:
    """
    Learns from human conversation history to generate wise, timely, personalised nudges.
    Runs continuously in the background, writing profiles to wisdom_profiles/ directory.
    """

    WISDOM_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'wisdom_profiles')
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'integrated_users.db')

    # Minimum conversations before the agent draws conclusions
    MIN_CONVERSATIONS = 3

    # Undelivered nudges older than this are expired automatically
    NUDGE_TTL_DAYS = 30

    # How many days of history to look back on per cycle
    LOOKBACK_DAYS = 90

    def __init__(self, dry_run: bool = False, verbose: bool = True):
        self.dry_run = dry_run
        self.verbose = verbose
        self._known_tables: set = set()
        self._known_tables_lock = threading.Lock()  # guards concurrent writes from ThreadPoolExecutor
        os.makedirs(self.WISDOM_DIR, exist_ok=True)
        self._setup_db_table()

    def _setup_db_table(self):
        """Create wisdom_nudges table if it doesn't exist."""
        if self.dry_run:
            return
        conn = None
        try:
            conn = sqlite3.connect(self.DB_PATH)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS wisdom_nudges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    nudge_type TEXT,
                    title TEXT,
                    message TEXT,
                    pattern_reference TEXT,
                    historical_anchor TEXT,
                    urgency TEXT DEFAULT 'medium',
                    created_at TEXT,
                    delivered INTEGER DEFAULT 0,
                    dismissed INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS wisdom_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    pattern_type TEXT,
                    description TEXT,
                    frequency INTEGER DEFAULT 1,
                    first_seen TEXT,
                    last_seen TEXT,
                    resolved INTEGER DEFAULT 0,
                    confidence REAL DEFAULT 0.0,
                    updated_at TEXT
                )
            """)
            conn.commit()
        except Exception as e:
            self._log(f"DB setup warning: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _log(self, msg: str):
        if self.verbose:
            print(f"[WisdomAgent {datetime.now().strftime('%H:%M:%S')}] {msg}")

    # ─────────────────────────────────────────
    # Data fetching
    # ─────────────────────────────────────────

    def _get_conversation_history(self, user_id: str) -> List[Dict]:
        """Fetch all conversation messages for a user from the database."""
        messages = []
        conn = None
        try:
            conn = sqlite3.connect(self.DB_PATH)
            conn.row_factory = sqlite3.Row
            cutoff = (datetime.utcnow() - timedelta(days=self.LOOKBACK_DAYS)).isoformat()

            try:
                # Strategy 1: ai_conversations table — messages stored as JSON in conversation_data
                rows = conn.execute("""
                    SELECT session_id, conversation_data, created_at
                    FROM ai_conversations
                    WHERE user_id = ? AND created_at >= ?
                    ORDER BY created_at ASC
                """, (user_id, cutoff)).fetchall()

                for row in rows:
                    try:
                        data = json.loads(row['conversation_data'] or '[]')
                        if isinstance(data, list):
                            for msg in data:
                                role = msg.get('role', msg.get('sender_type', ''))
                                content = msg.get('content', msg.get('message', ''))
                                if content and role in ('user', 'human'):
                                    messages.append({
                                        'session_id': row['session_id'],
                                        'role': role,
                                        'content': content,
                                        'created_at': row['created_at']
                                    })
                    except (json.JSONDecodeError, TypeError):
                        continue

                if messages:
                    self._log(f"Loaded {len(messages)} user messages from 'ai_conversations'")
                    return messages
            except Exception as e1:
                self._log(f"  Strategy 1 (ai_conversations) unavailable: {e1}")

            try:
                # Strategy 2: messages table joined via conversation_id
                rows = conn.execute("""
                    SELECT m.content, m.sender_type as role, m.timestamp as created_at, ac.session_id
                    FROM messages m
                    JOIN ai_conversations ac ON ac.id = m.conversation_id
                    WHERE ac.user_id = ? AND m.timestamp >= ? AND m.sender_type = 'user'
                    ORDER BY m.timestamp ASC
                """, (user_id, cutoff)).fetchall()

                if rows:
                    messages = [dict(r) for r in rows]
                    self._log(f"Loaded {len(messages)} user messages from 'messages' join")
                    return messages
            except Exception as e2:
                self._log(f"  Strategy 2 (messages join) unavailable: {e2}")

            try:
                # Strategy 3: conversation_context table
                rows = conn.execute("""
                    SELECT context_data, created_at, character as session_id
                    FROM conversation_context
                    WHERE user_id = ? AND created_at >= ?
                    ORDER BY created_at ASC
                """, (user_id, cutoff)).fetchall()

                for row in rows:
                    try:
                        data = json.loads(row['context_data'] or '{}')
                        for msg in data.get('messages', []):
                            if msg.get('role') == 'user':
                                messages.append({
                                    'session_id': row['session_id'],
                                    'role': 'user',
                                    'content': msg.get('content', ''),
                                    'created_at': row['created_at']
                                })
                    except (json.JSONDecodeError, TypeError, KeyError) as row3_err:
                        self._log(f"  Warning: skipping malformed row in conversation_context: {row3_err}")
                        continue

                if messages:
                    self._log(f"Loaded {len(messages)} messages from 'conversation_context'")
            except Exception as e3:
                self._log(f"  Strategy 3 (conversation_context) unavailable: {e3}")

        except Exception as e:
            self._log(f"Error fetching conversations: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

        return messages

    def _get_all_user_ids(self) -> List[str]:
        """Get all user IDs by auto-discovering tables with a user_id column."""
        user_id_set: set = set()
        conn = None
        try:
            conn = sqlite3.connect(self.DB_PATH)
            conn.row_factory = sqlite3.Row
            tables = self._discover_user_tables(conn)
            for table in tables:
                safe_tname = ''.join(c for c in table['name'] if c.isalnum() or c == '_')
                try:
                    rows = conn.execute(
                        f"SELECT DISTINCT user_id FROM {safe_tname} WHERE user_id IS NOT NULL"
                    ).fetchall()
                    for r in rows:
                        if r[0]:
                            user_id_set.add(str(r[0]))
                except Exception as uid_err:
                    self._log(f"  Warning: could not scan user_ids from '{table['name']}': {uid_err}")
                    continue
            self._log(f"Found {len(user_id_set)} unique users across all tables")
        except Exception as e:
            self._log(f"Error fetching user IDs: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
        return list(user_id_set)

    def _load_wisdom_profile(self, user_id: str) -> WisdomProfile:
        """Load existing wisdom profile from disk, or create a new one."""
        path = os.path.join(self.WISDOM_DIR, f"{user_id}.json")
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                profile = WisdomProfile(user_id=user_id)
                profile.conversation_count = data.get('conversation_count', 0)
                profile.last_analyzed = data.get('last_analyzed', '')
                raw_ws = data.get('wisdom_score', 0.0)
                try:
                    _ws = float(raw_ws) if raw_ws is not None else 0.0
                    profile.wisdom_score = 0.0 if math.isnan(_ws) else max(0.0, min(100.0, _ws))
                except (ValueError, TypeError):
                    profile.wisdom_score = 0.0
                profile.strengths = data.get('strengths', [])[:10]
                profile.growth_areas = data.get('growth_areas', [])[:10]
                profile._data_hash = data.get('_data_hash', '')
                profile.score_history = data.get('score_history', [])
                # Restore patterns (needed for cumulative pattern history)
                _VALID_PTYPES = {'mistake', 'trigger', 'avoidance', 'strength', 'growth', 'general'}
                for p in data.get('patterns', []):
                    try:
                        raw_pt   = p.get('pattern_type', 'general')
                        raw_conf = p.get('confidence', 0.5)
                        raw_freq = p.get('frequency', 1)
                        try:
                            clamped_conf = max(0.0, min(1.0, float(raw_conf)))
                        except (ValueError, TypeError):
                            clamped_conf = 0.5
                        try:
                            clamped_freq = max(1, int(raw_freq))
                        except (ValueError, TypeError):
                            clamped_freq = 1
                        profile.patterns.append(LifePattern(
                            pattern_type=raw_pt if raw_pt in _VALID_PTYPES else 'general',
                            description=p.get('description', ''),
                            evidence=p.get('evidence', []),
                            frequency=clamped_freq,
                            first_seen=p.get('first_seen', ''),
                            last_seen=p.get('last_seen', ''),
                            resolved=p.get('resolved', False),
                            confidence=clamped_conf,
                        ))
                    except Exception:
                        continue
                # Restore only undelivered pending nudges from disk
                # (delivered=True nudges have already been shown and written to DB)
                _valid_nudge_types = {'warning', 'reflection', 'encouragement', 'lesson'}
                _valid_urgencies   = {'high', 'medium', 'low'}
                for n in data.get('pending_nudges', []):
                    try:
                        if n.get('delivered', False):
                            continue
                        raw_nt = n.get('nudge_type', 'reflection')
                        raw_urg = n.get('urgency', 'medium')
                        profile.pending_nudges.append(WisdomNudge(
                            user_id=user_id,
                            nudge_type=raw_nt if raw_nt in _valid_nudge_types else 'reflection',
                            title=n.get('title', ''),
                            message=n.get('message', ''),
                            pattern_reference=n.get('pattern_reference', ''),
                            historical_anchor=n.get('historical_anchor', ''),
                            urgency=raw_urg if raw_urg in _valid_urgencies else 'medium',
                            created_at=n.get('created_at', ''),
                            delivered=False,
                        ))
                    except Exception:
                        continue
                return profile
            except Exception as load_err:
                self._log(f"  Warning: could not load profile for {user_id}: {load_err} — starting fresh")
        return WisdomProfile(user_id=user_id)

    def _save_wisdom_profile(self, profile: WisdomProfile):
        """Save wisdom profile to disk and write nudges to DB."""
        if self.dry_run:
            return
        path = os.path.join(self.WISDOM_DIR, f"{profile.user_id}.json")
        try:
            with open(path, 'w') as f:
                json.dump(profile.to_dict(), f, indent=2)
        except Exception as e:
            self._log(f"Profile JSON write error for {profile.user_id}: {e}")
            return

        # Write nudges and patterns in a single DB connection
        if profile.pending_nudges or profile.patterns:
            conn = None
            try:
                conn = sqlite3.connect(self.DB_PATH)

                # ── Nudges ────────────────────────────────────────────
                if profile.pending_nudges:
                    # Expire undelivered nudges older than NUDGE_TTL_DAYS
                    ttl_cutoff = (datetime.utcnow() - timedelta(days=self.NUDGE_TTL_DAYS)).isoformat()
                    try:
                        conn.execute(
                            "UPDATE wisdom_nudges SET delivered = 1 WHERE user_id = ? AND delivered = 0 AND created_at < ?",
                            (profile.user_id, ttl_cutoff)
                        )
                    except Exception as ttl_err:
                        self._log(f"  Warning: could not expire old nudges for {profile.user_id}: {ttl_err}")

                    # Deduplicate by content-hash: (user_id, title, message[:80])
                    existing_hashes: set = set()
                    try:
                        rows = conn.execute(
                            "SELECT title, message FROM wisdom_nudges WHERE user_id = ? AND delivered = 0",
                            (profile.user_id,)
                        ).fetchall()
                        existing_hashes = {
                            hashlib.sha256(f"{profile.user_id}:{r[0]}:{(r[1] or '')[:80]}".encode()).hexdigest()
                            for r in rows
                        }
                    except Exception as exist_err:
                        self._log(f"  Warning: could not query existing nudges for {profile.user_id}: {exist_err} — may insert duplicates")
                    inserted = 0
                    for nudge in profile.pending_nudges:
                        nudge_hash = hashlib.sha256(
                            f"{nudge.user_id}:{nudge.title}:{nudge.message[:80]}".encode()
                        ).hexdigest()
                        if nudge_hash in existing_hashes:
                            continue
                        conn.execute("""
                            INSERT INTO wisdom_nudges
                            (user_id, nudge_type, title, message, pattern_reference, historical_anchor, urgency, created_at, delivered)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                        """, (
                            nudge.user_id, nudge.nudge_type, nudge.title, nudge.message,
                            nudge.pattern_reference, nudge.historical_anchor,
                            nudge.urgency, nudge.created_at
                        ))
                        inserted += 1
                    if inserted:
                        self._log(f"  Wrote {inserted} new nudge(s) to DB")

                # ── Patterns ──────────────────────────────────────────
                if profile.patterns:
                    for p in profile.patterns:
                        conn.execute("""
                            INSERT OR REPLACE INTO wisdom_patterns
                            (user_id, pattern_type, description, frequency, first_seen, last_seen, resolved, confidence, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            profile.user_id, p.pattern_type, p.description,
                            p.frequency, p.first_seen, p.last_seen,
                            int(p.resolved), p.confidence, datetime.now().isoformat()
                        ))

                conn.commit()
            except Exception as e:
                self._log(f"DB write error for {profile.user_id}: {e}")
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

    # ─────────────────────────────────────────
    # Full context gathering
    # ─────────────────────────────────────────

    # Tables to skip entirely — system/auth tables with no life context value
    _SKIP_TABLES = {
        'users', 'user_roles', 'sessions', 'auth_tokens', 'refresh_tokens',
        'password_resets', 'email_verifications', 'admin_logs', 'rate_limits',
        'migrations', 'schema_versions', 'sqlite_sequence', 'sqlite_stat1',
        'ai_budget_denials', 'ai_budget_settings', 'feature_flags',
        'feature_usage', 'response_feedback', 'ab_tests', 'ab_test_assignments',
        'message_usage', 'daily_stats', 'system_events', 'audit_log',
        # wisdom agent's own tables
        'wisdom_nudges', 'wisdom_patterns',
    }

    # Max rows to pull per table (keeps prompts manageable)
    _TABLE_ROW_LIMIT = 20

    def _discover_user_tables(self, conn) -> List[Dict]:
        """
        Scan the DB schema and return all tables that:
        1. Have a user_id column (directly linkable to a user)
        2. Are not in the skip list
        Row-count filtering per user is deferred to _gather_full_user_context.
        Returns list of dicts: {name, columns, ts_col, json_cols}
        """
        tables = []
        all_tables = [
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        ]

        for tname in all_tables:
            if tname in self._SKIP_TABLES:
                continue
            try:
                safe_tname_pragma = ''.join(c for c in tname if c.isalnum() or c == '_')
                cols_info = conn.execute(f"PRAGMA table_info({safe_tname_pragma})").fetchall()
                col_names = [c[1] for c in cols_info]

                # Must have a user_id column to be linkable
                if 'user_id' not in col_names:
                    continue

                # Detect timestamp column (for ordering by recency)
                ts_col = next((c for c in col_names
                               if c in ('created_at', 'updated_at', 'timestamp',
                                        'last_seen', 'last_updated', 'date')), None)

                # Detect JSON blob columns — use a set to deduplicate in case a column
                # name matches multiple keywords (e.g. 'pattern_data_metadata')
                json_cols = list(dict.fromkeys(
                    c for c in col_names
                    if any(kw in c for kw in ('_json', '_data', 'profile_json',
                                               'report_json', 'preferences',
                                               'context_data', 'pattern_data',
                                               'metadata', 'signals_json'))
                ))

                tables.append({
                    'name': tname,
                    'columns': col_names,
                    'ts_col': ts_col,
                    'json_cols': json_cols,
                })
            except Exception as pragma_err:
                self._log(f"  Warning: could not inspect table '{tname}': {pragma_err}")
                continue

        return tables

    def _read_table_for_user(self, conn, table: Dict, user_id: str) -> List[Dict]:
        """
        Read rows for a user from a discovered table.
        Orders by timestamp if available, limits rows, and expands JSON columns.
        """
        tname = table['name']
        ts_col = table['ts_col']
        json_cols = table['json_cols']

        # Sanitise table and column names — they come from DB schema (not user input)
        # but guard against any names with SQL-special characters from future migrations
        safe_tname = ''.join(c for c in tname if c.isalnum() or c == '_')
        safe_order = ''
        if ts_col:
            safe_ts = ''.join(c for c in ts_col if c.isalnum() or c == '_')
            safe_order = f"ORDER BY {safe_ts} DESC"
        try:
            rows = conn.execute(
                f"SELECT * FROM {safe_tname} WHERE user_id=? {safe_order} LIMIT {self._TABLE_ROW_LIMIT}",
                (user_id,)
            ).fetchall()
        except Exception as tbl_err:
            self._log(f"  Warning: could not read table '{tname}' for user {user_id}: {tbl_err}")
            return []

        if not rows:
            return []

        result = []
        for row in rows:
            r = dict(row)
            # Expand JSON columns into sub-dicts
            for jcol in json_cols:
                if r.get(jcol) and isinstance(r[jcol], str):
                    try:
                        r[jcol] = json.loads(r[jcol])
                    except (json.JSONDecodeError, ValueError) as jcol_err:
                        self._log(f"  Warning: could not parse JSON column '{jcol}' in '{tname}': {jcol_err}")
            # Strip None values to keep the context compact
            r = {k: v for k, v in r.items() if v is not None and v != '' and v != '[]' and v != '{}'}
            result.append(r)

        return result

    def _gather_full_user_context(self, user_id: str) -> Dict:
        """
        AUTO-DISCOVERING context gatherer.

        Scans the entire DB schema at runtime and reads every table that has
        a user_id column. New tables added to the app are automatically included
        without any code changes to this agent.

        Also reads the health profile JSON file (separate from DB).
        Returns a dict keyed by table name with the user's rows.
        """
        ctx = {}
        new_tables_found = []
        conn = None

        try:
            conn = sqlite3.connect(self.DB_PATH)
            conn.row_factory = sqlite3.Row

            # ── 1. Discover all user-linked tables ────────────────
            tables = self._discover_user_tables(conn)

            for table in tables:
                rows = self._read_table_for_user(conn, table, user_id)
                if rows:
                    ctx[table['name']] = rows
                    # Track tables we haven't seen before — only tables with actual rows
                    with self._known_tables_lock:
                        if table['name'] not in self._known_tables:
                            new_tables_found.append(table['name'])
                            self._known_tables.add(table['name'])

            # ── 2. Log any newly discovered tables ────────────────
            if new_tables_found:
                self._log(f"  ✨ New data sources discovered: {new_tables_found}")

            # ── 3. Health profile JSON file ───────────────────────
            # This lives outside the DB so needs special handling
            hp_path = os.path.join(
                os.path.dirname(self.DB_PATH), 'health_profiles', f"{user_id}.json"
            )
            if os.path.exists(hp_path):
                try:
                    with open(hp_path) as f:
                        hp = json.load(f)
                except Exception as hp_err:
                    self._log(f"  Warning: could not parse health profile for {user_id}: {hp_err}")
                    hp = {}
                if hp:
                    ctx['_health_profile_file'] = {
                        'conditions': [
                            f"{c['name']} ({c.get('status','active')})" +
                            (f", diagnosed {c['diagnosed_date']}" if c.get('diagnosed_date') else '')
                            for c in hp.get('conditions', []) if isinstance(c, dict) and c.get('name')
                        ],
                        'medications': [
                            f"{m['name']} {m.get('dose','')}"
                            for m in hp.get('medications', []) if isinstance(m, dict) and m.get('name')
                        ],
                        'supplements': [
                            f"{s['name']} {s.get('dose','')}"
                            for s in hp.get('supplements', []) if isinstance(s, dict) and s.get('name')
                        ],
                        'symptoms': [
                            s.get('description', '') for s in hp.get('symptoms', []) if isinstance(s, dict)
                        ],
                        'allergies': [
                            r for r in hp.get('diet', {}).get('restrictions', [])
                            if isinstance(r, str) and r.startswith('ALLERGY:')
                        ],
                        'test_results_count': len(hp.get('test_results', [])),
                        'recent_tests': [
                            f"{t['test_name']}: {t['value']} (ref: {t.get('reference_range','')})"
                            for t in hp.get('test_results', [])[-10:] if isinstance(t, dict) and t.get('test_name')
                        ],
                        'health_insights': [
                            i.get('insight', '') for i in hp.get('conversation_insights', [])[-20:] if isinstance(i, dict)
                        ],
                        'action_plans': [
                            f"{p['title']} ({p.get('status','active')})"
                            for p in hp.get('action_plans', []) if isinstance(p, dict) and p.get('title')
                        ],
                    }

            # ── 4. Scan for other JSON profile directories ────────
            # Wrapped separately so an os.listdir failure doesn't drop DB context
            try:
                base_dir = os.path.dirname(self.DB_PATH)
                for dirname in os.listdir(base_dir):
                    dirpath = os.path.join(base_dir, dirname)
                    if (os.path.isdir(dirpath) and
                            dirname.endswith('_profiles') and
                            dirname not in ('health_profiles', 'wisdom_profiles',
                                            'personality_profiles', 'user_profiles')):
                        fpath = os.path.join(dirpath, f"{user_id}.json")
                        if os.path.exists(fpath):
                            try:
                                with open(fpath) as f:
                                    ctx[f'_file_{dirname}'] = json.load(f)
                                self._log(f"  ✨ New profile directory found: {dirname}/")
                            except Exception as file_parse_err:
                                self._log(f"  Warning: could not parse {dirname}/{user_id}.json: {file_parse_err}")
            except Exception as ls_err:
                self._log(f"  Warning: could not scan profile directories: {ls_err}")

        except Exception as e:
            self._log(f"Context gathering error: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

        total_sources = len([k for k in ctx if ctx[k]])
        self._log(f"  Context: {total_sources} data sources loaded")
        return ctx

    def _compute_context_hash(self, ctx: Dict, messages: List[Dict]) -> str:
        """
        Compute a hash from already-gathered context and messages.
        Accepts pre-fetched data to avoid a redundant DB round-trip.
        Hashes message content (not just count) so edits/additions both trigger re-analysis.
        Captures row count + first-row content fingerprint so both additions AND modifications
        to existing rows trigger re-analysis.
        """
        ctx_summary = {}
        for k, v in ctx.items():
            if isinstance(v, list):
                # row count + fingerprint of first row (catches both adds and in-place edits)
                first = json.dumps(v[0], sort_keys=True, default=str)[:120] if v else ''
                ctx_summary[k] = f"{len(v)}:{first}"
            else:
                # Use json.dumps with sort_keys for stable serialisation across Python versions
                ctx_summary[k] = json.dumps(v, sort_keys=True, default=str)[:120]
        msg_digest = json.dumps(
            [{'r': m.get('role', ''), 'c': m.get('content', '')[:200]} for m in messages],
            sort_keys=True
        )
        combined = json.dumps(ctx_summary, sort_keys=True, default=str) + msg_digest
        return hashlib.sha256(combined.encode()).hexdigest()

    # ─────────────────────────────────────────
    # Core AI analysis
    # ─────────────────────────────────────────

    def _analyze_with_ai(self, user_id: str, messages: List[Dict],
                          existing_profile: WisdomProfile, ctx: Dict,
                          wisdom_context: str = '',
                          hypothesis_summary: str = '',
                          hypothesis_notes: List[str] = None) -> Dict:
        """
        Use AI to analyze the FULL user context:
        conversations + health + psychology + life patterns + goals + behaviour
        + Eastern/Western historical wisdom knowledge base
        + active hypothesis state (what schools have been tested, confirmed, rejected)
        """
        if hypothesis_notes is None:
            hypothesis_notes = []
        try:
            from openai import OpenAI
            from dotenv import load_dotenv
            load_dotenv(override=True)

            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return self._rule_based_analysis(messages, existing_profile)

            client = OpenAI(api_key=api_key, timeout=60.0)

            # ── Build conversation digest ──────────────────
            # Cap digest to ~4 000 chars (≈ 1 000 tokens) so the full prompt stays
            # within gpt-4o-mini's context window even for prolific users.
            user_msgs = [m for m in messages if m.get('role', '').lower() in ('user', 'human')]
            recent_msgs = user_msgs[-60:]
            _DIGEST_CHAR_BUDGET = 4000
            _MSG_CHAR_LIMIT = 300
            digest_lines = [
                f"[{m.get('created_at','')[:10]}] {m.get('content','')[:_MSG_CHAR_LIMIT]}"
                for m in recent_msgs
            ]
            # Trim from the oldest end until we fit the budget — O(n) reversed accumulation
            total_chars = sum(len(l) for l in digest_lines)
            if total_chars > _DIGEST_CHAR_BUDGET:
                kept, running = [], 0
                for line in reversed(digest_lines):
                    if running + len(line) > _DIGEST_CHAR_BUDGET:
                        break
                    kept.append(line)
                    running += len(line)
                digest_lines = list(reversed(kept))
            conv_digest = "\n".join(digest_lines) or "No conversation messages yet."

            # ── Build dynamic context sections from auto-discovered tables ──
            # Extract known high-value tables with special formatting
            health       = ctx.get('_health_profile_file', {})
            user_profile = ctx.get('user_profiles', [{}])[0] if ctx.get('user_profiles') else {}
            behaviour    = ctx.get('user_behavioral_patterns', [])
            _cp_list     = ctx.get('companion_profiles', [])
            _cp_first    = _cp_list[0] if _cp_list and _cp_list[0] is not None else {}
            companion    = _cp_first.get('profile_json', {})
            if isinstance(companion, str):
                try: companion = json.loads(companion)
                except Exception: companion = {}

            existing_patterns = "\n".join([
                f"- {p.pattern_type}: {p.description} (seen {p.frequency}x, resolved={p.resolved})"
                for p in existing_profile.patterns
            ]) or "None yet"

            # ── Person overview ────────────────────────────
            prefs = user_profile.get('preferences', {})
            if isinstance(prefs, str):
                try: prefs = json.loads(prefs)
                except Exception: prefs = {}
            name     = f"{user_profile.get('first_name','')} {user_profile.get('last_name','')}".strip() or 'Unknown'
            age      = prefs.get('age', '?')
            location = user_profile.get('location', '?')
            occ      = prefs.get('occupation', '?')
            bio      = user_profile.get('bio', '')[:200]
            interests = ', '.join(prefs.get('interests', []))

            # ── Health section ─────────────────────────────
            health_section = ""
            if health:
                health_section = f"""
HEALTH PROFILE:
- Conditions: {', '.join(health.get('conditions', [])) or 'None'}
- Medications: {', '.join(health.get('medications', [])) or 'None'}
- Supplements: {', '.join(health.get('supplements', [])) or 'None'}
- Symptoms: {', '.join(health.get('symptoms', [])) or 'None'}
- Allergies: {', '.join(health.get('allergies', [])) or 'None'}
- Test results ({health.get('test_results_count', 0)} total, recent):
{chr(10).join('    ' + t for t in health.get('recent_tests', []))}
- Action plans: {', '.join(health.get('action_plans', [])) or 'None'}"""

            # ── Psychology / behaviour section ─────────────
            psych_section = ""
            if behaviour or companion:
                comm = next((b for b in behaviour
                             if b.get('pattern_type') == 'communication_style'), {})
                comm_data = comm.get('pattern_data', {})
                if isinstance(comm_data, str):
                    try: comm_data = json.loads(comm_data)
                    except Exception: comm_data = {}
                values  = companion.get('detected_values', {})
                domains = companion.get('life_domains', {})
                psych_section = f"""
PSYCHOLOGY & BEHAVIOUR:
- Avg message length: {comm_data.get('avg_message_length','?')} chars, question rate: {comm_data.get('question_rate','?')}, exclamation rate: {comm_data.get('exclamation_rate','?')}
- Detected personal values: {json.dumps(values) if values else 'Not yet detected'}
- Life domain focus: {json.dumps(domains) if domains else 'Not yet mapped'}"""

            # ── All other discovered tables as generic sections ─
            # Skip the ones we've already formatted above + pure system tables
            already_formatted = {
                '_health_profile_file', 'user_profiles', 'user_behavioral_patterns',
                'companion_profiles', 'ai_conversations', 'messages',
                'conversation_context', 'admin_messages', 'message_visibility',
                'pinned_messages', 'ai_suggestions_tracking', 'conversation_quality_scores',
                'user_feedback_tracking', 'ab_test_assignments', 'user_engagement_signals',
            }
            dynamic_sections = ""
            for tname, rows in ctx.items():
                if tname in already_formatted or tname.startswith('_file_') or not rows:
                    continue
                # Human-readable section header
                header = tname.replace('_', ' ').title()
                _MAX_DISPLAY_ROWS = 8  # prompt budget: cap per-table rows in AI prompt
                dynamic_sections += f"\n{header.upper()} ({len(rows)} records):\n"
                for r in rows[:_MAX_DISPLAY_ROWS]:
                    # Pick the most meaningful columns to show
                    meaningful = {k: v for k, v in r.items()
                                  if k not in ('id', 'user_id', 'created_at', 'updated_at')
                                  and v not in (None, '', [], {})}
                    line = json.dumps(meaningful, default=str)[:200]
                    dynamic_sections += f"  {line}\n"

            # ── Any extra _file_ profile directories discovered ──
            file_sections = ""
            for k, v in ctx.items():
                if k.startswith('_file_') and v:
                    dirname = k[6:]  # strip '_file_'
                    file_sections += f"\n{dirname.replace('_',' ').upper()} (from file):\n"
                    file_sections += json.dumps(v, default=str)[:400] + "\n"

            # ── Hypothesis context ─────────────────────────────────
            hyp_section = ""
            if hypothesis_summary:
                hyp_section = f"\n{hypothesis_summary}"
            if hypothesis_notes:
                hyp_section += "\nHYPOTHESIS EVALUATION THIS CYCLE:\n" + \
                               "\n".join(f"  • {n}" for n in hypothesis_notes)

            system_prompt = """You are a deeply wise, compassionate mentor AI functioning as a life mentor.
You have access to a person's COMPLETE life picture across all data sources.
You also have a structured knowledge base of Eastern and Western wisdom traditions and a
hypothesis engine that tracks which interpretations have been tested and whether they worked.

Your role:
1. Synthesise ALL available data sources — health, psychology, behaviour, conversations, life patterns
2. Match patterns to the structured wisdom knowledge base provided — identify which historical
   patterns and philosophical frameworks are most relevant to THIS person
3. Choose between COMPETING interpretations — Stoic vs Buddhist, CBT vs Psychoanalytic,
   Confucian vs Existentialist — based on THIS person's evidence profile, not generic defaults
4. RESPECT the hypothesis engine: if a school has been CONFIRMED for this person, use it.
   If REJECTED, do NOT use it again — try the suggested alternative.
5. Form NEW hypotheses: for each nudge, state which interpretation you are testing and
   what change you predict — so the engine can verify it next cycle.
6. Personalise every nudge: use the person's name, reference their specific data, avoid generalities.

Return ONLY valid JSON matching the schema exactly."""

            user_prompt = f"""PERSON OVERVIEW:
- Name: {name}
- Age: {age}, Location: {location}
- Occupation: {occ}
- Bio: {bio}
- Interests: {interests}
{health_section}
{psych_section}

ALL OTHER DATA SOURCES (auto-discovered from database):
{dynamic_sections}
{file_sections}

EXISTING KNOWN PATTERNS (from previous analyses):
{existing_patterns}
{hyp_section}

EASTERN & WESTERN WISDOM KNOWLEDGE BASE (matched to detected patterns):
{wisdom_context}

RECENT CONVERSATION MESSAGES (chronological, user only):
{conv_digest}

Return your full wisdom analysis as JSON. The nudges must include a hypothesis field:
{{
  "patterns": [
    {{
      "pattern_type": "mistake|trigger|avoidance|strength|growth",
      "description": "Specific, personal pattern in plain language",
      "evidence": ["specific data point or quote supporting this"],
      "frequency": 2,
      "confidence": 0.8,
      "resolved": false,
      "data_sources": ["source tables that informed this pattern"],
      "matched_lesson": "wisdom lesson id from knowledge base, e.g. avoidance_of_discomfort"
    }}
  ],
  "strengths": ["Specific strength with evidence"],
  "growth_areas": ["Specific growth area tied to data"],
  "wisdom_score": 45,
  "nudges": [
    {{
      "nudge_type": "warning|reflection|encouragement|lesson",
      "title": "Short title (max 8 words)",
      "message": "Personal, specific 2-3 sentence advice. Use their name. Reference their actual data.",
      "pattern_reference": "Which pattern triggered this",
      "historical_anchor": "Real quote from the matched wisdom tradition. Include thinker + work.",
      "school_chosen": "Which school you chose and WHY (e.g. CBT because user shows anxiety pattern)",
      "schools_rejected": ["Schools not chosen and why"],
      "urgency": "high|medium|low",
      "hypothesis": {{
        "pattern_id": "matched_lesson id or custom",
        "pattern_description": "The specific pattern this nudge addresses",
        "school": "Exact school of thought used",
        "hypothesis": "If this interpretation is correct, then...",
        "predicted_change": "What observable change we expect to see in the next analysis cycle"
      }}
    }}
  ]
}}

Critical rules:
- NEVER use an interpretation that the hypothesis engine has marked REJECTED for this person
- If a school is CONFIRMED, PREFER it over untested alternatives
- For new patterns with no hypothesis history, choose the school best suited to this person's
  profile (communication style, values, cultural background, psychological indicators)
- Historical anchors must be from the matched wisdom lesson or genuinely relevant alternatives
- Cross-reference ALL data sources — health affects mood, psychology shapes decisions
- Wisdom score: rises when patterns resolve, falls when they worsen or new ones emerge
- Maximum 6 patterns, 4 nudges. Prioritise health/safety at high urgency."""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=4096
            )

            if not response.choices:
                self._log("AI returned empty choices list — falling back to rule-based analysis")
                return self._rule_based_analysis(messages, existing_profile)
            text = response.choices[0].message.content.strip()
            if text.startswith("```"):
                text = re.sub(r'^```(?:json)?\s*', '', text)
                text = re.sub(r'\s*```$', '', text)

            return json.loads(text)

        except json.JSONDecodeError as e:
            self._log(f"AI returned non-JSON: {e} — falling back to rule-based analysis")
            return self._rule_based_analysis(messages, existing_profile)
        except Exception as e:
            self._log(f"AI analysis failed: {e}")
            return self._rule_based_analysis(messages, existing_profile)

    def _rule_based_analysis(self, messages: List[Dict], profile: WisdomProfile) -> Dict:
        """
        Fallback: simple keyword-based pattern detection without AI.
        Used when no OpenAI key is available.
        """
        # Normalise smart-quotes/apostrophes so "can’t" matches the keyword "can't"
        def _normalise(text: str) -> str:
            return (text
                    .replace('\u2019', "'")
                    .replace('\u2018', "'")
                    .replace('\u201c', '"')
                    .replace('\u201d', '"'))
        user_msgs = [_normalise(m.get('content', '').lower()) for m in messages
                     if m.get('role', '').lower() in ('user', 'human')]

        # Keyword clusters
        clusters = {
            'stress_anxiety': ['stressed', 'anxious', 'overwhelmed', 'worried', 'panic', 'nervous'],
            'relationship_conflict': ['argument', 'fight', 'conflict', 'angry', 'hurt', 'ignored', 'rejected'],
            'self_doubt': ["can't", "don't know", 'unsure', 'not good enough', 'failure', 'worthless'],
            'avoidance': ['avoid', 'procrastinate', 'put off', 'not ready', 'maybe someday'],
            'seeking_validation': ['what do you think', 'am i right', 'is it okay', 'should i'],
        }

        def _word_match(text: str, phrase: str) -> bool:
            """Whole-phrase match with word-boundary awareness."""
            # Use \b for single words; for multi-word phrases check presence as substring
            if ' ' in phrase:
                return phrase in text
            return bool(re.search(r'\b' + re.escape(phrase) + r'\b', text))

        patterns = []
        for cluster, keywords in clusters.items():
            hits = sum(1 for msg in user_msgs if any(_word_match(msg, kw) for kw in keywords))
            if hits >= 2:
                patterns.append({
                    'pattern_type': 'trigger' if 'stress' in cluster else 'mistake',
                    'description': cluster.replace('_', ' ').title() + f" — mentioned in {hits} conversations",
                    'evidence': [],
                    'frequency': hits,
                    'confidence': min(0.4 + hits * 0.1, 0.8),
                    'resolved': False
                })

        # Generate a minimal nudge for the highest-frequency detected pattern
        # so the fallback path is not permanently silent when the AI is unavailable.
        nudges = []
        if patterns:
            top = max(patterns, key=lambda p: p['frequency'])
            nudges = [{
                'nudge_type': 'reflection',
                'title': f"Recurring pattern: {top['description'].split(' —')[0]}",
                'message': (
                    f"Your conversations show a recurring '{top['description']}' pattern "
                    f"({top['frequency']} times). Becoming aware of it is the first step."
                ),
                'pattern_reference': top['description'],
                'historical_anchor': '',
                'urgency': 'medium',
                'hypothesis': {}
            }]

        # Merge frequency counts into existing profile patterns where description matches
        existing_desc_map = {p.description.lower(): p for p in profile.patterns}
        merged_patterns = []
        for new_p in patterns:
            desc_lower = new_p['description'].lower()
            if desc_lower in existing_desc_map:
                existing_desc_map[desc_lower].frequency += new_p['frequency']
            else:
                merged_patterns.append(new_p)

        return {
            'patterns': merged_patterns,
            'strengths': [],
            'growth_areas': [],
            # Preserve prior wisdom score — don't stamp down a user who was at 72
            # because we fell back to rule-based analysis due to a transient API error.
            'wisdom_score': profile.wisdom_score,  # preserve prior score; never stamp a magic default
            'nudges': nudges
        }

    # ─────────────────────────────────────────
    # Main analysis loop
    # ─────────────────────────────────────────

    def analyze_user(self, user_id: str, force: bool = False) -> WisdomProfile:
        """
        Full analysis pipeline for a single user using ALL data sources.
        Automatically re-runs if any data has changed since last analysis.
        Returns updated WisdomProfile with patterns and nudges.
        """
        self._log(f"Analyzing user {user_id}...")

        # Load existing profile
        profile = self._load_wisdom_profile(user_id)

        # Gather full context from all sources ONCE — reused for hashing and analysis
        ctx = self._gather_full_user_context(user_id)
        messages = self._get_conversation_history(user_id)

        # Count all available data (conversations + health entries + life patterns)
        hp = ctx.get('_health_profile_file', {})
        health_count = len(hp.get('conditions', [])) + (1 if hp.get('test_results_count', 0) else 0)
        life_pat_count = len(ctx.get('life_patterns', []))
        total_data_points = len(messages) + health_count + life_pat_count

        if total_data_points < self.MIN_CONVERSATIONS and not force:
            self._log(f"  Skipping: only {total_data_points} data points (need {self.MIN_CONVERSATIONS})")
            return profile

        # Change detection — reuse already-gathered ctx (no second DB round-trip)
        current_hash = self._compute_context_hash(ctx, messages)
        stored_hash = getattr(profile, '_data_hash', '')

        if not force and current_hash == stored_hash and profile.last_analyzed:
            self._log(f"  No changes detected since last analysis — skipping")
            return profile

        # ── Max pattern age filter: drop patterns not seen within 2× LOOKBACK_DAYS ──
        _MAX_PATTERN_AGE_DAYS = self.LOOKBACK_DAYS * 2
        _age_cutoff = (datetime.utcnow() - timedelta(days=_MAX_PATTERN_AGE_DAYS)).isoformat()[:10]
        before_filter = len(profile.patterns)
        profile.patterns = [
            p for p in profile.patterns
            if not p.last_seen or p.last_seen[:10] >= _age_cutoff or p.resolved
        ]
        if len(profile.patterns) < before_filter:
            self._log(f"  Aged out {before_filter - len(profile.patterns)} stale pattern(s) (last_seen < {_age_cutoff})")

        sources_found = [k for k in ctx if ctx[k]]
        self._log(f"  Data sources: {len(sources_found)} tables/files")
        self._log(f"  {len(messages)} messages + {life_pat_count} life patterns — running full AI analysis...")

        # ── Hypothesis engine: evaluate prior hypotheses ──────────
        # NOTE: evaluation happens BEFORE AI so we pass hypothesis notes INTO the AI.
        # We will re-evaluate scores AFTER AI returns the new wisdom_score.
        hyp_engine = HypothesisEngine(verbose=self.verbose)
        hypotheses = hyp_engine.load(user_id)
        prev_score = profile.wisdom_score  # capture score BEFORE AI updates it
        # Load evaluation notes from the previous cycle (saved alongside hypotheses)
        # These are passed into the AI so it knows what was confirmed/rejected last time.
        hyp_notes_path = os.path.join(self.WISDOM_DIR, f"{user_id}_hyp_notes.json")
        hyp_notes: List[str] = []
        if os.path.exists(hyp_notes_path):
            try:
                with open(hyp_notes_path) as _f:
                    hyp_notes = json.load(_f)
            except Exception as hyp_load_err:
                self._log(f"  Warning: could not load hyp notes for {user_id}: {hyp_load_err} — skipping")
                hyp_notes = []

        # ── Knowledge base: find relevant wisdom for detected patterns ──
        # Use ctx-derived pattern descriptions when available so the wisdom context
        # reflects what the DB actually contains this cycle, not stale disk patterns.
        ctx_pattern_descs = [
            r.get('description', '') for r in ctx.get('wisdom_patterns', [])
            if r.get('description')
        ]
        pattern_descs = ctx_pattern_descs or [p.description for p in profile.patterns]
        user_domains = list({d for desc in pattern_descs
                             for lesson in match_lessons_to_patterns([desc])
                             for d in lesson.domains})
        wisdom_context = build_wisdom_context_for_prompt(
            pattern_descriptions=pattern_descs,
            user_domains=user_domains or ['health', 'mental_health', 'relationships'],
            max_lessons=4,
        )
        hyp_summary = hyp_engine.get_active_hypotheses_summary(hypotheses)

        # AI analysis with full context + wisdom KB + hypothesis state
        result = self._analyze_with_ai(
            user_id, messages, profile, ctx,
            wisdom_context=wisdom_context,
            hypothesis_summary=hyp_summary,
            hypothesis_notes=hyp_notes,
        )
        if not result:
            self._log(f"  Analysis returned empty result")
            return profile

        # ── Evaluate hypotheses using the ACTUAL new wisdom_score from AI ──
        # This is the correct place: we now have both prev_score and the AI's new score
        if hypotheses and profile.patterns:
            raw_new_score = result.get('wisdom_score', prev_score)
            try:
                new_score_clamped = max(0.0, min(100.0, float(raw_new_score)
                                                 if raw_new_score is not None else prev_score))
            except (ValueError, TypeError):
                new_score_clamped = prev_score
            hypotheses, hyp_notes = hyp_engine.evaluate(
                hypotheses=hypotheses,
                new_patterns=result.get('patterns', [p.to_dict() for p in profile.patterns]),
                new_wisdom_score=new_score_clamped,
                prev_wisdom_score=prev_score,
                new_conversations=messages,
            )
            if not self.dry_run:
                hyp_engine.save(user_id, hypotheses)
                # Persist evaluation notes for the NEXT cycle's AI prompt
                try:
                    with open(hyp_notes_path, 'w') as _f:
                        json.dump(hyp_notes, _f)
                except Exception as hyp_notes_err:
                    self._log(f"  Warning: could not save hyp notes for {user_id}: {hyp_notes_err}")

        # Update profile with patterns (cap at 30 to prevent unbounded growth)
        _MAX_PATTERNS = 30
        now = datetime.utcnow().isoformat()
        # Build a desc→pattern dict for O(1) update lookup (avoids O(n) inner scan)
        existing_desc_map = {p.description: p for p in profile.patterns}

        _VALID_PATTERN_TYPES = {'mistake', 'trigger', 'avoidance', 'strength', 'growth', 'general'}
        for raw_p in result.get('patterns', []):
            desc = raw_p.get('description', '')
            if not desc:
                continue
            if desc in existing_desc_map:
                # Update existing pattern via direct dict lookup — O(1)
                p = existing_desc_map[desc]
                p.frequency = max(p.frequency, raw_p.get('frequency', 1))
                p.last_seen = now
                p.resolved = raw_p.get('resolved', False)
                raw_conf = raw_p.get('confidence', p.confidence)
                try:
                    p.confidence = max(0.0, min(1.0, float(raw_conf)))
                except (ValueError, TypeError):
                    pass  # keep existing confidence if AI returned non-numeric
            else:
                raw_pt = raw_p.get('pattern_type', 'general')
                raw_conf = raw_p.get('confidence', 0.5)
                try:
                    clamped_conf = max(0.0, min(1.0, float(raw_conf)))
                except (ValueError, TypeError):
                    clamped_conf = 0.5
                new_p = LifePattern(
                    pattern_type=raw_pt if raw_pt in _VALID_PATTERN_TYPES else 'general',
                    description=desc,
                    evidence=raw_p.get('evidence', [])[:3],
                    frequency=raw_p.get('frequency', 1),
                    first_seen=now,
                    last_seen=now,
                    resolved=raw_p.get('resolved', False),
                    confidence=clamped_conf
                )
                profile.patterns.append(new_p)
                existing_desc_map[desc] = new_p  # keep map in sync

        # Update strengths and growth areas (module-level _merge_unique preserves order)
        # Keep only the most recently seen patterns (resolved ones deprioritised)
        if len(profile.patterns) > _MAX_PATTERNS:
            # Keep unresolved patterns preferentially; within each group keep the newest.
            # Sort key: (resolved, last_seen) descending — unresolved (False) sorts after resolved
            # (True) when descending, so we negate the resolved flag to put unresolved first.
            profile.patterns = sorted(
                profile.patterns,
                key=lambda p: (not p.resolved, p.last_seen),
                reverse=True   # unresolved+newest first → resolved+newest last
            )[:_MAX_PATTERNS]

        profile.strengths    = _merge_unique(profile.strengths,    result.get('strengths', []))
        profile.growth_areas = _merge_unique(profile.growth_areas, result.get('growth_areas', []))
        profile.conversation_count = len(messages)
        profile.last_analyzed = datetime.utcnow().isoformat()
        # Clamp wisdom_score to valid range to guard against AI hallucinating out-of-range values
        raw_score = result.get('wisdom_score', profile.wisdom_score)
        try:
            profile.wisdom_score = max(0.0, min(100.0, float(raw_score)
                                                if raw_score is not None else profile.wisdom_score))
        except (ValueError, TypeError):
            self._log(f"  Warning: non-numeric wisdom_score '{raw_score}' from result — keeping prior score")
        # Track score history — deduplicate: only one entry per UTC date
        today = datetime.utcnow().isoformat()[:10]
        if not profile.score_history or profile.score_history[-1].get('date') != today:
            profile.score_history.append({'score': profile.wisdom_score, 'date': today})
        profile._data_hash = current_hash

        # Generate nudges — only replace pending_nudges when AI returned actual nudges.
        # If AI returned 0 nudges (fallback/rate-limit), keep the existing undelivered ones.
        raw_nudges = result.get('nudges', [])
        _valid_nudge_types = {'warning', 'reflection', 'encouragement', 'lesson'}
        _valid_urgencies   = {'high', 'medium', 'low'}
        if raw_nudges:
            profile.pending_nudges = []
        for raw_n in raw_nudges:
            if not raw_n.get('message'):
                continue
            profile.pending_nudges.append(WisdomNudge(
                user_id=user_id,
                nudge_type=raw_n.get('nudge_type', 'reflection')
                           if raw_n.get('nudge_type') in _valid_nudge_types else 'reflection',
                title=raw_n.get('title', 'A Thought For You'),
                message=raw_n.get('message', ''),
                pattern_reference=raw_n.get('pattern_reference', ''),
                historical_anchor=raw_n.get('historical_anchor', ''),
                urgency=raw_n.get('urgency', 'medium')
                        if raw_n.get('urgency') in _valid_urgencies else 'medium',
            ))

        self._log(f"  Found {len(profile.patterns)} patterns, {len(profile.pending_nudges)} nudges | wisdom score: {profile.wisdom_score:.0f}")

        # ── Form new hypotheses from AI result ───────────────────
        if not self.dry_run:
            _all_schools_cached = get_all_schools()  # hoist outside loop — immutable corpus
            new_hypotheses = []
            existing_hyp_ids = {h.id for h in hypotheses}
            for raw_n in result.get('nudges', []):
                h_data = raw_n.get('hypothesis', {})
                if not h_data:
                    continue
                h = hyp_engine.propose(
                    user_id=user_id,
                    pattern_id=h_data.get('pattern_id', 'general'),
                    pattern_description=h_data.get('pattern_description', raw_n.get('pattern_reference', '')),
                    school_of_thought=h_data.get('school') or (_all_schools_cached[0] if _all_schools_cached else 'General'),
                    hypothesis_text=h_data.get('hypothesis', raw_n.get('message', '')[:200]),
                    predicted_change=h_data.get('predicted_change', ''),
                    nudge_given=raw_n.get('message', '')[:300],
                )
                if h.id not in existing_hyp_ids:
                    new_hypotheses.append(h)
            if new_hypotheses:
                hyp_engine.save(user_id, hypotheses + new_hypotheses)
                self._log(f"  Formed {len(new_hypotheses)} new hypothesis(es)")

        # Save profile
        self._save_wisdom_profile(profile)

        return profile

    def analyze_all_users(self, max_workers: int = 4) -> List[WisdomProfile]:
        """Analyze all users with sufficient conversation history.
        Uses a ThreadPoolExecutor for concurrent I/O-bound analysis.
        """
        user_ids = self._get_all_user_ids()
        self._log(f"Found {len(user_ids)} users to analyze (max_workers={max_workers})")
        profiles = []
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(self.analyze_user, uid): uid for uid in user_ids}
            for future in as_completed(futures):
                uid = futures[future]
                try:
                    profiles.append(future.result())
                except Exception as e:
                    self._log(f"Error analyzing user {uid}: {e}")
        return profiles

    def get_pending_nudges(self, user_id: str) -> List[Dict]:
        """Get undelivered nudges for a user from the DB."""
        nudges = []
        conn = None
        try:
            conn = sqlite3.connect(self.DB_PATH)
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT id, user_id, nudge_type, title, message,
                       pattern_reference, historical_anchor, urgency,
                       created_at, delivered, dismissed
                FROM wisdom_nudges
                WHERE user_id = ? AND delivered = 0 AND dismissed = 0
                ORDER BY
                    CASE urgency WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
                    created_at ASC
            """, (user_id,)).fetchall()
            nudges = [dict(r) for r in rows]
        except Exception as e:
            self._log(f"Error fetching nudges: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
        return nudges

    def mark_nudge_delivered(self, nudge_id: int):
        """Mark a nudge as delivered after showing it to the user."""
        if self.dry_run:
            return
        conn = None
        try:
            conn = sqlite3.connect(self.DB_PATH)
            conn.execute("UPDATE wisdom_nudges SET delivered = 1 WHERE id = ?", (nudge_id,))
            conn.commit()
        except Exception as e:
            self._log(f"Error marking nudge delivered: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def print_report(self, profile: WisdomProfile):
        """Print a human-readable wisdom report."""
        print()
        print("=" * 65)
        print(f"  WISDOM PROFILE — User {profile.user_id}")
        print("=" * 65)
        print(f"  Conversations analyzed : {profile.conversation_count}")
        last = profile.last_analyzed[:19] if profile.last_analyzed else 'Never'
        print(f"  Last analyzed          : {last}")
        print(f"  Wisdom score           : {profile.wisdom_score:.0f}/100")
        print()

        if profile.strengths:
            print("STRENGTHS:")
            for s in profile.strengths:
                print(f"  ✓ {s}")
            print()

        if profile.growth_areas:
            print("GROWTH AREAS:")
            for g in profile.growth_areas:
                print(f"  → {g}")
            print()

        if profile.score_history and len(profile.score_history) > 1:
            trend = " → ".join(
                f"{e['score']:.0f} ({e['date']})"
                for e in profile.score_history[-5:]
            )
            print(f"  Score trend (last {min(5, len(profile.score_history))}): {trend}")
            print()

        if profile.patterns:
            print(f"PATTERNS DETECTED ({len(profile.patterns)}):")
            for p in profile.patterns:
                status = "✓ resolved" if p.resolved else f"seen {p.frequency}x"
                print(f"  [{p.pattern_type.upper()}] {p.description}  ({status}, confidence: {p.confidence:.0%})")
                for ev in p.evidence[-2:]:
                    print(f"    → \"{ev[:80]}\"")
            print()

        if profile.pending_nudges:
            print(f"WISDOM NUDGES ({len(profile.pending_nudges)}):")
            for n in profile.pending_nudges:
                urgency_icon = {"high": "⚠️", "medium": "💡", "low": "🌱"}.get(n.urgency, "💡")
                print(f"\n  {urgency_icon} [{n.nudge_type.upper()}] {n.title}")
                print(f"     {n.message}")
                if n.historical_anchor:
                    print(f"     📖 {n.historical_anchor}")
            print()

        print("=" * 65)

    def get_agent_status(self) -> Dict:
        """Return a lightweight status snapshot for health-check / monitoring."""
        user_ids = []
        pending_nudge_count = 0
        conn = None
        try:
            conn = sqlite3.connect(self.DB_PATH)
            conn.row_factory = sqlite3.Row
            try:
                row = conn.execute(
                    "SELECT COUNT(*) as c FROM wisdom_nudges WHERE delivered = 0 AND dismissed = 0"
                ).fetchone()
                pending_nudge_count = row['c'] if row else 0
            except Exception:
                pass
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
        try:
            user_ids = [
                f.replace('.json', '') for f in os.listdir(self.WISDOM_DIR)
                if f.endswith('.json') and not f.endswith('_hypotheses.json')
            ]
        except Exception:
            pass
        return {
            'db_path': self.DB_PATH,
            'wisdom_dir': self.WISDOM_DIR,
            'users_with_profiles': len(user_ids),
            'pending_nudges_total': pending_nudge_count,
            'dry_run': self.dry_run,
            'status_at': datetime.utcnow().isoformat(),
        }

    def run_continuous(self, interval_minutes: int = 60):
        """Run continuously, re-analyzing all users at each interval.
        Sleeps in 60-second increments for graceful shutdown responsiveness.
        Uses exponential backoff (up to 5× the interval) on repeated failures.
        """
        self._log(f"Starting continuous mode — analyzing every {interval_minutes} minutes")
        consecutive_failures = 0
        max_backoff_multiplier = 5
        _SLEEP_TICK = 60  # seconds per sleep tick — allows Ctrl-C to interrupt promptly
        while True:
            try:
                profiles = self.analyze_all_users()
                self._log(f"Cycle complete: {len(profiles)} profiles updated")
                consecutive_failures = 0
                sleep_secs = interval_minutes * 60
            except Exception as e:
                consecutive_failures += 1
                backoff = min(consecutive_failures, max_backoff_multiplier)
                sleep_secs = interval_minutes * 60 * backoff
                self._log(f"Cycle error (failure #{consecutive_failures}): {e}")
                self._log(f"Backing off — sleeping {interval_minutes * backoff} minutes...")
            else:
                self._log(f"Sleeping {interval_minutes} minutes...")
            # Short-tick sleep so KeyboardInterrupt is responsive within 60 s
            target = time.monotonic() + sleep_secs
            while time.monotonic() < target:
                time.sleep(min(_SLEEP_TICK, max(0, target - time.monotonic())))


# ─────────────────────────────────────────────
# App integration helpers (used by app.py)
# ─────────────────────────────────────────────

def get_wisdom_nudges_for_user(user_id: str) -> List[Dict]:
    """
    Called by app.py to fetch pending nudges for display.
    Returns whatever nudges are already stored immediately (non-blocking).
    Dispatches a background re-analysis if the profile is stale (>24h) or new,
    so the HTTP request path is never blocked by the full AI analysis.
    Uses dry_run=True to skip _setup_db_table overhead on this read-only hot path.
    """
    agent = WisdomAgent(dry_run=True, verbose=False)
    profile = agent._load_wisdom_profile(user_id)

    needs_refresh = True  # default: always refresh if we can't parse last_analyzed
    if profile.last_analyzed:
        try:
            last_dt = datetime.fromisoformat(profile.last_analyzed[:19])  # strip tz suffix
            needs_refresh = (datetime.utcnow() - last_dt) > timedelta(hours=24)
        except (ValueError, TypeError):
            needs_refresh = True

    if needs_refresh:
        # Fire analysis in background — don't block the caller
        trigger_wisdom_analysis(user_id)

    return agent.get_pending_nudges(user_id)


def trigger_wisdom_analysis(user_id: str):
    """Called after a conversation ends to schedule background re-analysis.
    Uses dry_run=False so nudges are persisted, but catches any DB-setup errors
    gracefully so a locked DB on the main thread does not crash the background thread.
    """
    def _run():
        try:
            agent = WisdomAgent(dry_run=False, verbose=False)
        except Exception as setup_err:
            # DB table setup failed (e.g. locked) — fall back to a fully initialised
            # dry_run agent rather than a half-initialised __new__ bypass, so all
            # instance attributes are present and no AttributeError can occur.
            try:
                agent = WisdomAgent(dry_run=True, verbose=False)
                agent.dry_run = False  # allow writes even though table setup was skipped
            except Exception:
                return  # cannot construct agent at all — abort silently
        agent.analyze_user(user_id)
    threading.Thread(target=_run, daemon=True).start()


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Wisdom Agent — learns from conversation history')
    parser.add_argument('--user-id', help='Analyze a specific user by ID')
    parser.add_argument('--all-users', action='store_true', help='Analyze all users')
    parser.add_argument('--continuous', action='store_true', help='Run in continuous loop')
    parser.add_argument('--interval', type=int, default=60, help='Minutes between cycles in continuous mode')
    parser.add_argument('--nudges', action='store_true', help='Print pending nudges for user')
    parser.add_argument('--dry-run', action='store_true', help='Analyze without writing to disk or DB')
    parser.add_argument('--quiet', action='store_true', help='Suppress progress output')
    parser.add_argument('--force', action='store_true', help='Force re-analysis even if data unchanged')
    args = parser.parse_args()

    agent = WisdomAgent(dry_run=args.dry_run, verbose=not args.quiet)

    if args.continuous:
        agent.run_continuous(interval_minutes=args.interval)
    elif args.user_id and args.nudges:
        nudges = agent.get_pending_nudges(args.user_id)
        if nudges:
            print(f"\n{len(nudges)} pending nudge(s) for user {args.user_id}:")
            for n in nudges:
                print(f"\n  [{n['urgency'].upper()}] {n['title']}")
                print(f"  {n['message']}")
                if n['historical_anchor']:
                    print(f"  📖 {n['historical_anchor']}")
        else:
            print(f"No pending nudges for user {args.user_id}")
    elif args.user_id:
        profile = agent.analyze_user(args.user_id, force=getattr(args, 'force', False))
        agent.print_report(profile)
    elif args.all_users:
        profiles = agent.analyze_all_users()
        for p in profiles:
            agent.print_report(p)
    else:
        parser.print_help()
