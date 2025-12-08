"""
Simple script to verify conversation history persistence works
Run this locally to test before deploying
"""
import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:5000"  # Change if using different port
CHARACTER = "scientist"  # Test with scientist character

def test_conversation_history():
    """Test that conversation history persists across sessions"""
    
    print("="*60)
    print("TESTING CONVERSATION HISTORY PERSISTENCE")
    print("="*60)
    
    # Step 1: Send first message (should create new session)
    print("\n1️⃣ Sending first message (creating new session)...")
    response1 = requests.post(
        f"{BASE_URL}/{CHARACTER}/chat",
        json={"message": "Hello, my name is Alice"}
    )
    
    if response1.status_code != 200:
        print(f"❌ ERROR: {response1.status_code}")
        print(response1.text)
        return False
    
    data1 = response1.json()
    session_id = data1.get('session_id')
    
    if not session_id:
        print("❌ ERROR: No session_id in response!")
        print(f"Response: {data1}")
        return False
    
    print(f"✅ Session created: {session_id}")
    print(f"📝 Bot response: {data1.get('response', 'N/A')[:100]}...")
    
    # Step 2: Send second message with same session_id
    print(f"\n2️⃣ Sending second message (using session {session_id})...")
    response2 = requests.post(
        f"{BASE_URL}/{CHARACTER}/chat",
        json={
            "message": "Do you remember my name?",
            "session_id": session_id
        }
    )
    
    if response2.status_code != 200:
        print(f"❌ ERROR: {response2.status_code}")
        print(response2.text)
        return False
    
    data2 = response2.json()
    print(f"✅ Message sent successfully")
    print(f"📝 Bot response: {data2.get('response', 'N/A')[:100]}...")
    
    # Step 3: Fetch conversation history
    print(f"\n3️⃣ Fetching conversation history for session {session_id}...")
    response3 = requests.get(
        f"{BASE_URL}/{CHARACTER}/history",
        params={"session_id": session_id}
    )
    
    if response3.status_code != 200:
        print(f"❌ ERROR: {response3.status_code}")
        print(response3.text)
        return False
    
    history = response3.json()
    messages = history.get('messages', [])
    
    print(f"✅ Retrieved {len(messages)} messages from history")
    
    # Step 4: Verify history contains both messages
    print("\n4️⃣ Verifying history contents...")
    
    if len(messages) < 4:  # 2 user messages + 2 bot responses
        print(f"❌ ERROR: Expected at least 4 messages, got {len(messages)}")
        print(f"Messages: {json.dumps(messages, indent=2)}")
        return False
    
    # Check first user message
    user_messages = [m for m in messages if m.get('role') == 'user']
    
    if len(user_messages) < 2:
        print(f"❌ ERROR: Expected 2 user messages, got {len(user_messages)}")
        return False
    
    first_message = user_messages[0].get('content', '')
    second_message = user_messages[1].get('content', '')
    
    if "Alice" not in first_message:
        print(f"❌ ERROR: First message doesn't contain 'Alice'")
        print(f"   Got: {first_message}")
        return False
    
    if "remember my name" not in second_message.lower():
        print(f"❌ ERROR: Second message doesn't contain expected text")
        print(f"   Got: {second_message}")
        return False
    
    print("✅ History contains both messages!")
    print(f"   Message 1: {first_message}")
    print(f"   Message 2: {second_message}")
    
    # Print full history for inspection
    print("\n📋 Full conversation history:")
    print("-" * 60)
    for i, msg in enumerate(messages, 1):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')[:100]
        print(f"{i}. [{role}] {content}...")
    print("-" * 60)
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print(f"Session ID: {session_id}")
    print(f"Total messages: {len(messages)}")
    print("\nConversation history persistence is working correctly! 🎉")
    return True


def test_frontend_simulation():
    """Simulate what the frontend does"""
    
    print("\n" + "="*60)
    print("SIMULATING FRONTEND BEHAVIOR")
    print("="*60)
    
    # Simulate: User visits page (no session cookie)
    print("\n1️⃣ User visits character page (no session yet)...")
    print("   - Frontend checks cookie: None found")
    print("   - Frontend will create session on first message")
    
    # Simulate: User sends first message
    print("\n2️⃣ User sends first message...")
    response1 = requests.post(
        f"{BASE_URL}/{CHARACTER}/chat",
        json={"message": "Test message 1"}
    )
    
    if response1.status_code != 200:
        print(f"❌ ERROR: {response1.status_code}")
        return False
    
    data1 = response1.json()
    session_id = data1.get('session_id')
    print(f"   ✅ Session created: {session_id}")
    print(f"   - Frontend saves to cookie: session_{CHARACTER}")
    
    # Simulate: User leaves and returns
    print("\n3️⃣ User leaves page and returns...")
    print(f"   - Frontend reads cookie: {session_id}")
    print(f"   - Frontend calls /{CHARACTER}/history?session_id={session_id}")
    
    response_history = requests.get(
        f"{BASE_URL}/{CHARACTER}/history",
        params={"session_id": session_id}
    )
    
    if response_history.status_code != 200:
        print(f"❌ ERROR: History fetch failed")
        return False
    
    history = response_history.json()
    messages = history.get('messages', [])
    print(f"   ✅ History loaded: {len(messages)} messages")
    
    if len(messages) < 2:
        print(f"❌ ERROR: Expected at least 2 messages, got {len(messages)}")
        return False
    
    # Simulate: User sends another message
    print("\n4️⃣ User continues conversation...")
    response2 = requests.post(
        f"{BASE_URL}/{CHARACTER}/chat",
        json={
            "message": "Test message 2",
            "session_id": session_id
        }
    )
    
    if response2.status_code != 200:
        print(f"❌ ERROR: {response2.status_code}")
        return False
    
    print("   ✅ Message sent with existing session_id")
    
    # Verify final history
    print("\n5️⃣ Verifying final history...")
    response_final = requests.get(
        f"{BASE_URL}/{CHARACTER}/history",
        params={"session_id": session_id}
    )
    
    final_history = response_final.json()
    final_messages = final_history.get('messages', [])
    print(f"   ✅ Final history: {len(final_messages)} messages")
    
    if len(final_messages) < 4:
        print(f"❌ ERROR: Expected at least 4 messages, got {len(final_messages)}")
        return False
    
    print("\n✅ Frontend simulation successful!")
    return True


if __name__ == "__main__":
    print("\n🧪 Starting Conversation History Tests")
    print(f"Testing with: {BASE_URL}/{CHARACTER}\n")
    
    # Test 1: Basic history persistence
    try:
        success1 = test_conversation_history()
    except Exception as e:
        print(f"\n❌ Test 1 failed with exception: {e}")
        import traceback
        traceback.print_exc()
        success1 = False
    
    # Wait a bit
    if success1:
        time.sleep(2)
        
        # Test 2: Frontend simulation
        try:
            success2 = test_frontend_simulation()
        except Exception as e:
            print(f"\n❌ Test 2 failed with exception: {e}")
            import traceback
            traceback.print_exc()
            success2 = False
    else:
        success2 = False
    
    # Final report
    print("\n" + "="*60)
    print("FINAL TEST REPORT")
    print("="*60)
    print(f"Test 1 (History Persistence): {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Test 2 (Frontend Simulation): {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED! Safe to deploy.")
    else:
        print("\n⚠️  TESTS FAILED! Do not deploy yet.")
    
    print("="*60)
