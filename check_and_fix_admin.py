from integrated_database import IntegratedDatabase

db = IntegratedDatabase()
conn = db.get_connection()
cursor = conn.cursor()

# Check current role
cursor.execute('SELECT username, user_role FROM users WHERE username = "Wai Tse"')
result = cursor.fetchone()

if result:
    print(f"Username: {result[0]}")
    print(f"Current Role: {result[1]}")
    
    if result[1] != 'administrator':
        print("\n❌ Wai Tse is NOT an administrator!")
        print("Setting Wai Tse as administrator...")
        
        cursor.execute('UPDATE users SET user_role = ? WHERE username = ?', ('administrator', 'Wai Tse'))
        conn.commit()
        
        # Verify
        cursor.execute('SELECT user_role FROM users WHERE username = "Wai Tse"')
        new_role = cursor.fetchone()[0]
        print(f"✅ New Role: {new_role}")
    else:
        print("\n✅ Wai Tse is already an administrator")
else:
    print("❌ Wai Tse not found")

conn.close()
