"""
FormatPreferenceDetector
========================
Detects how a user prefers their answers formatted — bullet lists,
numbered steps, or flowing prose — and returns a compact format
instruction for the AI prompt.

Detection strategy (current message only — no DB query needed):

  BULLETS:  "give me a list", "list them out", "bullet points", "break it down",
            "what are the", "what are some", "pros and cons"

  STEPS:    "step by step", "walk me through", "how do i", "how to",
            "what steps", "in order", "one by one", "guide me"

  PROSE:    "just tell me", "just explain", "in plain english",
            "summarise", "summarize", "overview", "tldr", "tl;dr",
            "quick answer", "brief answer", "short answer"

Returns '' when no clear preference is detected in the current message.
All errors return '' — never blocks a response.
"""

from __future__ import annotations
import re
from typing import Optional

BULLET_PATTERNS = [
    r'\bgive me a list\b', r'\blist (them|it|these|those)\b',
    r'\bbullet[- ]?points?\b', r'\bbreak it down\b',
    r'\bwhat are (the|some|a few)\b', r'\bpros and cons\b',
    r'\badvantages and disadvantages\b', r'\bkey (points|things|factors|reasons)\b',
]

STEP_PATTERNS = [
    r'\bstep[- ]by[- ]step\b', r'\bwalk me through\b',
    r'\bhow (do i|do you|can i|to)\b', r'\bwhat (are the )?steps\b',
    r'\bin (what )?order\b', r'\bone by one\b', r'\bguide me\b',
    r'\bshow me how\b', r"\bwhat('s| is) the process\b",
]

PROSE_PATTERNS = [
    r'\bjust (tell|explain|give)\b', r'\bin plain (english|terms|language)\b',
    r'\bsummarize?\b', r'\boverview\b', r'\btl[;, ]?dr\b',
    r'\bquick (answer|summary|take)\b', r'\bbrief (answer|summary|explanation)\b',
    r'\bshort (answer|version|explanation)\b', r'\bin a nutshell\b',
    r'\bshort and sweet\b',
]


class FormatPreferenceDetector:
    """
    Detects format preference from the current user message and returns
    a one-line instruction for the AI prompt.
    """

    def build_format_instruction(self, user_message: str) -> str:
        """
        Analyse the current message and return a format instruction, or ''.
        """
        try:
            return self._detect(user_message or '')
        except Exception:
            return ''

    # ------------------------------------------------------------------
    def _detect(self, msg: str) -> str:
        t = msg.lower()

        bullet_hits = sum(1 for p in BULLET_PATTERNS if re.search(p, t))
        step_hits   = sum(1 for p in STEP_PATTERNS   if re.search(p, t))
        prose_hits  = sum(1 for p in PROSE_PATTERNS  if re.search(p, t))

        total = bullet_hits + step_hits + prose_hits
        if total == 0:
            return ''

        top = max(bullet_hits, step_hits, prose_hits)

        # Require a clear winner — if two formats tie, return ''
        winners = [
            f for f, s in [('bullet', bullet_hits), ('step', step_hits), ('prose', prose_hits)]
            if s == top and s > 0
        ]
        if len(winners) != 1:
            return ''

        winner = winners[0]
        if winner == 'bullet':
            return (
                "FORMAT: The user wants a bullet-point list. "
                "Use clear, concise bullets. No long paragraphs."
            )
        elif winner == 'step':
            return (
                "FORMAT: The user wants numbered steps. "
                "Present your answer as an ordered step-by-step sequence."
            )
        else:
            return (
                "FORMAT: The user wants a brief prose answer. "
                "Skip lists and bullet points — just explain in plain, flowing sentences."
            )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_instance: Optional[FormatPreferenceDetector] = None


def get_format_detector() -> FormatPreferenceDetector:
    global _instance
    if _instance is None:
        _instance = FormatPreferenceDetector()
    return _instance
