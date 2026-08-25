"""
Tests for the Gentle Companion (Sam) stack.

Covers:
- Memory module: extraction patterns, save/load, format-for-prompt
- Character factory: creates GentleCompanionChatbot correctly
- Chatbot: builds a prompt without coaching language, includes memory
- Template: renders via Jinja2 without errors

Run from repo root:
    python -m pytest tests/test_gentle_companion.py -v
or:
    python tests/test_gentle_companion.py
"""
import os
import sys
import json
import shutil
import tempfile
from pathlib import Path

# Make sure we can import the project
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# ──────────────────────────────────────────────────────────────────────────
# Memory module tests
# ──────────────────────────────────────────────────────────────────────────

def test_memory_extracts_meaningful_sentences(tmp_notes_dir):
    from ai_compare import gentle_companion_memory as mem

    user_id = "test_user_meaningful"
    msg = (
        "I'm feeling really overwhelmed with work lately. "
        "I want to call my mum more often. "
        "The weather is nice today."  # should NOT be saved
    )
    added = mem.maybe_extract_and_save(user_id, msg)
    assert added >= 2, f"Expected >=2 notes, got {added}"

    notes = mem.get_recent_notes(user_id)
    texts = [n["text"].lower() for n in notes]
    assert any("overwhelmed" in t for t in texts), "Feeling sentence not captured"
    assert any("want to call my mum" in t for t in texts), "Aspiration not captured"
    assert not any("weather is nice" in t for t in texts), "Trivial sentence wrongly captured"


def test_memory_dedups_identical_sentences(tmp_notes_dir):
    from ai_compare import gentle_companion_memory as mem

    user_id = "test_user_dedup"
    msg = "I feel anxious about tomorrow."
    mem.maybe_extract_and_save(user_id, msg)
    mem.maybe_extract_and_save(user_id, msg)  # same again
    notes = mem.get_recent_notes(user_id)
    matches = [n for n in notes if "anxious about tomorrow" in n["text"].lower()]
    assert len(matches) == 1, f"Dedup failed: got {len(matches)} copies"


def test_memory_caps_at_three_per_turn(tmp_notes_dir):
    from ai_compare import gentle_companion_memory as mem

    user_id = "test_user_cap"
    msg = (
        "I feel tired. I want to rest. I hope things improve. "
        "I'm worried about money. I tried meditation. I started yoga."
    )
    added = mem.maybe_extract_and_save(user_id, msg)
    assert added <= 3, f"Per-turn cap broken: added {added}"


def test_memory_format_for_prompt_empty(tmp_notes_dir):
    from ai_compare import gentle_companion_memory as mem
    block = mem.format_notes_for_prompt("nonexistent_user_xyz")
    assert block == "", "Empty memory should produce empty block"


def test_memory_format_for_prompt_has_soft_framing(tmp_notes_dir):
    from ai_compare import gentle_companion_memory as mem

    user_id = "test_user_format"
    mem.maybe_extract_and_save(user_id, "I want to learn piano.")
    block = mem.format_notes_for_prompt(user_id)
    assert "want to learn piano" in block.lower()
    # Soft framing must be present so Sam doesn't pounce on memories
    assert "don't bring these up unless" in block.lower()


def test_memory_clear_notes(tmp_notes_dir):
    from ai_compare import gentle_companion_memory as mem

    user_id = "test_user_clear"
    mem.maybe_extract_and_save(user_id, "I feel hopeful today.")
    assert len(mem.get_recent_notes(user_id)) >= 1
    assert mem.clear_notes(user_id) is True
    assert mem.get_recent_notes(user_id) == []


def test_memory_handles_empty_input(tmp_notes_dir):
    from ai_compare import gentle_companion_memory as mem
    # None / empty should be safe
    assert mem.maybe_extract_and_save(None, "I feel ok") == 0
    assert mem.maybe_extract_and_save("u1", "") == 0
    assert mem.maybe_extract_and_save("u1", None) == 0


def test_memory_truncates_very_long_sentences(tmp_notes_dir):
    from ai_compare import gentle_companion_memory as mem

    user_id = "test_user_long"
    long_sentence = "I feel " + ("really " * 100) + "tired."
    mem.maybe_extract_and_save(user_id, long_sentence)
    notes = mem.get_recent_notes(user_id)
    if notes:
        for n in notes:
            assert len(n["text"]) <= mem._MAX_NOTE_CHARS + 5  # allow ellipsis


# ──────────────────────────────────────────────────────────────────────────
# Privacy: forget-intent tests
# ──────────────────────────────────────────────────────────────────────────

def test_detect_forget_all(tmp_notes_dir):
    from ai_compare import gentle_companion_memory as mem
    cases = [
        "please forget everything",
        "forget all of what I said",
        "wipe your memory",
        "reset your memory",
        "clear your memory",
    ]
    for c in cases:
        intent = mem.detect_forget_intent(c)
        assert intent and intent["kind"] == "all", f"Missed forget-all: {c!r}"


def test_detect_forget_topic(tmp_notes_dir):
    from ai_compare import gentle_companion_memory as mem
    intent = mem.detect_forget_intent("Please forget what I said about my boss.")
    assert intent and intent["kind"] == "topic"
    assert "boss" in intent["topic"].lower()


def test_detect_forget_no_intent(tmp_notes_dir):
    from ai_compare import gentle_companion_memory as mem
    assert mem.detect_forget_intent("how are you today?") is None
    assert mem.detect_forget_intent("") is None


def test_forget_about_removes_matching_notes(tmp_notes_dir):
    from ai_compare import gentle_companion_memory as mem
    user_id = "test_forget_topic"
    mem.maybe_extract_and_save(user_id, "I'm worried about my boss's reaction.")
    mem.maybe_extract_and_save(user_id, "I want to learn piano.")
    assert len(mem.get_recent_notes(user_id)) == 2
    removed = mem.forget_about(user_id, "boss")
    assert removed == 1
    remaining = mem.get_recent_notes(user_id)
    assert len(remaining) == 1
    assert "piano" in remaining[0]["text"].lower()


def test_apply_forget_intent_all(tmp_notes_dir):
    from ai_compare import gentle_companion_memory as mem
    user_id = "test_apply_forget_all"
    mem.maybe_extract_and_save(user_id, "I feel anxious about money.")
    result = mem.apply_forget_intent(user_id, "please forget everything")
    assert result and result["kind"] == "all"
    assert mem.get_recent_notes(user_id) == []


def test_apply_forget_intent_topic(tmp_notes_dir):
    from ai_compare import gentle_companion_memory as mem
    user_id = "test_apply_forget_topic"
    mem.maybe_extract_and_save(user_id, "I'm scared about the surgery next week.")
    result = mem.apply_forget_intent(user_id, "forget what I said about the surgery")
    assert result and result["kind"] == "topic"
    assert result.get("removed", 0) >= 1


# ──────────────────────────────────────────────────────────────────────────
# Time-decay tests
# ──────────────────────────────────────────────────────────────────────────

def test_old_notes_are_pruned_on_load(tmp_notes_dir):
    """Notes older than the TTL must be silently dropped at load time."""
    from ai_compare import gentle_companion_memory as mem
    import json
    from datetime import datetime, timedelta, timezone

    user_id = "test_decay"
    p = mem._notes_path(user_id)
    old_iso = (datetime.now(timezone.utc) - timedelta(days=mem._NOTE_TTL_DAYS + 30)).isoformat()
    fresh_iso = datetime.now(timezone.utc).isoformat()
    with p.open("w", encoding="utf-8") as f:
        json.dump([
            {"text": "I felt sad two years ago.", "at": old_iso},
            {"text": "I feel hopeful today.", "at": fresh_iso},
        ], f)

    notes = mem.get_recent_notes(user_id)
    texts = [n["text"] for n in notes]
    assert "I feel hopeful today." in texts
    assert "I felt sad two years ago." not in texts


# ──────────────────────────────────────────────────────────────────────────
# Relevance scoring tests
# ──────────────────────────────────────────────────────────────────────────

def test_relevance_prefers_topic_overlap(tmp_notes_dir):
    """When the current message mentions a topic, related older notes
    should rank ahead of unrelated newer ones."""
    from ai_compare import gentle_companion_memory as mem
    import json
    from datetime import datetime, timedelta, timezone

    user_id = "test_relevance"
    p = mem._notes_path(user_id)
    old_iso = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
    new_iso = datetime.now(timezone.utc).isoformat()
    with p.open("w", encoding="utf-8") as f:
        json.dump([
            {"text": "I want to start running again.", "at": old_iso},
            {"text": "I tried that new coffee place yesterday.", "at": new_iso},
        ], f)

    relevant = mem.get_relevant_notes(user_id, "I went for a run today", limit=1)
    assert len(relevant) == 1
    assert "running" in relevant[0]["text"].lower()


def test_relevance_falls_back_to_recency_when_no_message(tmp_notes_dir):
    from ai_compare import gentle_companion_memory as mem
    user_id = "test_relevance_fallback"
    mem.maybe_extract_and_save(user_id, "I feel restless lately.")
    notes = mem.get_relevant_notes(user_id, "", limit=4)
    assert len(notes) >= 1
    assert "restless" in notes[0]["text"].lower()


def test_format_notes_uses_relevance_when_message_given(tmp_notes_dir):
    from ai_compare import gentle_companion_memory as mem
    user_id = "test_format_relevance"
    mem.maybe_extract_and_save(user_id, "I'm worried about the exam.")
    mem.maybe_extract_and_save(user_id, "I want to call my mum more often.")
    block = mem.format_notes_for_prompt(
        user_id, limit=1, current_message="thinking about the exam tomorrow"
    )
    assert "exam" in block.lower()
    assert "mum" not in block.lower()


# ──────────────────────────────────────────────────────────────────────────
# Regression: chat() signature must accept user_id (Dec 2024 / Apr 2026 bug)
# ──────────────────────────────────────────────────────────────────────────

def test_chat_signature_accepts_user_id(tmp_notes_dir):
    """Routes call bot.chat(..., user_id=user_id). The whole inheritance
    chain must accept this kwarg or chat fails with TypeError and the
    user sees a misleading 'temporary AI issue' message.

    This test guards against silent regressions in:
    - BaseChatbot.chat
    - Chatbot.chat
    - BaseEnhancedChatbot.chat
    - GentleCompanionChatbot (inherited)
    """
    import inspect
    from ai_compare.base_chatbot import BaseChatbot
    from ai_compare.chatbot import AIChatbot
    from ai_compare.base_enhanced_chatbot import BaseEnhancedChatbot
    from ai_compare.gentle_companion_chatbot import GentleCompanionChatbot

    for cls in (BaseChatbot, AIChatbot, BaseEnhancedChatbot, GentleCompanionChatbot):
        sig = inspect.signature(cls.chat)
        assert "user_id" in sig.parameters, (
            f"{cls.__name__}.chat() is missing the 'user_id' parameter. "
            f"This will surface to users as a fake 'temporary AI issue' message."
        )


# ──────────────────────────────────────────────────────────────────────────
# Chatbot integration: forget directive
# ──────────────────────────────────────────────────────────────────────────

def test_prompt_includes_forget_directive_on_intent(tmp_notes_dir):
    """When user says 'forget everything', the prompt should contain a
    directive to acknowledge gently — and NOT include past memory."""
    from ai_compare import gentle_companion_memory as mem
    from ai_compare.character_factory import CharacterFactory

    user_id = "test_forget_prompt"
    mem.maybe_extract_and_save(user_id, "I'm worried about money.")

    bot = CharacterFactory.create_character("gentle_companion")
    prompt = bot._build_enhanced_prompt(
        user_message="please forget everything",
        include_context=False,
        user_id=user_id,
    )
    assert "Note for you, Sam" in prompt
    assert "forget" in prompt.lower()
    # Memory must NOT be injected this turn
    assert "worried about money" not in prompt.lower()


# ──────────────────────────────────────────────────────────────────────────
# Factory tests
# ──────────────────────────────────────────────────────────────────────────

def test_factory_creates_gentle_companion():
    from ai_compare.character_factory import CharacterFactory
    from ai_compare.gentle_companion_chatbot import GentleCompanionChatbot

    bot = CharacterFactory.create_character("gentle_companion")
    assert isinstance(bot, GentleCompanionChatbot)
    assert bot.character_id == "gentle_companion"
    assert bot.display_name == "Sam"


def test_factory_lists_gentle_companion():
    from ai_compare.character_factory import CharacterFactory
    ids = CharacterFactory.get_all_character_ids()
    assert "gentle_companion" in ids


def test_factory_get_character_info():
    from ai_compare.character_factory import CharacterFactory
    info = CharacterFactory.get_character_info("gentle_companion")
    assert info["display_name"] == "Sam"
    assert info["tagline"]
    assert "primary_color" in info["theme"]


# ──────────────────────────────────────────────────────────────────────────
# Prompt build tests (the core behavioural contract)
# ──────────────────────────────────────────────────────────────────────────

def test_prompt_omits_coaching_rules(tmp_notes_dir):
    """Sam's prompt must NOT contain the base 'BE SPECIFIC / NO FILLER' rules."""
    from ai_compare.character_factory import CharacterFactory

    bot = CharacterFactory.create_character("gentle_companion")
    prompt = bot._build_enhanced_prompt(
        user_message="I've been feeling stuck lately.",
        include_context=False,
        user_id="test_user_prompt",
    )
    forbidden = [
        "BE SPECIFIC",
        "NO FILLER",
        "ASK ONE specific question",
        "Skip greetings",
    ]
    for f in forbidden:
        assert f not in prompt, f"Coaching rule leaked into Sam's prompt: {f!r}"


def test_prompt_contains_persona_anchors(tmp_notes_dir):
    from ai_compare.character_factory import CharacterFactory
    bot = CharacterFactory.create_character("gentle_companion")
    prompt = bot._build_enhanced_prompt(
        user_message="hi",
        include_context=False,
        user_id="test_user_persona",
    )
    # Key persona markers
    assert "Sam" in prompt
    assert "warm" in prompt.lower()
    assert "no lists" in prompt.lower() or "no bullet" in prompt.lower()


def test_prompt_includes_memory_when_present(tmp_notes_dir):
    from ai_compare import gentle_companion_memory as mem
    from ai_compare.character_factory import CharacterFactory

    user_id = "test_user_memory_in_prompt"
    mem.maybe_extract_and_save(user_id, "I want to start running again.")

    bot = CharacterFactory.create_character("gentle_companion")
    prompt = bot._build_enhanced_prompt(
        user_message="hey",
        include_context=False,
        user_id=user_id,
    )
    assert "want to start running" in prompt.lower(), \
        "Stored memory not injected into prompt"


def test_prompt_is_safe_with_no_user_id(tmp_notes_dir):
    """When user_id is None (e.g. anonymous), prompt build must still succeed."""
    from ai_compare.character_factory import CharacterFactory
    bot = CharacterFactory.create_character("gentle_companion")
    prompt = bot._build_enhanced_prompt(
        user_message="just venting",
        include_context=False,
        user_id=None,
    )
    assert isinstance(prompt, str) and len(prompt) > 100


# ──────────────────────────────────────────────────────────────────────────
# Template render test
# ──────────────────────────────────────────────────────────────────────────

def test_template_renders_without_errors():
    """Make sure templates/gentle_companion.html is valid Jinja and uses
    only fields we provide in character info."""
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    tpl_dir = ROOT / "templates"
    env = Environment(
        loader=FileSystemLoader(str(tpl_dir)),
        autoescape=select_autoescape(["html"]),
    )
    # Stub url_for since Flask isn't running
    env.globals["url_for"] = lambda *a, **kw: "#stub"

    tpl = env.get_template("gentle_companion.html")

    from ai_compare.character_factory import CharacterFactory
    info = CharacterFactory.get_character_info("gentle_companion")

    html = tpl.render(character=info, character_id="gentle_companion")
    assert "<html" in html.lower()
    assert "Sam" in html
    assert "A friendly ear" in html
    # No sidebar/counter remnants
    assert "messageCount" not in html
    assert "Quick Topics" not in html


# ──────────────────────────────────────────────────────────────────────────
# pytest fixture / standalone runner
# ──────────────────────────────────────────────────────────────────────────

try:
    import pytest

    @pytest.fixture
    def tmp_notes_dir(monkeypatch, tmp_path):
        """Redirect companion_notes/ to a temp dir for each test."""
        from ai_compare import gentle_companion_memory as mem
        monkeypatch.setattr(mem, "_NOTES_DIR", tmp_path)
        yield tmp_path

except ImportError:
    pytest = None


def _run_standalone():
    """Lightweight runner if pytest isn't available."""
    print("Running gentle_companion tests (standalone mode)...\n")
    from ai_compare import gentle_companion_memory as mem

    # Use a temp directory for notes
    tmp = Path(tempfile.mkdtemp(prefix="companion_test_"))
    original_dir = mem._NOTES_DIR
    mem._NOTES_DIR = tmp

    test_funcs = [
        (test_memory_extracts_meaningful_sentences, "memory: extracts meaningful sentences"),
        (test_memory_dedups_identical_sentences, "memory: dedup"),
        (test_memory_caps_at_three_per_turn, "memory: per-turn cap"),
        (test_memory_format_for_prompt_empty, "memory: empty format"),
        (test_memory_format_for_prompt_has_soft_framing, "memory: soft framing"),
        (test_memory_clear_notes, "memory: clear"),
        (test_memory_handles_empty_input, "memory: empty input"),
        (test_memory_truncates_very_long_sentences, "memory: long sentence truncation"),
        (test_detect_forget_all, "privacy: detect forget-all phrasings"),
        (test_detect_forget_topic, "privacy: detect forget-topic phrasing"),
        (test_detect_forget_no_intent, "privacy: no false positives"),
        (test_forget_about_removes_matching_notes, "privacy: forget by topic removes notes"),
        (test_apply_forget_intent_all, "privacy: apply forget-all"),
        (test_apply_forget_intent_topic, "privacy: apply forget-topic"),
        (test_old_notes_are_pruned_on_load, "decay: TTL prunes old notes"),
        (test_relevance_prefers_topic_overlap, "recall: relevance beats raw recency"),
        (test_relevance_falls_back_to_recency_when_no_message, "recall: falls back to recency"),
        (test_format_notes_uses_relevance_when_message_given, "recall: format uses relevance"),
        (test_chat_signature_accepts_user_id, "regression: chat() accepts user_id kwarg"),
        (test_prompt_includes_forget_directive_on_intent, "prompt: forget directive injected"),
        (test_factory_creates_gentle_companion, "factory: creates Sam"),
        (test_factory_lists_gentle_companion, "factory: registry contains"),
        (test_factory_get_character_info, "factory: character info"),
        (test_prompt_omits_coaching_rules, "prompt: no coaching rules"),
        (test_prompt_contains_persona_anchors, "prompt: persona anchors"),
        (test_prompt_includes_memory_when_present, "prompt: memory injected"),
        (test_prompt_is_safe_with_no_user_id, "prompt: safe with None user_id"),
        (test_template_renders_without_errors, "template: renders"),
    ]

    passed, failed = 0, 0
    for fn, label in test_funcs:
        try:
            # Pass tmp dir for tests that take it
            if "tmp_notes_dir" in fn.__code__.co_varnames:
                fn(tmp)
            else:
                fn()
            print(f"  PASS  {label}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {label}\n        {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR {label}\n        {type(e).__name__}: {e}")
            failed += 1

    mem._NOTES_DIR = original_dir
    shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(_run_standalone())
