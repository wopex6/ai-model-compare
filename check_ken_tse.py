import sqlite3

conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

# Check schema first
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
print("=" * 50)
print("USERS TABLE SCHEMA:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# Check ken tse
cursor.execute("SELECT * FROM users WHERE username = 'ken tse'")
ken = cursor.fetchone()

# Get column names
cursor.execute("PRAGMA table_info(users)")
col_names = [col[1] for col in cursor.fetchall()]

print("\n" + "=" * 50)
print("KEN TSE INFO:")
if ken:
    for i, col_name in enumerate(col_names):
        if col_name != 'password':  # Don't print password
            print(f"  {col_name}: {ken[i]}")
else:
    print("  Not found")

conn.close()
