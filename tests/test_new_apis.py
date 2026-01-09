"""
Test new API endpoints directly using requests.
"""
import requests

BASE_URL = "https://trabcd.pythonanywhere.com"

def test_health_endpoint():
    """Test /api/system/health endpoint"""
    print("Testing /api/system/health...")
    try:
        r = requests.get(f"{BASE_URL}/api/system/health", timeout=10)
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"  Uptime: {data.get('uptime_formatted', 'N/A')}")
            print(f"  Status: {data.get('status', 'N/A')}")
            return True
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False

def test_login_page():
    """Test that login page loads"""
    print("Testing login page...")
    try:
        r = requests.get(f"{BASE_URL}/", timeout=10)
        print(f"  Status: {r.status_code}")
        if r.status_code == 200 and ('login' in r.text.lower() or 'password' in r.text.lower()):
            print("  Login page loads correctly")
            return True
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False

def test_static_files():
    """Test static files load"""
    print("Testing static files...")
    files = [
        "/static/voice_input.js",
        "/static/manifest.json",
        "/static/auth_helper.js"
    ]
    all_ok = True
    for f in files:
        try:
            r = requests.get(f"{BASE_URL}{f}", timeout=10)
            status = "✅" if r.status_code == 200 else "❌"
            print(f"  {status} {f}: {r.status_code}")
            if r.status_code != 200:
                all_ok = False
        except Exception as e:
            print(f"  ❌ {f}: {e}")
            all_ok = False
    return all_ok

def test_analytics_page():
    """Test analytics page (requires auth, will get redirect)"""
    print("Testing analytics page...")
    try:
        r = requests.get(f"{BASE_URL}/admin/analytics", timeout=10, allow_redirects=False)
        print(f"  Status: {r.status_code}")
        # Either 200 (if session exists) or 302 (redirect to login)
        return r.status_code in [200, 302]
    except Exception as e:
        print(f"  Error: {e}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("API & ENDPOINT TESTS")
    print("="*50)
    
    results = []
    results.append(("Health API", test_health_endpoint()))
    results.append(("Login Page", test_login_page()))
    results.append(("Static Files", test_static_files()))
    results.append(("Analytics Page", test_analytics_page()))
    
    print("\n" + "="*50)
    passed = sum(1 for _, r in results if r)
    print(f"RESULTS: {passed}/{len(results)} passed")
    print("="*50)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")
