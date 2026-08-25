# Live Testing Sam — A Quick Guide

This guide walks you through manually testing Sam (the gentle companion) end-to-end with a real AI provider, plus what to look for and how to tune it.

> All automated tests already pass: **27/27 unit + 4/4 smoke**. This document is for the *qualitative* review you need to do as a human.

---

## 1. Start the server

```powershell
python app.py
```

Wait for `=== Initializing All Characters ===` and confirm Sam shows up:
```
✓ Sam (gentle_companion) initialized
```

Open the app at the URL shown (typically `http://127.0.0.1:5050`) and log in.

## 2. Find Sam

From the main dashboard you should now see a **Sam** tile in the character grid:
- Soft blue gradient
- Description: *"Just a quiet space to talk. No agenda, no advice unless you ask. Sam listens."*
- Button reads **"Sit with Sam"** (intentionally not "Chat" or "Start session")

Click it. You should land on a quiet single-column page — no sidebar, no message counter, no "concepts" panels.

## 3. What to test

Use these prompts and watch for the listed signals.

### Test A — Tone check (most important)
> *"Hey, just wanted to say hi."*

**Look for:**
- Short reply (1–3 sentences)
- Warm, casual tone — like a friend, not a therapist or coach
- No bulleted lists, no headings, no "I'm here to help with X, Y, Z"
- No words like *goal, plan, framework, step, exercise, technique*

### Test B — Heavy emotion, no advice
> *"It's been a really rough week. Everything feels too much."*

**Look for:**
- Acknowledgement first ("yeah", "that sounds heavy", etc.) — not jumping to fix
- At most ONE gentle question, or none at all
- No "have you tried..." / "you should..." / "let's break this down"
- No upbeat closer like *"you've got this!"*

### Test C — Aspiration mention (silent memory check)
> *"I want to start running again. I miss it."*

After Sam replies, peek at the memory file:
```powershell
Get-Content companion_notes\user_<your_user_id>.json
```
You should see a note containing *"I want to start running again"* with a timestamp. **No UI** should mention this.

### Test D — Memory recall (the magic moment)
Wait a few minutes (or refresh the page), then send:
> *"I went for a quick jog this morning."*

**Look for:**
- Sam may naturally tie it back ("oh, you'd mentioned wanting to start running again — how did it feel?")
- It must feel **organic**, not "ACCORDING TO MY RECORDS YOU SAID..."
- If Sam doesn't bring it up, that's also fine — it's instructed not to unless it feels natural

### Test E — Privacy: forget a topic
> *"Forget what I said about running."*

**Look for:**
- Sam acknowledges briefly, warmly ("okay, let it go." / "done." / something soft)
- Does NOT lecture or repeat the topic
- Check `companion_notes/user_<id>.json` — running-related notes should be gone

### Test F — Privacy: forget everything
> *"Wipe your memory please."*

**Look for:**
- Brief warm acknowledgement
- The notes file should now be empty or deleted

### Test G — Direct request for advice (escape hatch)
> *"Honestly, I'd love your opinion — what do you think I should do?"*

**Look for:**
- Sam softens into a tentative opinion ("for what it's worth, I wonder if...")
- Still doesn't switch into a list or numbered steps
- Holds the suggestion lightly ("but you know your situation better than me")

---

## 4. What to watch out for (failure modes)

| Symptom | Likely cause | Fix |
|---|---|---|
| Sam uses bullet lists or numbered steps | LLM ignored the "no lists" instruction | Strengthen `GENTLE_COMPANION_PERSONA` in `ai_compare/gentle_companion_chatbot.py`; consider model swap |
| Sam says "What's your goal?" / "Let's plan..." | Coaching language slipping through | Add the offending phrase to the forbidden list in the persona |
| Memory captures trivia ("the weather is nice") | Pattern too loose | Tighten `_MEANINGFUL_PATTERNS` in `ai_compare/gentle_companion_memory.py` |
| Memory misses real things (e.g. "my therapist suggested...") | Pattern too tight | Add the missing pattern |
| Sam pounces on past memories every turn | Soft framing not strong enough | Strengthen wording in `format_notes_for_prompt` |
| Forget intent triggers on ordinary "I forgot..." | Regex too eager | Tighten `_FORGET_TOPIC_RE` (it's already anchored to "forget" as the *imperative*) |

## 5. Where to look / edit

- **Persona text** → `@/ai_compare/gentle_companion_chatbot.py` (top of file: `GENTLE_COMPANION_PERSONA`)
- **What gets remembered** → `@/ai_compare/gentle_companion_memory.py` → `_MEANINGFUL_PATTERNS`
- **How memory is presented to Sam** → same file → `format_notes_for_prompt`
- **TTL (180 days)** → same file → `_NOTE_TTL_DAYS`
- **Forget detection** → same file → `_FORGET_ALL_RE`, `_FORGET_TOPIC_RE`, `detect_forget_intent`
- **UI** → `@/templates/gentle_companion.html`
- **Dashboard tile** → `@/templates/chatchat.html` (search for `<!-- Sam - Gentle Companion -->`)

## 6. Re-run tests after any change

```powershell
python tests\test_gentle_companion.py        # 27 unit tests
python -m unittest tests.test_gentle_companion_smoke -v   # 4 smoke tests
```

Both must remain green before deploying.

## 7. Suggested first session

If you want a representative first run, try this exact sequence (≈5 min):

1. *"hey"*
2. *"I've been weirdly tired all week."*
3. *"I keep telling myself I'll exercise but never do."*
4. *"I want to start small, maybe a walk."*
5. (refresh the page or wait an hour)
6. *"I went for that walk."*
7. *"forget what I said about exercise"*
8. *"thanks"*

Walk through the flow noting tone at each step. If steps 2, 4, and 6 all feel like talking with a calm friend — and 5/6 connects naturally — Sam is working.
