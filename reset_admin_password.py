#!/usr/bin/env python3
"""Reset administrator password to 'admin123'"""

from integrated_database import IntegratedDatabase
import bcrypt

db = IntegratedDatabase()

# New password
new_password = 'admin123'

# Hash the password
hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

# Update in database
conn = db.get_connection()
cursor = conn.cursor()

cursor.execute('''
    UPDATE users 
    SET password_hash = ?
    WHERE username = 'administrator'
''', (hashed.decode('utf-8'),))

conn.commit()
rows_updated = cursor.rowcount
conn.close()

if rows_updated > 0:
    print(f"\n✅ Administrator password reset successfully!")
    print(f"   Username: administrator")
    print(f"   Password: {new_password}")
    print(f"\n🔐 You can now login with these credentials")
else:
    print(f"\n❌ Failed to update password (no administrator user found)")
