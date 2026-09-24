# Handoff snapshot

_Generated 2026-09-24 17:05 by handoff.py — regenerate rather than edit._

## In progress

Auto-open review after upload, removed per-file status + Review/Refresh buttons, Retake replaced with cancel-x. Fixed user test renames reverting: pin_test_name() writes test_name_aliases on PUT so canonicalize keeps the chosen name. SW v115.

## Git

**Branch:** `cursor/emergency-card-paramedic-fields`  
**Uncommitted files:** 0

Recent commits:

```
aa42ae9 records: auto-open review, drop retake/review/refresh buttons, pin renamed tests
f45b436 handoff: snapshot after delete-resurrection merge fix
26f2802 profile merge: honor deletions in 3-way list merge
e89f6f7 handoff: snapshot after blank-lock/data-manager timeout deploy
1d83900 data manager: deliberate blank ref/unit vs absent import blank; fetch timeouts
8bbccc1 handoff: snapshot after data-manager reliability deploy
efc6d8f data manager: reliable saves, inline sticky search, blank ref/unit, keep scroll
9a96385 records: bulk bar on top, sticky dm search, readable history entries
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
409 passed, 1 warning in 21.47s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
