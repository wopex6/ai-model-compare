#!/usr/bin/env python3
"""
Test script to verify that messages are being saved immediately after each response
"""
import requests
import json
import time

def test_message_saving():
    base_url = "http://localhost:5000"
    
    print("🧪 Testing message saving after each response...")
    
    # 1. Create a new session
    print("\n1. Creating new session...")
    response = requests.post(f"{base_url}/chat/session")
    session_data = response.json()
    session_id = session_data['session_id']
    print(f"   Session ID: {session_id}")
    
    # 2. Send first message
    print("\n2. Sending first message...")
    message_response = requests.post(f"{base_url}/chat/message", json={
        "message": "Hello, this is test message 1",
        "session_id": session_id
    })
    print(f"   Response: {message_response.status_code}")
    
    # 3. Check if message was saved immediately
    print("\n3. Checking if messages were saved...")
    history_response = requests.get(f"{base_url}/chat/session?session_id={session_id}")
    history_data = history_response.json()
    
    if history_data.get('exists') and history_data.get('messages'):
        messages = history_data['messages']
        print(f"   ✅ Found {len(messages)} messages in session")
        for i, msg in enumerate(messages):
            print(f"      {i+1}. {msg['role']}: {msg['content'][:50]}...")
    else:
        print("   ❌ No messages found in session!")
        return False
    
    # 4. Send second message
    print("\n4. Sending second message...")
    message_response = requests.post(f"{base_url}/chat/message", json={
        "message": "This is test message 2",
        "session_id": session_id
    })
    
    # 5. Check messages again
    print("\n5. Checking messages after second exchange...")
    history_response = requests.get(f"{base_url}/chat/session?session_id={session_id}")
    history_data = history_response.json()
    
    if history_data.get('exists') and history_data.get('messages'):
        messages = history_data['messages']
        print(f"   ✅ Found {len(messages)} messages in session")
        
        # Should have 4 messages: user1, bot1, user2, bot2
        expected_count = 4
        if len(messages) >= expected_count:
            print(f"   ✅ Message saving is working! Expected at least {expected_count}, got {len(messages)}")
            return True
        else:
            print(f"   ❌ Missing messages! Expected at least {expected_count}, got {len(messages)}")
            return False
    else:
        print("   ❌ No messages found after second exchange!")
        return False

if __name__ == "__main__":
    try:
        success = test_message_saving()
        if success:
            print("\n🎉 Message saving test PASSED!")
        else:
            print("\n💥 Message saving test FAILED!")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
