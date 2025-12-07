"""Quick script to check assessment history for user Wai Tse (user_id=1)"""

from integrated_database import IntegratedDatabase

db = IntegratedDatabase()

# Check assessment history
print("\n" + "="*60)
print("📊 ASSESSMENT HISTORY CHECK")
print("="*60)

history = db.get_assessment_history(user_id=1, limit=10)

if not history:
    print("\n❌ No assessments found in history!")
    print("   The assessment may not have been saved properly.")
    print("\nChecking assessment_history table...")
    
    # Check if table exists and has any data
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assessment_history'")
    if cursor.fetchone():
        print("✅ assessment_history table exists")
        cursor.execute("SELECT COUNT(*) FROM assessment_history")
        count = cursor.fetchone()[0]
        print(f"   Total records in table: {count}")
        
        if count > 0:
            cursor.execute("SELECT id, user_id, completed_at FROM assessment_history ORDER BY completed_at DESC LIMIT 5")
            print("\n   Recent records:")
            for row in cursor.fetchall():
                print(f"   - ID: {row[0]}, User: {row[1]}, Date: {row[2]}")
    else:
        print("❌ assessment_history table does NOT exist!")
        print("   Database migration may be needed.")
    
    conn.close()
else:
    print(f"\n✅ Found {len(history)} assessment(s) for user 1:\n")
    
    for i, assessment in enumerate(history, 1):
        print(f"Assessment #{i}")
        print(f"  Date: {assessment['completed_at']}")
        print(f"  Version: {assessment['version']}")
        
        if assessment.get('completion_time_seconds'):
            minutes = assessment['completion_time_seconds'] // 60
            seconds = assessment['completion_time_seconds'] % 60
            print(f"  Time: {minutes}m {seconds}s")
        
        print(f"  Traits:")
        for trait, value in assessment['traits'].items():
            percentage = value * 100 if isinstance(value, float) else value
            print(f"    • {trait.title()}: {percentage:.1f}%")
        
        if assessment.get('notes'):
            print(f"  Notes: {assessment['notes']}")
        
        print()

# Check if we can compare assessments
if len(history) >= 2:
    print("="*60)
    print("📈 COMPARISON AVAILABLE")
    print("="*60)
    print(f"\nYou have {len(history)} assessments - comparison is possible!")
    
    comparison = db.compare_assessments(
        user_id=1,
        assessment1_id=history[1]['id'],  # Older
        assessment2_id=history[0]['id']   # Newer
    )
    
    print(f"\nComparing assessment #{history[1]['id']} to #{history[0]['id']}:")
    print(f"Time between: {comparison['time_between']}")
    print(f"Overall change: {comparison['overall_change']}%")
    print(f"Stability: {comparison['stability_assessment']}\n")
    
    print("Changes by trait:")
    for trait, data in comparison['comparison'].items():
        direction_emoji = "↑" if data['direction'] == 'increased' else "↓" if data['direction'] == 'decreased' else "→"
        print(f"  {direction_emoji} {trait.title()}: {data['old_value']}% → {data['new_value']}% ({data['change']:+.1f}%)")

print("\n" + "="*60)
print("Done!")
print("="*60 + "\n")
