"""
Life Transition Guide
=====================
Detects and supports users through major life transitions:

  - Career change / job loss / retirement
  - Relationship changes (marriage, divorce, breakup, new baby)
  - Relocation (new city, new country)
  - Health transitions (diagnosis, recovery, aging)
  - Loss and grief
  - Education transitions (starting, graduating)
  - Financial transitions (debt payoff, first home, inheritance)
  - Identity shifts (coming out, career pivot, empty nest)

Each transition has:
  - Detection signals from conversation
  - Stage mapping (denial/shock → adjustment → acceptance → growth)
  - Stage-appropriate guidance injected into AI prompt
  - Milestone tracking
  - Resource recommendations

All rule-based. No AI calls.
"""

import json
import sqlite3
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict


# ---------------------------------------------------------------------------
# Transition definitions
# ---------------------------------------------------------------------------

TRANSITION_TYPES = {
    'career_change': {
        'signals': ['new job', 'career change', 'switching careers', 'quit my job',
                    'got fired', 'laid off', 'redundancy', 'starting a business',
                    'going freelance', 'new role', 'first day at work'],
        'stages': ['shock_excitement', 'doubt_adjustment', 'learning_curve', 'settling_in', 'thriving'],
        'stage_guidance': {
            'shock_excitement': 'They may swing between excitement and anxiety. Normalise both feelings.',
            'doubt_adjustment': 'Imposter syndrome is common. Validate their competence and past experience.',
            'learning_curve': 'They\'re absorbing a lot. Encourage patience with themselves.',
            'settling_in': 'Building confidence. Help them see their progress.',
            'thriving': 'They\'ve made it. Help them set new growth goals.',
        },
        'typical_duration_weeks': 24,
        'resources': ['networking groups', 'skill assessment tools', 'career coaching'],
    },
    'job_loss': {
        'signals': ['lost my job', 'got fired', 'laid off', 'redundant', 'unemployed',
                    'let go', 'downsized', 'company closed'],
        'stages': ['shock_grief', 'anger_frustration', 'uncertainty', 'rebuilding', 'new_beginning'],
        'stage_guidance': {
            'shock_grief': 'Allow them to grieve. Job loss is a real loss of identity and routine.',
            'anger_frustration': 'Validate the anger. It\'s a natural response. Don\'t rush past it.',
            'uncertainty': 'Help them find structure in uncertainty. Small daily goals.',
            'rebuilding': 'Support practical steps — resume, networking, skills audit.',
            'new_beginning': 'Help them see this as a chapter, not the whole story.',
        },
        'typical_duration_weeks': 16,
        'resources': ['job search strategies', 'financial planning', 'unemployment benefits guide'],
    },
    'relationship_start': {
        'signals': ['new relationship', 'started dating', 'met someone', 'falling in love',
                    'new partner', 'got together', 'asked me out'],
        'stages': ['honeymoon', 'reality_check', 'deepening', 'committed'],
        'stage_guidance': {
            'honeymoon': 'Enjoy it! But gently help them maintain their own identity and friendships.',
            'reality_check': 'First disagreements are normal. Help them communicate, not avoid.',
            'deepening': 'Vulnerability is growing. Support honest communication.',
            'committed': 'Help them nurture the relationship while maintaining growth.',
        },
        'typical_duration_weeks': 52,
        'resources': ['communication skills', 'attachment styles', 'relationship books'],
    },
    'relationship_end': {
        'signals': ['broke up', 'breakup', 'divorce', 'separated', 'ended things',
                    'left me', 'splitting up', 'moving out', 'it\'s over'],
        'stages': ['shock_denial', 'grief_sadness', 'anger_bargaining', 'acceptance', 'rebuilding'],
        'stage_guidance': {
            'shock_denial': 'Be present. Don\'t try to fix it. Just be there.',
            'grief_sadness': 'Let them grieve. The relationship mattered. Their pain is valid.',
            'anger_bargaining': 'Anger is a step forward, not backward. Help them express it safely.',
            'acceptance': 'Gently help them see the lessons without forcing "bright sides".',
            'rebuilding': 'Support them in rediscovering who they are on their own.',
        },
        'typical_duration_weeks': 26,
        'resources': ['therapist/counsellor', 'support groups', 'self-care routines'],
    },
    'new_parent': {
        'signals': ['having a baby', 'pregnant', 'expecting', 'new baby', 'just had a baby',
                    'newborn', 'first child', 'becoming a parent', 'father', 'mother'],
        'stages': ['preparation_anxiety', 'overwhelm_wonder', 'exhaustion_bonding', 'finding_rhythm', 'confident_parent'],
        'stage_guidance': {
            'preparation_anxiety': 'Normalise the anxiety. Nobody feels fully ready.',
            'overwhelm_wonder': 'They\'re doing harder than they expected. Celebrate small wins.',
            'exhaustion_bonding': 'Sleep deprivation is real. Be extra gentle and supportive.',
            'finding_rhythm': 'Things are getting easier. Help them maintain self-care.',
            'confident_parent': 'They\'ve got this. Help them enjoy it.',
        },
        'typical_duration_weeks': 52,
        'resources': ['parenting classes', 'sleep consultants', 'parent support groups'],
    },
    'relocation': {
        'signals': ['moving to', 'relocated', 'new city', 'new country', 'emigrating',
                    'immigrating', 'moved house', 'just moved', 'settling in'],
        'stages': ['honeymoon_excitement', 'culture_shock', 'adjustment', 'adaptation', 'belonging'],
        'stage_guidance': {
            'honeymoon_excitement': 'Everything feels new and exciting. Help them stay grounded.',
            'culture_shock': 'Homesickness is normal. Validate what they miss.',
            'adjustment': 'They\'re learning the new normal. Help them build local connections.',
            'adaptation': 'Finding their place. Encourage exploration.',
            'belonging': 'Starting to feel at home. Help them maintain old connections too.',
        },
        'typical_duration_weeks': 36,
        'resources': ['local community groups', 'expat networks', 'language classes'],
    },
    'health_change': {
        'signals': ['diagnosed', 'diagnosis', 'chronic', 'surgery', 'treatment',
                    'recovery', 'condition', 'disability', 'illness', 'cancer',
                    'mental health', 'medication change'],
        'stages': ['shock_denial', 'information_seeking', 'emotional_processing', 'adaptation', 'new_normal'],
        'stage_guidance': {
            'shock_denial': 'Give them space to process. Don\'t rush to positivity.',
            'information_seeking': 'Help them find reliable information. Discourage doom-scrolling.',
            'emotional_processing': 'All feelings are valid. Fear, anger, sadness — all of it.',
            'adaptation': 'Help them find what they CAN control and enjoy.',
            'new_normal': 'Support their redefined normal. Celebrate resilience.',
        },
        'typical_duration_weeks': 36,
        'resources': ['medical professionals', 'support groups', 'reliable health information'],
    },
    'grief_loss': {
        'signals': ['died', 'passed away', 'lost my', 'funeral', 'grieving', 'mourning',
                    'death of', 'in memory', 'miss them so much', 'gone forever'],
        'stages': ['shock_numbness', 'intense_grief', 'disorganisation', 'reorganisation', 'integration'],
        'stage_guidance': {
            'shock_numbness': 'Be gentle. They may seem okay but are in shock. Don\'t push.',
            'intense_grief': 'The pain is immense. Just be present. Silence is okay.',
            'disorganisation': 'Everything feels wrong. Help with small practical things.',
            'reorganisation': 'Slowly finding new patterns. Don\'t rush it.',
            'integration': 'The loss becomes part of them, not all of them. Honour the memory.',
        },
        'typical_duration_weeks': 52,
        'resources': ['grief counsellor', 'bereavement support', 'grief support groups'],
    },
    'retirement': {
        'signals': ['retiring', 'retired', 'last day of work', 'pension',
                    'after retirement', 'post-retirement', 'leaving work for good'],
        'stages': ['euphoria', 'disenchantment', 'reorientation', 'stability', 'fulfillment'],
        'stage_guidance': {
            'euphoria': 'Enjoy the freedom! But gently prepare for the transition ahead.',
            'disenchantment': 'Loss of identity and routine is real. Normalise these feelings.',
            'reorientation': 'Help them explore new purposes — volunteering, hobbies, mentoring.',
            'stability': 'New routines are forming. Support consistency.',
            'fulfillment': 'They\'ve found their rhythm. Celebrate this achievement.',
        },
        'typical_duration_weeks': 40,
        'resources': ['retirement communities', 'volunteering', 'learning platforms', 'travel planning'],
    },
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class TransitionState:
    transition_type: str
    current_stage: str
    stage_index: int
    total_stages: int
    weeks_in_transition: int
    confidence: float
    guidance: str
    resources: List[str]
    detected_at: str
    last_signal: str

@dataclass
class TransitionReport:
    user_id: int
    active_transitions: List[TransitionState] = field(default_factory=list)
    past_transitions: List[Dict] = field(default_factory=list)


class LifeTransitionGuide:
    """
    Detects and supports users through major life transitions.

    Usage::

        guide = LifeTransitionGuide(db_conn)
        state = guide.detect_transition(user_id=42, message="I just got laid off yesterday")
        prompt_block = guide.build_prompt_block(state)
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
                CREATE TABLE IF NOT EXISTS life_transitions (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id           INTEGER NOT NULL,
                    transition_type   TEXT NOT NULL,
                    current_stage     TEXT,
                    stage_index       INTEGER DEFAULT 0,
                    confidence        REAL DEFAULT 0.5,
                    detected_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_signal_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_signal       TEXT DEFAULT '',
                    is_active         BOOLEAN DEFAULT 1,
                    resolved_at       DATETIME,
                    UNIQUE(user_id, transition_type, is_active)
                )
            ''')
            self.db.commit()
        except Exception as e:
            print(f"[LifeTransitionGuide] table init error: {e}")

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------
    def detect_transition(self, user_id: int, message: str) -> Optional[TransitionState]:
        msg_lower = message.lower()
        best_match = None
        best_score = 0

        for ttype, tdata in TRANSITION_TYPES.items():
            hits = sum(1 for sig in tdata['signals'] if sig in msg_lower)
            if hits > best_score:
                best_score = hits
                best_match = ttype

        if not best_match or best_score == 0:
            return None

        tdata = TRANSITION_TYPES[best_match]
        confidence = min(0.3 + best_score * 0.2, 0.95)

        # Check for existing active transition of same type
        existing = self._load_active(user_id, best_match)
        if existing:
            # Advance stage if appropriate
            return self._advance_stage(user_id, existing, message, confidence)

        # New transition
        stages = tdata['stages']
        first_stage = stages[0]
        guidance = tdata['stage_guidance'].get(first_stage, '')

        state = TransitionState(
            transition_type=best_match,
            current_stage=first_stage,
            stage_index=0,
            total_stages=len(stages),
            weeks_in_transition=0,
            confidence=confidence,
            guidance=guidance,
            resources=tdata.get('resources', []),
            detected_at=datetime.now().isoformat(),
            last_signal=message[:100],
        )

        self._save_transition(user_id, state)
        return state

    # ------------------------------------------------------------------
    # Stage advancement
    # ------------------------------------------------------------------
    def _advance_stage(self, user_id: int, existing: Dict,
                       message: str, confidence: float) -> TransitionState:
        ttype = existing['transition_type']
        tdata = TRANSITION_TYPES[ttype]
        stages = tdata['stages']

        current_index = existing.get('stage_index', 0)
        detected_at = existing.get('detected_at', datetime.now().isoformat())

        # Calculate weeks in transition
        try:
            start = datetime.fromisoformat(detected_at)
            weeks = (datetime.now() - start).days // 7
        except (ValueError, TypeError):
            weeks = 0

        # Simple stage advancement: based on time and signals
        expected_weeks_per_stage = tdata.get('typical_duration_weeks', 24) / len(stages)
        expected_stage = min(int(weeks / max(expected_weeks_per_stage, 1)), len(stages) - 1)

        # Also check for growth signals that might advance stage
        growth_signals = ['better', 'improving', 'progress', 'getting used to',
                          'starting to feel', 'beginning to', 'finally', 'accepting']
        has_growth = any(s in message.lower() for s in growth_signals)
        if has_growth and expected_stage <= current_index:
            expected_stage = min(current_index + 1, len(stages) - 1)

        new_index = max(current_index, expected_stage)
        new_stage = stages[new_index]
        guidance = tdata['stage_guidance'].get(new_stage, '')

        state = TransitionState(
            transition_type=ttype,
            current_stage=new_stage,
            stage_index=new_index,
            total_stages=len(stages),
            weeks_in_transition=weeks,
            confidence=max(confidence, existing.get('confidence', 0.5)),
            guidance=guidance,
            resources=tdata.get('resources', []),
            detected_at=detected_at,
            last_signal=message[:100],
        )

        # Update in DB
        self._update_transition(user_id, state)
        return state

    # ------------------------------------------------------------------
    # Get all active transitions for a user
    # ------------------------------------------------------------------
    def get_active_transitions(self, user_id: int) -> List[TransitionState]:
        if not self.db:
            return []
        try:
            cur = self.db.cursor()
            cur.execute('''
                SELECT transition_type, current_stage, stage_index, confidence,
                       detected_at, last_signal_at, last_signal
                FROM life_transitions
                WHERE user_id = ? AND is_active = 1
                ORDER BY detected_at DESC
            ''', (user_id,))
            results = []
            for row in cur.fetchall():
                ttype = row[0]
                tdata = TRANSITION_TYPES.get(ttype, {})
                stages = tdata.get('stages', [])
                guidance = tdata.get('stage_guidance', {}).get(row[1], '')

                try:
                    start = datetime.fromisoformat(row[4])
                    weeks = (datetime.now() - start).days // 7
                except (ValueError, TypeError):
                    weeks = 0

                results.append(TransitionState(
                    transition_type=ttype,
                    current_stage=row[1],
                    stage_index=row[2],
                    total_stages=len(stages),
                    weeks_in_transition=weeks,
                    confidence=row[3],
                    guidance=guidance,
                    resources=tdata.get('resources', []),
                    detected_at=row[4],
                    last_signal=row[6] or '',
                ))
            return results
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Prompt block
    # ------------------------------------------------------------------
    def build_prompt_block(self, state: TransitionState = None,
                           all_transitions: List[TransitionState] = None) -> str:
        transitions = all_transitions or ([state] if state else [])
        if not transitions:
            return ''

        lines = []
        for t in transitions[:2]:  # max 2 transitions in context
            label = t.transition_type.replace('_', ' ').title()
            stage_label = t.current_stage.replace('_', ' ').title()
            progress = f"Stage {t.stage_index + 1}/{t.total_stages}"

            lines.append(f"[LIFE TRANSITION — {label}]")
            lines.append(f"Current stage: {stage_label} ({progress}, week {t.weeks_in_transition})")
            lines.append(f"Guidance: {t.guidance}")

            if t.resources:
                lines.append(f"Resources to suggest: {', '.join(t.resources[:3])}")
            lines.append('')

        return '\n'.join(lines).strip()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _load_active(self, user_id: int, transition_type: str) -> Optional[Dict]:
        if not self.db:
            return None
        try:
            cur = self.db.cursor()
            cur.execute('''
                SELECT transition_type, current_stage, stage_index, confidence,
                       detected_at, last_signal
                FROM life_transitions
                WHERE user_id = ? AND transition_type = ? AND is_active = 1
            ''', (user_id, transition_type))
            row = cur.fetchone()
            if row:
                return {
                    'transition_type': row[0], 'current_stage': row[1],
                    'stage_index': row[2], 'confidence': row[3],
                    'detected_at': row[4], 'last_signal': row[5],
                }
        except Exception:
            pass
        return None

    def _save_transition(self, user_id: int, state: TransitionState):
        if not self.db:
            return
        try:
            cur = self.db.cursor()
            cur.execute('''
                INSERT OR REPLACE INTO life_transitions
                (user_id, transition_type, current_stage, stage_index, confidence, last_signal, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (user_id, state.transition_type, state.current_stage,
                  state.stage_index, state.confidence, state.last_signal))
            self.db.commit()
        except Exception as e:
            print(f"[LifeTransitionGuide] save error: {e}")

    def _update_transition(self, user_id: int, state: TransitionState):
        if not self.db:
            return
        try:
            cur = self.db.cursor()
            cur.execute('''
                UPDATE life_transitions SET
                    current_stage = ?, stage_index = ?, confidence = ?,
                    last_signal = ?, last_signal_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND transition_type = ? AND is_active = 1
            ''', (state.current_stage, state.stage_index, state.confidence,
                  state.last_signal, user_id, state.transition_type))
            self.db.commit()
        except Exception as e:
            print(f"[LifeTransitionGuide] update error: {e}")

    def resolve_transition(self, user_id: int, transition_type: str):
        if not self.db:
            return
        try:
            cur = self.db.cursor()
            cur.execute('''
                UPDATE life_transitions SET is_active = 0, resolved_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND transition_type = ? AND is_active = 1
            ''', (user_id, transition_type))
            self.db.commit()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Module-level factory
# ---------------------------------------------------------------------------
_instance = None

def get_life_transition_guide(db_connection=None) -> LifeTransitionGuide:
    global _instance
    if _instance is None or db_connection is not None:
        _instance = LifeTransitionGuide(db_connection)
    return _instance
