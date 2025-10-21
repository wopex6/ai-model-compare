"""
Set Ken as administrator and mark email as verified
"""

from integrated_database import IntegratedDatabase

db = IntegratedDatabase()

# Update Ken's account
import sqlite3
conn = db.get_connection()
cursor = conn.cursor()

# Set as administrator and verified
cursor.execute('''
    UPDATE users 
    SET user_role = 'administrator', email_verified = 1
    WHERE username = 'Ken'
''')

conn.commit()

# Check result
cursor.execute('SELECT username, email, user_role, email_verified FROM users WHERE username = "Ken"')
result = cursor.fetchone()

conn.close()

if result:
    print(f"✅ Updated Ken's account:")
    print(f"   Username: {result[0]}")
    print(f"   Email: {result[1]}")
    print(f"   Role: {result[2]}")
    print(f"   Email Verified: {bool(result[3])}")
else:
    print("❌ Ken not found")
