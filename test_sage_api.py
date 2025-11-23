"""Quick test to diagnose Sage Wei network error"""
import sys
import requests
import json

print("Testing Sage Wei endpoints...\n")

base_url = "http://localhost:5000"

# Test 1: Page load
print("1. Testing /sage page load...")
try:
    r = requests.get(f"{base_url}/sage", timeout=5)
    print(f"   Status: {r.status_code} {'✅' if r.status_code == 200 else '❌'}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Daily wisdom API
print("\n2. Testing /sage/daily-wisdom API...")
try:
    r = requests.get(f"{base_url}/sage/daily-wisdom", timeout=5)
    print(f"   Status: {r.status_code} {'✅' if r.status_code == 200 else '❌'}")
    if r.status_code == 200:
        data = r.json()
        print(f"   Wisdom: {data.get('daily_wisdom', 'N/A')[:60]}...")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Stats API
print("\n3. Testing /sage/stats API...")
try:
    r = requests.get(f"{base_url}/sage/stats", timeout=5)
    print(f"   Status: {r.status_code} {'✅' if r.status_code == 200 else '❌'}")
    if r.status_code == 200:
        data = r.json()
        print(f"   Stats: {data}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Chat API (this is likely where the error is)
print("\n4. Testing /sage/chat API...")
try:
    r = requests.post(
        f"{base_url}/sage/chat",
        json={"message": "Hello", "include_context": True},
        timeout=30
    )
    print(f"   Status: {r.status_code} {'✅' if r.status_code == 200 else '❌'}")
    if r.status_code == 200:
        data = r.json()
        print(f"   Response preview: {data.get('response', 'N/A')[:100]}...")
    else:
        print(f"   Error response: {r.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Diagnostic complete!")
