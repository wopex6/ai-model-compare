"""
Check if all new Phase 2 Nice-to-Have database tables exist
"""
import sqlite3

print("="*70)
print("DATABASE TABLE VERIFICATION")
print("="*70)

# Expected new tables from Phase 2 Nice-to-Have features
expected_tables = [
    'pattern_suggestions',
    'pattern_statistics', 
    'pattern_analysis_jobs',
    'explicit_context_archive',
    'archival_statistics'
]

conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

print("\n1. Checking for new tables...")
print("-"*70)

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
all_tables = [row[0] for row in cursor.fetchall()]

# Check each expected table
missing_tables = []
for table in expected_tables:
    if table in all_tables:
        print(f"✓ {table}")
    else:
        print(f"✗ {table} - MISSING")
        missing_tables.append(table)

# Check for modified column in explicit_context
print("\n2. Checking for modified columns...")
print("-"*70)

cursor.execute("PRAGMA table_info(explicit_context)")
columns = [col[1] for col in cursor.fetchall()]

if 'original_confidence' in columns:
    print("✓ explicit_context.original_confidence")
else:
    print("✗ explicit_context.original_confidence - MISSING")

# Show all current tables
print("\n3. All Database Tables:")
print("-"*70)
for table in sorted(all_tables):
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"  {table}: {count} rows")

conn.close()

# Summary
print("\n" + "="*70)
if missing_tables:
    print(f"⚠️  WARNING: {len(missing_tables)} tables missing!")
    print(f"Missing tables: {', '.join(missing_tables)}")
    print("\nTo create missing tables, run:")
    print("  from smart_response.pattern_expander import PatternExpander")
    print("  from smart_response.context_archival import ContextArchival")
    print("  PatternExpander()  # Creates pattern tables")
    print("  ContextArchival()  # Creates archival tables")
else:
    print("✅ All new tables exist in database!")
print("="*70)
