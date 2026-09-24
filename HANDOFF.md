# Handoff snapshot

_Generated 2026-09-24 20:13 by handoff.py — regenerate rather than edit._

## In progress

Copied missing health sections from profile 23 to profile 21 on production (conditions+9, meds+2, supps+5, symptoms+2, plans+4, insights+166 filtered of OCR dumps, diet+lifestyle dicts, location). App reloaded, verified. Open question: near-duplicate conditions now exist (Haemochromatosis vs carrier, Dyslipidaemia vs Hyperlipidaemia). Possible improvement: filter raw OCR dumps out of conversation_insights at ingest.

## Git

**Branch:** `cursor/emergency-card-paramedic-fields`  
**Uncommitted files:** 0

Recent commits:

```
dee3d68 handoff: snapshot after doc-outcome persistence deploy
3568290 Persist per-document review outcome across list re-renders
ce6776d handoff: snapshot after scroll-box deploy
aa93e11 records: scrollable list boxes, per-file review outcome, Full Overview
fa55cbc handoff: snapshot after records polish deploy
d52bc8c records: tidy status messages, auto-review flow, move editor card up
394f716 handoff: snapshot after auto-review + rename pin deploy
aa42ae9 records: auto-open review, drop retake/review/refresh buttons, pin renamed tests
```

## Production (PythonAnywhere)

**1 file(s) differ from production.** Deploy with `python pa_sync.py --push`.

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
1 file(s) stale. Re-run with --push to upload.
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
409 passed, 1 warning in 25.12s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
