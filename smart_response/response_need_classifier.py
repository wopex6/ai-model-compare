"""
Response Need Classifier
========================

Detects WHAT TYPE of response a user actually needs based on their message
content, tone, and conversational signals.

Response types (from user requirement):
  direction         - "what should I do?" / needs guidance on choices
  action_plan       - needs concrete step-by-step plan to execute
  immediate_result  - needs a quick fix / answer right now
  inspiration       - needs questions that open thinking / new perspective
  small_steps       - overwhelmed; needs broken-down micro-actions
  sympathy          - needs to feel heard first, advice secondary
  information       - needs explanation / facts / understanding
  validation        - needs to know they are on the right track

Each classification produces a structured prompt instruction injected
into the AI prompt so the AI adopts the correct response MODE.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

NEED_TYPES = [
    'direction',
    'action_plan',
    'immediate_result',
    'inspiration',
    'small_steps',
    'sympathy',
    'information',
    'validation',
]


@dataclass
class NeedClassification:
    primary_need: str           # dominant need type
    secondary_need: Optional[str]  # optional secondary need
    confidence: float           # 0.0 – 1.0
    signals: List[str]          # human-readable explanation of what triggered it
    prompt_instruction: str     # ready-to-inject prompt instruction


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------

class ResponseNeedClassifier:
    """
    Lightweight, zero-dependency classifier that scores a user message
    against heuristic signal patterns and returns a NeedClassification.

    Designed to run synchronously and never fail — all errors return a
    low-confidence 'information' classification.
    """

    # ---- Signal dictionaries ------------------------------------------------

    _SIGNALS: Dict[str, List[str]] = {

        'sympathy': [
            r"\bi(\'m| am) (so |really |just |)?(sad|upset|devastated|broken|hurt|lost|lonely|exhausted|overwhelmed|depressed|struggling|suffering)\b",
            r"\bnobody (understands?|cares?|listens?)\b",
            r"\bi (just |really |)need(ed)? (to )?(talk|vent|tell someone)\b",
            r"\bi don['']t know (what to do|where to turn|how to cope)\b",
            r"\bi feel (so |completely |totally )?(alone|hopeless|worthless|invisible|stuck|broken)\b",
            r"\bthis is (so |really |)hard\b",
            r"\bcan you (just |please |)listen\b",
            r"\bi['']ve been (crying|struggling|fighting|suffering)\b",
            r"\bmy (heart|soul|life) (is|feels?)\b",
        ],

        'direction': [
            r"\bwhat should i (do|choose|pick|decide|focus on)\b",
            r"\bwhich (is better|one should i|option|path|direction|way)\b",
            r"\bi('m| am) (not sure|unsure|confused|torn) (what|which|whether|about)\b",
            r"\bhelp me (decide|choose|figure out|think through)\b",
            r"\bshould i (go|stay|quit|start|stop|take|try|apply|accept)\b",
            r"\bi need (guidance|advice|direction|your opinion)\b",
            r"\bwhat would you (recommend|suggest|do|advise)\b",
            r"\bi('m| am) at a crossroads?\b",
            r"\bnot sure (which|what|whether|how) to\b",
        ],

        'action_plan': [
            r"\bhow (do|can|should) i (start|begin|get started|go about|implement|execute|build|create|set up)\b",
            r"\bgive me (a plan|steps|a roadmap|a strategy|a checklist|a framework)\b",
            r"\bwalk me through\b",
            r"\bstep.by.step\b",
            r"\bwhat (are the steps|is the process|do i need to do|should my plan be)\b",
            r"\bhow to (achieve|reach|accomplish|complete|finish|get to)\b",
            r"\bi want to (achieve|build|create|launch|start|finish|complete)\b",
            r"\bplan (for|to)\b",
            r"\bwhere do i (start|begin|go from here)\b",
        ],

        'immediate_result': [
            r"\b(quick|fast|urgent|asap|immediately|right now|in a hurry)\b",
            r"\bi need (this|it|the answer|to know) (now|immediately|urgently|quickly|asap|today)\b",
            r"\bcan you (quickly|just|briefly|fast)\b",
            r"\bshort (answer|version|summary|explanation)\b",
            r"\bjust (tell me|give me|say|the answer|a quick)\b",
            r"\btl;?dr\b",
            r"\bbottom line\b",
            r"\bno time (to|for)\b",
            r"\bin (one|a few|simple) (sentence|word|line)\b",
        ],

        'inspiration': [
            r"\bi feel (stuck|blocked|uninspired|unmotivated|bored|flat|stagnant)\b",
            r"\b(inspire|motivate|spark|ignite|challenge|push) me\b",
            r"\bwhat (else|more|could|might|if)\b.*\?\s*$",
            r"\bnew (perspective|angle|way of thinking|approach|idea|lens)\b",
            r"\bopen (my|the) (mind|thinking|eyes)\b",
            r"\bhelp me (think differently|see this differently|think outside)\b",
            r"\bwhat questions should i (ask|be asking|consider|explore)\b",
            r"\bbroaden my\b",
            r"\bchallenge (me|my thinking|my assumptions)\b",
        ],

        'small_steps': [
            r"\bi('m| am) (overwhelmed|paralysed|paralyzed|scared to start|frozen|anxious about)\b",
            r"\bdon['']t know where to (begin|start)\b",
            r"\btoo (big|much|overwhelming|daunting|scary)\b",
            r"\bbreak (it|this|that|things?) down\b",
            r"\bsmall(er)? (step|piece|chunk|part|bit)\b",
            r"\bbaby step\b",
            r"\bone (thing|step|action|task) at a time\b",
            r"\bi (can['']t|cannot) (handle|manage|do) (it all|everything|this)\b",
            r"\bjust (get started|take the first|do something small)\b",
        ],

        'information': [
            r"\bwhat (is|are|does|do|was|were|will|would)\b.*\?",
            r"\bhow (does|do|did|can|could|would|will)\b.*\?",
            r"\bexplain\b",
            r"\bdefine\b",
            r"\btell me (about|what|how|why)\b",
            r"\bi (want|need|would like) to (know|understand|learn)\b",
            r"\bwhy (is|are|does|do|did|would|should)\b.*\?",
            r"\bwhat('s| is) the (difference|meaning|reason|cause|effect|best way)\b",
        ],

        'validation': [
            r"\bam i (right|wrong|on the right track|making sense|overthinking|being silly|crazy)\b",
            r"\bdoes (this|that|my plan|my idea|it) (make sense|sound right|seem right|look right|work)\b",
            r"\bi think (i|this|that|my|the)\b.*\b(right\?|correct\?|okay\?|good\?|fine\?)",
            r"\bis (this|it|that|my approach) (okay|fine|good|reasonable|sensible|normal)\b",
            r"\bwhat do you think (of|about) (my|this|that|it)\b",
            r"\bam i (doing|going|heading) (this|it|the) (right way|correctly|in the right direction)\b",
            r"\bi just wanted to (check|confirm|make sure|verify)\b",
        ],
    }

    # ---- Prompt instructions per need type ----------------------------------

    _INSTRUCTIONS: Dict[str, str] = {
        'direction': (
            "RESPONSE MODE — DIRECTION: The user is at a decision point and needs guidance on which path to take. "
            "Do NOT give a generic 'it depends'. Weigh the options, state a clear recommendation with a brief reason, "
            "then invite them to push back if it doesn't fit."
        ),
        'action_plan': (
            "RESPONSE MODE — ACTION PLAN: The user wants a concrete, executable plan. "
            "Structure your response as numbered steps. Keep each step specific and doable. "
            "Start with the first action they can take TODAY."
        ),
        'immediate_result': (
            "RESPONSE MODE — IMMEDIATE RESULT: The user needs a quick, direct answer. "
            "Lead with the answer in the first sentence. Skip preamble entirely. "
            "You may offer to elaborate, but the core answer must come first."
        ),
        'inspiration': (
            "RESPONSE MODE — INSPIRATION / QUESTIONS: The user is stuck or needs a new perspective. "
            "Instead of giving answers, ask 1–2 powerful questions that open up their thinking. "
            "Or reframe the situation from an unexpected angle. Avoid generic advice."
        ),
        'small_steps': (
            "RESPONSE MODE — SMALL STEPS: The user feels overwhelmed. "
            "Do NOT give a full plan — that will increase anxiety. "
            "Identify the single smallest possible action they can take in the next 5–15 minutes. "
            "Make it so small it feels almost too easy. Acknowledge their feeling first."
        ),
        'sympathy': (
            "RESPONSE MODE — SYMPATHY / LISTENING: The user needs to feel heard, not fixed. "
            "Start by reflecting their emotional state back with warmth and without judgment. "
            "Do NOT jump to advice or solutions. Ask one gentle follow-up question to help them say more. "
            "Only offer practical help if they explicitly ask."
        ),
        'information': (
            "RESPONSE MODE — INFORMATION: The user wants to understand something. "
            "Explain clearly and accurately. Match depth to their apparent knowledge level. "
            "Use a concrete example if it helps. Be factual."
        ),
        'validation': (
            "RESPONSE MODE — VALIDATION: The user wants to know if they are on the right track. "
            "Be honest — if they are, tell them clearly and specifically why. "
            "If they are slightly off, acknowledge what IS right first, then gently correct. "
            "Avoid vague reassurance."
        ),
    }

    # -------------------------------------------------------------------------

    def classify(self, message: str) -> NeedClassification:
        """
        Classify a user message into its primary (and optional secondary) need.

        Returns a NeedClassification with a ready-to-use prompt instruction.
        Always returns a result — never raises.
        """
        try:
            return self._classify_safe(message)
        except Exception:
            return NeedClassification(
                primary_need='information',
                secondary_need=None,
                confidence=0.0,
                signals=[],
                prompt_instruction=self._INSTRUCTIONS['information'],
            )

    def _classify_safe(self, message: str) -> NeedClassification:
        msg = message.strip().lower()
        scores: Dict[str, float] = {need: 0.0 for need in NEED_TYPES}
        matched_signals: Dict[str, List[str]] = {need: [] for need in NEED_TYPES}

        for need, patterns in self._SIGNALS.items():
            for pattern in patterns:
                if re.search(pattern, msg, re.IGNORECASE):
                    scores[need] += 1.0
                    matched_signals[need].append(pattern)

        # Normalise: short urgent messages boost immediate_result
        word_count = len(msg.split())
        if word_count <= 8 and '?' in msg:
            scores['immediate_result'] += 0.5

        # Emotional words with no question → sympathy gets a boost
        if '?' not in msg and scores['sympathy'] > 0:
            scores['sympathy'] += 0.5

        # Sort by score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary_need, primary_score = ranked[0]
        secondary_need, secondary_score = ranked[1] if len(ranked) > 1 else (None, 0)

        # Confidence: ratio of primary to total signal count
        total_signals = sum(scores.values())
        confidence = min(primary_score / max(total_signals, 1), 1.0) if total_signals > 0 else 0.0

        # If no signals fired at all, fall back to 'information' at low confidence
        if primary_score == 0:
            primary_need = 'information'
            confidence = 0.1

        # Only report secondary if it has meaningful weight
        if secondary_score < 0.5 or secondary_score < primary_score * 0.4:
            secondary_need = None

        return NeedClassification(
            primary_need=primary_need,
            secondary_need=secondary_need,
            confidence=round(confidence, 2),
            signals=matched_signals[primary_need],
            prompt_instruction=self._INSTRUCTIONS[primary_need],
        )

    def get_instruction(self, message: str, min_confidence: float = 0.2) -> str:
        """
        Convenience method: returns the prompt instruction string,
        or empty string if confidence is below the threshold.
        """
        result = self.classify(message)
        if result.confidence >= min_confidence:
            return result.prompt_instruction
        return ""


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_classifier: Optional[ResponseNeedClassifier] = None


def get_need_classifier() -> ResponseNeedClassifier:
    """Get or create the module-level ResponseNeedClassifier singleton."""
    global _classifier
    if _classifier is None:
        _classifier = ResponseNeedClassifier()
    return _classifier
