"""
Quick script to see what's actually being sent to the AI
Run this to inspect the exact prompt the AI receives
"""

import sqlite3
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from smart_response.conversation_context import ConversationContextManager

# Connect to database
db = sqlite3.connect('integrated_users.db')
context_manager = ConversationContextManager(db)

# Check what context is available for a user
user_id = 23  # Change to your test user_id
character = "coach"  # Change to your test character

print("="*80)
print(f"CHECKING CONTEXT FOR USER {user_id} with {character}")
print("="*80)

# Get the context that would be passed to AI
context = context_manager.get_context_for_ai(user_id, character, [])

# Format it as it would appear in the AI prompt
formatted_prompt = context_manager.format_context_for_prompt(context)

print("\nFORMATTED CONTEXT (What AI Sees):")
print("-"*80)
print(formatted_prompt)
print("-"*80)

# Check explicit context specifically
from smart_response.explicit_context_handler import ExplicitContextHandler
handler = ExplicitContextHandler(db)

explicit = handler.get_explicit_context(user_id, character)

print("\nEXPLICIT CONTEXT IN DATABASE:")
print("-"*80)
for item in explicit:
    print(f"  {item['type']}.{item['key']} = {item['value']}")
    print(f"    Priority: {item['priority']}, Confidence: {item['confidence']:.2f}")
    print(f"    From: {item['original_statement'][:50]}...")
    print()

db.close()

print("\n" + "="*80)
print("VERIFICATION CHECKLIST:")
print("="*80)
print("\n1. Does 'EXPLICIT STATEMENTS' section appear?")
print("2. Are your emotions listed?")
print("3. Are your goals listed?")
print("4. Is the text clear and readable?")
print("\nIf YES to all → Context is being sent to AI correctly! ✓")
