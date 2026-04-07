"""
Emotional Intelligence Engine
==============================
Goes beyond basic sentiment analysis to provide nuanced emotional understanding:

  - Emotion taxonomy (32 emotions, not just pos/neg/neutral)
  - Emotional trajectory tracking (how feelings evolve over time)
  - Empathy calibration (match response depth to emotional intensity)
  - Motivation engine (context-aware encouragement)
  - Emotional memory (remember what topics trigger what emotions)

Works entirely rule-based (no AI calls) and runs on every message.
"""

import json
import sqlite3
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from collections import Counter


# ---------------------------------------------------------------------------
# Emotion taxonomy — grouped by family
# ---------------------------------------------------------------------------

EMOTION_FAMILIES = {
    'joy':       ['happy', 'excited', 'grateful', 'proud', 'hopeful', 'content', 'relieved', 'amused'],
    'sadness':   ['sad', 'lonely', 'disappointed', 'grief', 'heartbroken', 'melancholy', 'nostalgic'],
    'anger':     ['angry', 'frustrated', 'resentful', 'irritated', 'furious', 'bitter'],
    'fear':      ['anxious', 'scared', 'worried', 'nervous', 'insecure', 'overwhelmed', 'panicked'],
    'surprise':  ['surprised', 'shocked', 'amazed', 'confused', 'stunned'],
    'disgust':   ['disgusted', 'ashamed', 'embarrassed', 'guilty', 'regretful'],
    'trust':     ['trusting', 'vulnerable', 'open', 'safe', 'accepted'],
    'anticipation': ['eager', 'curious', 'motivated', 'determined', 'restless'],
}

# Keyword → (emotion, intensity 0-1)
EMOTION_KEYWORDS = {
    # Joy family
    'happy': ('happy', 0.6), 'so happy': ('happy', 0.9), 'thrilled': ('excited', 0.9),
    'excited': ('excited', 0.7), 'grateful': ('grateful', 0.7), 'thankful': ('grateful', 0.6),
    'proud': ('proud', 0.7), 'proud of myself': ('proud', 0.9),
    'hopeful': ('hopeful', 0.6), 'looking forward': ('hopeful', 0.5),
    'relieved': ('relieved', 0.7), 'finally': ('relieved', 0.4),
    'content': ('content', 0.5), 'at peace': ('content', 0.7),
    'love': ('happy', 0.8), 'amazing': ('excited', 0.7), 'wonderful': ('happy', 0.7),
    'great news': ('excited', 0.8), 'best day': ('happy', 0.9),

    # Sadness family
    'sad': ('sad', 0.6), 'so sad': ('sad', 0.9), 'depressed': ('sad', 0.8),
    'lonely': ('lonely', 0.7), 'so alone': ('lonely', 0.9),
    'disappointed': ('disappointed', 0.6), 'let down': ('disappointed', 0.7),
    'grief': ('grief', 0.9), 'lost someone': ('grief', 0.9), 'passed away': ('grief', 0.95),
    'miss them': ('grief', 0.7), 'heartbroken': ('heartbroken', 0.9),
    'crying': ('sad', 0.7), 'tears': ('sad', 0.6), 'can\'t stop crying': ('sad', 0.9),

    # Anger family
    'angry': ('angry', 0.7), 'so angry': ('angry', 0.9), 'furious': ('furious', 0.95),
    'frustrated': ('frustrated', 0.6), 'so frustrated': ('frustrated', 0.8),
    'resentful': ('resentful', 0.7), 'bitter': ('bitter', 0.7),
    'irritated': ('irritated', 0.5), 'annoyed': ('irritated', 0.4),
    'pissed off': ('angry', 0.8), 'hate': ('angry', 0.7), 'unfair': ('resentful', 0.5),

    # Fear family
    'anxious': ('anxious', 0.6), 'so anxious': ('anxious', 0.9),
    'scared': ('scared', 0.7), 'terrified': ('scared', 0.95),
    'worried': ('worried', 0.5), 'really worried': ('worried', 0.8),
    'nervous': ('nervous', 0.5), 'insecure': ('insecure', 0.6),
    'overwhelmed': ('overwhelmed', 0.7), 'completely overwhelmed': ('overwhelmed', 0.95),
    'panicking': ('panicked', 0.9), 'panic attack': ('panicked', 0.95),
    'dread': ('scared', 0.7), 'afraid': ('scared', 0.6),

    # Surprise
    'surprised': ('surprised', 0.5), 'shocked': ('shocked', 0.8),
    'can\'t believe': ('shocked', 0.7), 'never expected': ('surprised', 0.6),
    'confused': ('confused', 0.5), 'don\'t understand': ('confused', 0.5),

    # Disgust / shame
    'ashamed': ('ashamed', 0.7), 'so ashamed': ('ashamed', 0.9),
    'embarrassed': ('embarrassed', 0.6), 'humiliated': ('embarrassed', 0.9),
    'guilty': ('guilty', 0.6), 'feel guilty': ('guilty', 0.7),
    'regret': ('regretful', 0.6), 'wish i hadn\'t': ('regretful', 0.7),
    'disgusted': ('disgusted', 0.7), 'hate myself': ('ashamed', 0.9),

    # Trust / vulnerability
    'trust you': ('trusting', 0.7), 'feel safe': ('safe', 0.7),
    'vulnerable': ('vulnerable', 0.7), 'opening up': ('vulnerable', 0.6),
    'honest with you': ('vulnerable', 0.7), 'never told anyone': ('vulnerable', 0.9),

    # Anticipation / motivation
    'motivated': ('motivated', 0.7), 'determined': ('determined', 0.7),
    'ready': ('determined', 0.5), 'can\'t wait': ('eager', 0.7),
    'curious': ('curious', 0.5), 'want to learn': ('curious', 0.5),
    'restless': ('restless', 0.5), 'need a change': ('restless', 0.6),
}

# Empathy response templates per emotion family
EMPATHY_TEMPLATES = {
    'joy': {
        'acknowledge': "I can feel your {emotion} coming through — that's wonderful.",
        'mirror': "That sounds like a really {adjective} moment.",
        'deepen': "What made this feel so special for you?",
        'adjectives': ['exciting', 'meaningful', 'beautiful', 'rewarding'],
    },
    'sadness': {
        'acknowledge': "I hear how {emotion} you're feeling, and I want you to know that matters.",
        'mirror': "It sounds like you're carrying something really heavy right now.",
        'deepen': "Would it help to talk about what's weighing on you most?",
        'adjectives': ['painful', 'difficult', 'heavy', 'hard'],
    },
    'anger': {
        'acknowledge': "Your {emotion} makes complete sense given what you've described.",
        'mirror': "That situation sounds genuinely {adjective}.",
        'deepen': "What feels most unfair about this to you?",
        'adjectives': ['frustrating', 'infuriating', 'unfair', 'wrong'],
    },
    'fear': {
        'acknowledge': "It's completely understandable to feel {emotion} about this.",
        'mirror': "That sounds really {adjective}, and your feelings are valid.",
        'deepen': "What feels most uncertain or scary about this right now?",
        'adjectives': ['overwhelming', 'scary', 'uncertain', 'daunting'],
    },
    'surprise': {
        'acknowledge': "That must have been quite a {adjective} — it's a lot to process.",
        'mirror': "I can understand why you'd be {emotion} by that.",
        'deepen': "How are you feeling about it now that you've had a moment?",
        'adjectives': ['shock', 'surprise', 'curveball', 'revelation'],
    },
    'disgust': {
        'acknowledge': "Feeling {emotion} is a very human response to what happened.",
        'mirror': "Please be gentle with yourself — you deserve compassion right now.",
        'deepen': "What would it look like to give yourself some grace here?",
        'adjectives': ['uncomfortable', 'regrettable', 'painful', 'difficult'],
    },
    'trust': {
        'acknowledge': "Thank you for trusting me with this. It takes real courage.",
        'mirror': "I'm honoured that you feel safe enough to share this.",
        'deepen': "I'm here for whatever you need to share.",
        'adjectives': ['brave', 'courageous', 'honest', 'open'],
    },
    'anticipation': {
        'acknowledge': "I can feel your {emotion} — that energy is powerful.",
        'mirror': "It sounds like you're ready to {adjective}.",
        'deepen': "What's the first thing you want to tackle?",
        'adjectives': ['move forward', 'take action', 'make it happen', 'start'],
    },
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class EmotionalState:
    primary_emotion: str            # e.g., 'anxious'
    emotion_family: str             # e.g., 'fear'
    intensity: float                # 0.0 – 1.0
    secondary_emotions: List[str] = field(default_factory=list)
    confidence: float = 0.5

@dataclass
class EmotionalTrajectory:
    current: EmotionalState
    previous: Optional[EmotionalState] = None
    trend: str = 'stable'           # improving / stable / declining / volatile
    shift_description: str = ''     # e.g., "Moving from anxious to hopeful"


class EmotionalIntelligenceEngine:
    """
    Provides deep emotional understanding for every user message.

    Usage::

        engine = EmotionalIntelligenceEngine(db_conn)
        state = engine.analyse_emotion(user_id=42, message="I'm so scared about tomorrow")
        trajectory = engine.get_trajectory(user_id=42)
        prompt_block = engine.build_prompt_block(trajectory)
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
                CREATE TABLE IF NOT EXISTS emotional_history (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     INTEGER NOT NULL,
                    emotion     TEXT NOT NULL,
                    family      TEXT,
                    intensity   REAL,
                    confidence  REAL,
                    message_preview TEXT,
                    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS emotional_triggers (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     INTEGER NOT NULL,
                    topic       TEXT NOT NULL,
                    emotion     TEXT NOT NULL,
                    occurrences INTEGER DEFAULT 1,
                    last_seen   DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, topic, emotion)
                )
            ''')
            self.db.commit()
        except Exception as e:
            print(f"[EmotionalIntelligence] table init error: {e}")

    # ------------------------------------------------------------------
    # Core emotion analysis
    # ------------------------------------------------------------------
    def analyse_emotion(self, user_id: int, message: str,
                        topics: List[str] = None) -> EmotionalState:
        msg_lower = message.lower()
        detected = []

        for phrase, (emotion, intensity) in EMOTION_KEYWORDS.items():
            if phrase in msg_lower:
                detected.append((emotion, intensity, phrase))

        if not detected:
            # Fallback: light heuristic
            return self._fallback_analysis(message)

        # Sort by intensity, pick top
        detected.sort(key=lambda x: -x[1])
        primary = detected[0]
        family = self._get_family(primary[0])

        state = EmotionalState(
            primary_emotion=primary[0],
            emotion_family=family,
            intensity=primary[1],
            secondary_emotions=[d[0] for d in detected[1:4] if d[0] != primary[0]],
            confidence=min(0.4 + len(detected) * 0.1, 0.95),
        )

        # Save to history
        self._save_emotion(user_id, state, message)

        # Record topic-emotion associations
        if topics:
            for topic in topics[:5]:
                self._record_trigger(user_id, topic, state.primary_emotion)

        return state

    def _fallback_analysis(self, message: str) -> EmotionalState:
        # Simple punctuation / length heuristics
        if '!' in message and any(w in message.lower() for w in ['great', 'yes', 'awesome', 'love']):
            return EmotionalState('happy', 'joy', 0.4, confidence=0.3)
        if '?' in message and len(message) > 100:
            return EmotionalState('confused', 'surprise', 0.3, confidence=0.2)
        if message.isupper() and len(message) > 20:
            return EmotionalState('frustrated', 'anger', 0.5, confidence=0.3)
        return EmotionalState('neutral', 'none', 0.1, confidence=0.1)

    @staticmethod
    def _get_family(emotion: str) -> str:
        for family, emotions in EMOTION_FAMILIES.items():
            if emotion in emotions:
                return family
        return 'none'

    # ------------------------------------------------------------------
    # Trajectory (how emotions change over time)
    # ------------------------------------------------------------------
    def get_trajectory(self, user_id: int, current: EmotionalState = None) -> EmotionalTrajectory:
        previous = self._get_previous_emotion(user_id)
        if not current:
            current = EmotionalState('neutral', 'none', 0.1, confidence=0.1)

        if not previous:
            return EmotionalTrajectory(current=current, trend='stable')

        # Determine trend
        valence_map = {
            'joy': 1.0, 'anticipation': 0.7, 'trust': 0.6, 'surprise': 0.3,
            'none': 0.0, 'disgust': -0.4, 'sadness': -0.6, 'anger': -0.5, 'fear': -0.7,
        }
        cur_v = valence_map.get(current.emotion_family, 0) * current.intensity
        prev_v = valence_map.get(previous.emotion_family, 0) * previous.intensity
        diff = cur_v - prev_v

        if diff > 0.3:
            trend = 'improving'
        elif diff < -0.3:
            trend = 'declining'
        elif abs(diff) > 0.15:
            trend = 'volatile'
        else:
            trend = 'stable'

        shift = ''
        if trend == 'improving':
            shift = f"Moving from {previous.primary_emotion} toward {current.primary_emotion} — encouraging"
        elif trend == 'declining':
            shift = f"Shifted from {previous.primary_emotion} to {current.primary_emotion} — needs support"
        elif trend == 'volatile':
            shift = f"Fluctuating between {previous.primary_emotion} and {current.primary_emotion}"

        return EmotionalTrajectory(
            current=current, previous=previous,
            trend=trend, shift_description=shift,
        )

    # ------------------------------------------------------------------
    # Empathy calibration
    # ------------------------------------------------------------------
    def get_empathy_guidance(self, state: EmotionalState) -> Dict[str, str]:
        family = state.emotion_family
        template = EMPATHY_TEMPLATES.get(family, EMPATHY_TEMPLATES['sadness'])
        adj = template['adjectives'][0] if template['adjectives'] else 'significant'

        return {
            'acknowledge': template['acknowledge'].format(emotion=state.primary_emotion, adjective=adj),
            'mirror': template['mirror'].format(emotion=state.primary_emotion, adjective=adj),
            'deepen': template['deepen'],
            'intensity_note': self._intensity_guidance(state.intensity),
        }

    @staticmethod
    def _intensity_guidance(intensity: float) -> str:
        if intensity >= 0.8:
            return "HIGH intensity — prioritise emotional support over advice. Listen first."
        if intensity >= 0.5:
            return "MODERATE intensity — balance empathy with gentle guidance."
        return "LOW intensity — can blend emotional acknowledgment with practical support."

    # ------------------------------------------------------------------
    # Motivation engine
    # ------------------------------------------------------------------
    def get_motivation_context(self, user_id: int, state: EmotionalState) -> str:
        if state.emotion_family in ('joy', 'anticipation', 'trust'):
            return self._positive_momentum(state)
        if state.emotion_family in ('sadness', 'fear', 'disgust'):
            return self._gentle_encouragement(state)
        if state.emotion_family == 'anger':
            return self._channel_energy(state)
        return ''

    @staticmethod
    def _positive_momentum(state: EmotionalState) -> str:
        return (
            f"The user is feeling {state.primary_emotion}. "
            "Build on this positive momentum. Celebrate their progress and "
            "help them channel this energy into next steps."
        )

    @staticmethod
    def _gentle_encouragement(state: EmotionalState) -> str:
        return (
            f"The user is feeling {state.primary_emotion} (intensity: {state.intensity:.0%}). "
            "Be gentle. Validate before motivating. Only offer encouragement after "
            "they feel truly heard. Small wins matter more than big goals right now."
        )

    @staticmethod
    def _channel_energy(state: EmotionalState) -> str:
        return (
            f"The user is feeling {state.primary_emotion}. "
            "Acknowledge the anger as valid, then help them channel that energy "
            "constructively. What change can they influence?"
        )

    # ------------------------------------------------------------------
    # Emotional triggers (topic → emotion patterns)
    # ------------------------------------------------------------------
    def get_known_triggers(self, user_id: int) -> Dict[str, str]:
        if not self.db:
            return {}
        try:
            cur = self.db.cursor()
            cur.execute('''
                SELECT topic, emotion, occurrences FROM emotional_triggers
                WHERE user_id = ? AND occurrences >= 2
                ORDER BY occurrences DESC LIMIT 20
            ''', (user_id,))
            return {row[0]: row[1] for row in cur.fetchall()}
        except Exception:
            return {}

    # ------------------------------------------------------------------
    # Prompt block
    # ------------------------------------------------------------------
    def build_prompt_block(self, trajectory: EmotionalTrajectory,
                           empathy: Dict = None) -> str:
        state = trajectory.current
        if state.confidence < 0.2:
            return ''

        lines = [f"[EMOTIONAL INTELLIGENCE — {state.primary_emotion.upper()} ({state.intensity:.0%} intensity)]"]

        if trajectory.shift_description:
            lines.append(f"Trajectory: {trajectory.shift_description}")

        if empathy:
            lines.append(f"Empathy guidance: {empathy.get('intensity_note', '')}")
            lines.append(f"Suggested opening: {empathy.get('acknowledge', '')}")

        if state.secondary_emotions:
            lines.append(f"Also detecting: {', '.join(state.secondary_emotions)}")

        return '\n'.join(lines)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _save_emotion(self, user_id: int, state: EmotionalState, message: str):
        if not self.db:
            return
        try:
            preview = message[:80]
            cur = self.db.cursor()
            cur.execute('''
                INSERT INTO emotional_history (user_id, emotion, family, intensity, confidence, message_preview)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, state.primary_emotion, state.emotion_family,
                  state.intensity, state.confidence, preview))
            self.db.commit()
        except Exception:
            pass

    def _get_previous_emotion(self, user_id: int) -> Optional[EmotionalState]:
        if not self.db:
            return None
        try:
            cur = self.db.cursor()
            cur.execute('''
                SELECT emotion, family, intensity, confidence
                FROM emotional_history
                WHERE user_id = ?
                ORDER BY created_at DESC LIMIT 1 OFFSET 1
            ''', (user_id,))
            row = cur.fetchone()
            if row:
                return EmotionalState(
                    primary_emotion=row[0], emotion_family=row[1],
                    intensity=row[2], confidence=row[3],
                )
        except Exception:
            pass
        return None

    def _record_trigger(self, user_id: int, topic: str, emotion: str):
        if not self.db:
            return
        try:
            cur = self.db.cursor()
            cur.execute('''
                INSERT INTO emotional_triggers (user_id, topic, emotion)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, topic, emotion) DO UPDATE SET
                    occurrences = occurrences + 1,
                    last_seen = CURRENT_TIMESTAMP
            ''', (user_id, topic.lower(), emotion))
            self.db.commit()
        except Exception:
            pass

    def get_emotional_summary(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        if not self.db:
            return {}
        try:
            cur = self.db.cursor()
            cur.execute('''
                SELECT family, COUNT(*), AVG(intensity)
                FROM emotional_history
                WHERE user_id = ? AND created_at > datetime('now', ?)
                GROUP BY family ORDER BY COUNT(*) DESC
            ''', (user_id, f'-{days} days'))
            rows = cur.fetchall()
            return {
                'dominant_family': rows[0][0] if rows else 'unknown',
                'distribution': {r[0]: {'count': r[1], 'avg_intensity': round(r[2], 2)} for r in rows},
                'period_days': days,
            }
        except Exception:
            return {}


# ---------------------------------------------------------------------------
# Module-level factory
# ---------------------------------------------------------------------------
_instance = None

def get_emotional_intelligence(db_connection=None) -> EmotionalIntelligenceEngine:
    global _instance
    if _instance is None or db_connection is not None:
        _instance = EmotionalIntelligenceEngine(db_connection)
    return _instance
