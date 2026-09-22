# Handoff snapshot

_Generated 2026-09-22 21:42 by handoff.py — regenerate rather than edit._

## In progress

Deployed 67f6b06 (SW v101): removed stale onclick closure that re-opened the previous doc's review after a new photo; doc viewer now fits images to width (pinch zoom on) and PDFs with #view=Fit; explicit blank unit wins over value-text extraction.

## Git

**Branch:** `cursor/emergency-card-paramedic-fields`  
**Uncommitted files:** 0

Recent commits:

```
67f6b06 pwa: fix stale review showing previous doc; doc viewer fit + zoom; blank unit sticks
79a0173 handoff: snapshot after ref+unit merge-gate deploy
47dc854 test merge rules: same reference range AND unit required before merging
2da5613 handoff: snapshot after unit-aware test dedup deploy
f367461 test dedup: unit mismatch means different measurement; keep qualifiers in display key
f5a0f54 handoff: snapshot after test-dup keep-stored and edit-fields deploy
3a07353 test results: keep stored value on same-date dup; editable test name; all standard fields shown
4e3b7e2 handoff: snapshot after review-close, doc viewer, doc ordering and default range/unit deploy
```

## Production (PythonAnywhere)

Local and production match.

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
Everything on the server matches local.
```

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
409 passed, 1 warning in 20.39s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
