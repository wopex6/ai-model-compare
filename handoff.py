"""
Snapshot the working state for the next agent (or the next you).

Sessions end abruptly — a quota runs out mid-task and the context is gone.
What survives is the repo, and the repo alone is ambiguous: uncommitted edits
could be finished or half-written, and local files may or may not match what
is actually running in production.

Run this before switching tools, or whenever a session might be near its end:

    python handoff.py                      # print the snapshot
    python handoff.py -m "what I was doing"  # also write HANDOFF.md
    python handoff.py --full               # include the slow full test suite

It answers the three questions a new agent otherwise has to guess at:
what changed, is production in sync, and does the code still pass.
Everything it reports is derived live — nothing is remembered between runs,
so it cannot go stale the way a hand-written note does.
"""
import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HANDOFF_FILE = ROOT / 'HANDOFF.md'

# The Windows console defaults to cp1252, which mangles the punctuation in this
# report. The file is always written as UTF-8; this only fixes the terminal.
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

# Fast, deterministic, no network. The full suite takes ~9 minutes and ends in
# three known failures, which is a poor default for a status check.
QUICK_TESTS = [
    'tests/test_health_freshness.py',
    'tests/test_health_advice_api.py',
    'tests/test_health_insights.py',
    'tests/test_web_enhancements.py',
]


def run(cmd, timeout=900):
    """Run a command, returning (ok, output). Never raises."""
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                           timeout=timeout, shell=False)
        return p.returncode == 0, (p.stdout + p.stderr).strip()
    except FileNotFoundError:
        return False, 'not installed: ' + cmd[0]
    except subprocess.TimeoutExpired:
        return False, 'timed out after %ss' % timeout


def section(title, body):
    return '## ' + title + '\n\n' + (body.strip() or '_(nothing)_') + '\n'


def git_state():
    _, branch = run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
    _, log = run(['git', 'log', '--oneline', '-8'])
    _, status = run(['git', 'status', '--short'])
    _, stat = run(['git', 'diff', '--stat', 'HEAD'])

    dirty = [l for l in status.splitlines() if l.strip()]
    out = '**Branch:** `%s`  \n**Uncommitted files:** %d\n\n' % (branch, len(dirty))
    if dirty:
        out += ('> Uncommitted work is the main handoff hazard: the next agent\n'
                '> cannot tell finished edits from half-written ones. Commit\n'
                '> before switching, even as `wip:`.\n\n')
        out += '```\n' + '\n'.join(dirty[:40]) + '\n```\n\n'
        if stat:
            out += '<details><summary>diff --stat</summary>\n\n```\n' + stat + '\n```\n</details>\n\n'
    out += 'Recent commits:\n\n```\n' + log + '\n```'
    return out


def deploy_state():
    """pa_sync with no --push only reports drift; it uploads nothing.

    The check covers every tracked file (~450), fetched concurrently (~2 min)."""
    ok, out = run([sys.executable, 'pa_sync.py'], timeout=900)
    lines = [l for l in out.splitlines() if l.strip()]
    drift = [l for l in lines if l.startswith(('STALE', 'MISSING', 'ERROR'))]
    verdict = ('Local and production match.' if not drift else
               '**%d file(s) differ from production.** Deploy with '
               '`python pa_sync.py --push`.' % len(drift))
    body = verdict + '\n\n```\n' + '\n'.join(lines[-25:]) + '\n```'
    if drift:
        body += ('\n\nReload often returns `409 slow_startup_error` on the first '
                 'attempt — retry rather than debug it.')
    return body


def test_state(full):
    cmd = [sys.executable, '-m', 'pytest', '-q']
    cmd += (['tests/', '--ignore=tests/test_character_insights_e2e.py']
            if full else QUICK_TESTS)
    ok, out = run(cmd, timeout=1800)
    tail = '\n'.join(out.splitlines()[-12:])
    head = ('All passing.' if ok else
            '**Failures present** — check them against the known-failing list '
            'in AGENTS.md before assuming they are yours.')
    return head + '\n\n```\n' + tail + '\n```'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('-m', '--message', default='',
                    help='what you were working on; writes HANDOFF.md')
    ap.add_argument('--full', action='store_true', help='run the full test suite')
    ap.add_argument('--no-tests', action='store_true')
    ap.add_argument('--no-deploy', action='store_true')
    args = ap.parse_args()

    parts = ['# Handoff snapshot\n',
             '_Generated %s by handoff.py — regenerate rather than edit._\n'
             % datetime.now().strftime('%Y-%m-%d %H:%M')]

    if args.message:
        parts.append(section('In progress', args.message))
    parts.append(section('Git', git_state()))
    if not args.no_deploy:
        parts.append(section('Production (PythonAnywhere)', deploy_state()))
    if not args.no_tests:
        parts.append(section('Tests', test_state(args.full)))
    parts.append(section('Next agent: read first', 'See AGENTS.md for the '
                         'deploy path, known-failing tests and the shared-module '
                         'conventions. Skipping it reliably wastes a session.'))

    report = '\n'.join(parts)
    print(report)
    if args.message:
        HANDOFF_FILE.write_text(report, encoding='utf-8')
        print('\nWrote ' + str(HANDOFF_FILE))
    return 0


if __name__ == '__main__':
    sys.exit(main())
