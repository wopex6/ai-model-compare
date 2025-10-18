#!/usr/bin/env python3
"""
Test password authentication with various special characters to identify the issue
"""

import sqlite3
import bcrypt
from integrated_database import IntegratedDatabase
import requests

def test_password_characters():
    print("🔍 Testing Password Special Characters")
    print("=" * 50)
    
    # Test various passwords with special characters
    test_passwords = [
        "123",           # Simple (known working)
        ".//",           # Original problematic
        ".//.",          # Original intended
        "abc/def",       # Forward slash in middle
        "/abc",          # Forward slash at start
        "abc/",          # Forward slash at end
        "a.b",           # Period in middle
        ".abc",          # Period at start
        "abc.",          # Period at end
        "a/b/c",         # Multiple forward slashes
        "a.b.c",         # Multiple periods
        "!@#$%",         # Other special characters
        "pass/word",     # Common pattern with slash
        "user.name",     # Common pattern with period
    ]
    
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    
    working_passwords = []
    failing_passwords = []
    
    for i, password in enumerate(test_passwords):
        print(f"\n--- Test {i+1}: '{password}' (length: {len(password)}) ---")
        
        try:
            # Delete existing user
            cursor.execute('DELETE FROM users WHERE username = ?', ('TestUser',))
            
            # Create user with test password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute('''
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
            ''', ('TestUser', 'test@example.com', password_hash))
            conn.commit()
            
            # Test 1: Direct database authentication
            db = IntegratedDatabase()
            user = db.authenticate_user('TestUser', password)
            db_result = "✅ SUCCESS" if user else "❌ FAILED"
            print(f"   Database auth: {db_result}")
            
            # Test 2: API authentication
            try:
                response = requests.post('http://localhost:5000/api/auth/login', 
                                       json={'username': 'TestUser', 'password': password}, 
                                       timeout=5)
                api_result = "✅ SUCCESS" if response.status_code == 200 else f"❌ FAILED ({response.status_code})"
                print(f"   API auth: {api_result}")
                
                if user and response.status_code == 200:
                    working_passwords.append(password)
                    print(f"   ✅ BOTH WORK")
                else:
                    failing_passwords.append(password)
                    if user and response.status_code != 200:
                        print(f"   ⚠️  DB works but API fails - possible encoding issue")
                    elif not user and response.status_code == 200:
                        print(f"   ⚠️  API works but DB fails - unexpected")
                    else:
                        print(f"   ❌ BOTH FAIL")
                        
            except Exception as e:
                print(f"   API auth: ❌ ERROR ({e})")
                failing_passwords.append(password)
                
        except Exception as e:
            print(f"   Setup error: {e}")
            failing_passwords.append(password)
    
    conn.close()
    
    # Summary
    print(f"\n" + "=" * 50)
    print(f"📊 SUMMARY:")
    print(f"✅ Working passwords ({len(working_passwords)}):")
    for pwd in working_passwords:
        print(f"   '{pwd}'")
    
    print(f"\n❌ Failing passwords ({len(failing_passwords)}):")
    for pwd in failing_passwords:
        print(f"   '{pwd}'")
    
    # Analysis
    if failing_passwords:
        print(f"\n🔍 ANALYSIS:")
        slash_failures = [p for p in failing_passwords if '/' in p]
        period_failures = [p for p in failing_passwords if '.' in p and '/' not in p]
        
        if slash_failures:
            print(f"   ⚠️  Forward slash (/) appears problematic in: {slash_failures}")
        if period_failures:
            print(f"   ⚠️  Period (.) appears problematic in: {period_failures}")
        
        print(f"\n💡 LIKELY CAUSES:")
        print(f"   - URL encoding issues (/ becomes %2F)")
        print(f"   - JSON escaping issues")
        print(f"   - Form data encoding issues")
        print(f"   - Frontend/backend character handling mismatch")

if __name__ == "__main__":
    test_password_characters()
    
    print(f"\n🔧 RECOMMENDATION:")
    print(f"   Use password '123' for now, then change it in Settings tab")
    print(f"   We'll investigate the special character handling issue")
