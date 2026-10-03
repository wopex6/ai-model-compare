# Handoff snapshot

_Generated 2026-10-03 10:26 by handoff.py — regenerate rather than edit._

## In progress

Phase 3 built: receptivity learning + delivery ladder + propose cards in /grow; deploy pending

## Git

**Branch:** `cursor/emergency-card-paramedic-fields`  
**Uncommitted files:** 25

> Uncommitted work is the main handoff hazard: the next agent
> cannot tell finished edits from half-written ones. Commit
> before switching, even as `wip:`.

```
M docs/growth_companion.md
 M smart_response/growth_engine.py
 M templates/admin_growth_inspector.html
 M templates/growth_companion.html
 M tests/test_growth_engine.py
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
docs/growth_companion.md              |  14 ++
 smart_response/growth_engine.py       | 247 ++++++++++++++++++++++++++++++++--
 templates/admin_growth_inspector.html |   3 +-
 templates/growth_companion.html       |  18 +++
 tests/test_growth_engine.py           | 133 +++++++++++++++++-
 5 files changed, 402 insertions(+), 13 deletions(-)
warning: LF will be replaced by CRLF in smart_response/growth_engine.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in templates/admin_growth_inspector.html.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in templates/growth_companion.html.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in tests/test_growth_engine.py.
The file will have its original line endings in your working directory
```
</details>

Recent commits:

```
cf1ccbb Phase 2: learning topics + deterministic stage tracking in /grow
b5a25a6 Handoff: identity scrub complete
9a9aa71 Post-rewrite cleanup: gitignore personality_profiles/uploads media, pa_sync exclusion, restore avatar
cb6d64b Remove '' surname entirely; untrack wisdom_profiles
4a6d39e Rename default admin user "Ken" to "Ken" across repo
112700b Handoff: Phase 1 /grow surface deployed
0ed316a Phase 1: /grow light surface â€” card feed + companion chat + correctable facts
478dfd2 Handoff: Growth Engine Phase 0 deployed
```

## Production (PythonAnywhere)

**5 file(s) differ from production.** Deploy with `python pa_sync.py --push`.

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
5 file(s) stale. Re-run with --push to upload.
```

Reload often returns `409 slow_startup_error` on the first attempt — retry rather than debug it.

## Tests

All passing.

```
automated_greeting_system.py:416
automated_greeting_system.py:416
  C:\Users\trabc\CascadeProjects\ai-model-compare - Claude\automated_greeting_system.py:416: DeprecationWarning: The default datetime adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
    cursor.execute('''

..\..\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37
  C:\Users\trabc\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37: DeprecationWarning: datetime.datetime.utcfromtimestamp() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.fromtimestamp(timestamp, datetime.UTC).
    EPOCH = datetime.datetime.utcfromtimestamp(0)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
495 passed, 5 warnings in 23.77s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
