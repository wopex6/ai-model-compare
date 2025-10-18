#!/usr/bin/env python3
"""
Debug script to compare session behavior with and without app restart
"""
import requests
import json
import os
from pathlib import Path

def test_session_behavior():
    base_url = "http://localhost:5000"
    conversations_dir = Path("conversations")
    
    print("🔍 Debugging session behavior differences...")
    
    # 1. Check what conversation files exist
    print("\n1. Checking existing conversation files:")
    if conversations_dir.exists():
        files = list(conversations_dir.glob("*.json"))
        print(f"   Found {len(files)} conversation files:")
        for f in files[-5:]:  # Show last 5 files
            stat = f.stat()
            print(f"   - {f.name} ({stat.st_size} bytes, modified: {stat.st_mtime})")
    else:
        print("   No conversations directory found!")
        return
    
    # 2. Test session creation
    print("\n2. Testing session creation...")
    try:
        response = requests.post(f"{base_url}/chat/session")
        session_data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Response: {session_data}")
        
        if 'session_id' in session_data:
            session_id = session_data['session_id']
            print(f"   ✅ New session created: {session_id}")
            
            # Check if file was created
            session_file = conversations_dir / f"{session_id}.json"
            if session_file.exists():
                print(f"   ✅ Session file created: {session_file}")
                with open(session_file, 'r') as f:
                    content = json.load(f)
                    print(f"   File content: {len(content.get('messages', []))} messages")
            else:
                print(f"   ❌ Session file NOT created: {session_file}")
        else:
            print("   ❌ No session_id in response")
            return
            
    except Exception as e:
        print(f"   ❌ Error creating session: {e}")
        return
    
    # 3. Test session loading with existing files
    print("\n3. Testing session loading with existing files...")
    if files:
        # Try to load the most recent file
        recent_file = max(files, key=lambda f: f.stat().st_mtime)
        session_id = recent_file.stem
        
        print(f"   Testing with existing session: {session_id}")
        
        try:
            response = requests.get(f"{base_url}/chat/session?session_id={session_id}")
            data = response.json()
            print(f"   Status: {response.status_code}")
            print(f"   Exists: {data.get('exists', False)}")
            print(f"   Messages: {len(data.get('messages', []))}")
            
            if data.get('exists') and data.get('messages'):
                print("   ✅ Session loading works!")
                # Show first few messages
                for i, msg in enumerate(data['messages'][:3]):
                    print(f"      {i+1}. {msg['role']}: {msg['content'][:50]}...")
            else:
                print("   ❌ Session loading failed!")
                print(f"   Error: {data.get('error', 'Unknown')}")
                
        except Exception as e:
            print(f"   ❌ Error loading session: {e}")
    
    # 4. Check conversation manager state
    print("\n4. Testing conversation manager directly...")
    try:
        # Import and test the conversation manager
        import sys
        sys.path.append('.')
        from ai_compare.conversation_manager import ConversationManager
        
        cm = ConversationManager()
        print(f"   Storage dir: {cm.storage_dir}")
        print(f"   Cache size: {len(cm.conversation_cache)}")
        
        # Test loading a session
        if files:
            test_session_id = recent_file.stem
            session_data = cm.load_session(test_session_id)
            if session_data:
                print(f"   ✅ Direct load works: {len(session_data['messages'])} messages")
            else:
                print(f"   ❌ Direct load failed for {test_session_id}")
                
    except Exception as e:
        print(f"   ❌ Error testing conversation manager: {e}")

if __name__ == "__main__":
    test_session_behavior()
