"""Check analytics tables status"""
import sqlite3

DB_PATH = 'integrated_users.db'

def check():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=== ANALYTICS TABLE CHECK ===\n")
    
    # Check if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%activity%' OR name LIKE '%analytics%' OR name LIKE '%stats%'")
    tables = cursor.fetchall()
    print(f"Tables found: {[t[0] for t in tables]}")
    
    # Check user_activity_log
    try:
        cursor.execute("SELECT COUNT(*) FROM user_activity_log")
        count = cursor.fetchone()[0]
        print(f"\nuser_activity_log: {count} rows")
        
        cursor.execute("PRAGMA table_info(user_activity_log)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"  Columns: {columns}")
        
        if count > 0:
            cursor.execute("SELECT * FROM user_activity_log ORDER BY id DESC LIMIT 5")
            print("  Recent entries:")
            for row in cursor.fetchall():
                print(f"    {row}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Check conversation_analytics
    try:
        cursor.execute("SELECT COUNT(*) FROM conversation_analytics")
        count = cursor.fetchone()[0]
        print(f"\nconversation_analytics: {count} rows")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Check daily_stats
    try:
        cursor.execute("SELECT COUNT(*) FROM daily_stats")
        count = cursor.fetchone()[0]
        print(f"\ndaily_stats: {count} rows")
    except Exception as e:
        print(f"  Error: {e}")
    
    conn.close()
    print("\n=== CHECK COMPLETE ===")

if __name__ == "__main__":
    check()
