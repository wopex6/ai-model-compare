"""
Migration script to populate test data for analytics dashboard:
1. Vary character effectiveness scores
2. Create background task log table with test data
3. Add token estimates to recent AI calls
"""
import sqlite3
import random
from datetime import datetime, timedelta

def migrate():
    print("=" * 60)
    print("📊 ANALYTICS TEST DATA MIGRATION")
    print("=" * 60)
    
    # Connect to smart_response.db
    conn = sqlite3.connect('smart_response.db')
    cursor = conn.cursor()
    
    # 1. Update character effectiveness with varied values
    print("\n1️⃣ Updating Character Effectiveness...")
    try:
        cursor.execute('SELECT character_id, display_name FROM character_library')
        characters = cursor.fetchall()
        
        if characters:
            # Assign varied effectiveness scores (different for each character)
            effectiveness_map = {
                'coordinator': 0.82,
                'life_coach': 0.78,
                'psychologist': 0.75,
                'stoic_philosopher': 0.71,
                'career_mentor': 0.68,
                'creative_muse': 0.65,
                'wellness_guide': 0.62,
                'relationship_counselor': 0.58
            }
            
            for char_id, name in characters:
                # Use mapped value or random if not in map
                score = effectiveness_map.get(char_id, round(random.uniform(0.45, 0.85), 2))
                usage = random.randint(10, 100)
                
                cursor.execute('''
                    UPDATE character_library 
                    SET effectiveness_score = ?, usage_count = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE character_id = ?
                ''', (score, usage, char_id))
                
                print(f"  ✅ {name}: {score*100:.0f}% ({usage} uses)")
            
            conn.commit()
            print(f"  Updated {len(characters)} characters")
        else:
            print("  ⚠️ No characters found")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # 2. Create background task log table
    print("\n2️⃣ Creating Background Task Log Table...")
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS background_task_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                last_run TIMESTAMP,
                next_run TIMESTAMP,
                status TEXT DEFAULT 'pending',
                run_count INTEGER DEFAULT 0,
                last_duration_ms INTEGER,
                last_error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert test task data
        now = datetime.now()
        tasks = [
            ('context_maintenance', now - timedelta(hours=2), now + timedelta(hours=4), 'completed', 15, 1250),
            ('pattern_expansion', now - timedelta(hours=6), now + timedelta(hours=18), 'completed', 8, 3200),
            ('character_expansion', now - timedelta(days=1), now + timedelta(days=6), 'completed', 2, 8500),
            ('monthly_cleanup', now - timedelta(days=15), now + timedelta(days=15), 'completed', 1, 12000),
        ]
        
        # Clear existing and insert fresh
        cursor.execute('DELETE FROM background_task_log')
        
        for task_name, last_run, next_run, status, run_count, duration in tasks:
            cursor.execute('''
                INSERT INTO background_task_log 
                (task_name, last_run, next_run, status, run_count, last_duration_ms)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (task_name, last_run.isoformat(), next_run.isoformat(), status, run_count, duration))
            print(f"  ✅ {task_name}: {status}, ran {run_count}x")
        
        conn.commit()
        print("  Task log table created and populated")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # 3. Add token estimates to recent AI calls (where missing)
    print("\n3️⃣ Adding Token Estimates to AI Calls...")
    try:
        # Check current state
        cursor.execute('''
            SELECT COUNT(*) FROM ai_usage_log 
            WHERE input_tokens = 0 OR input_tokens IS NULL
        ''')
        missing = cursor.fetchone()[0]
        
        if missing > 0:
            # Estimate tokens based on call type
            token_estimates = {
                'user_chat': (150, 300),      # input, output
                'domain_chat': (200, 400),
                'context_prompt': (100, 50),
                'character_matching': (80, 30),
                'background': (50, 100),
            }
            
            # Update with estimates
            cursor.execute('SELECT id, call_type FROM ai_usage_log WHERE input_tokens = 0 OR input_tokens IS NULL')
            rows = cursor.fetchall()
            
            for row_id, call_type in rows:
                base_in, base_out = token_estimates.get(call_type, (100, 200))
                # Add some variance
                in_tokens = base_in + random.randint(-20, 50)
                out_tokens = base_out + random.randint(-30, 80)
                
                cursor.execute('''
                    UPDATE ai_usage_log 
                    SET input_tokens = ?, output_tokens = ?
                    WHERE id = ?
                ''', (in_tokens, out_tokens, row_id))
            
            conn.commit()
            print(f"  ✅ Updated {len(rows)} AI calls with token estimates")
        else:
            print("  ✅ All AI calls already have token data")
        
        # Show sample
        cursor.execute('''
            SELECT timestamp, purpose, input_tokens, output_tokens, estimated_cost
            FROM ai_usage_log
            ORDER BY timestamp DESC
            LIMIT 5
        ''')
        print("\n  Recent AI Calls:")
        for row in cursor.fetchall():
            ts = row[0].split('.')[0] if row[0] else 'N/A'
            print(f"    [{ts}] {row[1] or 'N/A'}: {row[2]}/{row[3]} tokens, ${row[4]:.4f}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ Migration complete! Reload web app and refresh dashboard.")

if __name__ == "__main__":
    migrate()
