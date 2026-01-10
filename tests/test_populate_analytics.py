"""
Comprehensive Analytics Population Test
Populates all analytics data boxes in Admin Dashboard.
"""
import time
import requests
from playwright.sync_api import sync_playwright

BASE_URL = "https://trabcd.pythonanywhere.com"
TEST_USER = "Wai Tse"
TEST_PASSWORD = "123"

# Messages to populate explicit context (goals, preferences, values, emotions)
CONTEXT_MESSAGES = [
    # Goals
    "My goal is to become a better programmer this year",
    "I want to improve my fitness and run a marathon",
    "My aim is to save $10,000 by December",
    
    # Preferences
    "I prefer morning workouts over evening ones",
    "I like detailed explanations with examples",
    "I prefer practical advice over theoretical discussions",
    
    # Values
    "I believe honesty is the most important virtue",
    "Family comes first for me in all decisions",
    "I value continuous learning and growth",
    
    # Emotional states
    "I'm feeling really motivated about my new project",
    "I've been a bit anxious about the upcoming deadline",
    "I'm excited to share my progress with you",
    
    # Self-descriptions
    "I'm an introvert who enjoys deep conversations",
    "I work as a software developer",
    
    # Intentions
    "I plan to start meditation next week",
    "I intend to read more books this month",
]

# Different character conversations to populate character effectiveness
CHARACTER_CONVERSATIONS = {
    'coordinator': [
        "What should I focus on today?",
        "Help me prioritize my tasks",
    ],
    'life_coach': [
        "How can I stay motivated?",
        "What's a good morning routine?",
    ],
    'psychologist': [
        "How do I handle stress better?",
        "Why do I procrastinate?",
    ],
    'stoic_philosopher': [
        "What does Stoicism teach about adversity?",
        "How can I be more resilient?",
    ],
    'career_mentor': [
        "Should I ask for a raise?",
        "How do I handle a difficult colleague?",
    ],
}

def run_analytics_population_test():
    print("=" * 60)
    print("📊 ANALYTICS POPULATION TEST")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    
    total_messages = 0
    total_responses = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        # Login
        print("\n🔐 Logging in...")
        page.goto(BASE_URL, timeout=60000)
        page.wait_for_load_state('networkidle')
        
        if page.query_selector('input[name="username"]:visible'):
            page.fill('input[name="username"]', TEST_USER)
            page.fill('input[name="password"]', TEST_PASSWORD)
            page.click('button[type="submit"]')
            page.wait_for_timeout(3000)
        print("  ✅ Logged in")
        
        # Navigate to Life Companion
        print("\n🎭 Navigating to Life Companion...")
        page.goto(f"{BASE_URL}/life-companion", timeout=60000)
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)
        
        # Dismiss notifications
        try:
            page.evaluate("document.querySelectorAll('#ai-budget-notification, .notification').forEach(n => n.style.display = 'none')")
        except:
            pass
        
        # 1. Send context-rich messages to populate explicit context
        print("\n📝 Populating Explicit Context...")
        for msg in CONTEXT_MESSAGES[:10]:  # Limit to avoid rate limiting
            print(f"  📤 {msg[:40]}...")
            
            input_field = page.query_selector('#userInput, textarea#userInput')
            if input_field:
                input_field.fill(msg)
                send_btn = page.query_selector('#sendBtn')
                if send_btn:
                    send_btn.click()
                    total_messages += 1
                    
                    # Wait for response
                    try:
                        page.wait_for_selector('.typing-indicator:visible', timeout=5000)
                    except:
                        pass
                    try:
                        page.wait_for_selector('.typing-indicator:not(:visible)', timeout=30000)
                    except:
                        pass
                    
                    # Check for response
                    responses = page.query_selector_all('.message.bot-message')
                    if responses:
                        total_responses += 1
                    
                    page.wait_for_timeout(1000)
        
        print(f"  ✅ Sent {total_messages} context messages")
        
        # 2. Test with different characters for character effectiveness
        print("\n🎭 Testing Character Effectiveness...")
        for char_id, messages in list(CHARACTER_CONVERSATIONS.items())[:3]:  # Limit
            print(f"\n  Character: {char_id}")
            
            # Try to select character
            char_btn = page.query_selector(f'.domain-char-item[data-character-id="{char_id}"]')
            if char_btn:
                char_btn.click()
                page.wait_for_timeout(1500)
                print(f"    ✅ Selected {char_id}")
            
            for msg in messages[:1]:  # One message per character
                print(f"    📤 {msg[:30]}...")
                input_field = page.query_selector('#userInput')
                if input_field:
                    input_field.fill(msg)
                    send_btn = page.query_selector('#sendBtn')
                    if send_btn:
                        send_btn.click()
                        total_messages += 1
                        
                        try:
                            page.wait_for_selector('.typing-indicator:visible', timeout=5000)
                        except:
                            pass
                        try:
                            page.wait_for_selector('.typing-indicator:not(:visible)', timeout=30000)
                        except:
                            pass
                        
                        responses = page.query_selector_all('.message.bot-message')
                        if responses:
                            total_responses += 1
                        
                        page.wait_for_timeout(1000)
        
        # 3. Check explicit context via API
        print("\n📊 Verifying Context Data...")
        try:
            result = page.evaluate('''async () => {
                const r = await fetch('/api/user/explicit-context', {credentials: 'include'});
                return { status: r.status, data: await r.json() };
            }''')
            if result['status'] == 200:
                contexts = result['data'].get('contexts', [])
                print(f"  ✅ Explicit context items: {len(contexts)}")
                
                # Count by type
                by_type = {}
                for ctx in contexts:
                    t = ctx.get('context_type', 'unknown')
                    by_type[t] = by_type.get(t, 0) + 1
                for t, count in by_type.items():
                    print(f"    - {t}: {count}")
        except Exception as e:
            print(f"  ⚠️ Could not verify context: {e}")
        
        # 4. Check smart response analytics
        print("\n📈 Checking Analytics APIs...")
        try:
            result = page.evaluate('''async () => {
                const r = await fetch('/api/admin/smart-response-analytics', {credentials: 'include'});
                return { status: r.status, data: await r.json() };
            }''')
            if result['status'] == 200:
                data = result['data']
                print(f"  ✅ Smart Response Analytics:")
                if 'character_stats' in data:
                    print(f"    - Character stats: {len(data.get('character_stats', {}))} items")
                if 'explicit_context_stats' in data:
                    stats = data['explicit_context_stats']
                    print(f"    - Context stats: {stats.get('total_items', 0)} items")
        except Exception as e:
            print(f"  ⚠️ Analytics error: {e}")
        
        # 5. Navigate to admin analytics to verify
        print("\n🔍 Checking Admin Analytics Dashboard...")
        page.goto(f"{BASE_URL}/admin/analytics", timeout=60000)
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(3000)
        
        # Check key elements
        checks = [
            ('total-users', 'Total Users'),
            ('total-messages', 'Total Messages'),
            ('ai-calls-today', 'AI Calls Today'),
            ('context-items', 'Context Items'),
            ('cost-today', 'Cost Today'),
        ]
        
        for elem_id, name in checks:
            elem = page.query_selector(f'#{elem_id}')
            if elem:
                value = elem.text_content()
                print(f"  {name}: {value}")
        
        browser.close()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Messages sent: {total_messages}")
    print(f"AI responses: {total_responses}")
    print("\n✅ Test complete! Refresh Admin Analytics to see updated data.")

if __name__ == "__main__":
    run_analytics_population_test()
