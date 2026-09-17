# Handoff snapshot

_Generated 2026-09-17 16:08 by handoff.py — regenerate rather than edit._

## In progress

Made pa_sync derive the deploy set from git ls-files (was a manual 19-file list missing 105 tracked files), added fetch retries, pushed the 16 stale/missing files, un-ignored HANDOFF.md, untracked .~lock junk. Dictation: Whisper upload path retired; OS voice typing is the fallback.

## Git

**Branch:** `main`  
**Uncommitted files:** 9

> Uncommitted work is the main handoff hazard: the next agent
> cannot tell finished edits from half-written ones. Commit
> before switching, even as `wip:`.

```
M .gitignore
D  .~lock.app.py#
 M AGENTS.md
D  ai_compare/.~lock.chatbot.py#
D  ai_compare/.~lock.conversation_manager.py#
D  ai_compare/.~lock.motivational_system.py#
 M handoff.py
 M pa_sync.py
?? HANDOFF.md
```

<details><summary>diff --stat</summary>

```
.gitignore                                 |   4 +-
 .~lock.app.py#                             |   1 -
 AGENTS.md                                  |  12 +++-
 ai_compare/.~lock.chatbot.py#              |   1 -
 ai_compare/.~lock.conversation_manager.py# |   1 -
 ai_compare/.~lock.motivational_system.py#  |   1 -
 handoff.py                                 |   8 ++-
 pa_sync.py                                 | 105 ++++++++++++++++++++---------
 8 files changed, 91 insertions(+), 42 deletions(-)
warning: LF will be replaced by CRLF in .gitignore.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in AGENTS.md.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in handoff.py.
The file will have its original line endings in your working directory
warning: LF will be replaced by CRLF in pa_sync.py.
The file will have its original line endings in your working directory
```
</details>

Recent commits:

```
7dc75c2 dictation: retire the Whisper upload path; point to OS voice typing instead
f634433 fix(dictation): cut segments at natural pauses instead of a fixed clock
867e7a0 dictation: live mic-level readout, zh-HK fallback, named speech errors
ce1f6ab fix(dictation): skip silent segments before uploading to transcriber
da47a1e fix(dictation): auto-fallback to recorder when SpeechRecognition is broken
207a274 dictation: move website pill clear of browser-extension mic zone, add to medical_advisor chat
22c9704 fix(dictation): handle commands embedded mid-segment + cache-bust script
889adc4 fix(dictation): upload path now runs full command/punctuation pipeline
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
397 passed, 1 warning in 13.25s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
