# Handoff snapshot

_Generated 2026-10-02 21:34 by handoff.py — regenerate rather than edit._

## In progress

Removed '' surname from all tracked files (Ken->Ken); untracked+gitignored wisdom_profiles (PA copy persists, pa_sync never deletes); DB rename still pending - integrated_users.db locked

## Git

**Branch:** `cursor/emergency-card-paramedic-fields`  
**Uncommitted files:** 92

> Uncommitted work is the main handoff hazard: the next agent
> cannot tell finished edits from half-written ones. Commit
> before switching, even as `wip:`.

```
M .gitignore
 M DATABASE_MIGRATION_TESTING.md
 M DEPLOYMENT_COMPLETE.md
 M DEPLOY_NOW_GUIDE.md
 M DEPLOY_PHASE_3_1.md
 M FIXES_APPLIED_NOV2.md
 M FIXES_COMPLETE_NOV2.md
 M HANDOFF.md
 M INTEGRATED_README.md
 M PHASE1_COMPLETE_SUMMARY.md
 M PLAYWRIGHT_FINDINGS.md
 M PRODUCTION_UPDATE_GUIDE.md
 M QUICK_START.md
 M QUICK_TEST_GUIDE.md
 M TEST_AI_CHARACTERS.md
 M TEST_EMAIL_BANNER.md
 M USER_LOGON_README.md
 M add_user_roles.py
 M automated_trait_inference_test.py
 M check_admin_account.py
 M check_and_fix_admin.py
 M check_assessment_history.py
 M check_current_assessment.py
RM check_ken.py -> check_ken.py
 M check_original_profile.py
 M complete_restore.py
 M create_simple_login.py
 M direct_trait_inference_test.py
 M integrated_database.py
 M migrate_production_phase_3_1.py
 M pa_sync.py
 M playwright_debug_output.json
 M playwright_history_check.py
 M playwright_investigate_history.py
 M quick_restore.py
 M quick_test_history.py
 M restore_real_data.py
RM set_ken_admin.py -> set_ken_admin.py
 M start_integrated_system.py
 M static/multi_user_app.js
```

<details><summary>diff --stat</summary>

```
.gitignore                                 |  3 ++
 DATABASE_MIGRATION_TESTING.md              |  8 ++--
 DEPLOYMENT_COMPLETE.md                     |  2 +-
 DEPLOY_NOW_GUIDE.md                        |  4 +-
 DEPLOY_PHASE_3_1.md                        |  2 +-
 FIXES_APPLIED_NOV2.md                      |  2 +-
 FIXES_COMPLETE_NOV2.md                     |  6 +--
 HANDOFF.md                                 | 20 ++++-----
 INTEGRATED_README.md                       |  4 +-
 PHASE1_COMPLETE_SUMMARY.md                 |  2 +-
 PLAYWRIGHT_FINDINGS.md                     |  4 +-
 PRODUCTION_UPDATE_GUIDE.md                 |  2 +-
 QUICK_START.md                             | 12 +++---
 QUICK_TEST_GUIDE.md                        |  2 +-
 TEST_AI_CHARACTERS.md                      |  2 +-
 TEST_EMAIL_BANNER.md                       |  2 +-
 USER_LOGON_README.md                       |  2 +-
 add_user_roles.py                          | 10 ++---
 automated_trait_inference_test.py          |  2 +-
 check_admin_account.py                     |  4 +-
 check_and_fix_admin.py                     | 14 +++----
 check_assessment_history.py                |  2 +-
 check_current_assessment.py                |  2 +-
 check_ken.py => check_ken.py           |  6 +--
 check_original_profile.py                  |  2 +-
 complete_restore.py                        |  8 ++--
 create_simple_login.py                     | 14 +++----
 direct_trait_inference_test.py             |  2 +-
 integrated_database.py                     | 10 ++---
 migrate_production_phase_3_1.py            |  2 +-
 pa_sync.py                                 |  1 +
 playwright_debug_output.json               |  8 ++--
 playwright_history_check.py                |  2 +-
 playwright_investigate_history.py          |  2 +-
 quick_restore.py                           |  8 ++--
 quick_test_history.py                      |  2 +-
 restore_real_data.py                       | 20 ++++-----
 set_ken_admin.py => set_ken_admin.py   | 12 +++---
 start_integrated_system.py                 |  2 +-
 static/multi_user_app.js                   |  2 +-
 test_3_fixes.py                            | 14 +++----
 test_admin_chat.py                         | 10 ++---
 test_all_new_features.py                   |  8 ++--
 test_chart_expansion.py                    |  2 +-
 test_coach_integration.py                  |  2 +-
 test_ken_login.py => test_ken_login.py |  8 ++--
 test_new_features_playwright.py            |  2 +-
 test_personality_integration.py            |  2 +-
 test_personality_resolver.py               |  2 +-
 test_user_intelligence.py                  |  2 +-
 tests/generate_synthetic_data.py           |  2 +-
 tests/test_character_insights_e2e.py       |  2 +-
 tests/test_comprehensive.py                |  2 +-
 tests/test_heavy_usage.py                  |  2 +-
 tests/test_moltbook_integration.py         |  2 +-
 tests/test_patterns_context.py             |  2 +-
 tests/test_phase4_clarification.py         |  2 +-
 tests/test_phase5_character_traits.py      |  2 +-
 tests/test_phase5_enhancements.py          |  2 +-
 tests/test_phase5_local.py                 |  2 +-
 tests/test_phase5_requests.py              |  2 +-
 tests/test_phase65_collaboration.py        |  2 +-
 tests/test_phase6_context.py               |  2 +-
 tests/test_phase6_enhancements.py          |  2 +-
 tests/test_phase7_effectiveness.py         |  2 +-
 tests/test_phase8_expansion.py             |  2 +-
 tests/test_populate_analytics.py           |  2 +-
 tests/test_production.py                   |  2 +-
 tests/test_real_conversations.py           |  2 +-
 tests/test_report_format.py                |  6 +--
 wisdom_profiles/23.json                    | 65 ------------------------------
 wisdom_profiles/23_hypotheses.json         | 38 -----------------
 72 files changed, 158 insertions(+), 257 deletions(-)
warning: LF will be replaced by CRLF in .gitignore.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in DATABASE_MIGRATION_TESTING.md.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in DEPLOYMENT_COMPLETE.md.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in DEPLOY_NOW_GUIDE.md.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in DEPLOY_PHASE_3_1.md.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in FIXES_APPLIED_NOV2.md.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in FIXES_COMPLETE_NOV2.md.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in HANDOFF.md.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in INTEGRATED_README.md.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in PHASE1_COMPLETE_SUMMARY.md.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in PLAYWRIGHT_FINDINGS.md.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in PRODUCTION_UPDATE_GUIDE.md.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in QUICK_START.md.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in QUICK_TEST_GUIDE.md.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in TEST_AI_CHARACTERS.md.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in TEST_EMAIL_BANNER.md.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in USER_LOGON_README.md.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in add_user_roles.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in automated_trait_inference_test.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in check_admin_account.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in check_and_fix_admin.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in check_assessment_history.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in check_current_assessment.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in check_original_profile.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in complete_restore.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in create_simple_login.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in direct_trait_inference_test.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in integrated_database.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in migrate_production_phase_3_1.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in pa_sync.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in playwright_debug_output.json.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in playwright_history_check.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in playwright_investigate_history.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in quick_restore.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in quick_test_history.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in restore_real_data.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in start_integrated_system.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in static/multi_user_app.js.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in test_3_fixes.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in test_admin_chat.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in test_all_new_features.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in test_chart_expansion.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in test_coach_integration.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in test_new_features_playwright.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in test_personality_integration.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in test_personality_resolver.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in test_user_intelligence.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in tests/generate_synthetic_data.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in tests/test_character_insights_e2e.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in tests/test_comprehensive.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in tests/test_heavy_usage.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in tests/test_moltbook_integration.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in tests/test_patterns_context.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in tests/test_phase4_clarification.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in tests/test_phase5_character_traits.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in tests/test_phase5_enhancements.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in tests/test_phase5_local.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in tests/test_phase5_requests.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in tests/test_phase65_collaboration.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in tests/test_phase6_context.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in tests/test_phase6_enhancements.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in tests/test_phase7_effectiveness.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in tests/test_phase8_expansion.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in tests/test_populate_analytics.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in tests/test_production.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in tests/test_real_conversations.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in tests/test_report_format.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in check_ken.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in set_ken_admin.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in test_ken_login.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in check_ken.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in set_ken_admin.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in test_ken_login.py.
The file will have its original line endings in your working directory
```
</details>

Recent commits:

```
bcdcaa0 Rename default admin user "Ken" to "Ken" across repo
3813018 Handoff: Phase 1 /grow surface deployed
4189a42 Phase 1: /grow light surface â€” card feed + companion chat + correctable facts
313df20 Handoff: Growth Engine Phase 0 deployed
a176dc3 Growth Engine Phase 0: unified state + private reflection model + admin inspector
0c79697 Handoff: empty-column fix deployed
bd5a553 Hide empty Ref/Notes columns in overview tables
6af8417 Handoff: derived-value verification deployed
```

## Production (PythonAnywhere)

**73 file(s) differ from production.** Deploy with `python pa_sync.py --push`.

```
STALE    tests/test_real_conversations.py  local=2b249b268bb1 remote=f7e1cd98b56d
STALE    tests/test_report_format.py  local=4bbaac395ddc remote=07bc7dcff3d6
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
73 file(s) stale. Re-run with --push to upload.
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
495 passed, 1 warning in 53.25s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
