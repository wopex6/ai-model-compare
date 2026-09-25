# Handoff snapshot

_Generated 2026-09-25 19:33 by handoff.py — regenerate rather than edit._

## In progress

Added 'auto' reply-language mode (default): AI replies mirror the question's language, clinical terms stay in original wording; en/zh-HK remain as explicit overrides. SW v123. Backlog: real JWT_SECRET/FLASK_ENV on PA (.//. password too), bilingual crisis keywords, Chinese drug-name aliases.

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
46c64e7 Add 'auto' reply-language mode that mirrors the question's language
454519c push: send at high urgency so Doze doesn't defer reminders
2945a3d settings: save preferences even when notification permission is blocked
f0a346a settings: distinguish unsupported vs denied notification error
1584572 handoff: snapshot after private-details + web push deploy
e03bb05 private details in Personal Details + web push for reminders
9d85d5a handoff: snapshot after DOB-to-phone-local deploy
1ec1a1f emergency card: move date of birth into phone-only details
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
409 passed, 1 warning in 21.81s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
