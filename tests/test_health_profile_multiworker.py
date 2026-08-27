"""
Regression test for cross-process staleness in HealthContextManager.

Health profiles are cached per process, but production serves requests from
several worker processes backed by the same JSON file. Before the fix, a worker
kept serving its stale in-memory copy after another worker wrote the file,
which produced "Index out of range" errors on edit/delete and could silently
overwrite the other worker's data.

    python tests/test_health_profile_multiworker.py
"""
import json
import sys
import uuid

sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))

from ai_compare.medical_advisor_health_context import (  # noqa: E402
    HealthContextManager,
    HealthProfile,
)


def check(name, ok, detail=''):
    print(('  PASS  ' if ok else '  FAIL  ') + name + ('' if ok else f'  -> {detail}'))
    return ok


def run():
    results = []
    user_id = f'multiworker_test_{uuid.uuid4().hex[:8]}'

    # Worker A caches the profile.
    worker_a = HealthContextManager.get_profile(user_id)
    worker_a.add_condition('First condition')
    worker_a.save()
    results.append(check('worker A wrote one condition',
                         len(worker_a.data['conditions']) == 1))

    # Worker B is a separate process: its own object, reading the same file.
    worker_b = HealthProfile(user_id)
    results.append(check('worker B sees worker A\'s write',
                         len(worker_b.data['conditions']) == 1,
                         str(worker_b.data['conditions'])))

    worker_b.add_condition('Second condition')
    worker_b.save()

    # The bug: worker A's cached copy never noticed worker B's write.
    refreshed = HealthContextManager.get_profile(user_id)
    results.append(check('worker A picks up worker B\'s write',
                         len(refreshed.data['conditions']) == 2,
                         f"saw {len(refreshed.data['conditions'])} conditions"))

    # Index 1 must be addressable from worker A, which is exactly what the
    # PWA does when it edits the row it just rendered.
    try:
        refreshed.data['conditions'][1]['status'] = 'resolved'
        refreshed.save()
        ok = True
        detail = ''
    except IndexError as e:
        ok = False
        detail = str(e)
    results.append(check('worker A can edit the row worker B added', ok, detail))

    # Worker A's save must not have dropped worker B's row.
    on_disk = json.loads(refreshed.file_path.read_text(encoding='utf-8'))
    results.append(check('no data lost after the cross-worker save',
                         len(on_disk['conditions']) == 2,
                         f"{len(on_disk['conditions'])} conditions on disk"))
    results.append(check('edit landed on the right row',
                         on_disk['conditions'][1].get('status') == 'resolved',
                         str(on_disk['conditions'][1])))

    # A no-op get must not needlessly reload.
    results.append(check('unchanged file is not reloaded',
                         HealthContextManager.get_profile(user_id).reload_if_stale() is False))

    refreshed.file_path.unlink(missing_ok=True)
    HealthContextManager._profiles.pop(user_id, None)

    passed = sum(1 for r in results if r)
    print(f'\nTOTAL {len(results)}   PASSED {passed}   FAILED {len(results) - passed}')
    return all(results)


if __name__ == '__main__':
    print('Cross-process health profile staleness')
    sys.exit(0 if run() else 1)
