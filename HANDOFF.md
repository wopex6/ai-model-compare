# Handoff snapshot

_Generated 2026-09-17 21:12 by handoff.py — regenerate rather than edit._

## In progress

Dr. Health review + fixes: emergency card readable from the login screen without signing in (cached, dated), cached on every app start with persistent-storage request, service worker moved to the site root so it can claim scope /dr-health (allow-list + background revalidation + offline page), and per-browser install instructions that hide once installed. All deployed and verified on production. NOT yet fixed, in priority order: _facts_for_prompt() in ai_compare/health_insights.py feeds stopped meds/supplements to Tier 2 advice as VERIFIED FACTS; HealthProfile.save() is a direct overwrite and _load() substitutes a blank profile on corrupt JSON, so a crash mid-write can wipe a record; plaintext password in localStorage and un-namespaced chat/emergency caches that survive logout on a shared device; unescaped innerHTML in message_handler.js and the profile/emergency renderers; /emergency page still reads drHealth.vitals.v1, which the PWA deletes during its legacy migration, so it shows an empty card.

## Git

**Branch:** `main`  
**Uncommitted files:** 0

Recent commits:

```
6e7c430 install prompt: per-browser instructions, and hide it once installed
4f01c29 docs: AutoDoc regeneration from this session's test runs
80f16d8 pwa: serve the service worker from the root so it can claim /dr-health
8c62640 emergency card: cache it on every app start, and ask the OS to keep it
636cd67 emergency card: readable from the login screen without signing in
661203d pa_sync: derive deploy set from git ls-files, fetch concurrently
7dc75c2 dictation: retire the Whisper upload path; point to OS voice typing instead
f634433 fix(dictation): cut segments at natural pauses instead of a fixed clock
```

## Production (PythonAnywhere)

Local and production match.

```
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
ok       verify_wai_tse.py
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
........................................................................ [ 54%]
........................................................................ [ 72%]
........................................................................ [ 90%]
.....................................                                    [100%]
============================== warnings summary ===============================
..\..\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37
  C:\Users\trabc\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37: DeprecationWarning: datetime.datetime.utcfromtimestamp() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.fromtimestamp(timestamp, datetime.UTC).
    EPOCH = datetime.datetime.utcfromtimestamp(0)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
397 passed, 1 warning in 15.09s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
