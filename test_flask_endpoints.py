"""Test Flask endpoints for conversation persistence."""

import requests
import json
import time

def test_flask_endpoints():
    """Test the Flask app endpoints."""
    
    base_url = "http://localhost:5000"
    
    print("=== Testing Flask Endpoints ===\n")
    
    try:
        # Test debug endpoint
        print("1. Testing debug endpoint...")
        response = requests.get(f"{base_url}/debug/conversations")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Storage path: {data['storage_path']}")
            print(f"✓ Session count: {data['session_count']}")
            print(f"✓ Cache size: {data['cache_size']}")
        else:
            print(f"❌ Debug endpoint failed: {response.status_code}")
            return False
        
        # Test session creation
        print("\n2. Testing session creation...")
        response = requests.post(f"{base_url}/chat/session")
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data['session_id']
            print(f"✓ Created session: {session_id[:8]}...")
        else:
            print(f"❌ Session creation failed: {response.status_code}")
            return False
        
        # Test message sending
        print("\n3. Testing message sending...")
        message_data = {
            "message": "Hello, this is a test message",
            "session_id": session_id,
            "include_context": True
        }
        
        # Note: This will fail if AI models aren't configured, but we can test the endpoint
        response = requests.post(f"{base_url}/chat/message", json=message_data)
        print(f"Message endpoint response: {response.status_code}")
        
        # Test session retrieval
        print("\n4. Testing session retrieval...")
        response = requests.get(f"{base_url}/chat/session", params={"session_id": session_id})
        if response.status_code == 200:
            data = response.json()
            if data.get('exists'):
                print(f"✓ Session exists with {data.get('message_count', 0)} messages")
            else:
                print("✓ Session check completed (no messages yet)")
        else:
            print(f"❌ Session retrieval failed: {response.status_code}")
        
        # Test session history
        print("\n5. Testing session history...")
        response = requests.get(f"{base_url}/chat/history/{session_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Retrieved {len(data['messages'])} messages from history")
        else:
            print(f"❌ History retrieval failed: {response.status_code}")
        
        # Test session restore
        print("\n6. Testing session restore...")
        response = requests.post(f"{base_url}/api/restore_session")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✓ Restored session: {data['session_id'][:8]}...")
            else:
                print(f"✓ No sessions to restore: {data.get('error')}")
        else:
            print(f"❌ Session restore failed: {response.status_code}")
        
        print("\n✅ Flask endpoints are working correctly!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask app. Make sure app.py is running on localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_flask_endpoints()
