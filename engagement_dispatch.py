"""PythonAnywhere scheduled-task entry: push due engagement prompts to
subscribed devices. Runs on a schedule; the web app itself never sends push.

Mirrors push_dispatch.py — pick_due_prompt enforces the one-prompt-per-quiet
-window rule itself, so whichever task runs first wins the slot.
"""
import json
from ai_compare import engagement
from ai_compare.health_push import send_push, push_configured


def dispatch_due_prompts():
    """One deterministic prompt per user, to their subscribed devices."""
    sent, skipped, errors = 0, 0, []
    subs = {}  # user_id -> [subscription dict]
    for row in engagement.all_push_subscriptions():
        subs.setdefault(row['user_id'], []).append(
            {'endpoint': row['endpoint'], 'keys': json.loads(row['keys_json'])})
    for user_id, devices in subs.items():
        prompt = engagement.pick_due_prompt(user_id)
        if not prompt:
            skipped += 1
            continue
        p = prompt['prompt']
        body = f"{p['text']} — {p['question']}"
        url = '/chatchat?thread=' + prompt['id']
        for sub in devices:
            try:
                send_push(sub, 'Life Companion', body, url=url)
                sent += 1
            except Exception as exc:
                errors.append(str(exc)[:200])
    return {'sent': sent, 'skipped_users': skipped, 'errors': errors}


if __name__ == '__main__':
    if not push_configured():
        print('push not configured (VAPID keys missing)')
    else:
        print(dispatch_due_prompts())
