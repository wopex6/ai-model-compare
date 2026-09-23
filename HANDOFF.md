# Handoff snapshot

_Generated 2026-09-23 16:35 by handoff.py — regenerate rather than edit._

## In progress

Deployed 2e127d6: fixed false L flags from /L units in lab_results.js (arithmetic now authoritative when range parses), consistent displayVal when unit embedded, per-row Ref column in Full overview. New node test tests/test_lab_results.js.

## Git

**Branch:** `cursor/emergency-card-paramedic-fields`  
**Uncommitted files:** 0

Recent commits:

```
2e127d6 lab results: fix false Low flags from '/L' units; per-row ref in overview
63e4ff8 handoff: snapshot after gallery/UTC/collapsible-docs deploy
1c7e3f8 records: gallery picker, UTC timestamps, collapsible stored documents
072358a handoff: snapshot after wrapped-table ref/unit recovery deploy
949cbfc records: timestamps on stored docs; recover ref/unit from wrapped lab tables
59d782f handoff: snapshot after stored-review and busy-button deploy
d178178 records: reopen stored analysis without re-analysing; upload button busy state
a0da3a3 handoff: snapshot after stale-review, viewer zoom and blank-unit deploy
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
409 passed, 1 warning in 47.18s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
