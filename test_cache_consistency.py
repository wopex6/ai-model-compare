"""Test cache consistency with JSON files."""

import json
import os
from pathlib import Path
from ai_compare.conversation_manager import ConversationManager

def test_cache_consistency():
    """Test that cache stays consistent with JSON files."""
    
    print("=== Testing Cache Consistency ===\n")
    
    # Create conversation manager
    manager = ConversationManager()
    print(f"Storage directory: {manager.storage_dir.absolute()}")
    
    # Test 1: Create session and add messages
    print("\n1. Creating session and adding messages...")
    session_id = manager.create_session("cache_test")
    
    # Add initial messages
    manager.save_message(session_id, "user", "Message 1")
    manager.save_message(session_id, "assistant", "Response 1")
    manager.save_message(session_id, "user", "Message 2")
    
    # Get message count from cache
    cached_history = manager.get_conversation_history(session_id)
    cached_count = len(cached_history)
    print(f"Cache shows {cached_count} messages")
    
    # Get message count from file
    session_file = manager.storage_dir / f"{session_id}.json"
    with open(session_file, 'r', encoding='utf-8') as f:
        file_data = json.load(f)
    file_count = len(file_data['messages'])
    print(f"File shows {file_count} messages")
    
    assert cached_count == file_count, f"Cache/file mismatch: {cached_count} vs {file_count}"
    print("✓ Cache and file consistent after initial save")
    
    # Test 2: Force reload and compare
    print("\n2. Testing force reload...")
    force_reload_history = manager.get_conversation_history(session_id, force_reload=True)
    force_reload_count = len(force_reload_history)
    print(f"Force reload shows {force_reload_count} messages")
    
    assert force_reload_count == file_count, f"Force reload mismatch: {force_reload_count} vs {file_count}"
    print("✓ Force reload matches file")
    
    # Test 3: Add more messages and verify consistency
    print("\n3. Adding more messages...")
    manager.save_message(session_id, "assistant", "Response 2")
    manager.save_message(session_id, "user", "Message 3")
    
    # Check file again
    with open(session_file, 'r', encoding='utf-8') as f:
        file_data = json.load(f)
    new_file_count = len(file_data['messages'])
    print(f"File now shows {new_file_count} messages")
    
    # Check cache
    new_cached_history = manager.get_conversation_history(session_id)
    new_cached_count = len(new_cached_history)
    print(f"Cache now shows {new_cached_count} messages")
    
    assert new_cached_count == new_file_count, f"Cache/file mismatch after save: {new_cached_count} vs {new_file_count}"
    print("✓ Cache and file consistent after additional saves")
    
    # Test 4: Simulate app restart (clear cache)
    print("\n4. Simulating app restart (clearing cache)...")
    manager.conversation_cache.clear()
    print("Cache cleared")
    
    # Load from disk
    disk_history = manager.get_conversation_history(session_id, force_reload=True)
    disk_count = len(disk_history)
    print(f"Loaded from disk: {disk_count} messages")
    
    assert disk_count == new_file_count, f"Disk load mismatch: {disk_count} vs {new_file_count}"
    print("✓ Successfully loaded from disk after cache clear")
    
    # Test 5: Verify message content consistency
    print("\n5. Verifying message content...")
    for i, (cached_msg, file_msg) in enumerate(zip(new_cached_history, file_data['messages'])):
        assert cached_msg['content'] == file_msg['content'], f"Message {i} content mismatch"
        assert cached_msg['role'] == file_msg['role'], f"Message {i} role mismatch"
    print("✓ All message content matches between cache and file")
    
    # Cleanup
    manager.delete_session(session_id)
    print(f"\n✓ Cleaned up test session")
    
    print("\n🎉 All cache consistency tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_cache_consistency()
        print("\n✅ Cache consistency verified!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
