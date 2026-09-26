# Handoff snapshot

_Generated 2026-09-26 13:13 by handoff.py — regenerate rather than edit._

## In progress

Learning loop committed as 1422c89 on cursor/emergency-card-paramedic-fields. Confirmed layouts key off structure; review chips re-extract; apply-review confirms; sibling_date for same-structure pages within 2h. PWA v126. Not deployed. Next: multi-photo merge when page 2 has a different structure. Leave the leftover credential/test scripts untracked.

## Git

**Branch:** `cursor/emergency-card-paramedic-fields`  
**Uncommitted files:** 20

> Uncommitted work is the main handoff hazard: the next agent
> cannot tell finished edits from half-written ones. Commit
> before switching, even as `wip:`.

```
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
?? verify_wai_tse.py
```

Recent commits:

```
1422c89 Remember confirmed report layouts and reuse them on the next scan.
648c52b Handoff: spirometry-table parsing fix deployed
ca3e72a Classify report-table column roles before extracting test results
f7df04e Handoff: read-only emergency icon + security hardening (SW v124)
1a7c641 Make emergency icon read-only mirror; bilingual crisis signals
3a2331e Handoff: auto reply-language deployed (SW v123)
46c64e7 Add 'auto' reply-language mode that mirrors the question's language
454519c push: send at high urgency so Doze doesn't defer reminders
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
