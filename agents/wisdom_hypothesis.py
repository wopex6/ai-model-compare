"""
Wisdom Hypothesis Engine
========================
The agent doesn't just give advice — it forms hypotheses about WHY a user
behaves the way they do, tests them across analysis cycles, and adjusts its
interpretations based on what actually helps vs what doesn't.

Hypothesis lifecycle:
  PROPOSED → TESTING → CONFIRMED | REJECTED | REVISED

Example hypothesis:
  "Wai's avoidance of health discussions is driven by anxiety (CBT model),
   not stoic suppression. Evidence: low satisfaction scores on health topics,
   high question rate, emotional language."

After 3+ cycles:
  If the CBT-based nudges led to behaviour change → CONFIRMED
  If no change detected → REJECTED → try Stoic/Confucian model instead

This makes the wisdom agent genuinely adaptive rather than prescriptive.
"""

import os
import re
import sys
import json
import hashlib
import sqlite3
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.wisdom_knowledge_base import get_next_school


# ─────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────

@dataclass
class Hypothesis:
    """
    A testable hypothesis about why a user exhibits a pattern,
    formed from a specific school of thought's interpretation.
    """
    id: str                        # unique per user+pattern
    user_id: str
    pattern_id: str                # which WisdomLesson.id this relates to
    pattern_description: str       # the detected pattern in the user
    school_of_thought: str         # which interpretation is being tested
    hypothesis_text: str           # plain language statement of the hypothesis
    predicted_change: str          # what change we expect to see if correct
    nudge_given: str               # what advice was given based on this
    status: str = 'testing'        # 'proposed' | 'testing' | 'confirmed' | 'rejected' | 'revised'
    confidence: float = 0.5        # 0–1, updated based on evidence
    cycles_tested: int = 0
    evidence_for: List[str] = field(default_factory=list)
    evidence_against: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    revised_to_school: str = ''    # if rejected, which school to try next

    _VALID_STATUSES = frozenset({'proposed', 'testing', 'confirmed', 'rejected', 'revised'})

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'pattern_id': self.pattern_id,
            'pattern_description': self.pattern_description,
            'school_of_thought': self.school_of_thought,
            'hypothesis_text': self.hypothesis_text,
            'predicted_change': self.predicted_change,
            'nudge_given': self.nudge_given,
            'status': self.status if self.status in self._VALID_STATUSES else 'testing',
            'confidence': max(0.0, min(1.0, self.confidence)),  # clamp to [0, 1]
            'cycles_tested': max(0, self.cycles_tested),         # never negative
            'evidence_for': self.evidence_for,
            'evidence_against': self.evidence_against,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'revised_to_school': self.revised_to_school,
        }

    @staticmethod
    def from_dict(d: Dict) -> 'Hypothesis':
        h = Hypothesis(
            id=d['id'], user_id=d['user_id'], pattern_id=d['pattern_id'],
            pattern_description=d.get('pattern_description', ''),
            school_of_thought=d['school_of_thought'],
            hypothesis_text=d['hypothesis_text'],
            predicted_change=d.get('predicted_change', ''),
            nudge_given=d.get('nudge_given', ''),
        )
        raw_status = d.get('status', 'testing')
        h.status = raw_status if raw_status in Hypothesis._VALID_STATUSES else 'testing'
        raw_conf = d.get('confidence', 0.5)
        try:
            h.confidence = max(0.0, min(1.0, float(raw_conf)))
        except (ValueError, TypeError):
            h.confidence = 0.5
        raw_cycles = d.get('cycles_tested', 0)
        try:
            h.cycles_tested = max(0, int(raw_cycles))
        except (ValueError, TypeError):
            h.cycles_tested = 0
        h.evidence_for = d.get('evidence_for', [])
        h.evidence_against = d.get('evidence_against', [])
        h.created_at = d.get('created_at', h.created_at)
        h.updated_at = d.get('updated_at', h.updated_at)
        h.revised_to_school = d.get('revised_to_school', '')
        return h


# ─────────────────────────────────────────────────────
# Hypothesis Engine
# ─────────────────────────────────────────────────────

class HypothesisEngine:
    """
    Manages the lifecycle of hypotheses for all users.
    Stored as JSON per user in wisdom_profiles/{user_id}_hypotheses.json
    """

    WISDOM_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'wisdom_profiles'
    )

    # How many cycles before a hypothesis is judged
    MIN_CYCLES_TO_JUDGE = 3

    # Confidence thresholds
    CONFIRM_THRESHOLD = 0.70
    REJECT_THRESHOLD  = 0.30

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        try:
            os.makedirs(self.WISDOM_DIR, exist_ok=True)
        except OSError as mk_err:
            if verbose:
                print(f"[HypothesisEngine] Warning: could not create WISDOM_DIR: {mk_err}")

    def _log(self, msg: str):
        if self.verbose:
            print(f"[HypothesisEngine] {msg}")

    def _path(self, user_id: str) -> str:
        return os.path.join(self.WISDOM_DIR, f"{user_id}_hypotheses.json")

    _MAX_HYPOTHESES = 100  # cap to prevent unbounded growth across cycles

    def load(self, user_id: str) -> List[Hypothesis]:
        path = self._path(user_id)
        if not os.path.exists(path):
            return []
        try:
            with open(path) as f:
                data = json.load(f)
            hypotheses = []
            for i, d in enumerate(data):
                try:
                    hypotheses.append(Hypothesis.from_dict(d))
                except Exception as item_err:
                    self._log(f"  Warning: skipping corrupt hypothesis entry #{i}: {item_err}")
            # Trim oldest terminal-state hypotheses when over cap
            if len(hypotheses) > self._MAX_HYPOTHESES:
                terminal = [h for h in hypotheses if h.status in ('confirmed', 'rejected')]
                active   = [h for h in hypotheses if h.status not in ('confirmed', 'rejected')]
                terminal.sort(key=lambda h: h.updated_at)  # oldest first
                # Guard: if active alone already fills cap, keep no terminal entries
                slots_for_terminal = max(0, self._MAX_HYPOTHESES - len(active))
                keep_terminal = terminal[-slots_for_terminal:] if slots_for_terminal else []
                hypotheses = active + keep_terminal
                self._log(f"  Trimmed hypothesis list to {len(hypotheses)} (was {len(data)})")
            return hypotheses
        except Exception as load_err:
            self._log(f"  Warning: could not load hypotheses for {user_id}: {load_err} — starting fresh")
            return []

    def save(self, user_id: str, hypotheses: List[Hypothesis]) -> bool:
        """Persist hypotheses to disk. Returns False (and logs) on any write error."""
        path = self._path(user_id)
        try:
            with open(path, 'w') as f:
                json.dump([h.to_dict() for h in hypotheses], f, indent=2)
            return True
        except Exception as e:
            self._log(f"Warning: could not save hypotheses for {user_id}: {e}")
            return False

    # ─────────────────────────────────────────
    # Forming new hypotheses
    # ─────────────────────────────────────────

    def propose(
        self,
        user_id: str,
        pattern_id: str,
        pattern_description: str,
        school_of_thought: str,
        hypothesis_text: str,
        predicted_change: str,
        nudge_given: str,
    ) -> Hypothesis:
        """Create a new hypothesis for a user pattern."""
        # Include a short hash of pattern_description so two different patterns
        # that share the same lesson ID and school don't collide on the same ID
        desc_hash = hashlib.sha256(pattern_description.encode()).hexdigest()[:6]
        hyp_id = f"{user_id}_{pattern_id}_{school_of_thought}_{desc_hash}".replace(' ', '_').lower()
        h = Hypothesis(
            id=hyp_id,
            user_id=user_id,
            pattern_id=pattern_id,
            pattern_description=pattern_description,
            school_of_thought=school_of_thought,
            hypothesis_text=hypothesis_text,
            predicted_change=predicted_change,
            nudge_given=nudge_given,
            status='testing',
        )
        return h

    # ─────────────────────────────────────────
    # Evaluating hypotheses
    # ─────────────────────────────────────────

    def evaluate(
        self,
        hypotheses: List[Hypothesis],
        new_patterns: List[Dict],
        new_wisdom_score: float,
        prev_wisdom_score: float,
        new_conversations: List[Dict],
    ) -> Tuple[List[Hypothesis], List[str]]:
        """
        For each testing hypothesis, evaluate whether evidence supports or contradicts it.
        Returns updated hypotheses and a list of evaluation notes for the AI prompt.
        """
        notes = []

        # Hoist helpers outside the loop — re-defining them per iteration is wasteful
        def _wm(text: str, phrase: str) -> bool:
            """Word-boundary match to avoid fragment false positives."""
            if ' ' in phrase:
                return phrase in text
            return bool(re.search(r'\b' + re.escape(phrase) + r'\b', text))

        # _wm_desc is the same shape; alias it for readability at call sites below
        _wm_desc = _wm

        # Normalise smart-quotes once for all conversation texts
        def _normalise(text: str) -> str:
            return (text
                    .replace('\u2019', "'")
                    .replace('\u2018', "'")
                    .replace('\u201c', '"')
                    .replace('\u201d', '"'))

        positive_signals = ['better', 'improved', 'tried', 'did it', 'felt good',
                             'made progress', 'thank you', 'helpful', 'worked']
        negative_signals = ['still', 'same', 'worse', "didn't help", 'not working',
                             'giving up', 'nothing changes']

        for h in hypotheses:
            if h.status not in ('testing', 'proposed'):
                continue

            h.cycles_tested += 1
            h.updated_at = datetime.now().isoformat()

            # Evidence signals
            score_improved = new_wisdom_score > prev_wisdom_score + 2
            score_declined  = new_wisdom_score < prev_wisdom_score - 2

            # Check if predicted change is reflected in new patterns
            predicted_lower = h.predicted_change.lower()
            pattern_texts = [p.get('description', '').lower() for p in new_patterns]

            h_desc_lower = h.pattern_description.lower()

            pattern_resolved = any(
                p.get('resolved', False) and
                _wm_desc(h_desc_lower, p.get('description', '').lower())
                for p in new_patterns
            )
            pattern_persists = any(
                _wm_desc(h_desc_lower, pt)
                for pt in pattern_texts
            ) and not pattern_resolved

            # Check conversation content for change signals
            # Normalise smart-quotes so "didn’t help" matches the keyword "didn't help"
            conv_texts = _normalise(
                ' '.join(m.get('content', '') for m in new_conversations[-10:])
            ).lower()
            pos_count = sum(1 for s in positive_signals if _wm(conv_texts, s))
            neg_count = sum(1 for s in negative_signals if _wm(conv_texts, s))

            # Update confidence
            _MAX_EVIDENCE = 20  # cap to prevent unbounded growth across cycles
            _PASSIVE_DECAY = 0.02  # applied per cycle when no conversation data exists
            if not new_conversations:
                # User went silent this cycle — apply a small passive decay so stale
                # high-confidence hypotheses don't persist indefinitely without evidence.
                h.confidence = max(0.0, h.confidence - _PASSIVE_DECAY)
            if score_improved or pattern_resolved or pos_count > neg_count:
                h.confidence = min(1.0, h.confidence + 0.15)
                h.evidence_for.append(
                    f"[{datetime.now().strftime('%Y-%m-%d')}] "
                    f"score +{new_wisdom_score - prev_wisdom_score:.0f}, "
                    f"positive signals: {pos_count}"
                )
                if len(h.evidence_for) > _MAX_EVIDENCE:
                    h.evidence_for = h.evidence_for[-_MAX_EVIDENCE:]
            elif score_declined or (pattern_persists and h.cycles_tested > 2) or neg_count > pos_count:
                h.confidence = max(0.0, h.confidence - 0.15)
                h.evidence_against.append(
                    f"[{datetime.now().strftime('%Y-%m-%d')}] "
                    f"pattern persists after {h.cycles_tested} cycles, "
                    f"negative signals: {neg_count}"
                )
                if len(h.evidence_against) > _MAX_EVIDENCE:
                    h.evidence_against = h.evidence_against[-_MAX_EVIDENCE:]

            # Judge after minimum cycles
            if h.cycles_tested >= self.MIN_CYCLES_TO_JUDGE:
                if h.confidence >= self.CONFIRM_THRESHOLD:
                    h.status = 'confirmed'
                    notes.append(
                        f"CONFIRMED: '{h.school_of_thought}' model explains "
                        f"'{h.pattern_description[:60]}' (confidence: {h.confidence:.0%})"
                    )
                    self._log(f"  ✓ Confirmed: {h.id}")
                elif h.confidence <= self.REJECT_THRESHOLD:
                    h.status = 'rejected'
                    # Suggest next school dynamically from knowledge base
                    # Pass all schools tried for this pattern so rotation avoids repeating them
                    h_desc_norm = h.pattern_description.lower()
                    tried_for_pattern = [
                        x.school_of_thought for x in hypotheses
                        if x.pattern_description.lower() == h_desc_norm
                    ]
                    h.revised_to_school = get_next_school(
                        h.school_of_thought, tried_for_pattern
                    )
                    notes.append(
                        f"REJECTED: '{h.school_of_thought}' model did NOT explain "
                        f"'{h.pattern_description[:60]}'. "
                        f"Try '{h.revised_to_school}' interpretation instead."
                    )
                    self._log(f"  ✗ Rejected: {h.id} → try {h.revised_to_school}")
                else:
                    notes.append(
                        f"STILL TESTING: '{h.school_of_thought}' for "
                        f"'{h.pattern_description[:60]}' — "
                        f"inconclusive after {h.cycles_tested} cycles "
                        f"(confidence: {h.confidence:.0%})"
                    )

        return hypotheses, notes

    def get_active_hypotheses_summary(self, hypotheses: List[Hypothesis]) -> str:
        """Build a summary string for the AI prompt.
        Only includes active (non-terminal) hypotheses in detail to keep prompt size bounded.
        Confirmed/rejected are summarised as counts to preserve context.
        """
        if not hypotheses:
            return "No prior hypotheses. Form new ones based on the data."

        active = [h for h in hypotheses if h.status in ('testing', 'proposed', 'revised')]
        confirmed = [h for h in hypotheses if h.status == 'confirmed']
        rejected  = [h for h in hypotheses if h.status == 'rejected']

        lines = ["ACTIVE HYPOTHESES (being tested across cycles):"]
        for h in active:
            status_icon = {'testing': '⟳', 'proposed': '?', 'revised': '↻'}.get(h.status, '?')
            lines.append(
                f"  {status_icon} [{h.school_of_thought}] "
                f"'{h.pattern_description[:70]}' — "
                f"status: {h.status}, confidence: {h.confidence:.0%}, "
                f"cycles: {h.cycles_tested}"
            )
            if h.evidence_for:
                lines.append(f"    Evidence for: {h.evidence_for[-1]}")
            if h.evidence_against:
                lines.append(f"    Evidence against: {h.evidence_against[-1]}")

        if confirmed:
            lines.append(f"CONFIRMED SCHOOLS ({len(confirmed)}): " +
                         ', '.join(f"'{h.school_of_thought}' for '{h.pattern_description[:40]}'" for h in confirmed))
        if rejected:
            lines.append(f"REJECTED SCHOOLS ({len(rejected)}) — do NOT reuse: " +
                         ', '.join(f"'{h.school_of_thought}' (try '{h.revised_to_school}')" for h in rejected))

        return "\n".join(lines)

    def get_rejected_schools(self, hypotheses: List[Hypothesis], pattern_desc: str) -> List[str]:
        """
        Return schools already tried (rejected or confirmed) for a given pattern.
        Used by the knowledge base rotation to skip already-tested interpretations.
        """
        pattern_desc_lower = pattern_desc.lower()

        def _wm_pattern(needle: str, haystack: str) -> bool:
            """Word-boundary match to avoid short pattern names matching inside longer ones."""
            if ' ' in needle:
                return needle in haystack
            return bool(re.search(r'\b' + re.escape(needle) + r'\b', haystack))

        return [
            h.school_of_thought for h in hypotheses
            if h.status in ('rejected', 'confirmed') and
            _wm_pattern(pattern_desc_lower, h.pattern_description.lower())
        ]

    def suggest_next_school_for_pattern(
        self, hypotheses: List[Hypothesis], pattern_desc: str, current_school: str
    ) -> str:
        """
        Suggest the next school to try for a pattern, skipping all previously tried ones.
        Delegates entirely to the knowledge base — no hardcoded logic here.
        """
        tried = self.get_rejected_schools(hypotheses, pattern_desc)
        return get_next_school(current_school, tried)


if __name__ == '__main__':
    engine = HypothesisEngine()
    print("Hypothesis Engine ready.")

    # Demo
    h = engine.propose(
        user_id='23',
        pattern_id='avoidance_of_discomfort',
        pattern_description='Avoids discussing health problems',
        school_of_thought='CBT / Psychology',
        hypothesis_text='The avoidance is anxiety-driven and will respond to graded exposure.',
        predicted_change='User begins proactively mentioning health topics within 3 cycles.',
        nudge_given='Use graded exposure: start with the least threatening health topic first.',
    )
    print(f"Proposed: {h.id} — status: {h.status}")
