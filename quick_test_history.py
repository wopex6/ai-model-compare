"""
Quick test to verify the history fix works
"""

from playwright.sync_api import sync_playwright
import time
import json

def quick_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        page = browser.new_context().new_page()
        
        # Track API responses
        responses = []
        
        def capture_response(response):
            if '/scientist/chat' in response.url or '/scientist/history' in response.url:
                try:
                    body = response.json()
                    responses.append({
                        'url': response.url,
                        'status': response.status,
                        'body': body
                    })
                    print(f"\n{'='*60}")
                    print(f"API: {response.url}")
                    print(f"Status: {response.status}")
                    print(f"Response: {json.dumps(body, indent=2)}")
                    print('='*60)
                except:
                    pass
        
        page.on("response", capture_response)
        
        print("\n=== LOGIN ===")
        page.goto("http://localhost:5000")
        time.sleep(1)
        page.fill('input[name="username"]', 'Wai Tse')
        page.fill('input[name="password"]', '123')
        page.click('button[type="submit"]')
        time.sleep(2)
        
        print("\n=== GO TO SCIENTIST ===")
        page.goto("http://localhost:5000/scientist")
        time.sleep(3)
        
        print("\n=== SEND MESSAGE ===")
        test_msg = f"Quick test {int(time.time())}"
        page.fill('#userInput', test_msg)
        page.click('.send-btn-sci')
        
        # Wait for response
        print("Waiting for AI response (10 seconds)...")
        time.sleep(10)
        
        # Check responses
        print("\n=== SUMMARY ===")
        chat_responses = [r for r in responses if '/chat' in r['url']]
        history_responses = [r for r in responses if '/history' in r['url']]
        
        print(f"Chat API calls: {len(chat_responses)}")
        print(f"History API calls: {len(history_responses)}")
        
        if chat_responses:
            last_chat = chat_responses[-1]['body']
            if 'error' in last_chat:
                print(f"\n❌ ERROR: {last_chat['error']}")
                print("❌ FIX FAILED - Still getting errors!")
            else:
                print(f"\n✅ SUCCESS: Got response without error")
                if 'response' in last_chat:
                    print(f"Response preview: {last_chat['response'][:100]}...")
        
        # Count messages on page
        user_msgs = page.query_selector_all('.message-sci.user')
        bot_msgs = page.query_selector_all('.message-sci.bot')
        print(f"\nMessages on page:")
        print(f"  User: {len(user_msgs)}")
        print(f"  Bot: {len(bot_msgs)}")
        
        if len(bot_msgs) > 0:
            print("\n✅ BOT RESPONSE VISIBLE - Fix working!")
        else:
            print("\n❌ NO BOT RESPONSE - Still broken!")
        
        print("\nPress Enter to close...")
        input()
        browser.close()

if __name__ == "__main__":
    quick_test()
