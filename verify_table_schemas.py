"""
Verify the schemas of new Phase 2 Nice-to-Have tables
"""
import sqlite3

def check_table_schema(cursor, table_name, expected_columns):
    """Check if table has all expected columns"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    actual_columns = {row[1]: row[2] for row in cursor.fetchall()}  # name: type
    
    print(f"\n{table_name}:")
    print("-" * 60)
    
    all_good = True
    for col_name, col_type in expected_columns.items():
        if col_name in actual_columns:
            print(f"  ✓ {col_name} ({actual_columns[col_name]})")
        else:
            print(f"  ✗ {col_name} - MISSING")
            all_good = False
    
    return all_good

print("="*70)
print("TABLE SCHEMA VERIFICATION")
print("="*70)

conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

# Define expected schemas
schemas = {
    'pattern_suggestions': {
        'id': 'INTEGER',
        'pattern_regex': 'TEXT',
        'context_type': 'TEXT',
        'description': 'TEXT',
        'sample_matches': 'TEXT',
        'confidence': 'REAL',
        'status': 'TEXT',
        'created_at': 'TIMESTAMP',
        'reviewed_by': 'INTEGER',
        'reviewed_at': 'TIMESTAMP',
        'activated_at': 'TIMESTAMP',
        'match_count': 'INTEGER',
        'false_positive_count': 'INTEGER',
        'notes': 'TEXT'
    },
    'pattern_statistics': {
        'id': 'INTEGER',
        'pattern_id': 'INTEGER',
        'pattern_regex': 'TEXT',
        'context_type': 'TEXT',
        'match_count': 'INTEGER',
        'success_count': 'INTEGER',
        'false_positive_count': 'INTEGER',
        'last_matched': 'TIMESTAMP',
        'avg_confidence': 'REAL',
        'created_at': 'TIMESTAMP'
    },
    'pattern_analysis_jobs': {
        'id': 'INTEGER',
        'started_at': 'TIMESTAMP',
        'completed_at': 'TIMESTAMP',
        'messages_analyzed': 'INTEGER',
        'patterns_suggested': 'INTEGER',
        'ai_calls_used': 'INTEGER',
        'status': 'TEXT',
        'error_message': 'TEXT'
    },
    'explicit_context_archive': {
        'id': 'INTEGER',
        'original_id': 'INTEGER',
        'user_id': 'INTEGER',
        'character': 'TEXT',
        'timestamp': 'TIMESTAMP',
        'context_type': 'TEXT',
        'context_key': 'TEXT',
        'context_value': 'TEXT',
        'original_statement': 'TEXT',
        'priority': 'TEXT',
        'confidence': 'REAL',
        'original_confidence': 'REAL',
        'active': 'INTEGER',
        'expires_at': 'TIMESTAMP',
        'extracted_via': 'TEXT',
        'archived_at': 'TIMESTAMP',
        'archive_reason': 'TEXT'
    },
    'archival_statistics': {
        'id': 'INTEGER',
        'run_date': 'TIMESTAMP',
        'contexts_archived': 'INTEGER',
        'contexts_expired': 'INTEGER',
        'contexts_decayed': 'INTEGER',
        'oldest_archived_days': 'INTEGER',
        'notes': 'TEXT'
    }
}

# Check each table
all_tables_valid = True
for table_name, expected_cols in schemas.items():
    is_valid = check_table_schema(cursor, table_name, expected_cols)
    if not is_valid:
        all_tables_valid = False

# Check explicit_context modification
print("\nexplicit_context (modified):")
print("-" * 60)
cursor.execute("PRAGMA table_info(explicit_context)")
columns = {row[1]: row[2] for row in cursor.fetchall()}

if 'original_confidence' in columns:
    print(f"  ✓ original_confidence ({columns['original_confidence']})")
else:
    print("  ✗ original_confidence - MISSING")
    all_tables_valid = False

conn.close()

# Summary
print("\n" + "="*70)
if all_tables_valid:
    print("✅ ALL TABLE SCHEMAS ARE CORRECT!")
    print("\nProduction database is ready for:")
    print("  • AI-Assisted Pattern Expansion")
    print("  • Context Expiration & Archival")
    print("  • Background Task Scheduling")
else:
    print("⚠️  Some schema issues detected - review output above")
print("="*70)
