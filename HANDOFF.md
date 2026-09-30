# Handoff snapshot

_Generated 2026-10-01 07:45 by handoff.py — regenerate rather than edit._

## In progress

Empty-column fix deployed (bd5a553): PWA Full Overview and website results tables now render Ref/Notes columns only when the group's data carries them — verified in node: spirometry group renders Date|Value, chem group keeps Ref.

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
 ENHANCEMENTS.md              | 280 +++++++++++++++++++++++++++++++++++++++++++
 README.md                    |   2 +-
 SYSTEM_REGENERATION_GUIDE.md |   2 +-
 4 files changed, 283 insertions(+), 3 deletions(-)
```
</details>

Recent commits:

```
bd5a553 Hide empty Ref/Notes columns in overview tables
6af8417 Handoff: derived-value verification deployed
86df6d6 Verify derived figures against their components
1a32efa Handoff: website gains the PWA's health tool surface
fd1772f Port the PWA's document inspection and health tools to the website
62620f0 Handoff: schema-coverage scoring for guided re-reads deployed
28c3af9 Score guided re-reads against the schema's missing columns
3bf8afc Handoff: directional coverage + orientation-loop fix deployed
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
........................................................................ [ 58%]
........................................................................ [ 72%]
........................................................................ [ 87%]
...............................................................          [100%]
============================== warnings summary ===============================
..\..\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37
  C:\Users\trabc\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37: DeprecationWarning: datetime.datetime.utcfromtimestamp() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.fromtimestamp(timestamp, datetime.UTC).
    EPOCH = datetime.datetime.utcfromtimestamp(0)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
495 passed, 1 warning in 63.58s (0:01:03)
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
