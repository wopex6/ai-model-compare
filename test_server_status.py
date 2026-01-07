"""Test if server is responding"""

import requests
import time

print("\n" + "="*60)
print("🔍 SERVER STATUS CHECK")
print("="*60)

# Wait a moment for server to fully start
time.sleep(2)

# Test 1: Basic health check
print("\n1️⃣ Testing basic connection...")
try:
    response = requests.get('http://localhost:5000/', timeout=5)
    print(f"   ✅ Server responding: {response.status_code}")
except requests.exceptions.ConnectionError:
    print("   ❌ Server not responding - Connection refused")
except requests.exceptions.Timeout:
    print("   ❌ Server not responding - Timeout")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Login endpoint
print("\n2️⃣ Testing login endpoint...")
try:
    response = requests.post(
        'http://localhost:5000/api/auth/login',
        json={'username': 'test', 'password': 'test'},
        timeout=5
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Login endpoint working")
    else:
        print(f"   Response: {response.text[:200]}")
except requests.exceptions.ConnectionError:
    print("   ❌ Cannot connect to login endpoint")
except requests.exceptions.Timeout:
    print("   ❌ Login endpoint timeout")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Personality test page
print("\n3️⃣ Testing personality test page...")
try:
    response = requests.get('http://localhost:5000/personality-test', timeout=5)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Personality test page accessible")
    else:
        print(f"   ❌ Page issue: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*60 + "\n")
