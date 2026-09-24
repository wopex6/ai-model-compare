# Handoff snapshot

_Generated 2026-09-24 21:14 by handoff.py — regenerate rather than edit._

## In progress

Shipped phone-only emergency fields (full name/address/phone/Medicare in drHealth.emergencyLocal.v1, merged at render, editable in PWA modal + standalone icon page; deployed v119). OPEN for user: (a) retire vs erase - retired profiles 1/23 still exist as *_retired.json + docs dir on PA; (b) git history still contains the sensitive files - needs filter-repo+force-push; (c) Wai T password was public - should be changed.

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
?? fix_wai_tse_auth.py
?? migrate_wai_tse_data.py
?? setup_correct_password.py
?? test_admin_access.py
?? test_chat_fixes.py
?? test_contact_admin_visibility.py
?? test_email_banner_playwright.py
?? test_integrated_system.py
?? test_reply_buttons.py
?? test_special_characters.py
?? verify_wai_tse.py
```

Recent commits:

```
bedae29 emergency card: phone-only private details
69b5ca6 handoff: snapshot after profile retirement and sensitive-data removal
1a8002d Remove leaked patient data and credentials from tracked files
e8862ed handoff: snapshot after profile 23-to-21 data copy
dee3d68 handoff: snapshot after doc-outcome persistence deploy
3568290 Persist per-document review outcome across list re-renders
ce6776d handoff: snapshot after scroll-box deploy
aa93e11 records: scrollable list boxes, per-file review outcome, Full Overview
```

## Production (PythonAnywhere)

Local and production match.

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
409 passed, 1 warning in 23.48s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
