import json
from pathlib import Path
from datetime import datetime

conversations_dir = Path("conversations")
files = sorted(conversations_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)

print("=== RECENT SESSIONS WITH MESSAGES ===\n")

count = 0
for f in files[:50]:
    try:
        with open(f, encoding='utf-8') as file:
            data = json.load(file)
            messages = data.get("messages", [])
            
            if len(messages) > 0:
                user_count = len([m for m in messages if m.get("role") == "user"])
                assistant_count = len([m for m in messages if m.get("role") == "assistant"])
                
                modified = datetime.fromtimestamp(f.stat().st_mtime)
                
                # Check if balanced
                balance_status = "✅ BALANCED" if user_count == assistant_count else "⚠️ UNBALANCED"
                
                print(f"{count + 1}. {f.name}")
                print(f"   Modified: {modified}")
                print(f"   Total: {len(messages)} messages")
                print(f"   User: {user_count}, Assistant: {assistant_count} {balance_status}")
                
                # Show sample messages
                if len(messages) > 0:
                    last_msg = messages[-1]
                    role = last_msg.get("role", "unknown")
                    content = last_msg.get("content", "")[:80]
                    print(f"   Last: [{role}] {content}...")
                
                print()
                
                count += 1
                if count >= 10:
                    break
    except Exception as e:
        continue

print(f"\nShowing {count} most recent sessions with messages")
