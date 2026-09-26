# Working on this repository

Read this before making changes. It is written for AI coding agents working in
alternating sessions — one agent picks up where another stopped, often mid-task
after a quota ran out. Most of what follows is knowledge that is expensive to
rediscover and easy to get wrong.

Everything here applies to the whole `ai-model-compare` app. The health profile
(Dr. Health) is one feature among many; the chat characters, domain agents,
personality system and multi-user layer are all subject to the same rules.

---

## 1. Handoff protocol

**Commit before the session ends.** This is the single most important habit.
Uncommitted work is ambiguous: the next agent cannot tell a finished edit from
a half-written one, and has no way to undo a bad change. A `wip:` commit with
an honest message is far better than a clean tree that never happens.

Before switching tools, run:

```bash
python handoff.py -m "what I was doing and what is left"
```

That writes `HANDOFF.md` with the live state of git, production drift and the
test suite. It derives everything fresh, so unlike a hand-written note it
cannot silently go stale. Starting a session? Read `HANDOFF.md`, then
`git log --oneline -10`, then this file.

**Assume nothing carries over.** The next agent has none of your context: no
memory of what you tried, what you rejected, or why. If a decision is not in a
commit message, a code comment or this file, it is lost.

**One agent at a time.** Two agents on the same working tree will overwrite
each other silently — git only helps once changes are committed. Finish or
commit before handing over.

---

## 2. Deployment

Production is PythonAnywhere: <https://trabcd.pythonanywhere.com>
(remote root `/home/trabcd/ai-model-compare`).

```bash
python pa_sync.py           # report drift only, uploads nothing
python pa_sync.py --push    # upload stale files, verify, reload
```

Things that will otherwise cost you an hour:

- **There is no shell on production.** The PythonAnywhere console API cannot
  execute commands until its console iframe has been opened in a browser, so
  `pip install` on the server is not available. New pure-Python dependencies
  must be vendored as wheels in `vendor/` and loaded from `sys.path`; see
  `_get_pdf_reader()` in `app.py` for the pattern.
- **`pa_sync.py` normalises CRLF to LF.** That corrupts binaries. Wheels and
  images must be uploaded raw through the Files API, never through `pa_sync`.
- **Reload commonly returns `409 slow_startup_error` on the first attempt.**
  Retry after ~20s. It is boot lag, not a failure.
- **The deploy set is derived from `git ls-files`** — every tracked text file
  syncs automatically; new files need no registration. Exclusions live in
  `pa_sync.py` (`_EXCLUDE_DIRS` / `_EXCLUDE_FILES` / `_EXCLUDE_EXT`): vendored
  wheels, binaries, patient-data dirs and local-only tooling. If you add a
  file that must NOT reach production, add it there — otherwise it will deploy.
- **The drift check now covers ~450 files, so it takes several minutes** and
  produces a long report. `python pa_sync.py | grep -v "^ok "` shows only
  drift.
- **Verify, do not assume.** `pa_sync` compares digests after upload. Never
  report something as deployed without that output.

### PWA caching

`static/dr_health_sw.js` precaches the app shell. It is served from the site
root by the `/dr_health_sw.js` route in `app.py` and registered with
`scope: '/dr-health'` — **do not register it from `/static/`**. A worker can
only claim a scope at or below its own path, so the `/static/` location capped
its scope at a directory no page lives in, and for a long time it silently
controlled nothing and cached nothing usable.

`SHELL_ASSETS` is an allow-list: only those paths are ever cached, and anything
else — every API, chat, session and history call — always goes to the network.
A new file the PWA needs offline must be added there or it is simply never
cached. Never add a path that returns user data.

Cached assets are served from the copy on the device and revalidated in the
background, so a stale asset self-heals after one launch. Bumping `CACHE_NAME`
still forces the change through immediately and drops old caches, but
forgetting it no longer strands users the way it used to. Opening the app is
network-first with the stored shell as the offline fallback, so template edits
appear immediately.

Nothing here can be verified from a dev machine: it needs a real device over
HTTPS, installed to the home screen, then put into airplane mode. Say so rather
than implying coverage. Note also that WebKit deletes script-writable storage
after seven days without interaction unless the app was **installed to the home
screen** (`display: standalone` qualifies) — which is why the offline emergency
card depends on installing rather than bookmarking. The same constraint applies
on **Android and iPhone**; do not write install steps or UI that assume Safari
only.

The Emergency home-screen icon is a second installed app at
`/dr-health/emergency` (white cross on red, own manifest, no login). It reads
the same `drHealth.emergencyCard.v1` cache the main app writes. Keep it under
`/dr-health` so the existing worker can cache it. Navigate fallbacks must store
that path separately — never write the Emergency HTML into the main
`/dr-health` app shell. `/emergency` redirects there; do not revive a worker
registered from `/static/emergency_sw.js`. A new file the PWA needs offline
must be added to `SHELL_ASSETS` in `static/dr_health_sw.js`.

On iPhone, two home-screen apps from the same origin have isolated
localStorage, so the Emergency icon often cannot see the card Dr. Health
cached. Pair them with `emergency_pair_token` / `POST /api/health-profile/emergency-card/pair`
and `drHealth.emergencyPair.v1`. Do not store the account password in
localStorage; the JWT and this setup code are enough.

### Push notifications

Reminder pushes use Web Push (`ai_compare/health_push.py`). Subscriptions are
stored in `health_profiles/push_subscriptions.json` (gitignored, excluded from
deploy). VAPID keys come from `VAPID_PRIVATE_KEY` / `VAPID_PUBLIC_KEY` in
`.env`. Sending needs `pywebpush` + `py_vapid` + `http_ece` + `cryptography` +
`cffi` + `pycparser` + `six`, vendored as wheels in `vendor/` — the compiled
ones (`.so` files) cannot be zipimported, so `health_push._import_pywebpush()`
extracts `vendor/*.whl` into `vendor/_extracted/` (gitignored) on first use.
New wheels must be uploaded to PA with a raw Files-API POST — `pa_sync`
excludes them. A PythonAnywhere scheduled task (id 1527586, daily 22:00 UTC ≈
8am Melbourne) runs `push_dispatch.py`. The schedule API needs the **trailing
slash** — POST `/schedule` silently becomes a GET through the redirect. iOS
only delivers web push to apps installed to the home screen.

---

## 3. Testing

```bash
python -m pytest tests/ -q --ignore=tests/test_character_insights_e2e.py
```

Takes ~9 minutes. For a fast check, run only the files you touched.

**Known failures — not yours:**

| Test | Why |
| --- | --- |
| `test_web_enhancements.py::TestModelsRetryAndSession` (3 tests) | `asyncio.run()` inside an already-running loop. Test pollution from another test; all 278 pass when the file runs alone. |
| `test_character_insights_e2e.py` | Playwright E2E; needs a live server and real model calls. |
| `test_production` in `test_moltbook_integration.py`, `test_phase4`…`test_phase8` (6 tests) | They log into **live production** with the password `"123"`, which was rotated. They also hard-code a credential in a tracked file; fix that rather than restoring the password. |
| `test_comprehensive.py::test_life_companion[chromium]` | Playwright; needs a live server. |

Confirm a suspicious failure in isolation before trying to fix it.

**Templates contain inline JavaScript,** which no linter sees. Syntax-check it
by extracting and running `node --check`:

```bash
python -c "
import re, subprocess, pathlib
for name in ['dr_health_app', 'health_profile']:
    src = pathlib.Path(f'templates/{name}.html').read_text(encoding='utf-8')
    for i, m in enumerate(re.finditer(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', src, re.S)):
        if not m.group(1).strip(): continue
        p = pathlib.Path(f'_js_{name}_{i}.js'); p.write_text(m.group(1), encoding='utf-8')
        r = subprocess.run(['node','--check',str(p)], capture_output=True, text=True)
        print(p.name, 'OK' if r.returncode==0 else r.stderr[:800]); p.unlink()
"
```

---

## 4. Conventions that are easy to violate

### Share logic, not UI

The PWA (`templates/dr_health_app.html`) and the website
(`templates/health_profile.html`) render the same data differently. Their
**shared logic lives in `static/`** and must not be copied back into either
template:

| Module | Owns |
| --- | --- |
| `ai_compare/report_format.py` | report-table layout: column roles from cell evidence, arithmetic relations, format signatures |
| `static/lab_results.js` | test-result grouping, sorting, reference ranges, abnormal flags, units, medical date parsing |
| `static/health_review.js` | item lifecycle: confirmation queue UI, current-vs-past partitioning, change notes, retire/revive |

Adding a feature to one page? Put the logic in the shared module and let each
page render it. Three copies of this logic existed before; consolidating them
was deliberate work, easily undone by accident.

### Report layouts are derived, not recognised by wording

`ai_compare/report_format.py` works out what each column of a report table
means **from the cells**, not from the heading. Adding an English keyword to a
list is how this went wrong before: a spirometry report with
Actual/Pred/%Pred columns produced 36 junk rows with `Pred` stored as a date,
and the fix at the time was to match the words `pred` and `%chng` — which only
ever covers the reports someone already thought of.

What the module actually does, and must keep doing:

- a column whose cells parse as dates is a date column; ranges (`a - b`,
 `< x`) are a reference column; short symbols with `/`, `%`, `^` are units;
 `H`/`L`/`N` are flags. All unlabelled columns work.
- a column that is ~100 x one column divided by another is a **derived
 percentage**, found by arithmetic. That is what '%Pred' means, so '% of
 expected' or a Chinese heading parses identically.
- `c = 100a/b` rearranges to `b = 100a/c`, so a ratio triple fits three ways
 and arithmetic alone cannot say which column is derived. The **per-cent
 sign** breaks the tie (notation, not vocabulary), then whichever column sits
 on a different scale from the other two.
- arithmetic needs two rows, so a one-row table falls back to the heading.
 Every column therefore carries a `basis` — `cells`, `arithmetic`, `heading`,
 `default` — and it travels into the saved analysis. A reading that rested on
 a heading is weaker than one the numbers confirmed; do not drop `basis`.
- a sparse heading row spanning several columns is a **qualifier** (Pre-Bronch,
 a specimen, a fasting state) carried forward over the columns it introduces.
 Structural, so it needs no knowledge of what the label says.
- rows matching the metadata pattern are excluded from the column profile as
 well as from the output — a report that prints ranges on their own
 `Reference` row would otherwise make a results column look like ranges.
- a table of findings, visit facts or discharge fields has no numeric
 measurement column. The first payload column becomes `stated` (not skipped).
 Extra columns stay in `fields` under the report's own headings. `None` on a
 Severity column is a word, not a unit.

Each layout gets a **signature** (roles included) and a **structure** (cell
shapes only), stored per profile in `report_formats` with
`seen_count`/`first_seen`/`last_seen`. Date headings collapse to `<date>` in
both, so the same laboratory's report next month is recognised rather
than looking brand new. `remember()` returns `known` or `new`, and that lands
in the extraction record. Two readings of one layout that disagree both get
kept in `role_changes` — overwriting would hide which one is wrong.

A format the user has accepted or corrected is `confirmed`. Confirmed
`column_roles` key off **structure**, not signature: Pred vs %Pred disagree on
role but share a grid, and the user's reading must apply to both. The next
scan overlays those roles before extract (`apply_remembered`). Changing a
role chip in the review modal re-extracts the same stored grid
(`POST /api/health-profile/report-format`) without a model call. Saving the
review calls `confirm()`. Dating a filed row records `last_report_date` so a
sibling page of the same structure uploaded within two hours inherits it.
Deleting every row that came from one column demotes that column to `text`.
`format_structure` / `source_role` stay on the row (and in `MANAGED_KEYS`) so
those edits can find the layout; they are never free-text extras.

Heading keywords survive only in `_HINTS`, as a tie-break and a fallback. Every
role they suggest is reachable from the cells alone. **Do not promote a hint
into a decision, and do not add a new report's vocabulary to that list to make
one report work** — if the cells cannot distinguish it, fix the evidence test.

### Nothing is dropped for want of a schema field

A test-result row may carry a `fields` dict keyed by **the report's own column
headings** (`'Pre-Bronch %Pred'`, `'Method'`). `add_test_result(..., fields=)`
stores it; a re-scan only fills gaps in it, like the value itself. The hub
editor renders a box for every key the schema does not declare, including each
`fields` entry, via `extraFields()` and the `fields.<heading>` convention in
`readForm()`. So a new report kind stores and edits its whole reading with no
schema change and no migration.

`MANAGED_KEYS` in `dr_health_hub.js` is the exception: `status`,
`last_confirmed_at`, `history`, `ref_locked`, `date_source`,
`format_structure`, `format_signature`, `source_role` and friends stay
visible but never get a free-text box. Hand-editing a lifecycle timestamp
or a layout id corrupts the confirmation queue and the learning loop.

A row with no date in the document is still dated (dedup is by name + date, and
two undated reports would otherwise collapse into one), but it is marked
`date_source: 'filed'`. Do not present a filed date as the day of the
measurement.

### The full reading of a document is inspectable

`analyze_and_store` returns `format_analysis` **alongside** `extracted`, never
inside it — the advice prompt serialises `extracted`, and the layout record is
for people. It reaches the user through
`GET /api/health-profile/document-result?download=1`, which writes one file
holding the transcribed text, every extracted row, every skipped row **with the
reason**, and the role and basis of each column. `<hash>_result.json` is
indented for the same reason. Never add that path to `SHELL_ASSETS`.

### Duplicate test results keep the stored value

Same canonical test name + same normalized date = the same measurement, and
the stored row wins: `add_test_result` discards an incoming differing value
and only backfills empty `reference_range`/`notes`/`date`. The stored value
was reviewed (by the user or a prior import); a re-scan must not clobber it.
Exception: merging requires the same **reference range and unit** — when both
are determinable and either disagrees, they are not the same measurement. The
name key strips qualifiers like '(NGSP)'/'(IFCC)', so 'HbA1c (IFCC)' in
mmol/mol must not dedup onto 'HbA1c (NGSP)' in %. The same gate applies to
name canonicalisation in `_resolve_test_name` (via `_name_series_accepts`):
a variant only folds onto an existing series when its ref and unit agree.
Same name+date+identical value is still one reading regardless of how the
ref was transcribed. `normalizeTestType` keeps qualifiers in the display key
for the same reason. A row may also carry a `unit` field;
`lab_results.js` prefers it over extracting the unit from `value`, and the
group header derives its default range/unit from the newest row.

### Items are retired, never deleted

Health items carry `status` / `started_on` / `ended_on` / `last_confirmed_at` /
`history`. "No longer true" is a state — the record is what makes *"I stopped
that in March"* answerable later. See `ai_compare/health_freshness.py`.

Consequences, all of which have bitten already:

- Anything listing medications, supplements, symptoms or conditions **must
  filter to active**, or stopped items read as current. This matters most in
  the AI context (`format_for_prompt` and `_facts_for_prompt`), drug-interaction
  checks, polypharmacy counts and reminders — a stopped drug presented as
  current is a safety bug. Stopped items still belong in the prompt, labelled
  `STOPPED — do not treat as current`.
- Stopped items still belong in the AI context, under an explicit *"STOPPED —
  do not treat as current"* heading. What someone came off changes the advice.
- UI helpers that split a list **must preserve original indices**. The item
  endpoints address rows by position, so renumbering deletes the wrong row.

### Provenance: AI guesses are not facts

Every stored item carries a `source` (`user_entered`, `document_extracted`,
`ai_inferred`, `clinician_report`, `unknown`). An AI inference **must never
overwrite** something the user or a lab report stated — it becomes a proposal
in `pending_changes` instead. See `merge_incoming()`. When adding an ingest
path, set `profile.ingest_source` rather than labelling items by hand.

### One-shot migrations are guarded

Profile JSON migrations run once per profile behind a flag
(`provenance_backfilled`, `lifecycle_backfilled`). New migrations must follow
the same pattern and be idempotent. Never backdate a "confirmed" timestamp
during a backfill — it hides stale data instead of surfacing it.

---

## 5. Safety and privacy

- **Never commit patient data.** `health_profiles/` and
  `health_uploaded_documents/` are gitignored — the latter holds real medical
  PDFs and OCR output. `health_profiles/_backups/` is where `save()` rotates
  timestamped copies (last 20 per user) — that is the recovery path, do not
  delete it, and it stays inside the gitignored tree. Be careful with
  `git add -A`; check `git status` first.
- **`save()` merges foreign writes.** Profiles are cached per worker; when the
  file changed since load, `save()` three-way merges the remote copy into ours
  (`merge_profiles`) instead of clobbering. Lists union by item key, dicts
  merge per field, scalar conflicts keep the in-flight (ours) value.
- **Uploaded documents are evidence, not cache.** `keep_forever` on a doc
  exempts it from retention cleanup; the retention default for new profiles is
  3650 days (~keep). `GET /documents` lists `expires_at`/`expiring_soon`, the
  digest warns 30 days ahead, and `PUT /documents` toggles keep. The full
  record exports via `GET /api/health-profile/export` (zip: profile JSON +
  originals); a change log is at `GET /api/health-profile/changes?days=N`.
- **Secrets come from the environment.** `PYTHONANYWHERE_API_TOKEN`, model API
  keys and `JWT_SECRET`/`SECRET_KEY` load from `.env`. Never hardcode, echo or
  commit them. `app.py` warns on startup when insecure defaults are in use.
- This app gives health information. Advice paths are deliberately conservative
  (deterministic Tier 1 observations, hash-gated and validated Tier 2 AI
  advice, a standing disclaimer). Do not loosen validation or let unverified
  AI-inferred data become citable.

---

## 6. Layout

```
app.py                          Flask app and all HTTP routes (large)
ai_compare/
  medical_advisor_health_context.py   HealthProfile: atomic save, ingest, AI context
  report_format.py                    report-table layout from cell evidence, not headings
  health_insights.py                  provenance, reminders, observations, advice
  health_freshness.py                 lifecycle, change history, confirmation queue
  character_routes.py                 per-character chat endpoints
templates/
  dr_health_app.html              Dr. Health PWA (inline JS)
  health_profile.html             health profile website (inline JS)
static/
  lab_results.js                  shared: test-result logic
  health_review.js                shared: lifecycle + confirmation UI
  emergency_card.js               shared: emergency card render (PWA + home-screen icon)
  dr_health_sw.js                 service worker — bump CACHE_NAME on asset change
tests/                          pytest
vendor/                         vendored wheels (no pip on production)
pa_sync.py                      deploy: diff all tracked files, upload, verify, reload
handoff.py                      session handoff snapshot
```

---

## 7. General practice (applies beyond this repo)

- **Verify with tools; do not assert from memory.** Read the file, run the
  test, check the endpoint. Open editor tabs are frequently stale and are not
  evidence of anything.
- **Reproduce before fixing.** Then fix the root cause, not the symptom.
- **Write the regression test first** where the infrastructure allows it.
- **Never report something as deployed, passing or committed without tool
  output showing it.** Overstating state is the fastest way to mislead both the
  user and the next agent.
- **Say what you did not verify.** Authenticated flows, device behaviour and
  anything needing a real browser usually cannot be checked from here — flag
  them rather than implying coverage.
- **Match the surrounding code.** Read neighbouring files for style, error
  handling and library choices before introducing your own.
- **Do not add or remove comments that are not yours to change**, and do not
  create summary or plan documents as files — put reasoning in commit messages
  and durable notes in this file.
- **Escalate rather than work around** auth problems, permission errors or
  failing CI that would require weakening a security control.

---

## 8. Open work (replace this when it ships)

As of 26 Sep 2026, branch `cursor/emergency-card-paramedic-fields`, PWA cache
`dr-health-shell-v126`. Learning loop is committed on this branch. Not
deployed — only `pa_sync.py --push` if asked.

Shipped this session (do not redo):

- `ai_compare/report_format.py` — cell/arithmetic layout, not heading keywords.
  See section 4. `describe()` returns `signature` **and** `structure`.
- Confirmed layouts: `confirm()` / `apply_remembered()` / `learn_from_edit()` /
  `learn_from_delete()` / `sibling_date()`. Review role chips re-extract via
  `POST /api/health-profile/report-format`. Apply-review confirms the reading.
- `add_test_result(..., fields=, unit=, layout=)` stores extra columns and the
  format ids. Hub editor renders extras; `MANAGED_KEYS` hides the ids.
- `GET /api/health-profile/document-result?download=1` — whole reading as a file.
- Emergency-card hub links: `closeEmergency({ keepHistoryEntry: true })`.
- `_fill_test_defaults` no longer doubles a single-letter unit (`0.96 L L`).

Next, in order:

1. **Several images for one report.** `sibling_date` only helps when the later
   page shares **structure** (same headings/shapes). A photo of page 2 that
   dropped the date heading is a *different* structure and still loses the
   date and patient header from page 1. Overlapping screenshots still
   duplicate rows. Merge pages that arrive together, not just inherit a date.
2. Surface `confirmed` in the hub so the user can edit a stored layout
   without re-uploading. The flag is set; there is no format-editor page.
3. After-visit return — photograph the new script or letter, park extracted
   meds as proposals, offer to mark visit questions answered. Never retire or
   add a drug as fact until the user confirms.
4. Chat “I stopped X / my GP started Y” as confirmation-queue proposals.
   `---PROFILE_UPDATE---` already writes `ai_inferred`; if the model skips
   that block the record still shows the old current meds.
5. Deterministic drug-interaction flags in chat context. The hub tool exists;
   the model does not see it.

Still hard-coded, and worth knowing before adding more: 186 test-name aliases
in `_TEST_NAME_CANONICAL`, 31 unit aliases, 14 specimen prefixes,
`_DIMENSIONLESS_TESTS`, `_CONCENTRATION_UNITS`, `COMMON_PANELS` and 25
`_ANTICOAGULANT_MARKERS`. These are vocabulary, not layout, and the layout was
the part that broke on every new report. `_resolve_test_name` already learns
aliases at runtime and `pin_test_name` lets the user override, so extend that
mechanism rather than the tables.

Not verified from a desktop: the emergency-card link fix on a real phone (the
bug is a history/popstate race, so it needs a device or a real browser), v126 on
an installed phone, role-chip re-extract in a real review modal, the analysis
download against a real stored document — there is no patient data on this
machine, so those paths were only exercised at source/test level. Local Flask
on :5050/:5051 may still be a process started before these routes existed; a
404 there is a stale process, not a missing feature.

Do not revive `/static/emergency_sw.js`, a second emergency-card editor, or
password-in-localStorage. Do not commit AutoDoc leftovers (`README.md`,
`ENHANCEMENTS.md`, `AI_REGENERATION_SPEC.md`, `SYSTEM_REGENERATION_GUIDE.md`).
`pa_sync` still uploads dirty tracked files, so restore those four before a
deploy if AutoDoc has touched them.
