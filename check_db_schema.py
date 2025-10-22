from integrated_database import IntegratedDatabase

db = IntegratedDatabase()
conn = db.get_connection()
cursor = conn.cursor()

# Check users table structure
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()

print("Users Table Columns:")
print("-" * 60)
for col in columns:
    print(f"  {col[1]:20s} {col[2]:15s} {'NOT NULL' if col[3] else ''}")

conn.close()
