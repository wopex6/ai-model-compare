import sqlite3

# Connect to database
conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

# Check if Vera exists
cursor.execute("SELECT id, username, email, user_role FROM users WHERE username = 'Vera'")
user = cursor.fetchone()

if user:
    user_id, username, email, role = user
    print(f"\n✓ User Found:")
    print(f"  ID: {user_id}")
    print(f"  Username: {username}")
    print(f"  Email: {email}")
    print(f"  Role: {role}")
    
    # Check AI usage
    print(f"\n📊 AI Usage:")
    
    # Total calls
    cursor.execute("""
        SELECT COUNT(*) FROM ai_usage_log 
        WHERE user_id = ? AND success = 1
    """, (user_id,))
    total_calls = cursor.fetchone()[0]
    print(f"  Total calls: {total_calls}")
    
    # User prompts vs auto calls
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN (is_background = 0 AND is_automated = 0) THEN 1 END) as user_calls,
            COUNT(CASE WHEN (is_background = 1 OR is_automated = 1) THEN 1 END) as auto_calls
        FROM ai_usage_log 
        WHERE user_id = ? AND success = 1
    """, (user_id,))
    user_calls, auto_calls = cursor.fetchone()
    print(f"  User prompts: {user_calls}")
    print(f"  Auto calls: {auto_calls}")
    
    # Today's calls
    cursor.execute("""
        SELECT COUNT(*) FROM ai_usage_log 
        WHERE user_id = ? AND DATE(timestamp) = DATE('now') AND success = 1
    """, (user_id,))
    today_calls = cursor.fetchone()[0]
    print(f"  Today: {today_calls}")
    
    # This month's calls
    cursor.execute("""
        SELECT COUNT(*) FROM ai_usage_log 
        WHERE user_id = ? 
        AND DATE(timestamp, 'start of month') = DATE('now', 'start of month')
        AND success = 1
    """, (user_id,))
    month_calls = cursor.fetchone()[0]
    print(f"  This month: {month_calls}")
    
    # Recent calls (last 5)
    cursor.execute("""
        SELECT timestamp, call_type, character, is_background, is_automated
        FROM ai_usage_log 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 5
    """, (user_id,))
    recent = cursor.fetchall()
    
    if recent:
        print(f"\n📝 Recent Calls (last 5):")
        for timestamp, call_type, character, is_bg, is_auto in recent:
            call_nature = "AUTO" if (is_bg or is_auto) else "USER"
            char_info = f"({character})" if character else ""
            print(f"  {timestamp} - {call_type} {char_info} [{call_nature}]")
    
else:
    print("\n❌ User 'Vera' not found in database")
    
    # Show all users
    cursor.execute("SELECT username FROM users ORDER BY username")
    all_users = cursor.fetchall()
    print(f"\n📋 All users in database ({len(all_users)}):")
    for (username,) in all_users:
        print(f"  - {username}")

conn.close()
