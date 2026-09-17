"""
Compare local files against what is actually deployed on PythonAnywhere and
upload the stale ones through the Files API.

The console-based deploy path is unreliable (consoles must be opened in a
browser before they will execute input), so this verifies byte-for-byte
instead of assuming a git pull succeeded.

    python pa_sync.py            # report only
    python pa_sync.py --push     # upload stale files, then reload the web app
"""
import hashlib
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import requests

import deploy_anywhere as d

HEADERS = {'Authorization': f'Token {d.API_TOKEN}'}
REMOTE_ROOT = '/home/trabcd/ai-model-compare'

_HERE = os.path.dirname(os.path.abspath(__file__))

# Deploy set = every tracked text file, minus explicit exclusions.  A manual
# FILES list silently stopped covering new files — 105 tracked source files
# were missing from it, and pa_sync reported "everything matches" while
# production ran stale code.  Deriving from `git ls-files` cannot drift.
_EXCLUDE_DIRS = (
    'vendor/',                     # binary wheels — raw upload only
    'node_modules/',
    'health_profiles/',            # patient data (gitignored, belt+braces)
    'health_uploaded_documents/',  # patient data (gitignored, belt+braces)
)
_EXCLUDE_FILES = {
    'pa_sync.py', 'deploy_anywhere.py', 'handoff.py',
    '.env', '.gitignore', '.gitattributes',
    'nul',                         # reserved device name on Windows
}
_EXCLUDE_EXT = (
    '.png', '.ico', '.jpg', '.jpeg', '.gif', '.webp', '.svg',
    '.woff', '.woff2', '.ttf', '.eot',
    '.whl', '.zip', '.gz', '.mp3', '.mp4', '.webm', '.m4a', '.pdf',
    '.db', '.sqlite', '.sqlite3', '.pyc',
)


def deploy_files():
    out = subprocess.run(['git', 'ls-files'], capture_output=True,
                         text=True, cwd=_HERE)
    if out.returncode != 0:
        raise SystemExit('git ls-files failed: ' + out.stderr.strip())
    files = []
    for rel in out.stdout.splitlines():
        if rel in _EXCLUDE_FILES or rel.startswith(_EXCLUDE_DIRS):
            continue
        if '.~lock.' in rel or rel.lower().endswith(_EXCLUDE_EXT):
            continue
        if not os.path.exists(os.path.join(_HERE, rel)):
            continue  # tracked but cannot exist locally (e.g. 'aux', 'nul')
        files.append(rel)
    return files


FILES = deploy_files()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def remote_url(rel):
    return f'{d.API_BASE}/files/path{REMOTE_ROOT}/{rel}'


def fetch_remote(rel, tries=3):
    """GET the remote file. Returns response, or None after repeated failures.

    ~450 files are fetched per run — one flaky request must not abort it."""
    for attempt in range(tries):
        try:
            return requests.get(remote_url(rel), headers=HEADERS, timeout=120)
        except requests.RequestException as e:
            if attempt == tries - 1:
                print(f'ERROR    {rel}  ({type(e).__name__} after {tries} tries)')
                return None


def local_bytes(rel):
    return open(rel, 'rb').read().replace(b'\r\n', b'\n')


def main():
    push = '--push' in sys.argv
    stale = []
    errors = []

    # ~450 remote fetches — done concurrently or this takes ~15 minutes.
    results = {}
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(fetch_remote, rel): rel for rel in FILES}
        for fut, rel in futures.items():
            results[rel] = fut.result()

    for rel in FILES:
        resp = results[rel]
        if resp is None:
            errors.append(rel)
            continue
        if resp.status_code != 200:
            print(f'MISSING  {rel}  (remote {resp.status_code})')
            stale.append(rel)
            continue
        remote = resp.content.replace(b'\r\n', b'\n')
        if digest(local_bytes(rel)) == digest(remote):
            print(f'ok       {rel}')
        else:
            print(f'STALE    {rel}  local={digest(local_bytes(rel))} remote={digest(remote)}')
            stale.append(rel)

    if not stale:
        print('\nEverything on the server matches local.')
        return 1 if errors else 0

    if not push:
        print(f'\n{len(stale)} file(s) stale. Re-run with --push to upload.')
        return 1

    print()
    for rel in stale:
        content = local_bytes(rel)
        resp = requests.post(remote_url(rel), headers=HEADERS, timeout=120,
                             files={'content': (rel.split('/')[-1], content)})
        print(f'uploaded {rel}  -> {resp.status_code}')

    print('\nVerifying...')
    bad = 0
    for rel in stale:
        resp = fetch_remote(rel)
        remote = resp.content.replace(b'\r\n', b'\n') if resp else b''
        ok = resp is not None and digest(local_bytes(rel)) == digest(remote)
        print(f'{"ok      " if ok else "MISMATCH"} {rel}')
        bad += 0 if ok else 1

    if bad:
        return 1

    print('\nReloading web app...')
    resp = requests.post(f'{d.API_BASE}/webapps/trabcd.pythonanywhere.com/reload/',
                         headers=HEADERS, timeout=180)
    print('reload ->', resp.status_code, resp.text[:200])
    return 0


if __name__ == '__main__':
    sys.exit(main())
