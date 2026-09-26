# Handoff snapshot

_Generated 2026-09-26 13:12 by handoff.py — regenerate rather than edit._

## In progress

Learning loop for report layouts is in: confirmed column_roles key off structure (not signature), apply_remembered on next scan, review role chips re-extract via POST /api/health-profile/report-format, apply-review confirms, item PUT/DELETE learn conservatively, sibling_date for same-structure pages within 2h. PWA cache v126. Multi-photo merge of different structures is still open. Not deployed. 82 format/safety/emergency tests passed.

## Git

**Branch:** `cursor/emergency-card-paramedic-fields`  
**Uncommitted files:** 31

> Uncommitted work is the main handoff hazard: the next agent
> cannot tell finished edits from half-written ones. Commit
> before switching, even as `wip:`.

```
M AGENTS.md
 M ai_compare/medical_advisor_health_context.py
 M app.py
 M handoff.py
 M static/dr_health_hub.js
 M static/dr_health_sw.js
 M templates/dr_health_app.html
 M tests/test_emergency_home_icon.py
 M tests/test_health_profile_safety.py
?? ai_compare/report_format.py
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
?? tests/test_report_format.py
?? verify_wai_tse.py
```

<details><summary>diff --stat</summary>

```
AGENTS.md                                    | 151 +++++++-
 ai_compare/medical_advisor_health_context.py | 405 +++++++++++-----------
 app.py                                       |  89 ++++-
 handoff.py                                   |   1 +
 static/dr_health_hub.js                      |  79 ++++-
 static/dr_health_sw.js                       |   2 +-
 templates/dr_health_app.html                 | 229 ++++++++++--
 tests/test_emergency_home_icon.py            | 136 ++++++++
 tests/test_health_profile_safety.py          | 498 ++++++++++++++++++++++++++-
 9 files changed, 1317 insertions(+), 273 deletions(-)
warning: LF will be replaced by CRLF in handoff.py.
The file will have its original line endings in your working directory
```
</details>

Recent commits:

```
648c52b Handoff: spirometry-table parsing fix deployed
ca3e72a Classify report-table column roles before extracting test results
f7df04e Handoff: read-only emergency icon + security hardening (SW v124)
1a7c641 Make emergency icon read-only mirror; bilingual crisis signals
3a2331e Handoff: auto reply-language deployed (SW v123)
46c64e7 Add 'auto' reply-language mode that mirrors the question's language
454519c push: send at high urgency so Doze doesn't defer reminders
2945a3d settings: save preferences even when notification permission is blocked
```

## Tests

All passing.

```
........................................................................ [ 66%]
........................................................................ [ 82%]
........................................................................ [ 99%]
...                                                                      [100%]
============================== warnings summary ===============================
..\..\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37
  C:\Users\trabc\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37: DeprecationWarning: datetime.datetime.utcfromtimestamp() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.fromtimestamp(timestamp, datetime.UTC).
    EPOCH = datetime.datetime.utcfromtimestamp(0)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
435 passed, 1 warning in 19.59s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
