# Handoff snapshot

_Generated 2026-09-23 09:22 by handoff.py — regenerate rather than edit._

## In progress

Deployed d178178 (SW v102): GET /document-result reopens stored analysis without an AI call; stored docs get a Review button when has_result; Use-this-photo shows busy pulse while uploading.

## Git

**Branch:** `cursor/emergency-card-paramedic-fields`  
**Uncommitted files:** 0

Recent commits:

```
d178178 records: reopen stored analysis without re-analysing; upload button busy state
a0da3a3 handoff: snapshot after stale-review, viewer zoom and blank-unit deploy
67f6b06 pwa: fix stale review showing previous doc; doc viewer fit + zoom; blank unit sticks
79a0173 handoff: snapshot after ref+unit merge-gate deploy
47dc854 test merge rules: same reference range AND unit required before merging
2da5613 handoff: snapshot after unit-aware test dedup deploy
f367461 test dedup: unit mismatch means different measurement; keep qualifiers in display key
f5a0f54 handoff: snapshot after test-dup keep-stored and edit-fields deploy
```

## Production (PythonAnywhere)

**4 file(s) differ from production.** Deploy with `python pa_sync.py --push`.

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
4 file(s) stale. Re-run with --push to upload.
```

Reload often returns `409 slow_startup_error` on the first attempt — retry rather than debug it.

## Tests

All passing.

```
automated_greeting_system.py:416
automated_greeting_system.py:416
  C:\Users\trabc\CascadeProjects\ai-model-compare - Claude\automated_greeting_system.py:416: DeprecationWarning: The default datetime adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
    cursor.execute('''

..\..\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37
  C:\Users\trabc\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37: DeprecationWarning: datetime.datetime.utcfromtimestamp() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.fromtimestamp(timestamp, datetime.UTC).
    EPOCH = datetime.datetime.utcfromtimestamp(0)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
409 passed, 5 warnings in 44.17s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
