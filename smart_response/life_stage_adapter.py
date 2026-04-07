"""
Life Stage Adapter
==================
Detects the user's current life stage from profile data and conversation signals,
then tailors guidance, vocabulary, and priorities accordingly.

Life stages modelled:
  young_adult (18-25)  |  early_career (25-35)  |  mid_career (35-50)
  senior_career (50-60)|  pre_retirement (60-67) |  retirement (67+)
  student              |  new_parent             |  career_changer

Each stage carries default priorities, common challenges, vocabulary tweaks,
and resource recommendations that get injected into the AI prompt context.
"""

import json
import sqlite3
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict


# ---------------------------------------------------------------------------
# Data definitions
# ---------------------------------------------------------------------------

LIFE_STAGES = {
    'student': {
        'age_range': (16, 25),
        'priorities': ['academic_growth', 'career_exploration', 'social_skills', 'financial_literacy', 'identity'],
        'common_challenges': [
            'exam stress', 'choosing a major', 'peer pressure',
            'first job search', 'budgeting on limited income', 'self-identity'
        ],
        'tone': 'encouraging and relatable, avoid being preachy',
        'vocabulary_hints': 'Use approachable language. Metaphors from pop culture welcome.',
        'resources': ['study techniques', 'career quizzes', 'budgeting apps', 'mental health hotlines'],
    },
    'young_adult': {
        'age_range': (22, 30),
        'priorities': ['career_launch', 'relationships', 'financial_foundation', 'independence', 'health_habits'],
        'common_challenges': [
            'imposter syndrome', 'dating and relationships', 'rent and budgeting',
            'quarter-life crisis', 'work-life balance', 'building credit'
        ],
        'tone': 'peer-like, direct, motivating',
        'vocabulary_hints': 'Keep it real. Short, actionable advice works best.',
        'resources': ['salary negotiation', 'investing basics', 'therapy options'],
    },
    'early_career': {
        'age_range': (28, 38),
        'priorities': ['career_growth', 'long_term_relationships', 'financial_planning', 'health', 'purpose'],
        'common_challenges': [
            'promotion politics', 'work burnout', 'marriage/partnership',
            'buying a home', 'starting a family', 'managing stress'
        ],
        'tone': 'professional yet warm, action-oriented',
        'vocabulary_hints': 'Balance empathy with practical frameworks.',
        'resources': ['leadership skills', 'couples counselling', 'mortgage basics', 'stress management'],
    },
    'new_parent': {
        'age_range': (25, 45),
        'priorities': ['child_wellbeing', 'partner_relationship', 'career_juggling', 'sleep_health', 'identity_shift'],
        'common_challenges': [
            'sleep deprivation', 'parenting guilt', 'career slowdown',
            'relationship strain', 'loss of identity', 'financial pressure'
        ],
        'tone': 'compassionate, normalising, non-judgmental',
        'vocabulary_hints': 'Validate struggles first. Small wins matter enormously.',
        'resources': ['parenting communities', 'couples therapy', 'time management', 'postpartum support'],
    },
    'mid_career': {
        'age_range': (38, 52),
        'priorities': ['legacy', 'health_maintenance', 'financial_security', 'relationships', 'meaning'],
        'common_challenges': [
            'mid-life reassessment', 'aging parents', 'teenage children',
            'career plateau', 'health scares', 'meaning and purpose'
        ],
        'tone': 'respectful of experience, thought-provoking',
        'vocabulary_hints': 'Honour their experience. Ask deeper questions.',
        'resources': ['career pivoting', 'health screenings', 'estate planning', 'mentoring others'],
    },
    'career_changer': {
        'age_range': (25, 60),
        'priorities': ['skill_transfer', 'financial_bridge', 'confidence', 'networking', 'learning'],
        'common_challenges': [
            'fear of starting over', 'financial gap', 'imposter syndrome',
            'skill gaps', 'age bias', 'family pressure'
        ],
        'tone': 'empowering, realistic, step-by-step',
        'vocabulary_hints': 'Emphasise transferable skills. Celebrate courage.',
        'resources': ['skill assessment', 'portfolio building', 'networking strategies', 'financial runway planning'],
    },
    'senior_career': {
        'age_range': (50, 62),
        'priorities': ['retirement_planning', 'health', 'legacy', 'relationships', 'purpose_beyond_work'],
        'common_challenges': [
            'ageism', 'retirement anxiety', 'empty nest',
            'health management', 'succession planning', 'relevance'
        ],
        'tone': 'respectful, wisdom-acknowledging',
        'vocabulary_hints': 'Acknowledge depth of experience. Discuss legacy and meaning.',
        'resources': ['retirement calculators', 'health plans', 'volunteer opportunities', 'memoir writing'],
    },
    'pre_retirement': {
        'age_range': (60, 70),
        'priorities': ['retirement_transition', 'health_optimisation', 'social_connections', 'hobbies', 'financial_drawdown'],
        'common_challenges': [
            'identity without work', 'downsizing', 'health concerns',
            'social isolation', 'financial anxiety', 'boredom'
        ],
        'tone': 'warm, forward-looking, respectful',
        'vocabulary_hints': 'Focus on possibilities and autonomy.',
        'resources': ['retirement communities', 'travel planning', 'health optimisation', 'learning platforms'],
    },
    'retirement': {
        'age_range': (67, 100),
        'priorities': ['health', 'social_connection', 'purpose', 'legacy', 'enjoyment'],
        'common_challenges': [
            'loneliness', 'health decline', 'loss of purpose',
            'grief and loss', 'technology adaptation', 'financial management'
        ],
        'tone': 'gentle, patient, warm, deeply respectful',
        'vocabulary_hints': 'Slower pace. Acknowledge wisdom. Be a companion, not a coach.',
        'resources': ['senior centres', 'telehealth', 'memoir writing', 'family connection tools'],
    },
}

# Signals that hint at life stage from conversation content
STAGE_SIGNALS = {
    'student':        ['exam', 'assignment', 'professor', 'lecture', 'campus', 'dorm', 'GPA', 'graduate', 'thesis', 'semester'],
    'new_parent':     ['baby', 'toddler', 'nappy', 'diaper', 'breastfeed', 'daycare', 'sleep training', 'parenting', 'maternity', 'paternity'],
    'career_changer': ['career change', 'switching careers', 'new field', 'starting over', 'pivot', 'retrain', 'bootcamp'],
    'pre_retirement': ['retirement', 'retire', 'pension', 'superannuation', 'downsizing', 'empty nest'],
    'retirement':     ['retired', 'grandchild', 'grandkid', 'senior', 'aged care', 'nursing home'],
}


@dataclass
class LifeStageProfile:
    """Resolved life-stage information for a user."""
    stage: str                          # key into LIFE_STAGES
    confidence: float                   # 0.0 – 1.0
    source: str                         # 'profile_age', 'conversation_signal', 'explicit', 'default'
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    priorities: List[str] = field(default_factory=list)
    challenges: List[str] = field(default_factory=list)
    tone: str = ''
    vocabulary_hints: str = ''
    resources: List[str] = field(default_factory=list)


class LifeStageAdapter:
    """
    Detects and adapts to a user's current life stage.

    Usage::

        adapter = LifeStageAdapter(db_conn)
        profile = adapter.detect_life_stage(user_id, message="I just had my first baby")
        prompt_block = adapter.build_prompt_block(profile)
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
            cursor = self.db.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS life_stage_history (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     INTEGER NOT NULL,
                    stage       TEXT NOT NULL,
                    confidence  REAL DEFAULT 0.5,
                    source      TEXT,
                    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.db.commit()
        except Exception as e:
            print(f"[LifeStageAdapter] table init error: {e}")

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------
    def detect_life_stage(self, user_id: int, message: str = '',
                          age: Optional[int] = None,
                          explicit_stage: Optional[str] = None) -> LifeStageProfile:
        """
        Resolve the user's life stage from multiple signals.

        Priority order:
          1. Explicit stage stored / provided
          2. Age from profile
          3. Conversation signal keywords
          4. Previously detected stage (cached)
          5. Default ('young_adult')
        """
        # 1. Explicit override
        if explicit_stage and explicit_stage in LIFE_STAGES:
            return self._build_profile(explicit_stage, 1.0, 'explicit', user_id)

        # 2. Try stored stage first (DB cache)
        cached = self._load_cached_stage(user_id)

        # 3. Age from profile
        if age is None:
            age = self._fetch_age_from_profile(user_id)

        age_stage, age_conf = self._stage_from_age(age) if age else (None, 0.0)

        # 4. Conversation signals
        signal_stage, signal_conf = self._stage_from_signals(message)

        # Merge: pick highest-confidence source
        candidates = []
        if age_stage:
            candidates.append((age_stage, age_conf, 'profile_age'))
        if signal_stage:
            candidates.append((signal_stage, signal_conf, 'conversation_signal'))
        if cached:
            candidates.append((cached['stage'], cached['confidence'] * 0.9, 'cached'))  # decay

        if not candidates:
            return self._build_profile('young_adult', 0.2, 'default', user_id)

        best = max(candidates, key=lambda c: c[1])
        profile = self._build_profile(best[0], best[1], best[2], user_id)

        # Persist if significantly more confident than cache
        if not cached or best[1] > cached.get('confidence', 0) * 0.95:
            self._save_stage(user_id, profile)

        return profile

    # ------------------------------------------------------------------
    # Age → stage
    # ------------------------------------------------------------------
    @staticmethod
    def _stage_from_age(age: int) -> Tuple[str, float]:
        if age < 18:
            return 'student', 0.7
        if age <= 24:
            return 'student', 0.8
        if age <= 30:
            return 'young_adult', 0.75
        if age <= 38:
            return 'early_career', 0.7
        if age <= 52:
            return 'mid_career', 0.7
        if age <= 62:
            return 'senior_career', 0.65
        if age <= 70:
            return 'pre_retirement', 0.65
        return 'retirement', 0.7

    # ------------------------------------------------------------------
    # Conversation → stage
    # ------------------------------------------------------------------
    @staticmethod
    def _stage_from_signals(message: str) -> Tuple[Optional[str], float]:
        if not message:
            return None, 0.0
        msg_lower = message.lower()
        best_stage, best_score = None, 0.0
        for stage, keywords in STAGE_SIGNALS.items():
            hits = sum(1 for kw in keywords if kw.lower() in msg_lower)
            if hits and hits > best_score:
                best_stage = stage
                best_score = hits
        if best_stage:
            confidence = min(0.4 + best_score * 0.15, 0.9)
            return best_stage, confidence
        return None, 0.0

    # ------------------------------------------------------------------
    # Profile builder
    # ------------------------------------------------------------------
    def _build_profile(self, stage: str, confidence: float,
                       source: str, user_id: int = None) -> LifeStageProfile:
        info = LIFE_STAGES.get(stage, LIFE_STAGES['young_adult'])
        return LifeStageProfile(
            stage=stage,
            confidence=round(confidence, 2),
            source=source,
            priorities=info['priorities'],
            challenges=info['common_challenges'],
            tone=info['tone'],
            vocabulary_hints=info['vocabulary_hints'],
            resources=info['resources'],
        )

    # ------------------------------------------------------------------
    # Prompt block (injected into AI system prompt)
    # ------------------------------------------------------------------
    def build_prompt_block(self, profile: LifeStageProfile) -> str:
        if not profile or profile.confidence < 0.3:
            return ''
        stage_label = profile.stage.replace('_', ' ').title()
        lines = [
            f"[LIFE STAGE AWARENESS — {stage_label} (confidence {profile.confidence:.0%})]",
            f"Tone guidance: {profile.tone}",
            f"Vocabulary: {profile.vocabulary_hints}",
            f"Likely priorities: {', '.join(profile.priorities[:4])}",
            f"Common challenges at this stage: {', '.join(profile.challenges[:3])}",
        ]
        return '\n'.join(lines)

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _load_cached_stage(self, user_id: int) -> Optional[Dict]:
        if not self.db:
            return None
        try:
            cursor = self.db.cursor()
            cursor.execute('''
                SELECT stage, confidence, source, detected_at
                FROM life_stage_history
                WHERE user_id = ?
                ORDER BY detected_at DESC LIMIT 1
            ''', (user_id,))
            row = cursor.fetchone()
            if row:
                return {'stage': row[0], 'confidence': row[1], 'source': row[2], 'detected_at': row[3]}
        except Exception:
            pass
        return None

    def _save_stage(self, user_id: int, profile: LifeStageProfile):
        if not self.db:
            return
        try:
            cursor = self.db.cursor()
            cursor.execute('''
                INSERT INTO life_stage_history (user_id, stage, confidence, source)
                VALUES (?, ?, ?, ?)
            ''', (user_id, profile.stage, profile.confidence, profile.source))
            self.db.commit()
        except Exception as e:
            print(f"[LifeStageAdapter] save error: {e}")

    def _fetch_age_from_profile(self, user_id: int) -> Optional[int]:
        if not self.db:
            return None
        try:
            cursor = self.db.cursor()
            cursor.execute('SELECT birth_date FROM user_profiles WHERE user_id = ? LIMIT 1', (user_id,))
            row = cursor.fetchone()
            if row and row[0]:
                from datetime import date as _date
                birth = datetime.strptime(str(row[0]), '%Y-%m-%d').date()
                today = _date.today()
                return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # Manual override (admin / user-settings)
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Character-aware tone adaptation (Enhancement 8)
    # ------------------------------------------------------------------
    CHARACTER_STAGE_TONES = {
        'coach': {
            'student': 'Be encouraging and structured. Break goals into study-friendly chunks. Use relatable examples.',
            'young_adult': 'Be direct and action-oriented. Challenge them to grow. Respect their independence.',
            'early_career': 'Focus on career strategy and skill-building. Be a career ally.',
            'mid_career': 'Discuss leadership, balance, and legacy. Acknowledge their experience.',
            'parent': 'Respect time constraints. Offer efficient, practical advice.',
            'mid_life': 'Support reinvention. Validate the courage of change at this stage.',
            'pre_retirement': 'Help plan the next chapter with purpose and excitement.',
            'retired': 'Focus on meaning, contribution, and enjoying this earned freedom.',
            'elder': 'Honour their wisdom. Be a thoughtful listener.',
        },
        'sage': {
            'student': 'Inspire curiosity and wonder. Share timeless wisdom accessibly.',
            'young_adult': 'Offer perspective without being preachy. Let them find their own path.',
            'mid_life': 'This is your sweet spot — help them find deeper meaning.',
            'elder': 'Peer-to-peer wisdom exchange. Deep philosophical dialogue.',
        },
        'psychologist': {
            'student': 'Normalise developmental challenges. Use age-appropriate emotional vocabulary.',
            'young_adult': 'Support identity formation. Validate the difficulty of "adulting".',
            'parent': 'Address parental guilt and identity shifts with empathy.',
            'mid_life': 'Explore existential questions with depth. Support transitions.',
            'elder': 'Address aging, loss, and legacy with sensitivity and respect.',
        },
    }

    def get_character_stage_guidance(self, character_id: str, stage: str) -> str:
        """Return character-specific tone guidance for a life stage."""
        char_tones = self.CHARACTER_STAGE_TONES.get(character_id, {})
        return char_tones.get(stage, '')

    def set_life_stage(self, user_id: int, stage: str) -> LifeStageProfile:
        if stage not in LIFE_STAGES:
            raise ValueError(f"Unknown stage '{stage}'. Valid: {list(LIFE_STAGES.keys())}")
        profile = self._build_profile(stage, 1.0, 'explicit', user_id)
        self._save_stage(user_id, profile)
        return profile


# ---------------------------------------------------------------------------
# Module-level factory
# ---------------------------------------------------------------------------
_instance = None

def get_life_stage_adapter(db_connection=None) -> LifeStageAdapter:
    global _instance
    if _instance is None or db_connection is not None:
        _instance = LifeStageAdapter(db_connection)
    return _instance
