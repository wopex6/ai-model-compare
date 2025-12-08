"""
Playwright test to investigate conversation history issues
- Issue 1: Smart Response history not displayed
- Issue 2: Temporary AI problems
- Issue 3: Bot messages intermittently visible/invisible
"""

from playwright.sync_api import sync_playwright, expect
import time
import json

def investigate_history_issues():
    with sync_playwright() as p:
        # Launch browser with detailed logging
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context()
        
        # Enable console logging
        page = context.new_page()
        
        console_logs = []
        network_requests = []
        network_responses = []
        
        def log_console(msg):
            console_logs.append(f"[{msg.type}] {msg.text}")
            print(f"CONSOLE [{msg.type}]: {msg.text}")
        
        def log_request(request):
            if '/chat' in request.url or '/history' in request.url:
                network_requests.append({
                    'url': request.url,
                    'method': request.method,
                    'post_data': request.post_data
                })
                print(f"REQUEST: {request.method} {request.url}")
                if request.post_data:
                    print(f"  POST DATA: {request.post_data}")
        
        def log_response(response):
            if '/chat' in response.url or '/history' in response.url:
                try:
                    body = response.body()
                    network_responses.append({
                        'url': response.url,
                        'status': response.status,
                        'body': body.decode('utf-8')
                    })
                    print(f"RESPONSE: {response.status} {response.url}")
                    print(f"  BODY: {body.decode('utf-8')[:500]}")
                except Exception as e:
                    print(f"  Could not read body: {e}")
        
        page.on("console", log_console)
        page.on("request", log_request)
        page.on("response", log_response)
        
        print("\n=== STEP 1: LOGIN ===")
        page.goto("http://localhost:5000")
        time.sleep(1)
        
        # Login
        page.fill('input[name="username"]', 'Wai Tse')
        page.fill('input[name="password"]', '123')
        page.click('button[type="submit"]')
        time.sleep(2)
        
        print("\n=== STEP 2: NAVIGATE TO SCIENTIST ===")
        page.goto("http://localhost:5000/scientist")
        time.sleep(3)
        
        print("\n=== STEP 3: CHECK INITIAL HISTORY LOAD ===")
        # Wait for history to load
        time.sleep(2)
        
        # Count messages on page
        user_messages = page.query_selector_all('.message-sci.user, .message.user')
        bot_messages = page.query_selector_all('.message-sci.bot, .message.bot')
        
        print(f"✓ User messages visible: {len(user_messages)}")
        print(f"✓ Bot messages visible: {len(bot_messages)}")
        
        # Check if any messages exist
        if len(user_messages) > 0 or len(bot_messages) > 0:
            print("\n=== EXISTING CONVERSATION HISTORY ===")
            all_messages = page.query_selector_all('.message-sci, .message')
            for i, msg in enumerate(all_messages[:5]):
                text = msg.inner_text()[:100]
                print(f"  {i+1}. {text}")
        else:
            print("⚠️  No existing history found")
        
        print("\n=== STEP 4: SEND NEW MESSAGE ===")
        # Send a test message
        test_message = f"Test message at {time.time()}"
        page.fill('#userInput', test_message)
        
        print(f"Sending message: {test_message}")
        page.click('.send-btn-sci, .send-btn')
        
        # Wait for response (up to 30 seconds)
        print("Waiting for AI response...")
        time.sleep(5)
        
        # Check for response
        new_bot_messages = page.query_selector_all('.message-sci.bot, .message.bot')
        print(f"✓ Bot messages after send: {len(new_bot_messages)}")
        
        # Check if response contains error messages
        all_text = page.inner_text('body')
        if 'temporary' in all_text.lower() or 'error' in all_text.lower():
            print("\n⚠️  FOUND TEMPORARY/ERROR MESSAGE IN RESPONSE:")
            messages = page.query_selector_all('.message-sci, .message')
            for msg in messages[-3:]:
                print(f"  {msg.inner_text()[:200]}")
        
        print("\n=== STEP 5: LEAVE AND RETURN ===")
        page.goto("http://localhost:5000/chatchat")
        time.sleep(1)
        
        page.goto("http://localhost:5000/scientist")
        time.sleep(3)
        
        print("\n=== STEP 6: CHECK HISTORY AFTER RETURN ===")
        # Check if messages reappeared
        user_messages_after = page.query_selector_all('.message-sci.user, .message.user')
        bot_messages_after = page.query_selector_all('.message-sci.bot, .message.bot')
        
        print(f"✓ User messages after return: {len(user_messages_after)}")
        print(f"✓ Bot messages after return: {len(bot_messages_after)}")
        
        # NEW: Check CSS visibility of bot messages
        print("\n=== CHECKING BOT MESSAGE VISIBILITY ===")
        for i, bot_msg in enumerate(bot_messages_after[:3]):
            try:
                is_visible = bot_msg.is_visible()
                bounding_box = bot_msg.bounding_box()
                computed_style = page.evaluate('''(element) => {
                    const style = window.getComputedStyle(element);
                    return {
                        display: style.display,
                        visibility: style.visibility,
                        opacity: style.opacity,
                        textAlign: style.textAlign,
                        width: style.width,
                        height: style.height
                    };
                }''', bot_msg)
                
                print(f"  Bot message {i+1}:")
                print(f"    is_visible(): {is_visible}")
                print(f"    bounding_box: {bounding_box}")
                print(f"    CSS display: {computed_style['display']}")
                print(f"    CSS visibility: {computed_style['visibility']}")
                print(f"    CSS opacity: {computed_style['opacity']}")
                print(f"    CSS text-align: {computed_style['textAlign']}")
                print(f"    CSS width: {computed_style['width']}")
                print(f"    CSS height: {computed_style['height']}")
            except Exception as e:
                print(f"  Bot message {i+1}: ERROR - {e}")
        
        # Check for our test message
        page_text = page.inner_text('#chatMessages')
        if test_message[:20] in page_text:
            print(f"✓ Test message FOUND in history")
        else:
            print(f"✗ Test message NOT FOUND in history")
        
        print("\n=== ANALYSIS ===")
        
        # Check network requests
        chat_requests = [r for r in network_requests if '/chat' in r['url']]
        history_requests = [r for r in network_requests if '/history' in r['url']]
        
        print(f"Chat requests made: {len(chat_requests)}")
        print(f"History requests made: {len(history_requests)}")
        
        # Check responses
        chat_responses = [r for r in network_responses if '/chat' in r['url']]
        history_responses = [r for r in network_responses if '/history' in r['url']]
        
        print(f"Chat responses received: {len(chat_responses)}")
        print(f"History responses received: {len(history_responses)}")
        
        # Analyze history response
        if history_responses:
            print("\n=== HISTORY API RESPONSE ===")
            for resp in history_responses:
                try:
                    data = json.loads(resp['body'])
                    messages = data.get('messages', [])
                    print(f"Total messages in API: {len(messages)}")
                    
                    user_count = len([m for m in messages if m.get('role') == 'user'])
                    bot_count = len([m for m in messages if m.get('role') in ['assistant', 'bot']])
                    
                    print(f"  User messages: {user_count}")
                    print(f"  Assistant messages: {bot_count}")
                    
                    # Check for Smart Response artifacts
                    for i, msg in enumerate(messages[:5]):
                        content = msg.get('content', '')
                        if 'USER\'S EXPLICIT STATEMENTS' in content or 'Emotional state' in content or 'Goal:' in content:
                            print(f"\n⚠️  SMART RESPONSE ARTIFACT FOUND in message {i}:")
                            print(f"  {content[:200]}")
                except Exception as e:
                    print(f"Could not parse history response: {e}")
        
        # Check for errors in chat response
        if chat_responses:
            print("\n=== CHAT API RESPONSE ===")
            for resp in chat_responses[-1:]:  # Last chat response
                try:
                    data = json.loads(resp['body'])
                    if 'error' in data:
                        print(f"✗ ERROR in response: {data['error']}")
                    if 'response' in data:
                        response_text = data['response'][:200]
                        print(f"✓ Response: {response_text}")
                        
                        # Check for temporary/error messages
                        if 'temporary' in response_text.lower() or 'error' in response_text.lower():
                            print(f"\n⚠️  TEMPORARY AI PROBLEM DETECTED:")
                            print(f"  Full response: {data['response']}")
                except Exception as e:
                    print(f"Could not parse chat response: {e}")
        
        # Check console logs for errors
        error_logs = [log for log in console_logs if 'error' in log.lower()]
        if error_logs:
            print("\n=== CONSOLE ERRORS ===")
            for log in error_logs[-5:]:
                print(f"  {log}")
        
        print("\n=== SAVING DEBUG INFO ===")
        with open('playwright_debug_output.json', 'w') as f:
            json.dump({
                'console_logs': console_logs,
                'network_requests': network_requests,
                'network_responses': network_responses,
                'user_messages_count': len(user_messages_after),
                'bot_messages_count': len(bot_messages_after),
                'refresh_test_results': bot_message_counts
            }, f, indent=2)
        print("✓ Debug info saved to playwright_debug_output.json")
        
        # Take screenshot
        timestamp_str = str(int(time.time()))
        screenshot_path = f'test_screenshots/history_investigation_{timestamp_str}.png'
        page.screenshot(path=screenshot_path)
        print(f"✓ Screenshot saved to {screenshot_path}")
        
        # NEW: Test multiple refreshes to check for intermittent issues
        print("\n=== STEP 7: MULTIPLE REFRESH TEST (5 iterations) ===")
        bot_message_counts = []
        for iteration in range(5):
            print(f"\n  Iteration {iteration + 1}/5:")
            page.reload()
            time.sleep(3)
            
            user_msgs = page.query_selector_all('.message-sci.user, .message.user')
            bot_msgs = page.query_selector_all('.message-sci.bot, .message.bot')
            
            # Check visible bot messages
            visible_bot_msgs = [m for m in bot_msgs if m.is_visible()]
            
            print(f"    User messages: {len(user_msgs)}")
            print(f"    Bot messages (total): {len(bot_msgs)}")
            print(f"    Bot messages (visible): {len(visible_bot_msgs)}")
            
            bot_message_counts.append({
                'iteration': iteration + 1,
                'total': len(bot_msgs),
                'visible': len(visible_bot_msgs)
            })
            
            # If bot messages missing, take screenshot
            if len(bot_msgs) > 0 and len(visible_bot_msgs) < len(bot_msgs):
                screenshot_name = f'test_screenshots/bot_messages_missing_iter{iteration+1}.png'
                page.screenshot(path=screenshot_name)
                print(f"    ⚠️  MISMATCH! Screenshot: {screenshot_name}")
        
        print("\n  === CONSISTENCY CHECK ===")
        totals = [c['total'] for c in bot_message_counts]
        visibles = [c['visible'] for c in bot_message_counts]
        
        print(f"  Bot message totals: {totals}")
        print(f"  Bot message visible: {visibles}")
        
        if len(set(visibles)) > 1:
            print("  ⚠️  INTERMITTENT ISSUE CONFIRMED: Bot message visibility varies!")
        else:
            print("  ✓ Bot message visibility consistent across refreshes")
        
        # Keep browser open for manual inspection
        print("\n=== BROWSER OPEN FOR INSPECTION ===")
        print("Press Enter to close browser...")
        input()
        
        browser.close()

if __name__ == "__main__":
    investigate_history_issues()
