"""
Test script to populate analytics data:
1. Vary character effectiveness scores
2. Add test background task
3. Verify token/cost values in AI calls
"""
import sqlite3
import random
from datetime import datetime

DB_PATH = 'smart_response.db'

def update_character_effectiveness():
    """Update character effectiveness with varied values"""
    print("\n📊 Updating Character Effectiveness...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all characters
    cursor.execute('SELECT character_id, display_name FROM character_library')
    characters = cursor.fetchall()
    
    if not characters:
        print("  ⚠️ No characters found in database")
        conn.close()
        return
    
    # Assign varied effectiveness scores
    effectiveness_values = [0.85, 0.78, 0.72, 0.65, 0.58, 0.52, 0.45, 0.38]
    
    for i, (char_id, name) in enumerate(characters):
        score = effectiveness_values[i % len(effectiveness_values)]
        usage_count = random.randint(5, 50)
        
        cursor.execute('''
            UPDATE character_library 
            SET effectiveness_score = ?, usage_count = ?, updated_at = CURRENT_TIMESTAMP
            WHERE character_id = ?
        ''', (score, usage_count, char_id))
        
        print(f"  ✅ {name}: {score*100:.0f}% effective, {usage_count} uses")
    
    conn.commit()
    conn.close()
    print(f"  Updated {len(characters)} characters")

def check_ai_call_tokens():
    """Check token and cost values in AI calls"""
    print("\n🔍 Checking AI Call Token/Cost Values...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get recent AI calls
    cursor.execute('''
        SELECT id, timestamp, call_type, purpose, input_tokens, output_tokens, 
               estimated_cost, success
        FROM ai_usage_log
        ORDER BY timestamp DESC
        LIMIT 10
    ''')
    
    calls = cursor.fetchall()
    
    if not calls:
        print("  ⚠️ No AI calls found")
        conn.close()
        return
    
    print(f"  Found {len(calls)} recent calls:")
    
    missing_tokens = 0
    for call in calls:
        id, ts, call_type, purpose, in_tok, out_tok, cost, success = call
        time_str = ts.split('.')[0] if ts else 'N/A'
        
        # Check if tokens are missing
        if in_tok is None and out_tok is None:
            missing_tokens += 1
            status = "❌ NO TOKENS"
        else:
            status = f"✅ {in_tok or 0}/{out_tok or 0} tokens"
        
        print(f"    [{time_str}] {purpose or call_type}: ${cost:.4f} - {status}")
    
    if missing_tokens > 0:
        print(f"\n  ⚠️ {missing_tokens}/{len(calls)} calls missing token data")
        print("  → Token tracking may not be implemented in AI call logging")
    
    conn.close()

def show_current_analytics():
    """Show current analytics state"""
    print("\n📈 Current Analytics State:")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Character effectiveness
    cursor.execute('''
        SELECT display_name, effectiveness_score, usage_count 
        FROM character_library 
        ORDER BY effectiveness_score DESC
    ''')
    chars = cursor.fetchall()
    
    if chars:
        print("\n  Character Effectiveness:")
        for name, score, usage in chars:
            bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
            print(f"    {name}: {bar} {score*100:.0f}% ({usage} uses)")
    
    # AI call stats
    cursor.execute('''
        SELECT COUNT(*), SUM(estimated_cost), 
               SUM(input_tokens), SUM(output_tokens)
        FROM ai_usage_log 
        WHERE DATE(timestamp) = DATE('now')
    ''')
    row = cursor.fetchone()
    if row:
        calls, cost, in_tok, out_tok = row
        print(f"\n  Today's AI Calls: {calls or 0}")
        print(f"  Total Cost: ${cost or 0:.4f}")
        print(f"  Total Tokens: {(in_tok or 0) + (out_tok or 0)}")
    
    conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 ANALYTICS DATA TEST")
    print("=" * 60)
    
    update_character_effectiveness()
    check_ai_call_tokens()
    show_current_analytics()
    
    print("\n" + "=" * 60)
    print("✅ Done! Refresh Admin Analytics to see changes.")
