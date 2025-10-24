"""
Quick script to check if the administrator user exists and has the correct role
"""

from integrated_database import IntegratedDatabase

db = IntegratedDatabase()

# Check if administrator user exists
conn = db.get_connection()
cursor = conn.cursor()

cursor.execute("SELECT id, username, email, user_role FROM users WHERE username = 'administrator'")
result = cursor.fetchone()

if result:
    print(f"✅ Administrator user found:")
    print(f"   ID: {result[0]}")
    print(f"   Username: {result[1]}")
    print(f"   Email: {result[2]}")
    print(f"   Role: {result[3]}")
else:
    print("❌ Administrator user NOT found!")
    print("\n Creating administrator user...")
    
    # Create administrator user
    import bcrypt
    password_hash = bcrypt.hashpw('admin'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    cursor.execute('''
        INSERT INTO users (username, email, password_hash, user_role)
        VALUES (?, ?, ?, ?)
    ''', ('administrator', 'admin@example.com', password_hash, 'administrator'))
    
    user_id = cursor.lastrowid
    
    # Create profile
    cursor.execute('''
        INSERT INTO user_profiles (user_id, first_name, last_name, bio, preferences)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, 'Admin', 'User', 'System Administrator', '{}'))
    
    conn.commit()
    print(f"✅ Administrator user created with ID: {user_id}")

conn.close()
