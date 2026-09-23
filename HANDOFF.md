# Handoff snapshot

_Generated 2026-09-23 17:09 by handoff.py — regenerate rather than edit._

## In progress

Deployed 26f1f76: unit:null treated as absent so embedded units strip correctly (was literal 'null' group unit). User may still need a hard refresh — cached lab_results.js serves old flag logic.

## Git

**Branch:** `cursor/emergency-card-paramedic-fields`  
**Uncommitted files:** 0

Recent commits:

```
26f1f76 lab results: treat unit:null as absent, not an explicit blank unit
1e53295 handoff: snapshot after false-L-flag fix deploy
2e127d6 lab results: fix false Low flags from '/L' units; per-row ref in overview
63e4ff8 handoff: snapshot after gallery/UTC/collapsible-docs deploy
1c7e3f8 records: gallery picker, UTC timestamps, collapsible stored documents
072358a handoff: snapshot after wrapped-table ref/unit recovery deploy
949cbfc records: timestamps on stored docs; recover ref/unit from wrapped lab tables
59d782f handoff: snapshot after stored-review and busy-button deploy
```

## Production (PythonAnywhere)

Local and production match.

```
timed out after 900s
```

## Tests

All passing.

```
........................................................................ [ 52%]
........................................................................ [ 70%]
........................................................................ [ 88%]
.................................................                        [100%]
============================== warnings summary ===============================
..\..\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37
  C:\Users\trabc\AppData\Roaming\Python\Python312\site-packages\dateutil\tz\tz.py:37: DeprecationWarning: datetime.datetime.utcfromtimestamp() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.fromtimestamp(timestamp, datetime.UTC).
    EPOCH = datetime.datetime.utcfromtimestamp(0)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
409 passed, 1 warning in 42.27s
[AutoDoc] Monitoring stopped
```

## Next agent: read first

See AGENTS.md for the deploy path, known-failing tests and the shared-module conventions. Skipping it reliably wastes a session.
