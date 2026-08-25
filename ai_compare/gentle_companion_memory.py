"""
Gentle Companion Memory - silent theme tracking for Sam.

Sam quietly keeps a small journal of things the user has mentioned —
worries, hopes, attempts, feelings, people, events. These notes are
stored per-user as JSON and injected into Sam's prompt so references
feel natural and organic ("you mentioned X a while back...").

Design goals:
- Invisible to the user: never shown in UI, never labeled as "tracking"
- Cheap: regex-based extraction, no extra LLM calls
- Bounded: keeps only the most recent N notes per user
- Private-feeling: plain JSON per user, easy to inspect/delete
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional

# Store notes next to the app, in a gitignore-friendly folder
_NOTES_DIR = Path(__file__).resolve().parent.parent / "companion_notes"
_NOTES_DIR.mkdir(exist_ok=True)

# Cap notes per user so the file stays small and the prompt stays clean
_MAX_NOTES_PER_USER = 60
_MAX_NOTE_CHARS = 240
# Notes older than this are auto-pruned at save/read time
_NOTE_TTL_DAYS = 180
# Common English stop-words excluded from keyword overlap scoring
_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "if", "of", "to", "in", "on", "at",
    "for", "with", "by", "is", "am", "are", "was", "were", "be", "been",
    "being", "do", "does", "did", "have", "has", "had", "i", "you", "me",
    "my", "your", "we", "our", "they", "them", "their", "it", "its", "this",
    "that", "these", "those", "so", "just", "very", "really", "about",
    "like", "feel", "feeling", "felt", "think", "thought", "want", "wants",
    "would", "could", "should", "can", "will", "not", "no", "yes", "some",
    "any", "more", "less", "too", "as", "from", "out", "up", "down", "now",
    "then", "there", "here", "who", "what", "when", "why", "how",
})

# Patterns that suggest a sentence is worth quietly remembering.
# Deliberately conservative — we'd rather miss a theme than clutter memory.
_MEANINGFUL_PATTERNS = [
    # Feelings
    r"\bi (?:feel|am feeling|felt|'m feeling)\b",
    r"\bi'?m (?:so |really |kind of |a bit |quite )?(?:tired|sad|anxious|angry|stressed|lonely|lost|stuck|happy|excited|scared|worried|overwhelmed|frustrated|grateful|proud)\b",
    # Aspirations / intentions
    r"\bi (?:want|wish|hope|'d like|would like|plan|planning)\b",
    r"\bi'?m (?:trying|hoping|thinking about|considering)\b",
    # Worries
    r"\bi'?m (?:worried|scared|afraid|nervous) (?:about|of|that)\b",
    r"\bi (?:don't|do not) (?:know|understand) (?:what|how|why|if|whether)\b",
    # Actions taken / experiences
    r"\bi (?:tried|decided|started|finished|quit|stopped|managed to|realized|noticed)\b",
    # Relationships / mentions of specific people
    r"\bmy (?:mom|mum|dad|father|mother|partner|wife|husband|boyfriend|girlfriend|boss|friend|son|daughter|kid|sister|brother|therapist|team)\b",
    # Heavy / weighted
    r"\b(?:been struggling|can't stop|keep thinking|keep feeling|every day|lately|recently)\b",
]
_MEANINGFUL_RE = re.compile("|".join(_MEANINGFUL_PATTERNS), re.IGNORECASE)

# Sentence splitter — crude but good enough
_SENT_SPLIT_RE = re.compile(r"(?<=[\.\!\?])\s+")

# Patterns that indicate the user wants Sam to forget EVERYTHING.
# These must be unambiguous — anything that could include a topic
# ("forget what I said about X") is handled by the topic regex first.
_FORGET_ALL_RE = re.compile(
    r"\b(?:forget everything|wipe (?:your |my )?memory|reset (?:your |my )?memory|"
    r"clear (?:your |my )?memory|forget all|forget it all|please forget everything)\b",
    re.IGNORECASE,
)
_FORGET_TOPIC_RE = re.compile(
    r"\b(?:forget|drop|let go of|don'?t remember)\s+"
    r"(?:what i (?:said|told you|mentioned)\s+)?"
    r"(?:about\s+)?(.{2,80}?)(?:[\.\!\?,]|$)",
    re.IGNORECASE,
)


def _notes_path(user_id) -> Path:
    safe = str(user_id).replace(os.sep, "_").replace("/", "_")
    return _NOTES_DIR / f"user_{safe}.json"


def _load_notes(user_id, prune_expired: bool = True) -> List[Dict]:
    p = _notes_path(user_id)
    if not p.exists():
        return []
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        if prune_expired:
            cutoff = datetime.now(timezone.utc).timestamp() - _NOTE_TTL_DAYS * 86400
            kept = []
            for n in data:
                at = n.get("at")
                try:
                    t = datetime.fromisoformat(at) if at else None
                    if t and t.tzinfo is None:
                        t = t.replace(tzinfo=timezone.utc)
                    if not t or t.timestamp() >= cutoff:
                        kept.append(n)
                except Exception:
                    kept.append(n)  # keep on parse error
            # If pruning changed anything, persist quietly
            if len(kept) != len(data):
                try:
                    with p.open("w", encoding="utf-8") as f:
                        json.dump(kept, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
            return kept
        return data
    except Exception:
        return []


def _save_notes(user_id, notes: List[Dict]) -> None:
    p = _notes_path(user_id)
    # Keep only the most recent N
    trimmed = notes[-_MAX_NOTES_PER_USER:]
    try:
        with p.open("w", encoding="utf-8") as f:
            json.dump(trimmed, f, ensure_ascii=False, indent=2)
    except Exception:
        pass  # Memory is best-effort; never break the chat flow


def _looks_meaningful(sentence: str) -> bool:
    """Should Sam quietly remember this sentence?"""
    s = sentence.strip()
    if not s:
        return False
    # Word count sanity check
    word_count = len(s.split())
    if word_count < 4 or word_count > 40:
        return False
    return bool(_MEANINGFUL_RE.search(s))


def maybe_extract_and_save(user_id, user_message: str) -> int:
    """
    Look at the user's message; quietly save any sentences that seem worth
    remembering. Returns the number of notes added.

    Called once per user turn. Silent — never raises.
    """
    if not user_id or not user_message:
        return 0

    try:
        notes = _load_notes(user_id)
        existing_texts = {n.get("text", "").strip().lower() for n in notes}

        sentences = _SENT_SPLIT_RE.split(user_message.strip())
        added = 0
        now_iso = datetime.now(timezone.utc).isoformat()

        for sent in sentences:
            sent_clean = sent.strip()
            if len(sent_clean) > _MAX_NOTE_CHARS:
                sent_clean = sent_clean[:_MAX_NOTE_CHARS].rstrip() + "…"
            if not _looks_meaningful(sent_clean):
                continue
            key = sent_clean.lower()
            if key in existing_texts:
                continue  # Dedup
            notes.append({"text": sent_clean, "at": now_iso})
            existing_texts.add(key)
            added += 1
            if added >= 3:  # Max 3 new notes per turn to stay quiet
                break

        if added:
            _save_notes(user_id, notes)
        return added
    except Exception:
        return 0


def get_recent_notes(user_id, limit: int = 8) -> List[Dict]:
    """Return the most recent notes (newest last) for prompt injection."""
    if not user_id:
        return []
    notes = _load_notes(user_id)
    return notes[-limit:]


_WORD_RE = re.compile(r"[a-zA-Z']{2,}")


def _stem(word: str) -> str:
    """Tiny suffix-stripping stemmer. Good enough to make 'run' match
    'running' and 'worried' match 'worry'."""
    w = word.lower()
    # Apply in order, longest suffix first
    for suf in ("ying", "ies", "ied"):
        if w.endswith(suf) and len(w) > len(suf) + 1:
            return w[:-len(suf)] + "y"
    for suf in ("ing", "ed", "es"):
        if w.endswith(suf) and len(w) > len(suf) + 2:
            base = w[:-len(suf)]
            # Drop one trailing duplicate consonant (running -> run)
            if len(base) >= 2 and base[-1] == base[-2] and base[-1] not in "aeiou":
                base = base[:-1]
            return base
    if w.endswith("s") and len(w) > 3 and not w.endswith("ss"):
        return w[:-1]
    return w


def _tokenize(text: str) -> set:
    """Lowercase content-word set, stop-words removed, lightly stemmed.
    Strips possessives (boss's → boss) and trailing apostrophes."""
    out = set()
    for w in _WORD_RE.findall(text or ""):
        lw = w.lower()
        # Strip possessive 's and any trailing apostrophe
        if lw.endswith("'s"):
            lw = lw[:-2]
        lw = lw.strip("'")
        if not lw or lw in _STOPWORDS:
            continue
        out.add(_stem(lw))
    return out


def _score_note(note: Dict, query_tokens: set, now_ts: float) -> float:
    """Score a note for relevance + recency.

    Returns a float; higher is better.
    - Recency: gentle exponential decay over ~30 days
    - Overlap: count of shared content words with the current message
    """
    text = note.get("text", "")
    note_tokens = _tokenize(text)
    overlap = len(query_tokens & note_tokens) if query_tokens else 0

    # Age decay
    age_days = 0.0
    at = note.get("at")
    if at:
        try:
            t = datetime.fromisoformat(at)
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            age_days = max(0.0, (now_ts - t.timestamp()) / 86400.0)
        except Exception:
            age_days = 0.0
    # Weight: recent notes always have base score; overlap boosts older notes too
    recency_weight = 1.0 / (1.0 + age_days / 30.0)  # 1.0 today, 0.5 at 30d, ~0.14 at 180d
    return overlap * 2.0 + recency_weight


def get_relevant_notes(user_id, current_message: str = "", limit: int = 6) -> List[Dict]:
    """Return notes most relevant to the current message, blended with recency.

    When ``current_message`` is empty (e.g. session start), falls back to
    plain recency.
    """
    if not user_id:
        return []
    notes = _load_notes(user_id)
    if not notes:
        return []
    if not current_message.strip():
        return notes[-limit:]
    query_tokens = _tokenize(current_message)
    now_ts = datetime.now(timezone.utc).timestamp()
    scored = sorted(
        notes,
        key=lambda n: _score_note(n, query_tokens, now_ts),
        reverse=True,
    )
    top = scored[:limit]
    # Re-sort chronologically so the prompt reads in time order
    top.sort(key=lambda n: n.get("at") or "")
    return top


def format_notes_for_prompt(user_id, limit: int = 8, current_message: str = "") -> str:
    """
    Build a soft, non-prescriptive memory block for Sam's prompt.
    Returns an empty string when there's nothing to share.

    When ``current_message`` is provided, picks notes by relevance + recency;
    otherwise just returns the most recent notes.
    """
    if current_message:
        notes = get_relevant_notes(user_id, current_message, limit=limit)
    else:
        notes = get_recent_notes(user_id, limit=limit)
    if not notes:
        return ""

    lines = []
    for n in notes:
        text = n.get("text", "").strip()
        if not text:
            continue
        # Relative time hint (rough, friendly)
        when = _relative_time(n.get("at"))
        if when:
            lines.append(f"- ({when}) {text}")
        else:
            lines.append(f"- {text}")

    if not lines:
        return ""

    return (
        "\nThings this person has mentioned to you in past conversations "
        "(don't bring these up unless it feels organic — this is just so "
        "you have continuity):\n" + "\n".join(lines) + "\n"
    )


def _relative_time(iso_str: Optional[str]) -> str:
    if not iso_str:
        return ""
    try:
        t = datetime.fromisoformat(iso_str)
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - t
        secs = delta.total_seconds()
        if secs < 60 * 60:
            return "just now"
        if secs < 60 * 60 * 24:
            return "earlier today"
        days = int(secs // (60 * 60 * 24))
        if days == 1:
            return "yesterday"
        if days < 7:
            return f"{days} days ago"
        if days < 30:
            weeks = days // 7
            return "a week ago" if weeks == 1 else f"{weeks} weeks ago"
        months = days // 30
        return "a month ago" if months == 1 else f"{months} months ago"
    except Exception:
        return ""


def clear_notes(user_id) -> bool:
    """Let the user wipe their companion memory if they ever want to."""
    p = _notes_path(user_id)
    try:
        if p.exists():
            p.unlink()
        return True
    except Exception:
        return False


def forget_about(user_id, topic: str) -> int:
    """Remove notes whose text overlaps the given topic.

    Match logic: any content-word from ``topic`` appearing in the note's text
    counts. Returns the number of notes removed.
    """
    if not user_id or not topic:
        return 0
    topic_tokens = _tokenize(topic)
    if not topic_tokens:
        return 0
    try:
        notes = _load_notes(user_id)
        if not notes:
            return 0
        kept = []
        removed = 0
        for n in notes:
            note_tokens = _tokenize(n.get("text", ""))
            if note_tokens & topic_tokens:
                removed += 1
            else:
                kept.append(n)
        if removed:
            _save_notes(user_id, kept)
        return removed
    except Exception:
        return 0


def detect_forget_intent(user_message: str) -> Optional[Dict[str, str]]:
    """Detect whether the user is asking Sam to forget something.

    Returns:
        ``None`` if no forget intent detected.
        ``{"kind": "all"}`` if the user wants to wipe everything.
        ``{"kind": "topic", "topic": "<phrase>"}`` for targeted forgetting.

    Forget-all is checked first: its phrases are unambiguous wipes.
    Topic check follows for targeted forgetting like "forget what I said
    about my boss".
    """
    if not user_message:
        return None
    if _FORGET_ALL_RE.search(user_message):
        return {"kind": "all"}
    # Bare "forget what I said" without a topic = wipe
    if re.search(
        r"\bforget what i (?:said|told you|mentioned)\s*(?:[\.\!\?]|$)",
        user_message, re.IGNORECASE,
    ):
        return {"kind": "all"}
    m = _FORGET_TOPIC_RE.search(user_message)
    if m:
        topic = m.group(1).strip().rstrip(".!?,")
        # Reject empty / pure stop-word topics so "forget it" doesn't capture "it"
        if topic and _tokenize(topic):
            return {"kind": "topic", "topic": topic}
    return None


def apply_forget_intent(user_id, user_message: str) -> Optional[Dict]:
    """Detect a forget intent and apply it. Returns a small dict describing
    what happened, or ``None`` if no intent was found.

    The chatbot can use the result to inject a brief acknowledgement into
    Sam's prompt.
    """
    intent = detect_forget_intent(user_message)
    if not intent:
        return None
    if intent["kind"] == "all":
        ok = clear_notes(user_id)
        return {"kind": "all", "ok": ok}
    topic = intent.get("topic", "")
    removed = forget_about(user_id, topic)
    return {"kind": "topic", "topic": topic, "removed": removed}
