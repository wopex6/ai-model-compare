"""
Test WK4 psychology traits API endpoint
"""

import requests
import json

# Login first
login_url = "http://localhost:5000/api/auth/login"
login_data = {
    "username": "wk4",
    "password": "123"
}

print("="*80)
print("TESTING WK4 PSYCHOLOGY TRAITS API")
print("="*80)

# Login
print("\n1. Logging in...")
response = requests.post(login_url, json=login_data)
if response.status_code == 200:
    token = response.json().get('token')
    print(f"   ✅ Logged in successfully")
    print(f"   Token: {token[:50]}...")
    
    # Get psychology traits
    print("\n2. Fetching psychology traits...")
    traits_url = "http://localhost:5000/api/user/psychology-traits"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(traits_url, headers=headers)
    if response.status_code == 200:
        traits = response.json()
        print(f"   ✅ Got {len(traits)} traits")
        
        print("\n3. Traits details:")
        for trait in traits:
            print(f"   - {trait['trait_name']}: {trait['trait_value']:.2f}")
        
        # Check for Big Five
        big_five = [t for t in traits if t['trait_name'] in ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']]
        print(f"\n4. Big Five traits found: {len(big_five)}/5")
        
        if len(big_five) >= 5:
            print("\n" + "="*80)
            print("✅ API TEST PASSED!")
            print("="*80)
        else:
            print("\n" + "="*80)
            print("❌ API TEST FAILED - Missing Big Five traits")
            print("="*80)
    else:
        print(f"   ❌ Failed to get traits: {response.status_code}")
        print(f"   Error: {response.text}")
else:
    print(f"   ❌ Login failed: {response.status_code}")
    print(f"   Error: {response.text}")

print("="*80)
