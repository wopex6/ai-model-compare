import sqlite3

conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

cursor.execute("SELECT username, email, user_role FROM users WHERE user_role = 'administrator'")
admins = cursor.fetchall()

print("=" * 50)
print("ADMINISTRATORS:")
if admins:
    for admin in admins:
        print(f"  Username: {admin[0]}")
        print(f"  Email: {admin[1]}")
        print(f"  Role: {admin[2]}")
        print()
else:
    print("  No administrators found")

conn.close()
