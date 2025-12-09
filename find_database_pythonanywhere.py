#!/usr/bin/env python3
"""Find the actual database location on PythonAnywhere"""

import os
import glob

print("="*70)
print("  Finding Database on PythonAnywhere")
print("="*70)
print()

# Check common locations
locations_to_check = [
    '~/ai-model-compare/integrated_users.db',
    '~/ai-model-compare/databases/integrated_users.db',
    '~/ai-model-compare/databases/production_integrated_users.db',
    './integrated_users.db',
    './databases/integrated_users.db',
    './databases/production_integrated_users.db',
]

print("🔍 Checking common locations...")
print()

found_databases = []

for loc in locations_to_check:
    expanded = os.path.expanduser(loc)
    if os.path.exists(expanded):
        size = os.path.getsize(expanded) / (1024 * 1024)
        print(f"✅ Found: {expanded}")
        print(f"   Size: {size:.2f} MB")
        found_databases.append(expanded)
    else:
        print(f"❌ Not found: {expanded}")

print()

# Search for any .db files in project
print("🔍 Searching for all .db files in project...")
print()

home = os.path.expanduser('~/ai-model-compare')
if os.path.exists(home):
    for root, dirs, files in os.walk(home):
        for file in files:
            if file.endswith('.db'):
                full_path = os.path.join(root, file)
                size = os.path.getsize(full_path) / (1024 * 1024)
                print(f"📁 {full_path}")
                print(f"   Size: {size:.2f} MB")
                if full_path not in found_databases:
                    found_databases.append(full_path)

print()
print("="*70)

if found_databases:
    print(f"✅ Found {len(found_databases)} database(s)")
    print()
    print("📋 What to do:")
    print()
    
    if len(found_databases) == 1:
        db_path = found_databases[0]
        print(f"1. Your database is at: {db_path}")
        print()
        print("2. Run migration with this command:")
        print(f"   python apply_schema_migration.py")
        print()
        print("   The script will be updated to use the correct path.")
    else:
        print("Multiple databases found. Likely locations:")
        for i, db in enumerate(found_databases, 1):
            print(f"{i}. {db}")
        print()
        print("Choose the main production database (largest file usually)")
else:
    print("❌ No databases found!")
    print()
    print("📋 This means:")
    print("   - Database hasn't been created yet")
    print("   - Need to create databases folder and upload database")
    print()
    print("To fix:")
    print("1. Create databases folder:")
    print("   mkdir -p ~/ai-model-compare/databases")
    print()
    print("2. Upload your local database via Files tab")
    print("   Upload to: ~/ai-model-compare/databases/")
    print("   Rename to: production_integrated_users.db")
    print()
    print("3. Then run the migration script")

print()
print("="*70)
