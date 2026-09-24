# Handoff snapshot

_Generated 2026-09-24 13:58 by handoff.py — regenerate rather than edit._

## In progress

data manager fixes: profile snapshots now sync after save/delete (stale-index bug), history field excluded from edit form, blank ref/unit allowed and propagate to whole group, scroll position preserved, search box inline in sticky index bar. Deployed SW v113.

## Git

**Branch:** `cursor/emergency-card-paramedic-fields`  
**Uncommitted files:** 0

Recent commits:

```
efc6d8f data manager: reliable saves, inline sticky search, blank ref/unit, keep scroll
9a96385 records: bulk bar on top, sticky dm search, readable history entries
fb56c9b records: test-name search in overview + data manager; review check-all
c85b41d handoff: snapshot after bulk-delete/undo/audit deploy
793c969 records: bulk doc delete, import undo, added-count, drop stale status
7c42aa0 test data: append-only audit log of changes, 30-day window (configurable)
5c47839 lab results: unify reference-range display; revert Record(s) marker
aba948e handoff: snapshot after unit carry-over fix deploy
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
409 passed, 1 warning in 45.68s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
