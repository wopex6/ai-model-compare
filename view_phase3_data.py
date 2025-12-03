"""
View Phase 3 Data - See what's stored in the database
Shows actual personality interpretations from your interactions
"""

import sqlite3
import json
from datetime import datetime

print("="*80)
print("PHASE 3: DATABASE VIEWER - See Personality Interpretations")
print("="*80)
print()

conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

# Check personality_interpretations table
print("STORED PERSONALITY INTERPRETATIONS")
print("-"*80)

cursor.execute("""
    SELECT 
        id,
        user_id,
        character,
        event_type,
        raw_message,
        interpretation,
        emotional_impact,
        recommended_approach,
        confidence,
        created_at
    FROM personality_interpretations
    ORDER BY created_at DESC
    LIMIT 10
""")

rows = cursor.fetchall()

if rows:
    print(f"\nFound {len(rows)} recent interpretations:\n")
    
    for i, row in enumerate(rows, 1):
        print(f"\n{'='*80}")
        print(f"INTERPRETATION #{i}")
        print(f"{'='*80}")
        print(f"User ID:       {row[1]}")
        print(f"Character:     {row[2]}")
        print(f"Event Type:    {row[3]}")
        print(f"Timestamp:     {row[9]}")
        print()
        print(f"User Message:")
        print(f'  "{row[4]}"')
        print()
        print(f"Interpretation:")
        print(f"  {row[5]}")
        print()
        print(f"Emotional Impact:")
        print(f"  {row[6]}")
        print()
        print(f"Recommended Approach:")
        print(f"  {row[7]}")
        print()
        print(f"Confidence: {row[8]:.0%}")
else:
    print("\nNo interpretations stored yet.")
    print("Try chatting with a character to generate some!")

# Check history_secondary for personality data
print("\n\n" + "="*80)
print("HISTORY WITH PERSONALITY INTERPRETATIONS")
print("-"*80)

cursor.execute("""
    SELECT 
        id,
        user_id,
        character,
        personality_interpretation,
        interpretation_confidence,
        analysis_timestamp
    FROM history_secondary
    WHERE personality_interpretation IS NOT NULL
    ORDER BY analysis_timestamp DESC
    LIMIT 5
""")

history_rows = cursor.fetchall()

if history_rows:
    print(f"\nFound {len(history_rows)} history entries with personality data:\n")
    
    for i, row in enumerate(history_rows, 1):
        print(f"\n{'='*80}")
        print(f"HISTORY ENTRY #{i}")
        print(f"{'='*80}")
        print(f"User ID:    {row[1]}")
        print(f"Character:  {row[2]}")
        print(f"Timestamp:  {row[5]}")
        print()
        if row[3]:
            print(f"Personality Interpretation Stored:")
            # Try to parse as JSON
            try:
                import json
                interp = json.loads(row[3])
                print(f"  Meaning: {interp.get('interpreted_meaning', 'N/A')}")
                print(f"  Approach: {interp.get('recommended_approach', 'N/A')}")
            except:
                print(f"  {row[3][:150]}...")  # Show first 150 chars
        print()
        print(f"Confidence: {row[4]:.0%}" if row[4] else "Confidence: N/A")
else:
    print("\nNo history entries with personality data yet.")

# Statistics
print("\n\n" + "="*80)
print("STATISTICS")
print("-"*80)

# Count by event type
cursor.execute("""
    SELECT event_type, COUNT(*) 
    FROM personality_interpretations 
    GROUP BY event_type
    ORDER BY COUNT(*) DESC
""")

event_counts = cursor.fetchall()

if event_counts:
    print("\nInterpretations by Event Type:")
    for event_type, count in event_counts:
        print(f"  {event_type}: {count}")

# Count by user
cursor.execute("""
    SELECT user_id, COUNT(*) 
    FROM personality_interpretations 
    GROUP BY user_id
    ORDER BY COUNT(*) DESC
""")

user_counts = cursor.fetchall()

if user_counts:
    print("\nInterpretations by User:")
    for user_id, count in user_counts:
        print(f"  User {user_id}: {count} interpretations")

# Average confidence
cursor.execute("""
    SELECT AVG(confidence) 
    FROM personality_interpretations
""")

avg_conf = cursor.fetchone()[0]
if avg_conf:
    print(f"\nAverage Interpretation Confidence: {avg_conf:.0%}")

# Explicit context with emotional states
print("\n\n" + "="*80)
print("EXPLICIT CONTEXT (Emotional States)")
print("-"*80)

cursor.execute("""
    SELECT 
        user_id,
        character,
        context_value,
        original_statement,
        confidence,
        timestamp
    FROM explicit_context
    WHERE context_type = 'emotional_state'
      AND active = 1
    ORDER BY timestamp DESC
    LIMIT 10
""")

context_rows = cursor.fetchall()

if context_rows:
    print(f"\nFound {len(context_rows)} active emotional states:\n")
    
    for i, row in enumerate(context_rows, 1):
        print(f"{i}. User {row[0]} with {row[1]}:")
        print(f"   Emotion: {row[2]}")
        print(f'   From: "{row[3][:60]}..."')
        print(f"   Confidence: {row[4]:.0%}, {row[5]}")
        print()
else:
    print("\nNo emotional states stored yet.")

conn.close()

print("\n" + "="*80)
print("HOW TO GENERATE MORE DATA")
print("="*80)
print()
print("To see Phase 3 in action with your own personality:")
print()
print("1. Start the app: python app.py")
print("2. Login as a user")
print("3. Chat with any character")
print("4. Say things like:")
print('   - "I\'m feeling stressed about my work"')
print('   - "I failed my exam today"')
print('   - "My goal is to learn Python"')
print()
print("5. Run this script again to see the interpretations!")
print()
print("The system will:")
print("  - Detect your personality traits (or use defaults)")
print("  - Interpret your message through that lens")
print("  - Store the interpretation in the database")
print("  - Use it to tailor AI responses")
print()
print("="*80)
