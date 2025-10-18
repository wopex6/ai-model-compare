#!/usr/bin/env python3
"""
Direct password test without Flask server
"""

from integrated_database import IntegratedDatabase

def test_passwords_directly():
    print("🔍 DIRECT PASSWORD TEST (No Flask)")
    print("=" * 40)
    
    db = IntegratedDatabase()
    
    # Test passwords you've been trying
    test_passwords = ["123", ".//", ".//.", "122"]
    
    for password in test_passwords:
        print(f"\nTesting password: '{password}'")
        print(f"Length: {len(password)}")
        print(f"Characters: {list(password)}")
        
        # This will trigger our debug output in integrated_database.py
        result = db.authenticate_user('Wai Tse', password)
        
        if result:
            print(f"✅ SUCCESS: {result}")
        else:
            print(f"❌ FAILED: Invalid credentials")
        
        print("-" * 30)

if __name__ == "__main__":
    test_passwords_directly()
