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
import sys

import requests

import deploy_anywhere as d

HEADERS = {'Authorization': f'Token {d.API_TOKEN}'}
REMOTE_ROOT = '/home/trabcd/ai-model-compare'

FILES = [
    'app.py',
    'requirements.txt',
    'ai_compare/medical_advisor_health_context.py',
    'ai_compare/health_insights.py',
    'ai_compare/health_freshness.py',
    'ai_compare/character_routes.py',
    'ai_compare/base_enhanced_chatbot.py',
    'templates/dr_health_app.html',
    'templates/health_profile.html',
    'templates/medical_advisor.html',
    'templates/chatchat.html',
    'static/dr_health_hub.js',
    'static/lab_results.js',
    'static/health_review.js',
    'static/health_dictation.js',
    'static/multi_user_app.js',
    'static/conversation_box.js',
    'static/dr_health_sw.js',
    'static/dr_health_manifest.json',
]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def remote_url(rel):
    return f'{d.API_BASE}/files/path{REMOTE_ROOT}/{rel}'


def main():
    push = '--push' in sys.argv
    stale = []

    for rel in FILES:
        local = open(rel, 'rb').read().replace(b'\r\n', b'\n')
        resp = requests.get(remote_url(rel), headers=HEADERS, timeout=120)
        if resp.status_code != 200:
            print(f'MISSING  {rel}  (remote {resp.status_code})')
            stale.append(rel)
            continue
        remote = resp.content.replace(b'\r\n', b'\n')
        if digest(local) == digest(remote):
            print(f'ok       {rel}')
        else:
            print(f'STALE    {rel}  local={digest(local)} remote={digest(remote)}')
            stale.append(rel)

    if not stale:
        print('\nEverything on the server matches local.')
        return 0

    if not push:
        print(f'\n{len(stale)} file(s) stale. Re-run with --push to upload.')
        return 1

    print()
    for rel in stale:
        content = open(rel, 'rb').read().replace(b'\r\n', b'\n')
        resp = requests.post(remote_url(rel), headers=HEADERS, timeout=120,
                             files={'content': (rel.split('/')[-1], content)})
        print(f'uploaded {rel}  -> {resp.status_code}')

    print('\nVerifying...')
    bad = 0
    for rel in stale:
        local = open(rel, 'rb').read().replace(b'\r\n', b'\n')
        remote = requests.get(remote_url(rel), headers=HEADERS,
                              timeout=120).content.replace(b'\r\n', b'\n')
        ok = digest(local) == digest(remote)
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
