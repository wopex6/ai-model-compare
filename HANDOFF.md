# Handoff snapshot

_Generated 2026-09-27 22:31 by handoff.py — regenerate rather than edit._

## In progress

Fixed PWA '+ field' focus + verified fields persistence. ROOT CAUSE of user's lost data: local server on :5051 ran week-old Python (debug reloads templates, not Python) and silently dropped the fields bag — restarted it, verified fields persist via Playwright repro. User's 10 typed records are NOT recoverable: never reached any store (profile/backups/audit/uploads/chat all checked). test_audit now carries the fields bag for future recovery. Port 5050 also runs stale Sep-26 code — user should restart it too. Not deployed (local-only request; SW bumped to v134 for next deploy).

## Git

**Branch:** `cursor/emergency-card-paramedic-fields`  
**Uncommitted files:** 20

> Uncommitted work is the main handoff hazard: the next agent
> cannot tell finished edits from half-written ones. Commit
> before switching, even as `wip:`.

```
?? check_wk_credentials.py
?? debug_auth.py
?? direct_password_test.py
?? final_password_fix.py
?? fix_exact_password.py
?? fix_login.py
?? fix_password_match.py
?? fix_slash_password.py
?? fix_to_correct_password.py
?? fix_ken_auth.py
?? migrate_ken_data.py
?? setup_correct_password.py
?? test_admin_access.py
?? test_chat_fixes.py
?? test_contact_admin_visibility.py
?? test_email_banner_playwright.py
?? test_integrated_system.py
?? test_reply_buttons.py
?? test_special_characters.py
?? verify_ken.py
```

Recent commits:

```
372cac8 Dr. Health: focus new-field input after '+ field'; audit detail carries fields bag
8f9e14c Handoff: field-alias + name-pattern learning deployed (SW v133).
d1205aa Dr. Health: learn field aliases and name composition positionally
743bc49 Handoff: positional integrity + rejection learning deployed (SW v132).
a6cefd4 Dr. Health: positional integrity + rejection learning for report grids
beb9796 Handoff: review UX fixes + name-style learning deployed.
52c47f1 Dr. Health review: duplicate-row tools, field delete, blank-date manual rows, name-style learning
d7fddea Handoff: report learning + duplicate records deployed (SW v131).
```

## Production (PythonAnywhere)

**11 file(s) differ from production.** Deploy with `python pa_sync.py --push`.

```
ok       tests/test_review_flow.py
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
ok       view_phase3_data.py
ok       web_enhancement_plan.md
ok       web_enhancement_test_results.json
ok       web_enhancement_test_runner.py
ok       webhook_deploy.py
ok       wisdom_profiles/23.json
ok       wisdom_profiles/23_hypotheses.json
11 file(s) stale. Re-run with --push to upload.
```

Reload often returns `409 slow_startup_error` on the first attempt — retry rather than debug it.

## Tests

All passing.

```
........................................................................ [ 63%]
........................................................................ [ 79%]
........................................................................ [ 95%]
.....................                                                    [100%]
============================== warnings summary ===============================
..\..\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37
  C:\Users\trabc\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37: DeprecationWarning: datetime.datetime.utcfromtimestamp() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.fromtimestamp(timestamp, datetime.UTC).
    EPOCH = datetime.datetime.utcfromtimestamp(0)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
453 passed, 1 warning in 19.34s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
