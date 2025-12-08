#!/usr/bin/env python3
"""
Debug script to check conversation history messages
Shows what's actually stored in the session files
"""

import json
import os
from pathlib import Path
from datetime import datetime

def check_conversation_history():
    """Check what's stored in conversation history files"""
    
    conversations_dir = Path("conversations")
    
    if not conversations_dir.exists():
        print("❌ No conversations directory found")
        return
    
    print(f"📂 Checking conversations in: {conversations_dir}")
    print("=" * 80)
    
    # Get all session files
    session_files = list(conversations_dir.glob("*.json"))
    
    if not session_files:
        print("❌ No session files found")
        return
    
    print(f"✅ Found {len(session_files)} session files\n")
    
    # Check each session file
    for session_file in sorted(session_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
        print(f"\n📄 File: {session_file.name}")
        print(f"📅 Modified: {datetime.fromtimestamp(session_file.stat().st_mtime)}")
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            messages = data.get("messages", [])
            print(f"💬 Total messages: {len(messages)}")
            
            if not messages:
                print("   ⚠️  No messages in this session")
                continue
            
            # Count by role
            role_counts = {}
            for msg in messages:
                role = msg.get("role", "unknown")
                role_counts[role] = role_counts.get(role, 0) + 1
            
            print(f"   📊 By role: {role_counts}")
            
            # Show first 3 messages
            print(f"\n   📝 Sample messages:")
            for i, msg in enumerate(messages[:3], 1):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                timestamp = msg.get("timestamp", "")
                
                # Truncate content for display
                preview = content[:80] + "..." if len(content) > 80 else content
                
                role_emoji = "👤" if role == "user" else "🤖" if role == "assistant" else "⚙️"
                print(f"   {i}. {role_emoji} [{role}] {preview}")
                print(f"      ⏰ {timestamp}")
            
            if len(messages) > 3:
                print(f"   ... and {len(messages) - 3} more messages")
        
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")
        
        print("-" * 80)

if __name__ == "__main__":
    check_conversation_history()
