# Handoff snapshot

_Generated 2026-09-24 14:39 by handoff.py — regenerate rather than edit._

## In progress

Blank ref/unit: user-edit locks (ref_locked/unit_locked) vs absent import blanks; lock-aware backfill in dedupe/merge; displayRef fallback in groupTestResults; fetch timeouts on dm/profile/docs loads (fixes 'Loading...' hang). Browser-verified. SW v114.

## Git

**Branch:** `cursor/emergency-card-paramedic-fields`  
**Uncommitted files:** 0

Recent commits:

```
1d83900 data manager: deliberate blank ref/unit vs absent import blank; fetch timeouts
8bbccc1 handoff: snapshot after data-manager reliability deploy
efc6d8f data manager: reliable saves, inline sticky search, blank ref/unit, keep scroll
9a96385 records: bulk bar on top, sticky dm search, readable history entries
fb56c9b records: test-name search in overview + data manager; review check-all
c85b41d handoff: snapshot after bulk-delete/undo/audit deploy
793c969 records: bulk doc delete, import undo, added-count, drop stale status
7c42aa0 test data: append-only audit log of changes, 30-day window (configurable)
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
409 passed, 1 warning in 16.76s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
