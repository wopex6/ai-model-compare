# Handoff snapshot

_Generated 2026-09-29 09:35 by handoff.py — regenerate rather than edit._

## In progress

Spiro rescan: 14 local cycles on ST's sideways photo, last 5 consecutive golden. Added 3 misread gates to _layout_guided_read (blank measured cells, interior holes in a labelled row, 3+ consecutive rows echoing Actual==Pred). Qualifier repair via label remap; compact measured column survives mass delete/reject (profile 17 layout was self-poisoned, repaired). Committed f0272a3, deployed + digest-verified, /dr-health 200. Next: user re-analyses ST's doc in prod.

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

<details><summary>diff --stat</summary>

```
AI_REGENERATION_SPEC.md      |   2 +-
 ENHANCEMENTS.md              | 176 +++++++++++++++++++++++++++++++++++++++++++
 README.md                    |   2 +-
 SYSTEM_REGENERATION_GUIDE.md |   2 +-
 4 files changed, 179 insertions(+), 3 deletions(-)
```
</details>

Recent commits:

```
f0272a3 Re-read grids that are shaped right but read wrong
abb800f Handoff: compact-emission unit fix deployed
d653636 Keep compact-emission values bare of their slotted unit
def89d2 Don't glue a slotted unit onto the value in _fill_test_defaults
16fdb6a Handoff + autodoc updates
de0d959 Guided re-read: any missing expected row is a mis-shape
21a7342 Handoff: ST rotated-photo scan solved end-to-end
56120b6 AGENTS: note rotated-photo guided retry and multi-row headers
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
automated_greeting_system.py:416
automated_greeting_system.py:416
  C:\Users\trabc\CascadeProjects\ai-model-compare - Claude\automated_greeting_system.py:416: DeprecationWarning: The default datetime adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
    cursor.execute('''

..\..\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37
  C:\Users\trabc\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37: DeprecationWarning: datetime.datetime.utcfromtimestamp() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.fromtimestamp(timestamp, datetime.UTC).
    EPOCH = datetime.datetime.utcfromtimestamp(0)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
476 passed, 5 warnings in 23.16s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
