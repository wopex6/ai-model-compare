"""
Direct API test for Character Interpretation Storage
Tests that both responded and noticed characters store rich context

Run with: python test_interpretations_api.py
"""

import requests
import json

BASE_URL = "https://trabcd.pythonanywhere.com"
TEST_USER = "admin"
TEST_PASS = "admin"


def test_character_interpretations():
    """Test character interpretations via API"""
    
    print("\n" + "="*60)
    print("CHARACTER INTERPRETATION STORAGE TEST (API)")
    print("="*60)
    
    # Create session to persist cookies
    session = requests.Session()
    
    # Step 1: Login via form (to get session cookie)
    print("\n[1] Logging in...")
    
    # First get the login page to establish session
    session.get(f"{BASE_URL}/user_logon")
    
    # Submit login form
    login_response = session.post(f"{BASE_URL}/user_logon", data={
        "username": TEST_USER,
        "password": TEST_PASS
    }, allow_redirects=True)
    
    # Check if we got redirected to dashboard (success) or still on login (fail)
    if login_response.status_code == 200:
        if 'dashboard' in login_response.url or 'user_logon' not in login_response.url:
            print(f"    ✓ Logged in, redirected to: {login_response.url}")
        else:
            print(f"    ⚠️ May not be logged in, URL: {login_response.url}")
    else:
        print(f"    ❌ Login request failed: {login_response.status_code}")
        return
    
    # Step 2: Send test message via domain characters route
    test_message = "I'm stressed about my job deadline and worried about money"
    print(f"\n[2] Sending test message: '{test_message}'")
    
    route_response = session.post(f"{BASE_URL}/api/domain-characters/route", json={
        "message": test_message,
        "use_ai": True,
        "character_id": "coordinator"
    })
    
    if route_response.status_code == 200:
        route_data = route_response.json()
        if route_data.get('success'):
            print(f"    ✓ Message routed successfully")
            print(f"    ✓ Got {len(route_data.get('responses', []))} response(s)")
            for resp in route_data.get('responses', []):
                print(f"      - {resp.get('character_id', 'Unknown')}: {resp.get('content', '')[:100]}...")
        else:
            print(f"    ❌ Routing failed: {route_data.get('error', 'Unknown')}")
    else:
        print(f"    ❌ Route request failed: {route_response.status_code}")
        print(f"    Response: {route_response.text[:200]}")
    
    # Step 3: Check cross-domain insights
    print(f"\n[3] Checking cross-domain insights...")
    
    cross_response = session.post(f"{BASE_URL}/api/domain-characters/cross-domain", json={
        "message": test_message
    })
    
    if cross_response.status_code == 200:
        cross_data = cross_response.json()
        
        if cross_data.get('success'):
            print("    ✓ Cross-domain analysis successful")
            
            # Show responded characters
            responded = cross_data.get('responded', [])
            print(f"\n    ✓ RESPONDED ({len(responded)} characters):")
            for char in responded:
                print(f"      - {char['character']} ({char['domain']}): {char['concern_level']*100:.0f}%")
            
            # Show silent observers
            silent = cross_data.get('silent_observers', [])
            print(f"\n    👁️ NOTICED BUT DIDN'T RESPOND ({len(silent)} characters):")
            for char in silent:
                print(f"      - {char['character']} ({char['domain']}): {char['concern_level']*100:.0f}%")
            
            # Show cross-domain patterns
            cross_patterns = cross_data.get('cross_domain', {})
            if cross_patterns.get('correlations'):
                print(f"\n    🔗 CROSS-DOMAIN PATTERNS:")
                for corr in cross_patterns['correlations']:
                    print(f"      - {corr['description']}")
            
            # Show full interpretation data
            insights = cross_data.get('domain_insights', [])
            print(f"\n    📊 FULL INTERPRETATION DATA ({len(insights)} characters):")
            
            for insight in insights:
                if insight.get('concern_level', 0) > 0:
                    interp = insight.get('interpretation', {})
                    print(f"\n      {insight.get('display_name', 'Unknown')}:")
                    print(f"        Domain: {interp.get('domain', 'N/A')}")
                    print(f"        Concern: {insight.get('concern_level', 0)*100:.0f}%")
                    print(f"        Emotions: {interp.get('detected_emotions', [])}")
                    print(f"        User state: {interp.get('user_emotional_state', 'N/A')}")
                    print(f"        Perspective: {interp.get('character_perspective', 'N/A')}")
                    print(f"        Potential advice: {interp.get('potential_advice', 'N/A')}")
                    print(f"        Continuity tags: {interp.get('continuity_tags', [])}")
        else:
            print(f"    ❌ Cross-domain failed: {cross_data.get('error', 'Unknown')}")
    else:
        print(f"    ❌ Cross-domain request failed: {cross_response.status_code}")
    
    # Step 4: Check stored interpretations in database
    print(f"\n[4] Checking database storage...")
    
    history_response = session.get(f"{BASE_URL}/api/domain-characters/history/coordinator?limit=1")
    
    if history_response.status_code == 200:
        history_data = history_response.json()
        if history_data.get('success') and history_data.get('history'):
            latest = history_data['history'][0]
            history_id = latest.get('id')
            print(f"    ✓ Latest history ID: {history_id}")
            
            # Get interpretations
            interp_response = session.get(f"{BASE_URL}/api/domain-characters/interpretations/{history_id}")
            
            if interp_response.status_code == 200:
                interp_data = interp_response.json()
                if interp_data.get('success'):
                    interps = interp_data.get('interpretations', [])
                    print(f"    ✓ {len(interps)} interpretations stored in database:")
                    
                    for interp in interps:
                        status = "✓ Responded" if interp.get('responded') else "👁️ Noticed"
                        concern = interp.get('concern_level', 0)
                        print(f"      {status}: {interp.get('character_id')} ({concern*100:.0f}%)")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    test_character_interpretations()
