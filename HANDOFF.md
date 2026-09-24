# Handoff snapshot

_Generated 2026-09-24 22:04 by handoff.py — regenerate rather than edit._

## In progress

emergency card: DOB moved to phone-only private details; age optional + DOB-derived; suggest endpoint extended with DOB; one-time server DOB migration+clear; SW v121

## Git

**Branch:** `cursor/emergency-card-paramedic-fields`  
**Uncommitted files:** 24

> Uncommitted work is the main handoff hazard: the next agent
> cannot tell finished edits from half-written ones. Commit
> before switching, even as `wip:`.

```
M AI_REGENERATION_SPEC.md
 M ENHANCEMENTS.md
 M README.md
 M SYSTEM_REGENERATION_GUIDE.md
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

<details><summary>diff --stat</summary>

```
AI_REGENERATION_SPEC.md      |  2 +-
 ENHANCEMENTS.md              | 24 ++++++++++++++++++++++++
 README.md                    |  2 +-
 SYSTEM_REGENERATION_GUIDE.md |  2 +-
 4 files changed, 27 insertions(+), 3 deletions(-)
```
</details>

Recent commits:

```
1ec1a1f emergency card: move date of birth into phone-only details
244ead2 handoff: snapshot after emergency-suggest deploy
36d068a emergency card: suggest private details from stored documents
1d28b79 handoff: snapshot after phone-only emergency fields deploy
bedae29 emergency card: phone-only private details
69b5ca6 handoff: snapshot after profile retirement and sensitive-data removal
1a8002d Remove leaked patient data and credentials from tracked files
e8862ed handoff: snapshot after profile 23-to-21 data copy
```

## Production (PythonAnywhere)

**4 file(s) differ from production.** Deploy with `python pa_sync.py --push`.

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
409 passed, 1 warning in 22.39s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
