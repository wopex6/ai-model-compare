# Handoff snapshot

_Generated 2026-10-02 20:03 by handoff.py — regenerate rather than edit._

## In progress

Growth Companion Phase 0 landed: growth_engine.py (unified state + derive_reflections + commitments view over engagement threads/habits/explicit goals), /api/growth/state, admin inspector at /admin/growth-inspector + /api/growth/insights/<id>[/derive] (admin-gated), living design doc docs/growth_companion.md, 13 tests. Deployed & verified on production. Next: Phase 1 /grow light surface (companion chat + card feed) per megaplan.

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
 ENHANCEMENTS.md              | 336 +++++++++++++++++++++++++++++++++++++++++++
 README.md                    |   2 +-
 SYSTEM_REGENERATION_GUIDE.md |   2 +-
 4 files changed, 339 insertions(+), 3 deletions(-)
```
</details>

Recent commits:

```
a176dc3 Growth Engine Phase 0: unified state + private reflection model + admin inspector
0c79697 Handoff: empty-column fix deployed
bd5a553 Hide empty Ref/Notes columns in overview tables
6af8417 Handoff: derived-value verification deployed
86df6d6 Verify derived figures against their components
1a32efa Handoff: website gains the PWA's health tool surface
fd1772f Port the PWA's document inspection and health tools to the website
62620f0 Handoff: schema-coverage scoring for guided re-reads deployed
```

## Production (PythonAnywhere)

**369 file(s) differ from production.** Deploy with `python pa_sync.py --push`.

```
ok       migrate_old_assessments_to_history.py
ok       migrate_production_latest_schema.py
ok       migrate_production_phase_3_1.py
ok       migrate_routed_messages.py
ok       migrate_smart_response_tables.py
ok       motivational_coach_demo.py
ok       ocr_snapshots/app_20260824_211115.py
ok       ocr_snapshots/test_ocr_live_20260824_211115.py
ok       pa_console.py
ok       personality_profiles/WK7_profile.json
ok       personality_profiles/WK_profile.json
ok       personality_profiles/sessions/WK7_session.json
ok       personality_profiles/sessions/WK_session.json
ok       personality_profiles/sessions/test_user_1761913076470_session.json
ok       personality_profiles/sessions/test_user_1761913255521_session.json
ok       personality_profiles/sessions/test_user_1761913670659_session.json
ok       personality_profiles/sessions/test_user_1761913706407_session.json
ok       personality_profiles/sessions/test_user_1761954180907_session.json
ok       personality_profiles/sessions/test_user_1761955083583_session.json
ok       personality_profiles/sessions/test_user_1761955380402_session.json
ok       personality_profiles/sessions/test_user_1761957912201_session.json
ok       personality_profiles/sessions/test_user_1761959949391_session.json
ok       personality_profiles/sessions/test_user_1761960293931_session.json
ok       personality_profiles/sessions/test_user_1762054114844_session.json
4 file(s) stale. Re-run with --push to upload.
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
495 passed, 1 warning in 50.24s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
