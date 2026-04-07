"""
Crisis Detector & Intervention System
======================================
Detects signals of mental health crisis, self-harm risk, and acute distress
in user messages.  When triggered it:

  1. Flags the message with a severity level (watch / concern / urgent / critical)
  2. Injects safety-focused instructions into the AI prompt
  3. Provides localised crisis resources
  4. Optionally notifies an admin / support contact (for critical)

This module is ALWAYS active and runs before any other processing.
False-positive is acceptable; false-negative is not.
"""

import re
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict


# ---------------------------------------------------------------------------
# Severity levels
# ---------------------------------------------------------------------------
SEVERITY_WATCH    = 'watch'       # Mild distress signals — monitor
SEVERITY_CONCERN  = 'concern'     # Notable distress — gentle check-in
SEVERITY_URGENT   = 'urgent'      # Clear crisis language — provide resources
SEVERITY_CRITICAL = 'critical'    # Imminent danger signals — resources + escalate


# ---------------------------------------------------------------------------
# Signal dictionaries (kept intentionally broad for safety)
# ---------------------------------------------------------------------------

CRITICAL_SIGNALS = [
    'want to die', 'want to kill myself', 'going to kill myself',
    'end my life', 'end it all', 'suicide', 'suicidal',
    'don\'t want to live', 'no reason to live', 'better off dead',
    'plan to end', 'overdose', 'slit my wrist', 'jump off',
    'hang myself', 'shoot myself', 'kill myself',
    'goodbye forever', 'final goodbye', 'this is my last',
    'nobody will miss me', 'world without me',
]

URGENT_SIGNALS = [
    'self-harm', 'self harm', 'cutting myself', 'hurting myself',
    'can\'t go on', 'can\'t take it anymore', 'can\'t do this anymore',
    'nothing matters', 'no point in living', 'wish i was dead',
    'wish i wasn\'t alive', 'don\'t want to wake up',
    'life is meaningless', 'everyone would be better',
    'i give up on life', 'tired of living', 'tired of life',
    'want to disappear', 'want to vanish forever',
    'abuse', 'being abused', 'hitting me', 'hurting me',
    'domestic violence', 'sexual assault', 'raped',
]

CONCERN_SIGNALS = [
    'hopeless', 'helpless', 'worthless', 'useless',
    'hate myself', 'hate my life', 'disgusted with myself',
    'can\'t cope', 'falling apart', 'breaking down',
    'panic attack', 'can\'t breathe', 'chest pain anxiety',
    'haven\'t eaten', 'can\'t sleep for days', 'insomnia weeks',
    'drinking too much', 'using drugs', 'relapsed',
    'binge', 'purge', 'eating disorder', 'anorexia', 'bulimia',
    'completely alone', 'nobody cares about me',
    'trapped', 'no way out', 'prison in my mind',
]

WATCH_SIGNALS = [
    'so stressed', 'overwhelmed', 'exhausted', 'burned out',
    'crying a lot', 'can\'t stop crying', 'barely functioning',
    'anxious all the time', 'constant anxiety', 'dread',
    'losing interest', 'don\'t enjoy anything', 'numb',
    'isolating', 'withdrawing', 'avoiding everyone',
    'nightmares', 'flashbacks', 'triggered',
    'grief', 'mourning', 'lost someone',
]


# ---------------------------------------------------------------------------
# Crisis resources (localised)
# ---------------------------------------------------------------------------

CRISIS_RESOURCES = {
    'global': {
        'name': 'Crisis Text Line',
        'contact': 'Text HOME to 741741',
        'url': 'https://www.crisistextline.org/',
    },
    'AU': {
        'name': 'Lifeline Australia',
        'phone': '13 11 14',
        'text': 'Text 0477 13 11 14',
        'url': 'https://www.lifeline.org.au/',
        'additional': [
            {'name': 'Beyond Blue', 'phone': '1300 22 4636', 'url': 'https://www.beyondblue.org.au/'},
            {'name': 'Kids Helpline', 'phone': '1800 55 1800', 'url': 'https://kidshelpline.com.au/'},
            {'name': '13YARN (Aboriginal)', 'phone': '13 92 76'},
        ]
    },
    'US': {
        'name': '988 Suicide & Crisis Lifeline',
        'phone': '988',
        'text': 'Text 988',
        'url': 'https://988lifeline.org/',
        'additional': [
            {'name': 'SAMHSA Helpline', 'phone': '1-800-662-4357'},
            {'name': 'Trevor Project (LGBTQ+)', 'phone': '1-866-488-7386'},
        ]
    },
    'UK': {
        'name': 'Samaritans',
        'phone': '116 123',
        'url': 'https://www.samaritans.org/',
        'additional': [
            {'name': 'Mind', 'phone': '0300 123 3393'},
            {'name': 'Childline', 'phone': '0800 1111'},
        ]
    },
    'NZ': {
        'name': 'Lifeline NZ',
        'phone': '0800 543 354',
        'url': 'https://www.lifeline.org.nz/',
        'additional': [
            {'name': 'Need to Talk?', 'phone': '1737'},
        ]
    },
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CrisisAssessment:
    severity: str               # watch / concern / urgent / critical
    confidence: float           # 0.0 – 1.0
    matched_signals: List[str]
    response_guidance: str      # injected into AI prompt
    resources: List[Dict]       # crisis helplines
    should_escalate: bool       # True for critical
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class CrisisDetector:
    """
    Scans every user message for crisis signals and returns an assessment.

    Usage::

        detector = CrisisDetector(db_conn, locale='AU')
        assessment = detector.assess(user_id=42, message="I can't take it anymore")
        if assessment.severity in ('urgent', 'critical'):
            prompt_block = detector.build_prompt_block(assessment)
    """

    def __init__(self, db_connection=None, locale: str = 'AU'):
        self.db = db_connection
        self.locale = locale
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
                CREATE TABLE IF NOT EXISTS crisis_log (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     INTEGER NOT NULL,
                    severity    TEXT NOT NULL,
                    confidence  REAL,
                    signals     TEXT,
                    message_preview TEXT,
                    escalated   BOOLEAN DEFAULT 0,
                    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.db.commit()
        except Exception as e:
            print(f"[CrisisDetector] table init error: {e}")

    # ------------------------------------------------------------------
    # Main assessment
    # ------------------------------------------------------------------
    # Context patterns that suggest the user is NOT personally in crisis
    _DEFLATION_PATTERNS = [
        'read about', 'article about', 'book about', 'movie about', 'show about',
        'friend who', 'someone i know', 'my friend', 'a friend', 'colleague',
        'in the news', 'documentary', 'research on', 'study about',
        'used to', 'years ago', 'when i was', 'back when', 'in the past',
        'hypothetically', 'what if someone', 'asking for a friend',
        'no longer', 'not anymore', 'i\'m over it', 'i\'m past that',
    ]

    def assess(self, user_id: int, message: str) -> CrisisAssessment:
        msg_lower = message.lower()
        matched = {'critical': [], 'urgent': [], 'concern': [], 'watch': []}

        for sig in CRITICAL_SIGNALS:
            if sig in msg_lower:
                matched['critical'].append(sig)
        for sig in URGENT_SIGNALS:
            if sig in msg_lower:
                matched['urgent'].append(sig)
        for sig in CONCERN_SIGNALS:
            if sig in msg_lower:
                matched['concern'].append(sig)
        for sig in WATCH_SIGNALS:
            if sig in msg_lower:
                matched['watch'].append(sig)

        # Context filtering: reduce confidence if message appears third-person/hypothetical/past
        deflation = sum(1 for p in self._DEFLATION_PATTERNS if p in msg_lower)
        if deflation > 0:
            # Downgrade non-critical matches (never downgrade critical for safety)
            if not matched['critical']:
                matched['urgent'] = []  # clear if likely not personal
            if deflation >= 2:
                matched['concern'] = []

        # Determine severity (highest match wins)
        if matched['critical']:
            severity = SEVERITY_CRITICAL
            confidence = min(0.7 + len(matched['critical']) * 0.1, 1.0)
        elif matched['urgent']:
            severity = SEVERITY_URGENT
            confidence = min(0.5 + len(matched['urgent']) * 0.1, 0.9)
        elif matched['concern']:
            severity = SEVERITY_CONCERN
            confidence = min(0.3 + len(matched['concern']) * 0.1, 0.8)
        elif matched['watch']:
            severity = SEVERITY_WATCH
            confidence = min(0.2 + len(matched['watch']) * 0.1, 0.6)
        else:
            return CrisisAssessment(
                severity='none', confidence=0.0, matched_signals=[],
                response_guidance='', resources=[], should_escalate=False,
            )

        # Escalation check via history (repeated crisis signals)
        recent_count = self._recent_crisis_count(user_id, hours=24)
        if recent_count >= 2 and severity == SEVERITY_CONCERN:
            severity = SEVERITY_URGENT
            confidence = min(confidence + 0.15, 0.95)
        if recent_count >= 3 and severity == SEVERITY_URGENT:
            severity = SEVERITY_CRITICAL
            confidence = min(confidence + 0.1, 1.0)

        all_matched = []
        for signals in matched.values():
            all_matched.extend(signals)

        resources = self._get_resources()
        guidance = self._build_guidance(severity, all_matched)
        should_escalate = severity == SEVERITY_CRITICAL

        assessment = CrisisAssessment(
            severity=severity,
            confidence=round(confidence, 2),
            matched_signals=all_matched[:10],
            response_guidance=guidance,
            resources=resources,
            should_escalate=should_escalate,
        )

        # Log
        self._log_assessment(user_id, assessment, message)

        return assessment

    # ------------------------------------------------------------------
    # Response guidance per severity
    # ------------------------------------------------------------------
    @staticmethod
    def _build_guidance(severity: str, signals: List[str]) -> str:
        if severity == SEVERITY_CRITICAL:
            return (
                "⚠️ CRITICAL SAFETY PROTOCOL ⚠️\n"
                "The user may be in immediate danger. Your response MUST:\n"
                "1. Acknowledge their pain with genuine empathy — do NOT minimise\n"
                "2. Gently ask if they are safe right now\n"
                "3. Provide crisis helpline numbers (included below)\n"
                "4. Encourage them to contact someone they trust\n"
                "5. Do NOT give generic advice. Be present and human.\n"
                "6. Do NOT try to 'fix' them. Listen and connect.\n"
                "7. Remind them: reaching out takes courage and they matter.\n"
                "NEVER say 'I'm just an AI'. Be the compassionate presence they need right now."
            )
        elif severity == SEVERITY_URGENT:
            return (
                "[SAFETY AWARENESS — URGENT]\n"
                "The user is showing significant distress. Your response should:\n"
                "1. Validate their feelings — 'What you're feeling is real and it matters'\n"
                "2. Gently explore their safety — 'Are you safe right now?'\n"
                "3. Mention professional support is available (provide numbers)\n"
                "4. Offer one small grounding step (deep breath, reach out to someone)\n"
                "5. Be warm, present, and non-judgmental\n"
                "Do NOT rush to solutions or positive platitudes."
            )
        elif severity == SEVERITY_CONCERN:
            return (
                "[SAFETY AWARENESS — CONCERN]\n"
                "The user is showing signs of distress. Your response should:\n"
                "1. Acknowledge their struggle with empathy\n"
                "2. Gently check in — 'How are you really doing?'\n"
                "3. Normalise seeking help — 'Many people find it helpful to talk to someone'\n"
                "4. Mention support resources are available if needed\n"
                "5. Focus on connection before advice"
            )
        elif severity == SEVERITY_WATCH:
            return (
                "[SAFETY AWARENESS — MONITORING]\n"
                "The user may be going through a difficult time. Be extra:\n"
                "- Empathetic and patient\n"
                "- Careful not to dismiss their feelings\n"
                "- Ready to explore deeper if they want to share more"
            )
        return ''

    # ------------------------------------------------------------------
    # Resources
    # ------------------------------------------------------------------
    def _get_resources(self) -> List[Dict]:
        resources = []
        locale_data = CRISIS_RESOURCES.get(self.locale, CRISIS_RESOURCES.get('AU'))
        if locale_data:
            primary = {k: v for k, v in locale_data.items() if k != 'additional'}
            resources.append(primary)
            for extra in locale_data.get('additional', []):
                resources.append(extra)
        # Always include global fallback
        resources.append(CRISIS_RESOURCES['global'])
        return resources

    def build_resource_text(self, resources: List[Dict] = None) -> str:
        resources = resources or self._get_resources()
        lines = ["If you need immediate support, please reach out:"]
        for r in resources[:4]:
            parts = [r.get('name', '')]
            if r.get('phone'):
                parts.append(f"📞 {r['phone']}")
            if r.get('text'):
                parts.append(f"💬 {r['text']}")
            if r.get('contact'):
                parts.append(r['contact'])
            lines.append('  • ' + ' — '.join(parts))
        return '\n'.join(lines)

    # ------------------------------------------------------------------
    # Prompt block
    # ------------------------------------------------------------------
    def build_prompt_block(self, assessment: CrisisAssessment) -> str:
        if assessment.severity == 'none':
            return ''
        lines = [assessment.response_guidance]
        if assessment.severity in (SEVERITY_URGENT, SEVERITY_CRITICAL):
            lines.append('\nCRISIS RESOURCES TO INCLUDE IN YOUR RESPONSE:')
            lines.append(self.build_resource_text(assessment.resources))
        return '\n'.join(lines)

    # ------------------------------------------------------------------
    # Persistence & history
    # ------------------------------------------------------------------
    def _log_assessment(self, user_id: int, assessment: CrisisAssessment, message: str):
        if not self.db or assessment.severity == 'none':
            return
        try:
            preview = message[:100] + '...' if len(message) > 100 else message
            cur = self.db.cursor()
            cur.execute('''
                INSERT INTO crisis_log (user_id, severity, confidence, signals, message_preview, escalated)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, assessment.severity, assessment.confidence,
                  json.dumps(assessment.matched_signals), preview, assessment.should_escalate))
            self.db.commit()
        except Exception as e:
            print(f"[CrisisDetector] log error: {e}")

    def _recent_crisis_count(self, user_id: int, hours: int = 24) -> int:
        if not self.db:
            return 0
        try:
            cur = self.db.cursor()
            cur.execute('''
                SELECT COUNT(*) FROM crisis_log
                WHERE user_id = ? AND severity IN ('concern', 'urgent', 'critical')
                AND created_at > datetime('now', ?)
            ''', (user_id, f'-{hours} hours'))
            return cur.fetchone()[0]
        except Exception:
            return 0

    def get_crisis_history(self, user_id: int, days: int = 30) -> List[Dict]:
        if not self.db:
            return []
        try:
            cur = self.db.cursor()
            cur.execute('''
                SELECT severity, confidence, signals, created_at
                FROM crisis_log
                WHERE user_id = ? AND created_at > datetime('now', ?)
                ORDER BY created_at DESC LIMIT 50
            ''', (user_id, f'-{days} days'))
            return [{'severity': r[0], 'confidence': r[1],
                     'signals': json.loads(r[2]) if r[2] else [], 'date': r[3]}
                    for r in cur.fetchall()]
        except Exception:
            return []


    # ------------------------------------------------------------------
    # DATA RETENTION (W10)
    # ------------------------------------------------------------------
    DEFAULT_RETENTION_DAYS = 90  # Purge crisis logs older than this

    def purge_expired_logs(self, retention_days: int = None) -> int:
        """Delete crisis_log entries older than retention_days. Returns rows deleted."""
        if not self.db:
            return 0
        days = retention_days or int(os.environ.get('CRISIS_RETENTION_DAYS', self.DEFAULT_RETENTION_DAYS))
        try:
            cur = self.db.cursor()
            cur.execute('DELETE FROM crisis_log WHERE created_at < datetime("now", ?)', (f'-{days} days',))
            self.db.commit()
            count = cur.rowcount
            if count:
                print(f"[CrisisDetector] Purged {count} crisis logs older than {days} days")
            return count
        except Exception as e:
            print(f"[CrisisDetector] purge error: {e}")
            return 0


# ---------------------------------------------------------------------------
# Module-level factory
# ---------------------------------------------------------------------------
_instance = None

def get_crisis_detector(db_connection=None, locale='AU') -> CrisisDetector:
    global _instance
    if _instance is None or db_connection is not None:
        _instance = CrisisDetector(db_connection, locale)
    return _instance
