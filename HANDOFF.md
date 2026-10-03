# Handoff snapshot

_Generated 2026-10-03 16:08 by handoff.py — regenerate rather than edit._

## In progress

Fixed health_profile render crash: symptom triggers stored as string crashed .join(); added load-time normalization + add_symptom coercion + template concat guard + real error message in catch. Copied Ken T (uid 21) health profile + uploaded docs to Ken (uid 1) on production via Files API; verified via live API. Next: deploy this fix.

## Git

**Branch:** `cursor/emergency-card-paramedic-fields`  
**Uncommitted files:** 27

> Uncommitted work is the main handoff hazard: the next agent
> cannot tell finished edits from half-written ones. Commit
> before switching, even as `wip:`.

```
M AI_REGENERATION_SPEC.md
 M ENHANCEMENTS.md
 M README.md
 M SYSTEM_REGENERATION_GUIDE.md
 M ai_compare/medical_advisor_health_context.py
 M templates/health_profile.html
 M tests/test_health_profile_safety.py
?? check_wk_credentials.py
?? debug_auth.py
?? direct_password_test.py
?? final_password_fix.py
?? fix_exact_password.py
?? fix_login.py
?? fix_password_match.py
?? fix_slash_password.py
?? fix_to_correct_password.py
?? fix_user_auth.py
?? migrate_user_data.py
?? setup_correct_password.py
?? test_admin_access.py
?? test_chat_fixes.py
?? test_contact_admin_visibility.py
?? test_email_banner_playwright.py
?? test_integrated_system.py
?? test_reply_buttons.py
?? test_special_characters.py
?? verify_user.py
```

<details><summary>diff --stat</summary>

```
AI_REGENERATION_SPEC.md                      |  2 +-
 ENHANCEMENTS.md                              |  8 +++++++
 README.md                                    |  2 +-
 SYSTEM_REGENERATION_GUIDE.md                 |  2 +-
 ai_compare/medical_advisor_health_context.py | 25 ++++++++++++++++++++++
 templates/health_profile.html                |  7 +++---
 tests/test_health_profile_safety.py          | 32 ++++++++++++++++++++++++++++
 7 files changed, 72 insertions(+), 6 deletions(-)
warning: LF will be replaced by CRLF in templates/health_profile.html.
The file will have its original line endings in your working directory
```
</details>

Recent commits:

```
7b51808 Fix TTS double-narration and decimal-point chunking
176f262 /grow: auto-growing composer, logout button, signed-in name
3b169b0 Fix card removal on /grow: getElementById takes raw ids, not CSS.escape
b45728b Phase 3: receptivity learning + delivery calibration ladder
cf1ccbb Phase 2: learning topics + deterministic stage tracking in /grow
b5a25a6 Handoff: identity scrub complete
9a9aa71 Post-rewrite cleanup: gitignore personality_profiles/uploads media, pa_sync exclusion, restore avatar
cb6d64b Remove '' surname entirely; untrack wisdom_profiles
```

## Production (PythonAnywhere)

**7 file(s) differ from production.** Deploy with `python pa_sync.py --push`.

```
ok       tests/test_real_conversations.py
ok       tests/test_report_format.py
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
7 file(s) stale. Re-run with --push to upload.
```

Reload often returns `409 slow_startup_error` on the first attempt — retry rather than debug it.

## Tests

All passing.

```
........................................................................ [ 58%]
........................................................................ [ 72%]
........................................................................ [ 87%]
...............................................................          [100%]
============================== warnings summary ===============================
..\..\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37
  C:\Users\trabc\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37: DeprecationWarning: datetime.datetime.utcfromtimestamp() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.fromtimestamp(timestamp, datetime.UTC).
    EPOCH = datetime.datetime.utcfromtimestamp(0)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
495 passed, 1 warning in 67.41s (0:01:07)
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
