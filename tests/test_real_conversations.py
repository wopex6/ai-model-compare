"""
Real Conversation Test
Runs actual AI conversations to populate analytics data.
"""
import time
import requests
from playwright.sync_api import sync_playwright

BASE_URL = "https://trabcd.pythonanywhere.com"
TEST_USER = "Wai Tse"
TEST_PASSWORD = "123"

# Test conversations for different characters
TEST_CONVERSATIONS = [
    {
        "character": "life_coach",
        "messages": [
            "I want to improve my productivity this year",
            "What specific steps should I take?",
            "How do I stay motivated?"
        ]
    },
    {
        "character": "psychologist",
        "messages": [
            "I've been feeling stressed lately about work",
            "How can I manage these feelings better?",
        ]
    },
    {
        "character": "stoic_philosopher",
        "messages": [
            "What does it mean to live a good life?",
            "How do I handle disappointment?"
        ]
    },
    {
        "character": "career_mentor",
        "messages": [
            "Should I ask for a promotion at work?",
            "How do I prepare for the conversation?"
        ]
    },
    {
        "character": "financial_advisor",
        "messages": [
            "How should I start budgeting better?",
            "What's a good savings strategy?"
        ]
    }
]

def run_real_conversations():
    print("=" * 60)
    print("🤖 REAL AI CONVERSATION TEST")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    print(f"Conversations planned: {len(TEST_CONVERSATIONS)}")
    
    total_messages = 0
    total_responses = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        # Login
        print("\n🔐 Logging in...")
        page.goto(BASE_URL, timeout=30000)
        page.wait_for_load_state('networkidle')
        
        if page.query_selector('input[name="username"]:visible'):
            page.fill('input[name="username"]', TEST_USER)
            page.fill('input[name="password"]', TEST_PASSWORD)
            page.click('button[type="submit"]')
            page.wait_for_timeout(3000)
        print("  ✅ Logged in")
        
        # Go to Life Companion for domain characters
        print("\n🎭 Navigating to Life Companion...")
        page.goto(f"{BASE_URL}/life-companion", timeout=30000)
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)
        
        for conv in TEST_CONVERSATIONS:
            character = conv["character"]
            messages = conv["messages"]
            
            print(f"\n💬 Testing {character}...")
            
            # Try to select character (correct selector: dataset.characterId)
            char_btn = page.query_selector(f'.domain-char-item[data-character-id="{character}"]')
            if not char_btn:
                # Try alternate selectors
                char_btn = page.query_selector(f'[data-character-id="{character}"]')
            if char_btn:
                char_btn.click()
                page.wait_for_timeout(1500)
                print(f"  ✅ Selected {character}")
            else:
                # List available characters for debugging
                available = page.query_selector_all('.domain-char-item')
                print(f"  ⚠️ Could not find {character}, found {len(available)} character buttons")
            
            for msg in messages:
                print(f"  📤 Sending: {msg[:40]}...")
                
                # Find input and send message
                input_field = page.query_selector('#userInput, textarea#userInput')
                if input_field:
                    input_field.fill(msg)
                    
                    send_btn = page.query_selector('#sendBtn, button:has-text("Send")')
                    if send_btn:
                        send_btn.click()
                        total_messages += 1
                        
                        # Wait for AI response (up to 30 seconds)
                        print("  ⏳ Waiting for AI response...")
                        
                        # Wait for typing indicator to appear and disappear
                        try:
                            page.wait_for_selector('.typing-indicator:visible', timeout=5000)
                        except:
                            pass
                        
                        try:
                            page.wait_for_selector('.typing-indicator:not(:visible)', timeout=30000)
                        except:
                            pass
                        
                        page.wait_for_timeout(2000)
                        
                        # Check for response (correct selectors for domain characters page)
                        responses = page.query_selector_all('.message.bot-message, .bot-message')
                        if responses:
                            total_responses += 1
                            last_response = responses[-1].text_content()[:100] if responses else ""
                            print(f"  📥 Response received ({len(responses)} messages)")
                        else:
                            print("  ⚠️ No visible response found")
                else:
                    print("  ❌ Input field not found")
                
                # Small delay between messages
                page.wait_for_timeout(1000)
        
        # Check analytics
        print("\n📊 Checking Analytics Dashboard...")
        page.goto(f"{BASE_URL}/admin/analytics", timeout=30000)
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)
        
        # Check for data
        stats_cards = page.query_selector_all('.stat-card, .stats-card')
        print(f"  Stats cards found: {len(stats_cards)}")
        
        # Get some stats values
        for card in stats_cards[:4]:
            text = card.text_content().strip()[:50]
            print(f"  📈 {text}")
        
        browser.close()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Messages sent: {total_messages}")
    print(f"AI responses received: {total_responses}")
    print(f"Characters tested: {len(TEST_CONVERSATIONS)}")
    
    # Test API endpoints to verify data
    print("\n🔌 Verifying API Data...")
    
    endpoints = [
        ('/api/analytics/engagement', 'Engagement'),
        ('/api/analytics/conversations', 'Conversations'),
        ('/api/analytics/hourly', 'Hourly Activity'),
    ]
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ {name}: {data}")
            else:
                print(f"  ⚠️ {name}: {response.status_code}")
        except Exception as e:
            print(f"  ❌ {name}: {e}")
    
    print("\n✅ Test complete!")
    return total_messages, total_responses

if __name__ == "__main__":
    run_real_conversations()
