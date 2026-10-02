# Handoff snapshot

_Generated 2026-10-02 21:51 by handoff.py — regenerate rather than edit._

## In progress

Full history rewrite done: all /Ken traces + personal-data paths purged; personality_profiles untracked; force-push pending

## Git

**Branch:** `cursor/emergency-card-paramedic-fields`  
**Uncommitted files:** 23

> Uncommitted work is the main handoff hazard: the next agent
> cannot tell finished edits from half-written ones. Commit
> before switching, even as `wip:`.

```
M  .gitignore
M  pa_sync.py
A  static/avatars/dr_nova.jpg
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
.gitignore                 |   3 +++
 pa_sync.py                 |   1 +
 static/avatars/dr_nova.jpg | Bin 0 -> 1522220 bytes
 3 files changed, 4 insertions(+)
```
</details>

Recent commits:

```
fc41348 Remove '' surname entirely; untrack wisdom_profiles
621fc12 Rename default admin user "Ken" to "Ken" across repo
1a73747 Handoff: Phase 1 /grow surface deployed
d7eed63 Phase 1: /grow light surface â€” card feed + companion chat + correctable facts
750cd42 Handoff: Growth Engine Phase 0 deployed
ecd3a49 Growth Engine Phase 0: unified state + private reflection model + admin inspector
569db1f Handoff: empty-column fix deployed
369abb3 Hide empty Ref/Notes columns in overview tables
```

## Production (PythonAnywhere)

**147 file(s) differ from production.** Deploy with `python pa_sync.py --push`.

```
STALE    tests/test_real_conversations.py  local=16c209a93eaa remote=f7e1cd98b56d
STALE    tests/test_report_format.py  local=4bbaac395ddc remote=07bc7dcff3d6
STALE    tests/test_review_flow.py  local=65d2f53785cb remote=2a16d5f9f448
ok       tests/test_ui_features.py
STALE    tests/test_user_logon_shared_modules.py  local=ca12e2256781 remote=46573208bde1
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
147 file(s) stale. Re-run with --push to upload.
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
495 passed, 1 warning in 49.90s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
