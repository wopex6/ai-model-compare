"""
Life Companion Profile
======================
Builds and maintains a persistent, evolving profile of each user that goes
beyond single-session context.  Tracks:

  - Core values and beliefs
  - Recurring life themes
  - Communication preferences (learned over time)
  - Relationship map (key people mentioned)
  - Life domains status (work, health, relationships, finance, learning, creativity)
  - Growth trajectory (improving / stable / declining per domain)
  - Trust level with the companion (how much they share)

The profile is updated incrementally after every conversation and summarised
periodically via a lightweight rule-based engine (no AI calls).
"""

import json
import sqlite3
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from collections import Counter


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LIFE_DOMAINS = [
    'work', 'health', 'relationships', 'finance',
    'learning', 'creativity', 'mental_wellbeing', 'physical_health',
]

DOMAIN_SENTIMENT = {
    'positive': ['great', 'amazing', 'happy', 'love', 'excited', 'proud', 'progress',
                 'improved', 'better', 'wonderful', 'fantastic', 'thriving', 'succeeding'],
    'negative': ['stressed', 'worried', 'struggling', 'failing', 'terrible', 'awful',
                 'anxious', 'depressed', 'stuck', 'hopeless', 'overwhelmed', 'frustrated'],
    'neutral':  ['okay', 'fine', 'alright', 'normal', 'same', 'unchanged', 'stable'],
}

DOMAIN_KEYWORDS = {
    'work':            ['job', 'boss', 'colleague', 'project', 'meeting', 'promotion', 'salary',
                        'office', 'client', 'deadline', 'manager', 'career', 'work', 'resume'],
    'health':          ['health', 'doctor', 'hospital', 'exercise', 'diet', 'sleep', 'sick',
                        'medication', 'fitness', 'weight', 'pain', 'therapy', 'checkup'],
    'relationships':   ['partner', 'wife', 'husband', 'girlfriend', 'boyfriend', 'friend',
                        'family', 'mother', 'father', 'sister', 'brother', 'child', 'date',
                        'marriage', 'divorce', 'breakup', 'relationship'],
    'finance':         ['money', 'budget', 'savings', 'debt', 'invest', 'mortgage', 'rent',
                        'salary', 'tax', 'expense', 'bill', 'loan', 'credit', 'retirement fund'],
    'learning':        ['learn', 'study', 'course', 'book', 'reading', 'skill', 'class',
                        'certificate', 'degree', 'training', 'knowledge', 'practice'],
    'creativity':      ['create', 'art', 'music', 'write', 'paint', 'design', 'craft',
                        'photography', 'dance', 'sing', 'compose', 'build', 'imagine'],
    'mental_wellbeing': ['anxiety', 'depression', 'stress', 'mindfulness', 'meditation',
                         'self-care', 'mental health', 'therapy', 'counselling', 'emotions',
                         'burnout', 'loneliness', 'grief', 'trauma'],
    'physical_health': ['gym', 'run', 'walk', 'yoga', 'workout', 'sports', 'injury',
                        'nutrition', 'vitamin', 'calories', 'steps', 'marathon', 'swim'],
}

VALUE_SIGNALS = {
    'family_first':   ['family comes first', 'family is everything', 'my kids', 'my children'],
    'ambition':       ['want to succeed', 'climb the ladder', 'achieve', 'ambitious', 'goal-driven'],
    'security':       ['stable', 'security', 'safe', 'predictable', 'routine'],
    'freedom':        ['freedom', 'independence', 'on my own terms', 'flexible', 'autonomy'],
    'growth':         ['grow', 'improve', 'develop', 'evolve', 'learn', 'better myself'],
    'connection':     ['belong', 'community', 'together', 'connect', 'relationship'],
    'creativity':     ['creative', 'express', 'art', 'imagine', 'innovate', 'original'],
    'service':        ['help others', 'give back', 'volunteer', 'community service', 'make a difference'],
    'health_focus':   ['healthy lifestyle', 'fitness', 'wellness', 'self-care', 'longevity'],
    'spirituality':   ['faith', 'spiritual', 'prayer', 'meditation', 'purpose', 'meaning'],
}

PERSON_PATTERNS = [
    r"my (?:wife|husband|partner|girlfriend|boyfriend|fiancee?)\s+(\w+)",
    r"my (?:son|daughter|child|kid|baby)\s+(\w+)",
    r"my (?:mother|father|mom|dad|mum)\s+(\w+)",
    r"my (?:sister|brother)\s+(\w+)",
    r"my (?:friend|best friend|mate)\s+(\w+)",
    r"my (?:boss|manager|colleague)\s+(\w+)",
    r"my (?:therapist|counsellor|coach|doctor)\s+(\w+)",
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class DomainStatus:
    domain: str
    sentiment: str = 'unknown'          # positive / negative / neutral / unknown
    confidence: float = 0.0
    last_mentioned: Optional[str] = None
    mention_count: int = 0
    trajectory: str = 'stable'          # improving / stable / declining

@dataclass
class PersonReference:
    name: str
    relationship: str                   # partner, child, friend, boss, etc.
    sentiment: str = 'neutral'
    mention_count: int = 1
    first_mentioned: str = field(default_factory=lambda: datetime.now().isoformat())
    last_mentioned: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class CompanionProfile:
    user_id: int
    # Core identity
    detected_values: Dict[str, float] = field(default_factory=dict)     # value → strength 0-1
    life_domains: Dict[str, DomainStatus] = field(default_factory=dict)
    people: Dict[str, PersonReference] = field(default_factory=dict)    # name → PersonReference
    # Communication
    trust_level: float = 0.3            # 0 = guarded, 1 = fully open
    avg_message_depth: str = 'surface'  # surface / moderate / deep
    topics_discussed: List[str] = field(default_factory=list)
    # Meta
    total_interactions: int = 0
    first_interaction: Optional[str] = None
    last_interaction: Optional[str] = None
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class LifeCompanionProfiler:
    """
    Incrementally builds a rich user profile from every message.

    Usage::

        profiler = LifeCompanionProfiler(db_conn)
        profiler.process_message(user_id=42, message="My wife Sarah and I are stressed about money")
        profile = profiler.get_profile(user_id=42)
        prompt_block = profiler.build_prompt_block(profile)
    """

    def __init__(self, db_connection=None):
        self.db = db_connection
        self._ensure_tables()

    # ------------------------------------------------------------------
    # Tables
    # ------------------------------------------------------------------
    def _ensure_tables(self):
        if not self.db:
            return
        try:
            cur = self.db.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS companion_profiles (
                    user_id       INTEGER PRIMARY KEY,
                    profile_json  TEXT NOT NULL,
                    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS companion_people (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id       INTEGER NOT NULL,
                    name          TEXT NOT NULL,
                    relationship  TEXT,
                    sentiment     TEXT DEFAULT 'neutral',
                    mention_count INTEGER DEFAULT 1,
                    first_mentioned DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_mentioned  DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, name)
                )
            ''')
            self.db.commit()
        except Exception as e:
            print(f"[CompanionProfile] table init error: {e}")

    # ------------------------------------------------------------------
    # Process a new message (call after every user message)
    # ------------------------------------------------------------------
    def process_message(self, user_id: int, message: str,
                        character_id: str = 'general') -> CompanionProfile:
        profile = self.get_profile(user_id)
        msg_lower = message.lower()

        # Update interaction counts
        profile.total_interactions += 1
        now = datetime.now().isoformat()
        if not profile.first_interaction:
            profile.first_interaction = now
        profile.last_interaction = now

        # 1. Detect domains mentioned & sentiment
        self._update_domains(profile, msg_lower)

        # 2. Detect values
        self._update_values(profile, msg_lower)

        # 3. Detect people
        self._update_people(profile, message, user_id)

        # 4. Update trust level heuristic
        self._update_trust(profile, message)

        # 5. Update message depth
        self._update_depth(profile, message)

        # Save
        profile.updated_at = now
        self._save_profile(user_id, profile)
        return profile

    # ------------------------------------------------------------------
    # Domain detection & sentiment
    # ------------------------------------------------------------------
    def _update_domains(self, profile: CompanionProfile, msg_lower: str):
        now = datetime.now().isoformat()
        for domain, keywords in DOMAIN_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw in msg_lower)
            if hits == 0:
                continue

            status = profile.life_domains.get(domain, DomainStatus(domain=domain))
            status.mention_count += hits
            status.last_mentioned = now

            # Sentiment for this message
            pos = sum(1 for w in DOMAIN_SENTIMENT['positive'] if w in msg_lower)
            neg = sum(1 for w in DOMAIN_SENTIMENT['negative'] if w in msg_lower)
            if pos > neg:
                new_sent = 'positive'
            elif neg > pos:
                new_sent = 'negative'
            else:
                new_sent = 'neutral'

            # Trajectory: compare new sentiment to previous
            if status.sentiment != 'unknown':
                sent_order = {'negative': 0, 'neutral': 1, 'positive': 2, 'unknown': 1}
                diff = sent_order.get(new_sent, 1) - sent_order.get(status.sentiment, 1)
                if diff > 0:
                    status.trajectory = 'improving'
                elif diff < 0:
                    status.trajectory = 'declining'
                # else: stable

            status.sentiment = new_sent
            status.confidence = min(0.3 + status.mention_count * 0.05, 1.0)
            profile.life_domains[domain] = status

    # ------------------------------------------------------------------
    # Values detection
    # ------------------------------------------------------------------
    @staticmethod
    def _update_values(profile: CompanionProfile, msg_lower: str):
        for value, signals in VALUE_SIGNALS.items():
            if any(s in msg_lower for s in signals):
                current = profile.detected_values.get(value, 0.0)
                profile.detected_values[value] = min(current + 0.15, 1.0)

    # ------------------------------------------------------------------
    # People detection
    # ------------------------------------------------------------------
    def _update_people(self, profile: CompanionProfile, message: str, user_id: int):
        for pattern in PERSON_PATTERNS:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                name = match.group(1).strip().title()
                # Extract relationship from pattern
                rel_match = re.search(r'my (\w+(?:\s+\w+)?)', match.group(0), re.IGNORECASE)
                relationship = rel_match.group(1).lower() if rel_match else 'unknown'

                now = datetime.now().isoformat()
                if name in profile.people:
                    profile.people[name].mention_count += 1
                    profile.people[name].last_mentioned = now
                else:
                    profile.people[name] = PersonReference(
                        name=name, relationship=relationship,
                        first_mentioned=now, last_mentioned=now,
                    )
                # Persist
                self._save_person(user_id, profile.people[name])

    # ------------------------------------------------------------------
    # Trust level heuristic
    # ------------------------------------------------------------------
    @staticmethod
    def _update_trust(profile: CompanionProfile, message: str):
        msg_lower = message.lower()
        deep_signals = [
            'to be honest', 'honestly', 'i never told', 'secret',
            'vulnerable', 'ashamed', 'afraid to say', 'hard to admit',
            'between us', 'deep down', 'truth is', 'confess',
            'scared', 'terrified', 'trauma', 'abuse', 'suicidal',
        ]
        if any(s in msg_lower for s in deep_signals):
            profile.trust_level = min(profile.trust_level + 0.08, 1.0)
        elif len(message) > 200:
            profile.trust_level = min(profile.trust_level + 0.02, 1.0)
        # Natural decay toward 0.5 (equilibrium) if nothing notable
        else:
            if profile.trust_level > 0.5:
                profile.trust_level = max(profile.trust_level - 0.005, 0.5)
            elif profile.trust_level < 0.5:
                profile.trust_level = min(profile.trust_level + 0.005, 0.5)

    # ------------------------------------------------------------------
    # Message depth
    # ------------------------------------------------------------------
    @staticmethod
    def _update_depth(profile: CompanionProfile, message: str):
        length = len(message)
        deep_markers = ['because', 'the reason', 'i think', 'i feel',
                        'it makes me', 'reminds me', 'i remember', 'meaning']
        depth_score = sum(1 for m in deep_markers if m in message.lower())
        if length > 250 or depth_score >= 3:
            profile.avg_message_depth = 'deep'
        elif length > 100 or depth_score >= 1:
            profile.avg_message_depth = 'moderate'
        else:
            profile.avg_message_depth = 'surface'

    # ------------------------------------------------------------------
    # Prompt block for AI
    # ------------------------------------------------------------------
    def build_prompt_block(self, profile: CompanionProfile) -> str:
        if not profile or profile.total_interactions < 2:
            return ''

        lines = ["[LIFE COMPANION PROFILE]"]

        # Values
        top_values = sorted(profile.detected_values.items(), key=lambda x: -x[1])[:4]
        if top_values:
            vals = ', '.join(f"{v.replace('_', ' ')} ({s:.0%})" for v, s in top_values)
            lines.append(f"Core values: {vals}")

        # Domain status
        active = [ds for ds in profile.life_domains.values()
                  if ds.confidence > 0.3 and ds.sentiment != 'unknown']
        if active:
            domain_strs = [f"{ds.domain}: {ds.sentiment} ({ds.trajectory})" for ds in
                           sorted(active, key=lambda d: -d.confidence)[:5]]
            lines.append(f"Life areas: {'; '.join(domain_strs)}")

        # Key people
        if profile.people:
            people_strs = [f"{p.name} ({p.relationship})" for p in
                           sorted(profile.people.values(), key=lambda p: -p.mention_count)[:5]]
            lines.append(f"Important people: {', '.join(people_strs)}")

        # Trust & depth
        trust_label = 'guarded' if profile.trust_level < 0.35 else (
            'open' if profile.trust_level > 0.65 else 'moderate')
        lines.append(f"Trust level: {trust_label} | Message depth: {profile.avg_message_depth}")
        lines.append(f"Total interactions: {profile.total_interactions}")

        return '\n'.join(lines)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def get_profile(self, user_id: int) -> CompanionProfile:
        if not self.db:
            return CompanionProfile(user_id=user_id)
        try:
            cur = self.db.cursor()
            cur.execute('SELECT profile_json FROM companion_profiles WHERE user_id = ?', (user_id,))
            row = cur.fetchone()
            if row:
                return self._deserialize(user_id, row[0])
        except Exception:
            pass
        return CompanionProfile(user_id=user_id)

    def _save_profile(self, user_id: int, profile: CompanionProfile):
        if not self.db:
            return
        try:
            data = self._serialize(profile)
            cur = self.db.cursor()
            cur.execute('''
                INSERT OR REPLACE INTO companion_profiles (user_id, profile_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, data))
            self.db.commit()
        except Exception as e:
            print(f"[CompanionProfile] save error: {e}")

    def _save_person(self, user_id: int, person: PersonReference):
        if not self.db:
            return
        try:
            cur = self.db.cursor()
            cur.execute('''
                INSERT INTO companion_people (user_id, name, relationship, sentiment, mention_count, last_mentioned)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, name) DO UPDATE SET
                    mention_count = mention_count + 1,
                    last_mentioned = CURRENT_TIMESTAMP
            ''', (user_id, person.name, person.relationship, person.sentiment, person.mention_count))
            self.db.commit()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _serialize(profile: CompanionProfile) -> str:
        d = {
            'detected_values': profile.detected_values,
            'life_domains': {k: asdict(v) for k, v in profile.life_domains.items()},
            'people': {k: asdict(v) for k, v in profile.people.items()},
            'trust_level': profile.trust_level,
            'avg_message_depth': profile.avg_message_depth,
            'topics_discussed': profile.topics_discussed[-50:],
            'total_interactions': profile.total_interactions,
            'first_interaction': profile.first_interaction,
            'last_interaction': profile.last_interaction,
        }
        return json.dumps(d)

    @staticmethod
    def _deserialize(user_id: int, json_str: str) -> CompanionProfile:
        try:
            d = json.loads(json_str)
            profile = CompanionProfile(user_id=user_id)
            profile.detected_values = d.get('detected_values', {})
            profile.life_domains = {
                k: DomainStatus(**v) for k, v in d.get('life_domains', {}).items()
            }
            profile.people = {
                k: PersonReference(**v) for k, v in d.get('people', {}).items()
            }
            profile.trust_level = d.get('trust_level', 0.3)
            profile.avg_message_depth = d.get('avg_message_depth', 'surface')
            profile.topics_discussed = d.get('topics_discussed', [])
            profile.total_interactions = d.get('total_interactions', 0)
            profile.first_interaction = d.get('first_interaction')
            profile.last_interaction = d.get('last_interaction')
            return profile
        except Exception:
            return CompanionProfile(user_id=user_id)


# ---------------------------------------------------------------------------
# Module-level factory
# ---------------------------------------------------------------------------
_instance = None

def get_life_companion_profiler(db_connection=None) -> LifeCompanionProfiler:
    global _instance
    if _instance is None or db_connection is not None:
        _instance = LifeCompanionProfiler(db_connection)
    return _instance
