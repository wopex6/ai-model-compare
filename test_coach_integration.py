#!/usr/bin/env python3
"""
Test Script for Coach Smart Response Integration
Tests the /coach/chat endpoint with various message types
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
LOGIN_URL = f"{BASE_URL}/api/auth/login"
COACH_CHAT_URL = f"{BASE_URL}/coach/chat"
STATS_URL = f"{BASE_URL}/api/smart-response/stats"

# Test credentials (use your actual credentials)
USERNAME = "Wai Tse"
PASSWORD = "your_password"  # UPDATE THIS

def get_auth_token():
    """Login and get JWT token"""
    response = requests.post(LOGIN_URL, json={
        'username': USERNAME,
        'password': PASSWORD
    })
    
    if response.status_code == 200:
        data = response.json()
        return data.get('token')
    else:
        print(f"❌ Login failed: {response.json()}")
        return None

def test_coach_message(token, message):
    """Send a message to Coach and measure response"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    start_time = time.time()
    response = requests.post(COACH_CHAT_URL, 
        headers=headers,
        json={'message': message}
    )
    end_time = time.time()
    
    response_time = (end_time - start_time) * 1000  # Convert to ms
    
    if response.status_code == 200:
        data = response.json()
        response_type = data.get('type', 'unknown')
        response_text = data.get('response', '')[:100]  # First 100 chars
        confidence = data.get('confidence', 0)
        
        # Emoji based on type
        emoji = "⚡" if response_type == 'quick_reply' else "🤖"
        
        print(f"\n{emoji} Message: \"{message}\"")
        print(f"   Type: {response_type}")
        print(f"   Time: {response_time:.0f}ms")
        if confidence:
            print(f"   Confidence: {confidence:.2f}")
        print(f"   Response: \"{response_text}...\"")
        
        return {
            'type': response_type,
            'time': response_time,
            'confidence': confidence
        }
    else:
        print(f"\n❌ Error: {response.json()}")
        return None

def get_stats(token):
    """Get smart response statistics"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(STATS_URL, headers=headers)
    
    if response.status_code == 200:
        return response.json().get('stats')
    else:
        print(f"❌ Stats error: {response.json()}")
        return None

def main():
    print("=" * 80)
    print("COACH SMART RESPONSE INTEGRATION TEST")
    print("=" * 80)
    print()
    
    # Login
    print("🔐 Logging in...")
    token = get_auth_token()
    if not token:
        print("❌ Cannot proceed without authentication")
        return
    print("✅ Logged in successfully")
    
    # Test messages
    test_cases = [
        ("hi", "greeting - should be quick"),
        ("thanks for your help", "thanks - should be quick"),
        ("I'm struggling with my motivation and feel lost about my goals", "complex - should be full AI"),
        ("ok", "acknowledgment - should be quick"),
        ("yes", "agreement - should be quick"),
        ("how can I improve my productivity?", "question - should be full AI"),
        ("got it", "acknowledgment - should be quick"),
        ("thank you", "thanks - should be quick"),
        ("bye", "farewell - should be quick"),
    ]
    
    print("\n" + "=" * 80)
    print("TESTING MESSAGES")
    print("=" * 80)
    
    quick_count = 0
    ai_count = 0
    total_quick_time = 0
    total_ai_time = 0
    
    for message, description in test_cases:
        print(f"\n📝 Test: {description}")
        result = test_coach_message(token, message)
        
        if result:
            if result['type'] == 'quick_reply':
                quick_count += 1
                total_quick_time += result['time']
            elif result['type'] == 'full_ai':
                ai_count += 1
                total_ai_time += result['time']
        
        time.sleep(0.5)  # Small delay between tests
    
    # Get final stats
    print("\n" + "=" * 80)
    print("LEARNING STATISTICS")
    print("=" * 80)
    
    stats = get_stats(token)
    if stats:
        print(f"\n📊 User Learning Profile:")
        print(f"   Total interactions: {stats.get('interaction_count', 0)}")
        print(f"   Quick reply rate: {stats.get('quick_reply_rate', 0):.1%}")
        print(f"   Success rate: {stats.get('success_rate', 0):.1%}")
        print(f"   Confidence threshold: {stats.get('threshold', 0):.2f}")
        print(f"   Prefers detailed: {stats.get('prefer_detailed', False)}")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"\n⚡ Quick replies: {quick_count}/{len(test_cases)}")
    print(f"🤖 Full AI: {ai_count}/{len(test_cases)}")
    
    if quick_count > 0:
        avg_quick_time = total_quick_time / quick_count
        print(f"\n⏱️  Avg quick reply time: {avg_quick_time:.0f}ms")
    
    if ai_count > 0:
        avg_ai_time = total_ai_time / ai_count
        print(f"⏱️  Avg AI response time: {avg_ai_time:.0f}ms")
        
        if quick_count > 0:
            improvement = avg_ai_time / avg_quick_time
            print(f"\n🚀 Speed improvement: {improvement:.0f}x faster with quick replies!")
    
    # Cost calculation
    estimated_cost_before = len(test_cases) * 0.002
    estimated_cost_after = ai_count * 0.002
    savings = estimated_cost_before - estimated_cost_after
    savings_percent = (savings / estimated_cost_before) * 100 if estimated_cost_before > 0 else 0
    
    print(f"\n💰 Estimated cost savings:")
    print(f"   Before: ${estimated_cost_before:.4f}")
    print(f"   After: ${estimated_cost_after:.4f}")
    print(f"   Saved: ${savings:.4f} ({savings_percent:.0f}%)")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE!")
    print("=" * 80)
    print()

if __name__ == "__main__":
    print()
    print("⚠️  IMPORTANT: Update USERNAME and PASSWORD in the script first!")
    print()
    input("Press Enter to continue...")
    main()
