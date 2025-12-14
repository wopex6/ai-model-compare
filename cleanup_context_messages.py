"""
Clean up conversation history to remove enhanced messages with context/psych data
These messages were accidentally saved before the fix and should not be visible to users
"""
import json
import os
from pathlib import Path

def cleanup_conversation_file(filepath):
    """Remove user messages containing context/psych data from conversation history"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        original_count = len(data.get('messages', []))
        
        # Remove user messages that contain context data
        cleaned_messages = []
        removed_count = 0
        
        for msg in data.get('messages', []):
            # Check if this is an enhanced user message
            if msg.get('role') == 'user' and 'USER\'S EXPLICIT STATEMENTS' in msg.get('content', ''):
                print(f"  Removing enhanced message: {msg['content'][:100]}...")
                removed_count += 1
            else:
                cleaned_messages.append(msg)
        
        if removed_count > 0:
            data['messages'] = cleaned_messages
            data['metadata']['message_count'] = len(cleaned_messages)
            
            # Save cleaned data
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Cleaned {filepath.name}: removed {removed_count} enhanced messages")
            return removed_count
        else:
            print(f"✓ {filepath.name}: no enhanced messages found")
            return 0
            
    except Exception as e:
        print(f"❌ Error cleaning {filepath}: {e}")
        return 0

def main():
    """Clean up all conversation history files"""
    conversations_dir = Path('conversations')
    
    if not conversations_dir.exists():
        print("❌ conversations/ directory not found")
        return
    
    print("🧹 Cleaning conversation history files...\n")
    
    total_removed = 0
    files_processed = 0
    
    for filepath in conversations_dir.glob('*.json'):
        removed = cleanup_conversation_file(filepath)
        total_removed += removed
        files_processed += 1
    
    print(f"\n✅ CLEANUP COMPLETE:")
    print(f"   Files processed: {files_processed}")
    print(f"   Enhanced messages removed: {total_removed}")
    print(f"\n💡 Restart your Flask server to see clean history!")

if __name__ == '__main__':
    main()
