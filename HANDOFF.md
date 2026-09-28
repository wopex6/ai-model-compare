# Handoff snapshot

_Generated 2026-09-28 21:33 by handoff.py — regenerate rather than edit._

## In progress

ST scan fixed for real this time: the sideways grid kept 5/10 row labels which passed the old half-labels gate, so guided re-read never fired and a confirmed 7-col layout applied positionally. Gate now fires on ANY missing expected label. Local harness on the actual sideways photo produces all 10 golden rows again. Deployed + verified. Next: user to hit re-analyse on ST's stored doc.

## Git

**Branch:** `cursor/emergency-card-paramedic-fields`  
**Uncommitted files:** 43

> Uncommitted work is the main handoff hazard: the next agent
> cannot tell finished edits from half-written ones. Commit
> before switching, even as `wip:`.

```
M AI_REGENERATION_SPEC.md
 M ENHANCEMENTS.md
 M README.md
 M SYSTEM_REGENERATION_GUIDE.md
?? _append_shared_tests.py
?? _iter_sp.py
?? _last_text.md
?? _merge_dupes.py
?? _prod17_backup.json
?? _prod17_now.json
?? _prod17_now2.json
?? _prod_result.json
?? _st_photo_080524.jpeg
?? _st_photo_084600.jpeg
?? _st_photo_084858.jpeg
?? _st_prod_result.json
?? _st_rescan.json
?? _st_rescan.txt
?? _st_rescan2.json
?? _st_rescan3.json
?? _st_rescan4.json
?? _st_result.json
?? _st_spiro.json
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
```

<details><summary>diff --stat</summary>

```
AI_REGENERATION_SPEC.md      |  2 +-
 ENHANCEMENTS.md              | 16 ++++++++++++++++
 README.md                    |  2 +-
 SYSTEM_REGENERATION_GUIDE.md |  2 +-
 4 files changed, 19 insertions(+), 3 deletions(-)
```
</details>

Recent commits:

```
de0d959 Guided re-read: any missing expected row is a mis-shape
21a7342 Handoff: ST rotated-photo scan solved end-to-end
56120b6 AGENTS: note rotated-photo guided retry and multi-row headers
5caf895 Guided re-read: retry rotated photos, keep multi-row headers
69ffdcf Dr. Health: read a same-report grid by column identity, not position
af22eb5 Handoff: ST rescan diagnosis â€” mis-shape detection + role repair shipped
41fafc3 Guided re-read: prefer the fullest confirmed schema, detect mis-shape
4a258a2 Handoff: Sau Tse restored; label-variant matching shipped
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
........................................................................ [ 60%]
........................................................................ [ 75%]
........................................................................ [ 91%]
..........................................                               [100%]
============================== warnings summary ===============================
..\..\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37
  C:\Users\trabc\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37: DeprecationWarning: datetime.datetime.utcfromtimestamp() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.fromtimestamp(timestamp, datetime.UTC).
    EPOCH = datetime.datetime.utcfromtimestamp(0)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
474 passed, 1 warning in 23.46s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
