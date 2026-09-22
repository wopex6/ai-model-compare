# Handoff snapshot

_Generated 2026-09-22 17:04 by handoff.py — regenerate rather than edit._

## In progress

Deployed 3eea881 (SW v98): Reject All closes the review modal, stored documents open in an in-app viewer overlay with a Back button (window.open unreliable standalone), documents list newest-first at API + PWA + hub, Manage My Data 'Edit range' saves default reference_range+unit on the newest row (lab_results prefers item.unit). Left: none of the 4 requests open.

## Git

**Branch:** `cursor/emergency-card-paramedic-fields`  
**Uncommitted files:** 0

Recent commits:

```
3eea881 records: Reject All closes review, in-app doc viewer, newest-first docs, editable default range/unit
5cbcc53 handoff: snapshot after 100%-save and records layout deploy
b525d19 records: retain checkbox under option 2; Analyze scoped to option 3; save everything the review shows
24d8c10 handoff: snapshot after records-screen work
3998f3c records: 3-step add-info layout, document viewing, aligned lab columns
e5f235d handoff: snapshot after emergency closed-screen removal
521703c emergency card: drop the fake closed screen; align brief field rows
3b7c883 handoff: snapshot after visit brief and iOS reopen fix deploy
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
409 passed, 1 warning in 18.46s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
