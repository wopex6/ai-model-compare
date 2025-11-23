"""Check user WK credentials and registration status"""

from integrated_database import IntegratedDatabase
import bcrypt

db = IntegratedDatabase()

print("\n" + "="*80)
print("CHECKING USER WK CREDENTIALS")
print("="*80)

conn = db.get_connection()
cursor = conn.cursor()

# Check if user WK exists
cursor.execute("SELECT id, username, email, password_hash FROM users WHERE username = ?", ('WK',))
user_row = cursor.fetchone()

if user_row:
    user_id, username, email, password_hash = user_row
    print(f"\n✅ User WK found!")
    print(f"   User ID: {user_id}")
    print(f"   Username: {username}")
    print(f"   Email: {email}")
    print(f"   Password hash exists: {len(password_hash) > 0}")
    
    # Try to verify password
    test_password = 'testpass'
    try:
        is_valid = bcrypt.checkpw(test_password.encode('utf-8'), password_hash.encode('utf-8'))
        print(f"\n   Password 'testpass' is valid: {is_valid}")
    except Exception as e:
        print(f"\n   Error checking password: {e}")
    
    # Try some other common passwords
    common_passwords = ['.///', 'password', 'WK', '123456', 'wk']
    print(f"\n   Testing common passwords:")
    for pwd in common_passwords:
        try:
            is_valid = bcrypt.checkpw(pwd.encode('utf-8'), password_hash.encode('utf-8'))
            if is_valid:
                print(f"   ✅ Password '{pwd}' works!")
        except:
            pass
    
else:
    print("\n❌ User WK not found in database!")
    print("\nOptions:")
    print("1. Create user WK with password 'testpass'")
    print("2. Use existing user from database")
    
    # Show all users
    cursor.execute("SELECT id, username, email FROM users LIMIT 10")
    users = cursor.fetchall()
    
    print(f"\nExisting users ({len(users)} shown):")
    for user_id, username, email in users:
        print(f"  - {username} (ID: {user_id}, Email: {email})")
    
    # Ask if we should create user WK
    print("\n" + "="*80)
    print("CREATE USER WK?")
    print("="*80)
    create = input("Create user WK with password 'testpass'? (y/n): ")
    
    if create.lower() == 'y':
        password_hash = bcrypt.hashpw('testpass'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', ('WK', 'wk@test.com', password_hash))
        
        user_id = cursor.lastrowid
        
        # Create profile
        cursor.execute('''
            INSERT INTO user_profiles (user_id, first_name, last_name, bio, preferences)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, 'W', 'K', 'Test user', '{}'))
        
        conn.commit()
        print(f"\n✅ User WK created with ID: {user_id}")
        print("   Username: WK")
        print("   Password: testpass")
        print("   Email: wk@test.com")
    else:
        print("\nUser WK not created. Use existing user for testing.")

conn.close()

print("\n" + "="*80)
print("CHECK COMPLETE")
print("="*80 + "\n")
