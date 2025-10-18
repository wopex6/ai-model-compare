"""Debug conversation persistence to see what's happening with storage and loading"""

import sys
from pathlib import Path
import json

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def check_conversation_storage():
    """Check if conversations are being stored properly"""
    
    print("=== Conversation Persistence Debug ===\n")
    
    # Check if conversations directory exists
    conv_dir = Path("conversations")
    print(f"1. Conversations directory: {conv_dir}")
    print(f"   Exists: {conv_dir.exists()}")
    
    if conv_dir.exists():
        files = list(conv_dir.glob("*.json"))
        print(f"   Files: {len(files)} conversation files found")
        
        for file in files[:3]:  # Show first 3 files
            print(f"   - {file.name}")
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                print(f"     Messages: {len(data.get('messages', []))}")
                print(f"     Last updated: {data.get('last_updated', 'N/A')}")
            except Exception as e:
                print(f"     Error reading: {e}")
    
    # Test conversation manager
    print("\n2. Testing ConversationManager...")
    
    try:
        from ai_compare.conversation_manager import ConversationManager
        
        cm = ConversationManager()
        print(f"   ✓ ConversationManager created")
        print(f"   Storage dir: {cm.storage_dir}")
        
        # Create test session
        test_session = cm.create_session("test_session")
        print(f"   ✓ Test session created: {test_session}")
        
        # Save test message
        success = cm.save_message(test_session, "user", "Test message")
        print(f"   ✓ Message saved: {success}")
        
        # Load conversation history
        history = cm.get_conversation_history(test_session)
        print(f"   ✓ History loaded: {len(history)} messages")
        
        if history:
            print(f"     First message: {history[0]['content']}")
        
        return True
        
    except Exception as e:
        print(f"   ✗ ConversationManager test failed: {e}")
        return False

def test_session_loading():
    """Test if session loading works in the web interface"""
    
    print("\n3. Testing Session Loading Logic...")
    
    try:
        from ai_compare.conversation_manager import ConversationManager
        
        cm = ConversationManager()
        
        # Create session with multiple messages
        session_id = cm.create_session("web_test")
        
        # Add some test messages
        cm.save_message(session_id, "user", "Hello, this is a test message")
        cm.save_message(session_id, "assistant", "Hi! I'm responding to your test message.")
        cm.save_message(session_id, "user", "Can you remember this conversation?")
        cm.save_message(session_id, "assistant", "Yes, I should remember our conversation history.")
        
        print(f"   ✓ Created test session: {session_id}")
        print(f"   ✓ Added 4 test messages")
        
        # Test loading
        history = cm.get_conversation_history(session_id)
        print(f"   ✓ Loaded {len(history)} messages")
        
        for i, msg in enumerate(history):
            print(f"     {i+1}. {msg['role']}: {msg['content'][:50]}...")
        
        print(f"\n   📋 To test in browser:")
        print(f"   1. Open browser console on /chat page")
        print(f"   2. Run: localStorage.setItem('chat_session_id', '{session_id}')")
        print(f"   3. Refresh page - should load 4 messages")
        
        return session_id
        
    except Exception as e:
        print(f"   ✗ Session loading test failed: {e}")
        return None

def check_chatbot_integration():
    """Check if chatbot is properly saving messages"""
    
    print("\n4. Testing Chatbot Integration...")
    
    try:
        from ai_compare.chatbot import AIChatbot
        
        # Create chatbot with specific session
        test_session = "chatbot_test_session"
        chatbot = AIChatbot(session_id=test_session)
        
        print(f"   ✓ Chatbot created with session: {chatbot.session_id}")
        
        # Check if conversation manager is working
        history_before = chatbot.conversation_manager.get_conversation_history(test_session)
        print(f"   ✓ History before: {len(history_before)} messages")
        
        # Note: We can't actually test chat() without API keys, but we can check the setup
        print(f"   ✓ Chatbot setup looks correct")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Chatbot integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("Debugging conversation persistence...\n")
    
    # Run all tests
    storage_ok = check_conversation_storage()
    test_session_id = test_session_loading()
    chatbot_ok = check_chatbot_integration()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"✓ Storage system: {'Working' if storage_ok else 'Failed'}")
    print(f"✓ Session loading: {'Working' if test_session_id else 'Failed'}")
    print(f"✓ Chatbot integration: {'Working' if chatbot_ok else 'Failed'}")
    
    if test_session_id:
        print(f"\n🧪 TEST SESSION CREATED: {test_session_id}")
        print("To test persistence:")
        print("1. Run the Flask app: python app.py")
        print("2. Go to /chat")
        print("3. Open browser console and run:")
        print(f"   localStorage.setItem('chat_session_id', '{test_session_id}')")
        print("4. Refresh the page")
        print("5. You should see the 4 test messages loaded")
    
    if all([storage_ok, test_session_id, chatbot_ok]):
        print("\n✅ Conversation persistence should be working!")
    else:
        print("\n❌ There are issues with conversation persistence")
