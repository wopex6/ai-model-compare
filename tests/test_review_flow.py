"""
Playwright test for the Dr. Health PWA photo/review flow.
"""
import sys
import os
import time
import requests
import uuid

from playwright.sync_api import sync_playwright

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5050'

def make_user():
    suffix = uuid.uuid4().hex[:10]
    username = f'uitest_{suffix}'
    resp = requests.post(f'{BASE_URL}/api/auth/signup', timeout=60, json={
        'username': username,
        'email': f'{username}@example.com',
        'password': 'TestPass123!',
    })
    resp.raise_for_status()
    return username, 'TestPass123!'

def make_png(path):
    # Minimal 1x1 PNG
    png = bytes.fromhex(
        '89504e470d0a1a0a0000000d49484452'
        '000000010000000108060000001f15c4'
        '890000000b49444154789c6300010000'
        '0500010dd9a4a40000000049454e44ae'
        '426082'
    )
    with open(path, 'wb') as f:
        f.write(png)

def main():
    username, password = make_user()
    print(f'Created user {username}')

    png_path = 'test_review.png'
    make_png(png_path)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 390, 'height': 844},
            user_agent='Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
        )
        page = context.new_page()
        logs = []
        def handle_console(msg):
            logs.append(f'[{msg.type}] {msg.text}')
        page.on('console', handle_console)
        page.on('pageerror', lambda err: logs.append(f'[pageerror] {err}'))

        # Log in via API to get token, then set localStorage and reload
        resp = requests.post(f'{BASE_URL}/api/auth/login', timeout=60, json={
            'username': username,
            'password': password,
        })
        resp.raise_for_status()
        token = resp.json()['token']

        page.goto(f'{BASE_URL}/dr-health')
        page.evaluate('(token) => { localStorage.setItem("authToken", token); }', token)
        page.reload(wait_until='load')

        # Log in via the login form if token was not picked up
        if page.is_visible('#login-screen'):
            page.fill('#login-username', username)
            page.fill('#login-password', password)
            page.click('#login-btn')
            page.wait_for_selector('#login-screen.hidden', timeout=15000)

        # Go to Records screen
        page.evaluate('() => showScreen("profile-screen")')
        page.wait_for_selector('#profile-screen.active, #profile-screen:not([hidden])', timeout=5000)

        # Mock the upload endpoint so no AI calls are made
        page.route('**/api/health-profile/upload', lambda route, request: route.fulfill(
            status=200,
            content_type='application/json',
            body='{"success":true,"pending_review":{"test_results":[{"test_name":"Glucose","value":"90","reference_range":"70-100","date":"","notes":""}]},"source_file":"test_review.png","extracted_text":"Glucose 90","extracted_text_preview":"Glucose 90","stored_document":"test_review.png"}'
        ))

        # Upload the fake file via the hidden input
        page.set_input_files('#profile-file', png_path)

        page.wait_for_selector('#photo-preview', state='visible', timeout=5000)
        page.click('#accept-photo-btn')

        # Wait for status and review button
        page.wait_for_selector('#review-action', state='visible', timeout=10000)
        page.wait_for_timeout(500)
        status = page.text_content('#profile-status')
        print('profile-status:', status.strip())

        # The modal should not auto-open after a photo upload; the Review button opens it
        if page.locator('#review-modal.active').is_visible():
            print('FAIL: Modal auto-opened after photo upload')
        else:
            print('OK: Modal did not auto-open, Review button visible')

        # Click the Review button and verify modal
        page.locator('#review-latest-btn').click()
        modal = page.locator('#review-modal')
        try:
            modal.wait_for(state='visible', timeout=5000)
            modal_text = modal.inner_text()
            print('modal visible, text:', modal_text[:200])
            if 'test results' in modal_text.lower() or 'glucose' in modal_text.lower() or 'test_name' in modal_text:
                print('PASS: Review button opened the review modal with data')
            else:
                print('FAIL: Modal opened but did not contain expected data')
        except Exception as e:
            print('FAIL: Review button did not open modal:', e)
            print('Logs:', logs[-20:])

        browser.close()

if __name__ == '__main__':
    main()
