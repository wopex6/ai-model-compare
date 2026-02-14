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
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        print(f"  Uptime: {data.get('uptime_formatted', 'N/A')}")
        print(f"  Status: {data.get('status', 'N/A')}")
    except Exception as e:
        print(f"  Error: {e}")
        assert False, f"Health endpoint failed: {e}"

def test_login_page():
    """Test that login page loads"""
    print("Testing login page...")
    try:
        r = requests.get(f"{BASE_URL}/", timeout=10)
        print(f"  Status: {r.status_code}")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert 'login' in r.text.lower() or 'password' in r.text.lower(), "Login page content not found"
        print("  Login page loads correctly")
    except Exception as e:
        print(f"  Error: {e}")
        assert False, f"Login page failed: {e}"

def test_static_files():
    """Test static files load"""
    print("Testing static files...")
    files = [
        "/static/voice_input.js",
        "/static/manifest.json",
        "/static/auth_helper.js"
    ]
    failed = []
    for f in files:
        try:
            r = requests.get(f"{BASE_URL}{f}", timeout=10)
            status = "✅" if r.status_code == 200 else "❌"
            print(f"  {status} {f}: {r.status_code}")
            if r.status_code != 200:
                failed.append(f)
        except Exception as e:
            print(f"  ❌ {f}: {e}")
            failed.append(f)
    assert len(failed) == 0, f"Static files failed: {failed}"

def test_analytics_page():
    """Test analytics page (requires auth, will get redirect)"""
    print("Testing analytics page...")
    try:
        r = requests.get(f"{BASE_URL}/admin/analytics", timeout=10, allow_redirects=False)
        print(f"  Status: {r.status_code}")
        # Either 200 (if session exists) or 302 (redirect to login)
        assert r.status_code in [200, 302], f"Expected 200 or 302, got {r.status_code}"
    except Exception as e:
        print(f"  Error: {e}")
        assert False, f"Analytics page failed: {e}"

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
