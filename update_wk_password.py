"""Update user WK password to 'testpass'"""

from integrated_database import IntegratedDatabase
import bcrypt

db = IntegratedDatabase()

print("\n" + "="*80)
print("UPDATING USER WK PASSWORD")
print("="*80)

conn = db.get_connection()
cursor = conn.cursor()

# Update password for user WK
new_password = 'testpass'
password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

cursor.execute('''
    UPDATE users 
    SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
    WHERE username = ?
''', (password_hash, 'WK'))

if cursor.rowcount > 0:
    conn.commit()
    print(f"\n✅ Password updated for user WK")
    print(f"   New password: {new_password}")
    print(f"   You can now login as WK with password 'testpass'")
    
    # Verify the password works
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", ('WK',))
    stored_hash = cursor.fetchone()[0]
    
    is_valid = bcrypt.checkpw(new_password.encode('utf-8'), stored_hash.encode('utf-8'))
    print(f"\n✅ Verification: Password works: {is_valid}")
else:
    print("\n❌ Failed to update password - user WK not found")

conn.close()

print("\n" + "="*80)
print("UPDATE COMPLETE")
print("="*80 + "\n")
