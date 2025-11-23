#!/usr/bin/env python3
"""Test the permanent delete function directly"""

from integrated_database import IntegratedDatabase

# Create database instance
db = IntegratedDatabase()

# Try to delete user 46
user_id = 46

print(f"Attempting to permanently delete user {user_id}...")

try:
    result = db.permanent_delete_user(user_id)
    if result:
        print(f"✅ SUCCESS: User {user_id} deleted")
    else:
        print(f"❌ FAILED: Could not delete user {user_id}")
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
