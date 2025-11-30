"""
Quick test to verify Explicit Context Handler
"""
import sqlite3

# Check database
conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

# Check if table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='explicit_context'")
table_exists = cursor.fetchone()
print(f"✓ Table 'explicit_context' exists: {table_exists is not None}")

if table_exists:
    # Check structure
    cursor.execute("PRAGMA table_info(explicit_context)")
    columns = cursor.fetchall()
    print(f"✓ Table has {len(columns)} columns")
    
    # Check row count
    cursor.execute("SELECT COUNT(*) FROM explicit_context")
    count = cursor.fetchone()[0]
    print(f"✓ Current rows in table: {count}")
    
    # Test extraction
    print("\n--- Testing Extraction ---")
    from smart_response.explicit_context_handler import ExplicitContextHandler
    
    handler = ExplicitContextHandler(conn)
    
    # Test message
    test_message = "I'm feeling stressed about my project. My goal is to finish by Friday."
    
    print(f"\nTest message: '{test_message}'")
    print("\nExtracting...")
    
    extracted = handler.extract_explicit_context(
        user_id=999,  # Test user
        character='test_coach',
        message=test_message
    )
    
    print(f"\n✓ Extracted {len(extracted)} items:")
    for item in extracted:
        print(f"  - {item['type']}.{item['key']}: '{item['value']}'")
    
    # Check database
    cursor.execute("SELECT COUNT(*) FROM explicit_context WHERE user_id=999")
    test_count = cursor.fetchone()[0]
    print(f"\n✓ Test entries in database: {test_count}")
    
    # Show the entries
    cursor.execute("""
        SELECT context_type, context_key, context_value, priority, confidence
        FROM explicit_context 
        WHERE user_id=999
    """)
    
    print("\nStored entries:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}.{row[1]} = '{row[2]}' (priority: {row[3]}, confidence: {row[4]})")
    
    # Cleanup test data
    cursor.execute("DELETE FROM explicit_context WHERE user_id=999")
    conn.commit()
    print(f"\n✓ Test data cleaned up")

else:
    print("✗ Table 'explicit_context' does not exist!")

conn.close()
print("\n=== Test Complete ===")
