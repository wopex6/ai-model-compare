"""
Decision Support Framework
===========================
Helps users make better life decisions through structured thinking:

  - Decision capture (detect when user faces a choice)
  - Pros/cons structuring
  - Values alignment scoring (does this choice match their core values?)
  - Multi-perspective analysis (how would each character view this?)
  - Decision journaling (track outcomes for learning)
  - Regret minimisation framework
  - Time-horizon analysis (short-term vs long-term impact)

All rule-based. No AI calls. Integrates into prompt context so characters
can guide users through structured decision-making.
"""

import json
import sqlite3
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict


# ---------------------------------------------------------------------------
# Decision detection patterns
# ---------------------------------------------------------------------------

DECISION_SIGNALS = [
    r"should i (.+?)(?:\?|$|or )",
    r"i(?:'m| am) (?:torn|deciding|choosing) (?:between|whether) (.+?)(?:\.|$)",
    r"(?:can't|cannot) decide (?:if|whether|between) (.+?)(?:\.|$)",
    r"what (?:should|would) (?:i|you) do about (.+?)(?:\?|$)",
    r"(?:option a|option b|option 1|option 2|first option|second option)",
    r"(?:pros and cons|advantages|disadvantages) of (.+?)(?:\?|$)",
    r"is it (?:worth|better) to (.+?)(?:\?|$)",
    r"(?:stay or go|keep or leave|accept or decline|yes or no)",
    r"(?:big decision|major decision|life decision|tough choice|hard choice)",
]

# Decision domains
DECISION_DOMAINS = {
    'career':       ['job', 'career', 'promotion', 'quit', 'resign', 'offer', 'salary', 'role', 'position'],
    'relationship': ['marry', 'divorce', 'break up', 'move in', 'dating', 'propose', 'partner'],
    'finance':      ['buy', 'invest', 'spend', 'save', 'mortgage', 'rent', 'loan', 'debt'],
    'education':    ['study', 'degree', 'course', 'university', 'school', 'training', 'certif'],
    'health':       ['surgery', 'treatment', 'medication', 'therapy', 'diet', 'procedure'],
    'relocation':   ['move', 'relocate', 'country', 'city', 'apartment', 'house'],
    'lifestyle':    ['habit', 'routine', 'schedule', 'priority', 'balance', 'change'],
}

# Time horizons
TIME_HORIZONS = {
    'immediate':   {'label': 'Next week',     'weight': 0.15},
    'short_term':  {'label': 'Next 3 months', 'weight': 0.20},
    'medium_term': {'label': 'Next year',     'weight': 0.25},
    'long_term':   {'label': 'Next 5 years',  'weight': 0.25},
    'lifetime':    {'label': 'Life impact',   'weight': 0.15},
}

# Character perspectives for multi-angle analysis
CHARACTER_LENSES = {
    'coach':      'practical action — What concrete steps does each option require?',
    'stoic':      'what can you control? — Focus only on what\'s within your power.',
    'psychologist': 'emotional impact — How will each option affect your wellbeing?',
    'sage':       'wisdom and meaning — Which option aligns with your deeper purpose?',
    'scientist':  'evidence and data — What does the evidence suggest about outcomes?',
    'artist':     'creativity and expression — Which option opens more possibilities?',
    'mentor':     'growth potential — Which option helps you grow the most?',
    'friend':     'human connection — How will each option affect your relationships?',
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class DecisionOption:
    label: str
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    values_alignment: float = 0.0       # 0-1, how well it aligns with user values
    time_scores: Dict[str, float] = field(default_factory=dict)  # horizon → score

@dataclass
class Decision:
    id: int = 0
    user_id: int = 0
    title: str = ''
    domain: str = 'general'
    options: List[DecisionOption] = field(default_factory=list)
    user_values: List[str] = field(default_factory=list)
    status: str = 'open'                # open, decided, reviewing
    chosen_option: Optional[str] = None
    outcome_notes: str = ''
    outcome_satisfaction: Optional[int] = None  # 1-5
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    decided_at: Optional[str] = None
    reviewed_at: Optional[str] = None

@dataclass
class DecisionGuidance:
    """Structured guidance injected into AI prompt."""
    is_decision: bool = False
    domain: str = 'general'
    detected_options: List[str] = field(default_factory=list)
    framework_suggestion: str = ''
    character_perspectives: Dict[str, str] = field(default_factory=dict)
    values_to_consider: List[str] = field(default_factory=list)
    questions_to_ask: List[str] = field(default_factory=list)


class DecisionSupportEngine:
    """
    Detects decisions in conversation and provides structured support.

    Usage::

        engine = DecisionSupportEngine(db_conn)
        guidance = engine.analyse_message(user_id=42, message="Should I quit my job?",
                                          user_values=['security', 'growth'])
        prompt_block = engine.build_prompt_block(guidance)
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
                CREATE TABLE IF NOT EXISTS decisions (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id         INTEGER NOT NULL,
                    title           TEXT NOT NULL,
                    domain          TEXT DEFAULT 'general',
                    options_json    TEXT DEFAULT '[]',
                    user_values     TEXT DEFAULT '[]',
                    status          TEXT DEFAULT 'open',
                    chosen_option   TEXT,
                    outcome_notes   TEXT DEFAULT '',
                    outcome_satisfaction INTEGER,
                    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
                    decided_at      DATETIME,
                    reviewed_at     DATETIME
                )
            ''')
            self.db.commit()
        except Exception as e:
            print(f"[DecisionSupport] table init error: {e}")

    # ------------------------------------------------------------------
    # Analyse message for decision content
    # ------------------------------------------------------------------
    def analyse_message(self, user_id: int, message: str,
                        user_values: List[str] = None,
                        character_id: str = None) -> DecisionGuidance:
        guidance = DecisionGuidance()
        msg_lower = message.lower()

        # Detect if this is a decision
        for pattern in DECISION_SIGNALS:
            match = re.search(pattern, msg_lower)
            if match:
                guidance.is_decision = True
                if match.lastindex:
                    guidance.detected_options.append(match.group(1).strip())
                break

        if not guidance.is_decision:
            return guidance

        # Detect domain
        guidance.domain = self._detect_domain(msg_lower)

        # Extract options if "or" structure
        or_match = re.search(r'(.+?)\s+or\s+(.+?)(?:\?|$)', msg_lower)
        if or_match:
            guidance.detected_options = [
                or_match.group(1).strip(),
                or_match.group(2).strip(),
            ]

        # Values to consider
        guidance.values_to_consider = user_values or []

        # Framework suggestion based on domain
        guidance.framework_suggestion = self._suggest_framework(guidance.domain)

        # Character perspectives
        guidance.character_perspectives = self._get_perspectives(guidance.domain, character_id)

        # Questions to help clarify
        guidance.questions_to_ask = self._generate_questions(guidance.domain, guidance.detected_options)

        # Save decision to DB
        if guidance.detected_options:
            self._save_decision(user_id, message, guidance)

        return guidance

    # ------------------------------------------------------------------
    # Domain detection
    # ------------------------------------------------------------------
    @staticmethod
    def _detect_domain(msg_lower: str) -> str:
        scores = {}
        for domain, keywords in DECISION_DOMAINS.items():
            hits = sum(1 for kw in keywords if kw in msg_lower)
            if hits:
                scores[domain] = hits
        return max(scores, key=scores.get) if scores else 'general'

    # ------------------------------------------------------------------
    # Framework suggestions
    # ------------------------------------------------------------------
    @staticmethod
    def _suggest_framework(domain: str) -> str:
        frameworks = {
            'career': (
                "Use the CAREER DECISION FRAMEWORK:\n"
                "1. What energises you vs drains you in each option?\n"
                "2. Where do you see yourself in 3 years with each choice?\n"
                "3. What would you advise your best friend in this situation?\n"
                "4. Which option scares you in a good way (growth) vs bad way (misalignment)?"
            ),
            'relationship': (
                "Use the RELATIONSHIP CLARITY FRAMEWORK:\n"
                "1. How does each option make you feel in your body? (Gut check)\n"
                "2. What are your non-negotiable needs in this relationship?\n"
                "3. If nothing changed in 2 years, how would you feel?\n"
                "4. What would the wisest version of yourself choose?"
            ),
            'finance': (
                "Use the FINANCIAL DECISION FRAMEWORK:\n"
                "1. What's the worst realistic outcome? Can you recover from it?\n"
                "2. What's the opportunity cost of NOT doing this?\n"
                "3. Will this matter in 10 years?\n"
                "4. Does this align with your financial goals and values?"
            ),
            'health': (
                "Use the HEALTH DECISION FRAMEWORK:\n"
                "1. What does the evidence/research say?\n"
                "2. Have you consulted a qualified professional?\n"
                "3. What are the risks vs benefits?\n"
                "4. What does your body tell you?"
            ),
            'relocation': (
                "Use the RELOCATION FRAMEWORK:\n"
                "1. What are you moving TOWARD (not just away from)?\n"
                "2. What relationships and support will be affected?\n"
                "3. Can you test it before fully committing? (Visit, short stay)\n"
                "4. What does your ideal daily life look like in each location?"
            ),
        }
        return frameworks.get(domain, (
            "GENERAL DECISION FRAMEWORK:\n"
            "1. What matters most to you in this situation?\n"
            "2. What would you regret NOT trying in 5 years?\n"
            "3. What would you advise someone you love?\n"
            "4. Which option aligns with the person you want to become?"
        ))

    # ------------------------------------------------------------------
    # Multi-perspective analysis
    # ------------------------------------------------------------------
    @staticmethod
    def _get_perspectives(domain: str, character_id: str = None) -> Dict[str, str]:
        # Return relevant perspectives (not all — too noisy)
        relevant = {}
        priority = {
            'career':       ['coach', 'mentor', 'stoic', 'sage'],
            'relationship': ['psychologist', 'friend', 'sage', 'stoic'],
            'finance':      ['scientist', 'coach', 'stoic', 'mentor'],
            'health':       ['scientist', 'psychologist', 'coach', 'friend'],
            'education':    ['mentor', 'scientist', 'coach', 'sage'],
            'relocation':   ['friend', 'coach', 'sage', 'psychologist'],
        }
        chars = priority.get(domain, ['coach', 'psychologist', 'sage'])[:3]
        # If current character is in list, put it first
        if character_id and character_id in chars:
            chars.remove(character_id)
            chars.insert(0, character_id)

        for c in chars:
            if c in CHARACTER_LENSES:
                relevant[c] = CHARACTER_LENSES[c]
        return relevant

    # ------------------------------------------------------------------
    # Clarifying questions
    # ------------------------------------------------------------------
    @staticmethod
    def _generate_questions(domain: str, options: List[str]) -> List[str]:
        base = [
            "What's your biggest fear about this decision?",
            "What does your gut tell you?",
            "What would change if you didn't have to decide right now?",
        ]
        domain_qs = {
            'career': [
                "What does a fulfilling workday look like to you?",
                "Is this about money, meaning, or growth?",
            ],
            'relationship': [
                "What are your non-negotiable needs?",
                "How do you feel when you imagine each outcome?",
            ],
            'finance': [
                "What's the minimum you need to feel financially safe?",
                "Is this a want or a need?",
            ],
        }
        questions = domain_qs.get(domain, []) + base
        return questions[:5]

    # ------------------------------------------------------------------
    # Prompt block
    # ------------------------------------------------------------------
    def build_prompt_block(self, guidance: DecisionGuidance) -> str:
        if not guidance.is_decision:
            return ''

        lines = [f"[DECISION SUPPORT — {guidance.domain.upper()} DECISION DETECTED]"]

        if guidance.detected_options:
            lines.append(f"Options identified: {' vs '.join(guidance.detected_options)}")

        lines.append(f"\n{guidance.framework_suggestion}")

        if guidance.character_perspectives:
            lines.append("\nPerspectives to offer:")
            for char, lens in guidance.character_perspectives.items():
                lines.append(f"  • {char.title()}: {lens}")

        if guidance.values_to_consider:
            lines.append(f"\nUser's values to weigh: {', '.join(guidance.values_to_consider)}")

        lines.append("\nKey questions to explore:")
        for q in guidance.questions_to_ask[:4]:
            lines.append(f"  • {q}")

        lines.append("\nGUIDANCE: Help them think — don't decide for them. "
                      "Ask one question at a time. Validate the difficulty of deciding.")

        return '\n'.join(lines)

    # ------------------------------------------------------------------
    # Decision CRUD
    # ------------------------------------------------------------------
    def _save_decision(self, user_id: int, title: str, guidance: DecisionGuidance):
        if not self.db:
            return
        try:
            options = [asdict(DecisionOption(label=o)) for o in guidance.detected_options]
            cur = self.db.cursor()
            cur.execute('''
                INSERT INTO decisions (user_id, title, domain, options_json, user_values)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, title[:200], guidance.domain,
                  json.dumps(options), json.dumps(guidance.values_to_consider)))
            self.db.commit()
        except Exception as e:
            print(f"[DecisionSupport] save error: {e}")

    def record_outcome(self, user_id: int, decision_id: int,
                       chosen: str, notes: str = '', satisfaction: int = 3) -> bool:
        if not self.db:
            return False
        try:
            cur = self.db.cursor()
            cur.execute('''
                UPDATE decisions SET
                    status = 'decided', chosen_option = ?,
                    outcome_notes = ?, outcome_satisfaction = ?,
                    decided_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
            ''', (chosen, notes, satisfaction, decision_id, user_id))
            self.db.commit()
            return cur.rowcount > 0
        except Exception:
            return False

    def get_open_decisions(self, user_id: int) -> List[Dict]:
        if not self.db:
            return []
        try:
            cur = self.db.cursor()
            cur.execute('''
                SELECT id, title, domain, options_json, created_at
                FROM decisions WHERE user_id = ? AND status = 'open'
                ORDER BY created_at DESC LIMIT 10
            ''', (user_id,))
            return [{'id': r[0], 'title': r[1], 'domain': r[2],
                     'options': json.loads(r[3]) if r[3] else [], 'created_at': r[4]}
                    for r in cur.fetchall()]
        except Exception:
            return []

    def get_decision_history(self, user_id: int, days: int = 180) -> List[Dict]:
        if not self.db:
            return []
        try:
            cur = self.db.cursor()
            cur.execute('''
                SELECT id, title, domain, chosen_option, outcome_satisfaction, decided_at
                FROM decisions WHERE user_id = ? AND status = 'decided'
                AND decided_at > datetime('now', ?)
                ORDER BY decided_at DESC LIMIT 20
            ''', (user_id, f'-{days} days'))
            return [{'id': r[0], 'title': r[1], 'domain': r[2],
                     'chosen': r[3], 'satisfaction': r[4], 'date': r[5]}
                    for r in cur.fetchall()]
        except Exception:
            return []


# ---------------------------------------------------------------------------
# Module-level factory
# ---------------------------------------------------------------------------
_instance = None

def get_decision_support(db_connection=None) -> DecisionSupportEngine:
    global _instance
    if _instance is None or db_connection is not None:
        _instance = DecisionSupportEngine(db_connection)
    return _instance
