"""
Life Pattern Detector
=====================
Analyses conversation history to surface recurring patterns the user may not
see themselves:

  - Recurring struggles (same problem keeps coming back)
  - Growth patterns (areas where the user is improving)
  - Life rhythms (time-of-day / day-of-week mood patterns)
  - Avoidance patterns (topics they start but drop)
  - Breakthrough moments (significant positive shifts)

All analysis is rule-based (no AI calls).  Results are injected into the AI
prompt so characters can proactively reference patterns.
"""

import json
import sqlite3
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import Counter, defaultdict


# ---------------------------------------------------------------------------
# Pattern types
# ---------------------------------------------------------------------------

@dataclass
class RecurringPattern:
    pattern_type: str           # recurring_struggle, growth, avoidance, rhythm, breakthrough
    description: str
    frequency: int              # times observed
    first_seen: str
    last_seen: str
    domain: str = 'general'     # work, health, relationships, etc.
    confidence: float = 0.5
    actionable_insight: str = ''

@dataclass
class LifeRhythm:
    """Time-based mood/engagement pattern."""
    period: str                 # morning, afternoon, evening, night
    day_pattern: str            # weekday, weekend
    dominant_emotion: str
    avg_intensity: float
    sample_size: int

@dataclass
class PatternReport:
    user_id: int
    recurring_struggles: List[RecurringPattern] = field(default_factory=list)
    growth_areas: List[RecurringPattern] = field(default_factory=list)
    avoidance_patterns: List[RecurringPattern] = field(default_factory=list)
    breakthroughs: List[RecurringPattern] = field(default_factory=list)
    life_rhythms: List[LifeRhythm] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


# Domain keywords for classification
DOMAIN_KEYWORDS = {
    'work':          ['job', 'boss', 'colleague', 'project', 'deadline', 'meeting', 'salary', 'career', 'promotion', 'office', 'work'],
    'relationships': ['partner', 'wife', 'husband', 'friend', 'family', 'mother', 'father', 'dating', 'marriage', 'breakup', 'relationship'],
    'health':        ['health', 'exercise', 'sleep', 'diet', 'doctor', 'pain', 'sick', 'weight', 'anxiety', 'depression', 'therapy'],
    'finance':       ['money', 'budget', 'debt', 'savings', 'invest', 'rent', 'mortgage', 'expense', 'salary', 'bills'],
    'learning':      ['learn', 'study', 'course', 'book', 'skill', 'training', 'degree', 'practice'],
    'creativity':    ['create', 'art', 'music', 'write', 'design', 'paint', 'build', 'project'],
}

# Struggle indicators
STRUGGLE_WORDS = [
    'again', 'still', 'same problem', 'keeps happening', 'every time',
    'can\'t stop', 'stuck', 'not improving', 'getting worse', 'always',
    'never changes', 'back to square one', 'relapsed', 'struggling again',
]

# Growth indicators
GROWTH_WORDS = [
    'progress', 'improved', 'better', 'finally', 'breakthrough',
    'figured out', 'learned', 'growing', 'managed to', 'proud',
    'overcame', 'succeeded', 'accomplished', 'milestone', 'first time',
]

# Avoidance indicators
AVOIDANCE_WORDS = [
    'don\'t want to talk about', 'never mind', 'forget it', 'it\'s fine',
    'doesn\'t matter', 'let\'s change the subject', 'anyway',
    'not important', 'whatever', 'skip that',
]


class LifePatternDetector:
    """
    Detects recurring patterns across a user's conversation history.

    Usage::

        detector = LifePatternDetector(db_conn)
        detector.process_message(user_id=42, message="I'm stressed about work again",
                                 emotion='stressed', domain='work')
        report = detector.generate_report(user_id=42)
        prompt_block = detector.build_prompt_block(report)
    """

    def __init__(self, db_connection=None):
        self.db = db_connection
        self._ensure_tables()

    def _ensure_tables(self):
        if not self.db:
            return
        try:
            cur = self.db.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS life_patterns (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id       INTEGER NOT NULL,
                    pattern_type  TEXT NOT NULL,
                    domain        TEXT DEFAULT 'general',
                    description   TEXT,
                    keywords      TEXT,
                    emotion       TEXT,
                    intensity     REAL DEFAULT 0.5,
                    hour_of_day   INTEGER,
                    day_of_week   INTEGER,
                    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS pattern_summaries (
                    user_id       INTEGER PRIMARY KEY,
                    report_json   TEXT,
                    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.db.commit()
        except Exception as e:
            print(f"[LifePatternDetector] table init error: {e}")

    # ------------------------------------------------------------------
    # Process every message (lightweight tagging)
    # ------------------------------------------------------------------
    def process_message(self, user_id: int, message: str,
                        emotion: str = 'neutral', intensity: float = 0.5,
                        domain: str = None):
        msg_lower = message.lower()
        now = datetime.now()

        if not domain:
            domain = self._detect_domain(msg_lower)

        # Tag pattern type
        pattern_type = 'observation'
        if any(w in msg_lower for w in STRUGGLE_WORDS):
            pattern_type = 'struggle'
        elif any(w in msg_lower for w in GROWTH_WORDS):
            pattern_type = 'growth'
        elif any(w in msg_lower for w in AVOIDANCE_WORDS):
            pattern_type = 'avoidance'

        # Extract key phrases
        keywords = self._extract_key_phrases(msg_lower)

        self._save_pattern_entry(
            user_id=user_id,
            pattern_type=pattern_type,
            domain=domain,
            description=message[:200],
            keywords=keywords,
            emotion=emotion,
            intensity=intensity,
            hour=now.hour,
            day=now.weekday(),
        )

    # ------------------------------------------------------------------
    # Generate full report
    # ------------------------------------------------------------------
    def generate_report(self, user_id: int, days: int = 90) -> PatternReport:
        report = PatternReport(user_id=user_id)

        if not self.db:
            return report

        try:
            entries = self._load_entries(user_id, days)
            if len(entries) < 5:
                return report

            # 1. Recurring struggles
            report.recurring_struggles = self._find_recurring(
                entries, 'struggle', min_occurrences=3)

            # 2. Growth areas
            report.growth_areas = self._find_recurring(
                entries, 'growth', min_occurrences=2)

            # 3. Avoidance patterns
            report.avoidance_patterns = self._find_recurring(
                entries, 'avoidance', min_occurrences=2)

            # 4. Breakthroughs (growth with high intensity)
            report.breakthroughs = [
                p for p in report.growth_areas if p.confidence > 0.7
            ]

            # 5. Life rhythms
            report.life_rhythms = self._analyse_rhythms(entries)

            # Cache the report
            self._save_report(user_id, report)

        except Exception as e:
            print(f"[LifePatternDetector] report error: {e}")

        return report

    # ------------------------------------------------------------------
    # Find recurring patterns of a given type
    # ------------------------------------------------------------------
    def _find_recurring(self, entries: List[Dict], pattern_type: str,
                        min_occurrences: int = 3) -> List[RecurringPattern]:
        filtered = [e for e in entries if e['pattern_type'] == pattern_type]
        if not filtered:
            return []

        # Group by domain
        by_domain = defaultdict(list)
        for e in filtered:
            by_domain[e['domain']].append(e)

        patterns = []
        for domain, domain_entries in by_domain.items():
            if len(domain_entries) < min_occurrences:
                continue

            dates = [e['created_at'] for e in domain_entries]
            dates.sort()

            # Build description
            emotions = Counter(e['emotion'] for e in domain_entries if e['emotion'])
            top_emotion = emotions.most_common(1)[0][0] if emotions else 'mixed'

            if pattern_type == 'struggle':
                desc = f"Recurring {domain} struggle (feeling {top_emotion})"
                insight = f"You've mentioned {domain} difficulties {len(domain_entries)} times. Consider exploring what keeps triggering this."
            elif pattern_type == 'growth':
                desc = f"Growth in {domain} area"
                insight = f"You've shown {len(domain_entries)} signs of progress in {domain}. Keep building on this momentum!"
            elif pattern_type == 'avoidance':
                desc = f"Tendency to avoid {domain} topics"
                insight = f"You've redirected away from {domain} topics {len(domain_entries)} times. This might be worth exploring when you're ready."
            else:
                desc = f"Pattern in {domain}"
                insight = ''

            patterns.append(RecurringPattern(
                pattern_type=pattern_type,
                description=desc,
                frequency=len(domain_entries),
                first_seen=dates[0],
                last_seen=dates[-1],
                domain=domain,
                confidence=min(0.3 + len(domain_entries) * 0.1, 0.95),
                actionable_insight=insight,
            ))

        return sorted(patterns, key=lambda p: -p.frequency)

    # ------------------------------------------------------------------
    # Life rhythms (time-of-day / day-of-week patterns)
    # ------------------------------------------------------------------
    def _analyse_rhythms(self, entries: List[Dict]) -> List[LifeRhythm]:
        rhythms = []

        # Group by time period
        periods = {'morning': (5, 12), 'afternoon': (12, 17),
                   'evening': (17, 21), 'night': (21, 5)}

        for period_name, (start, end) in periods.items():
            if start < end:
                period_entries = [e for e in entries
                                 if e.get('hour') is not None and start <= e['hour'] < end]
            else:  # night wraps around
                period_entries = [e for e in entries
                                 if e.get('hour') is not None and (e['hour'] >= start or e['hour'] < end)]

            if len(period_entries) < 3:
                continue

            emotions = Counter(e['emotion'] for e in period_entries if e['emotion'])
            if emotions:
                top = emotions.most_common(1)[0]
                avg_int = sum(e.get('intensity', 0.5) for e in period_entries) / len(period_entries)
                rhythms.append(LifeRhythm(
                    period=period_name,
                    day_pattern='all',
                    dominant_emotion=top[0],
                    avg_intensity=round(avg_int, 2),
                    sample_size=len(period_entries),
                ))

        return rhythms

    # ------------------------------------------------------------------
    # Prompt block
    # ------------------------------------------------------------------
    def build_prompt_block(self, report: PatternReport) -> str:
        lines = []

        if report.recurring_struggles:
            lines.append("[LIFE PATTERNS — RECURRING STRUGGLES]")
            for p in report.recurring_struggles[:3]:
                lines.append(f"  • {p.description} (seen {p.frequency}x)")
                if p.actionable_insight:
                    lines.append(f"    Insight: {p.actionable_insight}")

        if report.growth_areas:
            lines.append("[LIFE PATTERNS — GROWTH AREAS]")
            for p in report.growth_areas[:3]:
                lines.append(f"  • {p.description} (seen {p.frequency}x)")

        if report.avoidance_patterns:
            lines.append("[LIFE PATTERNS — AVOIDANCE (handle gently)]")
            for p in report.avoidance_patterns[:2]:
                lines.append(f"  • {p.description}")

        if report.life_rhythms:
            lines.append("[LIFE RHYTHMS]")
            for r in report.life_rhythms[:3]:
                lines.append(f"  • {r.period}: usually {r.dominant_emotion} "
                             f"(intensity {r.avg_intensity:.0%}, n={r.sample_size})")

        return '\n'.join(lines) if lines else ''

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _detect_domain(msg_lower: str) -> str:
        scores = {}
        for domain, keywords in DOMAIN_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw in msg_lower)
            if hits:
                scores[domain] = hits
        if scores:
            return max(scores, key=scores.get)
        return 'general'

    @staticmethod
    def _extract_key_phrases(msg_lower: str) -> str:
        words = re.findall(r'\b[a-z]{3,}\b', msg_lower)
        # Simple: just store top content words (exclude stop words)
        stop = {'the', 'and', 'but', 'for', 'are', 'was', 'not', 'you',
                'all', 'can', 'had', 'her', 'his', 'how', 'its', 'may',
                'new', 'now', 'our', 'out', 'own', 'say', 'she', 'too',
                'use', 'way', 'who', 'did', 'get', 'has', 'him', 'let',
                'one', 'put', 'two', 'any', 'been', 'have', 'just', 'like',
                'that', 'this', 'what', 'with', 'will', 'from', 'they',
                'about', 'been', 'could', 'into', 'more', 'some', 'than',
                'them', 'then', 'these', 'time', 'very', 'when', 'your',
                'also', 'back', 'because', 'before', 'being', 'between',
                'both', 'come', 'each', 'even', 'first', 'going', 'here',
                'know', 'make', 'much', 'only', 'other', 'over', 'really',
                'right', 'said', 'same', 'should', 'still', 'such', 'take',
                'thing', 'think', 'those', 'through', 'want', 'well', 'would',
                'don', 'didn', 'doesn', 'isn', 'wasn', 'aren', 'couldn',
                'haven', 'shouldn', 'wouldn', 'won'}
        filtered = [w for w in words if w not in stop]
        return json.dumps(filtered[:15])

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _save_pattern_entry(self, user_id, pattern_type, domain, description,
                            keywords, emotion, intensity, hour, day):
        if not self.db:
            return
        try:
            cur = self.db.cursor()
            cur.execute('''
                INSERT INTO life_patterns
                (user_id, pattern_type, domain, description, keywords, emotion, intensity, hour_of_day, day_of_week)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, pattern_type, domain, description, keywords, emotion, intensity, hour, day))
            self.db.commit()
        except Exception as e:
            print(f"[LifePatternDetector] save error: {e}")

    def _load_entries(self, user_id: int, days: int) -> List[Dict]:
        try:
            cur = self.db.cursor()
            cur.execute('''
                SELECT pattern_type, domain, description, keywords, emotion, intensity,
                       hour_of_day, day_of_week, created_at
                FROM life_patterns
                WHERE user_id = ? AND created_at > datetime('now', ?)
                ORDER BY created_at DESC
            ''', (user_id, f'-{days} days'))
            cols = ['pattern_type', 'domain', 'description', 'keywords', 'emotion',
                    'intensity', 'hour', 'day', 'created_at']
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        except Exception:
            return []

    def _save_report(self, user_id: int, report: PatternReport):
        if not self.db:
            return
        try:
            data = json.dumps({
                'recurring_struggles': [p.description for p in report.recurring_struggles],
                'growth_areas': [p.description for p in report.growth_areas],
                'avoidance_patterns': [p.description for p in report.avoidance_patterns],
                'rhythms': [{'period': r.period, 'emotion': r.dominant_emotion} for r in report.life_rhythms],
            })
            cur = self.db.cursor()
            cur.execute('''
                INSERT OR REPLACE INTO pattern_summaries (user_id, report_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, data))
            self.db.commit()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Module-level factory
# ---------------------------------------------------------------------------
_instance = None

def get_life_pattern_detector(db_connection=None) -> LifePatternDetector:
    global _instance
    if _instance is None or db_connection is not None:
        _instance = LifePatternDetector(db_connection)
    return _instance
