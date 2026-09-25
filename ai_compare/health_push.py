"""Web Push delivery for Dr. Health reminders.

Subscriptions are stored in health_profiles/push_subscriptions.json — inside
the gitignored patient-data directory, so endpoints never enter git or the
deploy set. Sending uses pywebpush; production has no pip shell, so the wheels
are vendored under vendor/ and added to sys.path on demand.

The daily dispatch is run by push_dispatch.py (a PythonAnywhere scheduled
task), not by the web app — the web process should never block on push calls.
"""
import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = _REPO_ROOT / 'health_profiles'
SUBS_PATH = DATA_DIR / 'push_subscriptions.json'

_VAPID_EMAIL_DEFAULT = 'mailto:dr-health@trabcd.pythonanywhere.com'


def _env(name, default=''):
    """Read an env var, falling back to a naive .env parse for the scheduled
    task, which runs outside the Flask app that calls load_dotenv()."""
    val = os.environ.get(name)
    if val:
        return val
    env_file = _REPO_ROOT / '.env'
    try:
        for line in env_file.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line.startswith(name + '='):
                return line.split('=', 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return default


def vapid_public_key():
    return _env('VAPID_PUBLIC_KEY')


def push_configured():
    return bool(_env('VAPID_PRIVATE_KEY') and _env('VAPID_PUBLIC_KEY'))


def _import_pywebpush():
    try:
        import pywebpush  # noqa: F401 — installed locally
    except ImportError:
        vendor = _REPO_ROOT / 'vendor'
        extracted = vendor / '_extracted'
        # cryptography and cffi ship .so files, which zipimport cannot load —
        # the wheels must be unpacked into a real directory first.
        if vendor.is_dir() and not (extracted / 'pywebpush').is_dir():
            import zipfile
            extracted.mkdir(parents=True, exist_ok=True)
            for wheel in sorted(vendor.glob('*.whl')):
                try:
                    zipfile.ZipFile(wheel).extractall(extracted)
                except Exception:
                    pass
        if str(extracted) not in sys.path:
            sys.path.append(str(extracted))
        import pywebpush  # noqa: F401
    return pywebpush


def load_subscriptions():
    try:
        data = json.loads(SUBS_PATH.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_subscriptions(subs):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = SUBS_PATH.with_suffix('.tmp')
    tmp.write_text(json.dumps(subs, indent=1), encoding='utf-8')
    tmp.replace(SUBS_PATH)


def add_subscription(user_id, sub):
    """Store a PushSubscription JSON for a user. Returns False when malformed."""
    user_id = str(user_id)
    endpoint = str((sub or {}).get('endpoint') or '')
    keys = (sub or {}).get('keys') or {}
    p256dh, auth = str(keys.get('p256dh') or ''), str(keys.get('auth') or '')
    if not endpoint.startswith('https://') or not p256dh or not auth:
        return False
    subs = load_subscriptions()
    entries = [e for e in subs.get(user_id, []) if e.get('endpoint') != endpoint]
    entries.append({
        'endpoint': endpoint,
        'keys': {'p256dh': p256dh, 'auth': auth},
        'created_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    })
    subs[user_id] = entries
    save_subscriptions(subs)
    return True


def remove_subscription(user_id, endpoint):
    subs = load_subscriptions()
    keep = [e for e in subs.get(str(user_id), [])
            if e.get('endpoint') != endpoint]
    if keep:
        subs[str(user_id)] = keep
    else:
        subs.pop(str(user_id), None)
    save_subscriptions(subs)


def subscriptions_for(user_id):
    return list(load_subscriptions().get(str(user_id), []))


def send_push(subscription, title, body, url='/dr-health'):
    """Send one push message. Raises on failure (incl. WebPushException)."""
    pywebpush = _import_pywebpush()
    pywebpush.webpush(
        subscription_info={
            'endpoint': subscription['endpoint'],
            'keys': subscription['keys'],
        },
        data=json.dumps({'title': title, 'body': body, 'url': url}),
        vapid_private_key=_env('VAPID_PRIVATE_KEY'),
        vapid_claims={'sub': _env('VAPID_CLAIMS_EMAIL', _VAPID_EMAIL_DEFAULT)},
        timeout=15,
    )


def _expired(exc):
    resp = getattr(exc, 'response', None)
    return resp is not None and resp.status_code in (404, 410)


def dispatch_due_reminders(today=None, send=send_push):
    """Push one summary notification to each subscribed device that has due
    reminders. Returns counts; prunes subscriptions the push service reports
    as gone (404/410)."""
    from ai_compare import health_insights

    today = today or date.today()
    subs = load_subscriptions()
    sent = failed = 0
    pruned = []
    for user_id, entries in list(subs.items()):
        prof_path = DATA_DIR / (str(user_id) + '.json')
        if not prof_path.exists():
            continue
        try:
            data = json.loads(prof_path.read_text(encoding='utf-8'))
        except Exception:
            continue
        settings = health_insights.advice_settings(data)
        if not settings.get('notifications_enabled') or not settings.get('reminders_enabled'):
            continue
        due = [r for r in health_insights.build_reminders(data, today)
               if r.get('status') in ('overdue', 'due_today')]
        if not due:
            continue
        top = due[0]
        body = ('%d reminder%s need%s attention — %s'
                % (len(due), '' if len(due) == 1 else 's',
                   's' if len(due) == 1 else '', top.get('title') or ''))
        for entry in entries:
            try:
                send(entry, 'Dr. Health', body)
                sent += 1
            except Exception as exc:
                failed += 1
                if _expired(exc):
                    pruned.append((user_id, entry.get('endpoint')))
    for user_id, endpoint in pruned:
        entries = [e for e in subs.get(user_id, [])
                   if e.get('endpoint') != endpoint]
        if entries:
            subs[user_id] = entries
        else:
            subs.pop(user_id, None)
    if pruned:
        save_subscriptions(subs)
    return {'sent': sent, 'failed': failed, 'pruned': len(pruned)}
