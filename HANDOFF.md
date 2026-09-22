# Handoff snapshot

_Generated 2026-09-22 20:33 by handoff.py — regenerate rather than edit._

## In progress

Deployed 47dc854: merge requires same ref+unit at both dedup and name-canonicalisation (_name_series_accepts). Identical value still dedups. Open item: user's stored HbA1c(NGSP) row on production carries the IFCC ref (25-38) from the old backfill bug — user must fix it via Manage My Data (Edit range/row); cannot be repaired remotely.

## Git

**Branch:** `cursor/emergency-card-paramedic-fields`  
**Uncommitted files:** 0

Recent commits:

```
47dc854 test merge rules: same reference range AND unit required before merging
2da5613 handoff: snapshot after unit-aware test dedup deploy
f367461 test dedup: unit mismatch means different measurement; keep qualifiers in display key
f5a0f54 handoff: snapshot after test-dup keep-stored and edit-fields deploy
3a07353 test results: keep stored value on same-date dup; editable test name; all standard fields shown
4e3b7e2 handoff: snapshot after review-close, doc viewer, doc ordering and default range/unit deploy
3eea881 records: Reject All closes review, in-app doc viewer, newest-first docs, editable default range/unit
5cbcc53 handoff: snapshot after 100%-save and records layout deploy
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
........................................................................ [ 52%]
........................................................................ [ 70%]
........................................................................ [ 88%]
.................................................                        [100%]
============================== warnings summary ===============================
..\..\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37
  C:\Users\trabc\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37: DeprecationWarning: datetime.datetime.utcfromtimestamp() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.fromtimestamp(timestamp, datetime.UTC).
    EPOCH = datetime.datetime.utcfromtimestamp(0)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
409 passed, 1 warning in 19.50s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
