"""PythonAnywhere scheduled-task entry: push due reminders to subscribed
devices. Runs once daily; the web app itself never sends push."""
from ai_compare.health_push import dispatch_due_reminders, push_configured

if __name__ == '__main__':
    if not push_configured():
        print('push not configured (VAPID keys missing)')
    else:
        print(dispatch_due_reminders())
