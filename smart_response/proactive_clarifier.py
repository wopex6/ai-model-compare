"""
Proactive Clarifier
===================

When a user's message intent is ambiguous OR the situation is emotionally
critical, generates ONE targeted clarifying question instead of letting the
AI guess.  This saves an API call, improves response quality, and makes
users feel genuinely understood.

Triggers:
  1. ResponseNeedClassifier confidence < threshold (ambiguous intent)
  2. Multiple competing need types detected (conflicting signals)
  3. Emotionally critical keywords present (immediate attention)
  4. Very short/vague messages where any AI response would be generic

Returns a ClarificationDecision with:
  - should_clarify: bool
  - question: str  (the single question to ask)
  - reason: str    (internal explanation, for logging)
  - urgency: str   ('normal' | 'critical')
"""

import re
from dataclasses import dataclass
from typing import Optional, List, Dict


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class ClarificationDecision:
    should_clarify: bool
    question: str
    reason: str
    urgency: str = 'normal'       # 'normal' | 'critical'
    detected_need: str = ''       # primary need that triggered this


# ---------------------------------------------------------------------------
# Immediate-attention keywords (crisis / urgent support)
# ---------------------------------------------------------------------------

_CRITICAL_PATTERNS = [
    r"\b(suicid|self.harm|hurt myself|end my life|kill myself|not worth living|want to die)\b",
    r"\b(abuse|being abused|domestic violence|in danger|not safe)\b",
    r"\b(crisis|emergency|urgent help|desperate)\b",
    r"\bcan't (go on|take it anymore|cope|keep going)\b",
    r"\b(panic attack|breakdown|losing my mind)\b",
]

# Questions matched to each need type for clarification
_CLARIFYING_QUESTIONS: Dict[str, str] = {
    'direction': "To help you decide — what matters most to you right now: the outcome you want, or avoiding a specific risk?",
    'action_plan': "Before I map out a plan — what's the most important outcome you want from this, and do you have a deadline in mind?",
    'immediate_result': "What specifically do you need right now — a quick answer, a next action, or a summary?",
    'inspiration': "What's the main thing you feel stuck on — the idea itself, the motivation to start, or how to see it differently?",
    'small_steps': "What feels most overwhelming about this right now — the size of the task, not knowing where to start, or something else?",
    'sympathy': "I want to make sure I'm here in the right way for you — do you mostly need to talk it through, or would some practical thoughts help too?",
    'information': "To give you the most useful answer — are you looking for a quick overview, or a deeper explanation with examples?",
    'validation': "What would feel most helpful — confirming whether your approach is on track, or exploring if there's a better angle?",
}

# Generic fallback for truly ambiguous messages
_GENERIC_QUESTION = "To make sure I respond in the most useful way — what would feel most helpful right now: talking it through, a practical plan, or some perspective?"

# Critical-situation response (not a question — immediate empathy + safety)
_CRITICAL_RESPONSE = (
    "I can hear that things feel really serious right now. "
    "Before anything else — are you safe? "
    "I'm here with you."
)


# ---------------------------------------------------------------------------
# Clarifier
# ---------------------------------------------------------------------------

class ProactiveClarifier:
    """
    Decides whether to ask a clarifying question before sending to AI.

    Design principles:
    - Ask at most ONCE per conversation turn
    - Never ask when need is clearly detected (confidence >= threshold)
    - Critical situations bypass the question and trigger immediate empathy
    - Never raises — always returns a ClarificationDecision
    """

    def __init__(
        self,
        confidence_threshold: float = 0.35,
        min_words_for_vague: int = 4,
    ):
        self.confidence_threshold = confidence_threshold
        self.min_words_for_vague = min_words_for_vague

    def decide(self, message: str, need_confidence: float = 0.0,
               primary_need: str = 'information',
               secondary_need: Optional[str] = None) -> ClarificationDecision:
        """
        Decide whether to clarify, and if so, what to ask.

        Args:
            message:          The user's raw message
            need_confidence:  Confidence score from ResponseNeedClassifier
            primary_need:     Primary need type from ResponseNeedClassifier
            secondary_need:   Optional secondary need type

        Returns:
            ClarificationDecision (should_clarify=False means proceed to AI)
        """
        try:
            return self._decide_safe(message, need_confidence, primary_need, secondary_need)
        except Exception:
            return ClarificationDecision(
                should_clarify=False,
                question='',
                reason='error_fallback',
            )

    def _decide_safe(self, message: str, need_confidence: float,
                     primary_need: str, secondary_need: Optional[str]) -> ClarificationDecision:
        msg = message.strip()

        # ── 1. CRITICAL SITUATIONS — immediate empathy, no question ──────────
        if self._is_critical(msg):
            return ClarificationDecision(
                should_clarify=True,
                question=_CRITICAL_RESPONSE,
                reason='critical_situation_detected',
                urgency='critical',
                detected_need='sympathy',
            )

        # ── 2. VERY VAGUE MESSAGES — too little info to respond well ─────────
        word_count = len(msg.split())
        is_vague = word_count < self.min_words_for_vague and need_confidence < 0.3
        if is_vague:
            question = _CLARIFYING_QUESTIONS.get(primary_need, _GENERIC_QUESTION)
            return ClarificationDecision(
                should_clarify=True,
                question=question,
                reason=f'message_too_vague ({word_count} words, conf={need_confidence:.2f})',
                detected_need=primary_need,
            )

        # ── 3. AMBIGUOUS INTENT — competing needs, low confidence ────────────
        needs_conflict = (
            secondary_need is not None and
            secondary_need != primary_need and
            need_confidence < self.confidence_threshold
        )
        if needs_conflict:
            question = _CLARIFYING_QUESTIONS.get(primary_need, _GENERIC_QUESTION)
            return ClarificationDecision(
                should_clarify=True,
                question=question,
                reason=f'competing_needs ({primary_need} vs {secondary_need}, conf={need_confidence:.2f})',
                detected_need=primary_need,
            )

        # ── 4. LOW CONFIDENCE on its own ─────────────────────────────────────
        if need_confidence < self.confidence_threshold * 0.6:  # Very low threshold
            return ClarificationDecision(
                should_clarify=True,
                question=_GENERIC_QUESTION,
                reason=f'very_low_confidence ({need_confidence:.2f})',
                detected_need=primary_need,
            )

        # ── Default: no clarification needed ─────────────────────────────────
        return ClarificationDecision(
            should_clarify=False,
            question='',
            reason=f'clear_intent ({primary_need}, conf={need_confidence:.2f})',
            detected_need=primary_need,
        )

    def _is_critical(self, message: str) -> bool:
        """Check if message contains crisis/emergency indicators."""
        msg_lower = message.lower()
        return any(re.search(p, msg_lower, re.IGNORECASE) for p in _CRITICAL_PATTERNS)

    def format_clarification_response(self, decision: ClarificationDecision) -> dict:
        """Format as a chat response dict compatible with the existing pipeline."""
        return {
            'response': decision.question,
            'type': 'clarification',
            'urgency': decision.urgency,
            'detected_need': decision.detected_need,
            'clarification_reason': decision.reason.value if hasattr(decision.reason, 'value') else str(decision.reason),
            'skip_history_save': decision.urgency != 'critical',  # Save critical interactions
        }


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_clarifier: Optional['ProactiveClarifier'] = None


def get_clarifier() -> ProactiveClarifier:
    """Get or create the module-level ProactiveClarifier singleton."""
    global _clarifier
    if _clarifier is None:
        _clarifier = ProactiveClarifier()
    return _clarifier
