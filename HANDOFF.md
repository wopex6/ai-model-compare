# Handoff snapshot

_Generated 2026-09-29 20:21 by handoff.py — regenerate rather than edit._

## In progress

Website/PWA gap fill shipped (fd1772f, deployed, /health-profile 200): one shared pendingReviewCardHtml for all review cards, role chips re-extract via report-format with no model call, stored-doc list gains Review/Analysis/Delete/Keep links, tools card covers digest+visit brief+explain-test+interactions+emergency card+vitals+export+undo-import, test-audit ledger rendered. Still PWA-only: push subscription, SW/offline shell, emergency home icon, review-prompt bell queue.

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
 ENHANCEMENTS.md              | 256 +++++++++++++++++++++++++++++++++++++++++++
 README.md                    |   2 +-
 SYSTEM_REGENERATION_GUIDE.md |   2 +-
 4 files changed, 259 insertions(+), 3 deletions(-)
```
</details>

Recent commits:

```
fd1772f Port the PWA's document inspection and health tools to the website
62620f0 Handoff: schema-coverage scoring for guided re-reads deployed
28c3af9 Score guided re-reads against the schema's missing columns
3bf8afc Handoff: directional coverage + orientation-loop fix deployed
6d43d1b Try every orientation before trusting a guided re-read
d42dd36 Handoff: sideways-photo misread gates deployed
f0272a3 Re-read grids that are shaped right but read wrong
abb800f Handoff: compact-emission unit fix deployed
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
........................................................................ [ 60%]
........................................................................ [ 75%]
........................................................................ [ 90%]
............................................                             [100%]
============================== warnings summary ===============================
..\..\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37
  C:\Users\trabc\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37: DeprecationWarning: datetime.datetime.utcfromtimestamp() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.fromtimestamp(timestamp, datetime.UTC).
    EPOCH = datetime.datetime.utcfromtimestamp(0)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
476 passed, 1 warning in 36.54s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
