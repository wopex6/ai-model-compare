#!/usr/bin/env python3
"""
Find conversations with many messages
"""

import json
from pathlib import Path

def find_conversations():
    conversations_dir = Path('conversations')
    
    print("🔍 Looking for conversations with many messages...")
    
    found_conversations = []
    
    for conv_file in conversations_dir.glob('*.json'):
        try:
            with open(conv_file, 'r') as f:
                data = json.load(f)
            
            if 'messages' in data:
                msg_count = len(data['messages'])
                if msg_count >= 8:  # Look for substantial conversations
                    found_conversations.append((conv_file, msg_count, data))
                    
        except Exception as e:
            continue
    
    # Sort by message count
    found_conversations.sort(key=lambda x: x[1], reverse=True)
    
    print(f"Found {len(found_conversations)} conversations with 8+ messages:")
    
    for conv_file, msg_count, data in found_conversations[:5]:  # Show top 5
        print(f"\n📁 {conv_file.name}")
        print(f"   Messages: {msg_count}")
        print(f"   Created: {data.get('created_at', 'Unknown')}")
        print(f"   Size: {conv_file.stat().st_size} bytes")
        
        if data['messages']:
            first_msg = data['messages'][0]['content'][:60]
            print(f"   First: {first_msg}...")
            
            if len(data['messages']) > 1:
                last_msg = data['messages'][-1]['content'][:60]
                print(f"   Last: {last_msg}...")
    
    return found_conversations

if __name__ == "__main__":
    conversations = find_conversations()
    
    if conversations:
        largest = conversations[0]
        print(f"\n🎯 Largest conversation: {largest[0].name} with {largest[1]} messages")
    else:
        print("❌ No substantial conversations found")
