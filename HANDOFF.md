# Handoff snapshot

_Generated 2026-09-20 19:16 by handoff.py — regenerate rather than edit._

## In progress

Dr. Health PWA on cursor/emergency-card-paramedic-fields. Latest feature commit 4277472 is deployed (SW dr-health-shell-v93): packed chat context, Chat attach+queue, visit brief, lab explain, locale replies. Open work is in AGENTS.md section 8: (1) after-visit return with proposals not silent facts, (2) Chat I-stopped-X / GP-started-Y onto the confirmation queue, (3) deterministic interaction flags in chat context. Device v93, airplane-mode emergency card, and live Cantonese reply not verified. Local Flask on 5050/5051 may be stale until restarted. Ignore any older HANDOFF claims about vitals.v1, password in localStorage, or non-atomic profile save — those are already fixed. Do not commit AutoDoc leftovers.

## Git

**Branch:** `cursor/emergency-card-paramedic-fields`  
**Uncommitted files:** 0

Recent commits:

```
46c6990 docs: current Dr. Health open work for the next agent
4277472 chat and hub: packed context, visit brief, lab explain, and locale replies
349b9b4 emergency card: pair iPhone storage, install button, and safer profile saves
e0f1c14 hub back: always return to the previous screen, including Emergency Info
9e208ad hub back: go one level up, and drop the duplicate Cancel
c3e5738 emergency card: return to home, login, or hub â€” wherever it was opened from
59fb2fb emergency card: back when signed in, refresh and close on the home-screen icon
9c469e8 emergency card: home-screen icon, labelled meds, open details directly
```

## Production (PythonAnywhere)

**5 file(s) differ from production.** Deploy with `python pa_sync.py --push`.

```
ok       tests/test_ui_features.py
ok       tests/test_user_logon_shared_modules.py
ok       tests/test_web_enhancements.py
ok       token_test.py
ok       update_database.py
ok       update_wk_password.py
ok       upload_database_to_pythonanywhere.ps1
ok       uploads/ai_a6043c74-8f82-40d8-863c-971ba0f40619.md
ok       verbosity_system.py
ok       verify_database_schema.py
ok       verify_delete.py
ok       verify_personality_system.py
ok       verify_production_ready.py
ok       verify_shared_processing.py
ok       verify_table_schemas.py
ok       verify_timestamp_storage.py
ok       verify_wai_tse.py
ok       view_phase3_data.py
ok       web_enhancement_plan.md
ok       web_enhancement_test_results.json
ok       web_enhancement_test_runner.py
ok       webhook_deploy.py
ok       wisdom_profiles/23.json
ok       wisdom_profiles/23_hypotheses.json
5 file(s) stale. Re-run with --push to upload.
```

Reload often returns `409 slow_startup_error` on the first attempt — retry rather than debug it.

## Tests

All passing.

```
........................................................................ [ 52%]
........................................................................ [ 70%]
........................................................................ [ 88%]
.................................................                        [100%]
============================== warnings summary ===============================
..\..\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37
  C:\Users\trabc\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37: DeprecationWarning: datetime.datetime.utcfromtimestamp() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.fromtimestamp(timestamp, datetime.UTC).
    EPOCH = datetime.datetime.utcfromtimestamp(0)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
409 passed, 1 warning in 21.27s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
