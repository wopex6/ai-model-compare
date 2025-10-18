#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Database Tables:")
print("=" * 60)
for table in tables:
    print(f"\n📋 Table: {table[0]}")
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")

conn.close()
