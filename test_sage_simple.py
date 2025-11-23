"""Simple test to check if /sage route works"""
import requests
import sys

try:
    print("Testing /sage endpoint...")
    response = requests.get("http://localhost:5000/sage", timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Page loads successfully!")
        print(f"Content length: {len(response.text)} bytes")
        
        # Check for key elements
        if "Sage Wei" in response.text:
            print("✅ Sage Wei title found")
        else:
            print("❌ Sage Wei title NOT found")
            
        if "wisdom_sage.html" in response.text or "sage-container" in response.text:
            print("✅ Template content present")
        else:
            print("❌ Template content missing")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text[:500])
        
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to Flask server. Is it running on http://localhost:5000?")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
