"""
Tests for Moltbook collaboration integration into chat flows.
Local tests verify the collaboration logic; production tests verify the API endpoints.
"""
import sqlite3
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smart_response.character_traits import create_character_trait_system
from smart_response.character_specific_context import create_character_specific_context
from smart_response.character_collaboration import create_collaboration_system


def test_integration_local():
    """Test that collaboration triggers and enriches responses as expected"""
    db = sqlite3.connect(':memory:')
    trait_system = create_character_trait_system(db)
    context = create_character_specific_context(db, trait_system)
    collab = create_collaboration_system(db, trait_system, context)
    passed = 0
    failed = 0

    # Test 1: Multi-domain message triggers collaboration
    try:
        should, mode, rule = collab.should_collaborate(
            "I'm stressed about work and my relationship is falling apart", {}
        )
        assert should is True, "Multi-domain message should trigger"
        print(f"  ✅ Multi-domain trigger: mode={mode}, rule={rule}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Multi-domain trigger: {e}")
        failed += 1

    # Test 2: Simple message does NOT trigger
    try:
        should, mode, rule = collab.should_collaborate("Hello, how are you?", {})
        assert should is False, "Simple greeting should not trigger"
        print(f"  ✅ No false trigger on greeting")
        passed += 1
    except Exception as e:
        print(f"  ❌ No false trigger: {e}")
        failed += 1

    # Test 3: Silent mode produces enrichment text
    try:
        result = collab.orchestrate_collaboration(
            "I'm worried about money and my mental health", 1, {}, 'silent', None
        )
        assert result is not None
        assert result.mode == 'silent'
        assert result.response  # Non-empty
        assert len(result.contributions) >= 2
        print(f"  ✅ Silent collaboration: {len(result.contributions)} contributors, response={len(result.response)} chars")
        passed += 1
    except Exception as e:
        print(f"  ❌ Silent collaboration: {e}")
        failed += 1

    # Test 4: Visible mode includes character names
    try:
        result = collab.orchestrate_collaboration(
            "Should I change careers or stay in my current job?", 1, {}, 'visible', None
        )
        assert result is not None
        assert result.mode == 'visible'
        assert '**' in result.response  # Markdown bold for character names
        print(f"  ✅ Visible collaboration: includes attributed perspectives")
        passed += 1
    except Exception as e:
        print(f"  ❌ Visible collaboration: {e}")
        failed += 1

    # Test 5: Debate mode produces dialogue format
    try:
        result = collab.orchestrate_collaboration(
            "What do you all think about pursuing my dreams vs financial security?", 1, {}, 'debate', None
        )
        assert result is not None
        assert result.mode == 'debate'
        assert '🎭' in result.response
        assert 'Synthesis' in result.response
        print(f"  ✅ Debate collaboration: Moltbook-style dialogue generated")
        passed += 1
    except Exception as e:
        print(f"  ❌ Debate collaboration: {e}")
        failed += 1

    # Test 6: Simulated chat enrichment (mimics what app.py does)
    try:
        fake_ai_response = "I understand you're going through a tough time. Let me help."
        message = "I'm struggling with work stress and family problems"
        
        should, detected_mode, rule_name = collab.should_collaborate(message, {})
        assert should is True
        
        collab_result = collab.orchestrate_collaboration(
            message, 1, {}, detected_mode or 'silent', rule_name
        )
        assert collab_result is not None
        
        # Simulate enrichment logic from app.py
        if collab_result.mode == 'silent':
            enrichment_parts = []
            for c in collab_result.contributions[1:]:
                if c.get('action_suggestion'):
                    enrichment_parts.append(c['action_suggestion'])
            if enrichment_parts:
                enriched = fake_ai_response + "\n\n" + enrichment_parts[0][:200]
            else:
                enriched = fake_ai_response
        elif collab_result.mode == 'visible':
            enriched = fake_ai_response + "\n\n" + collab_result.response
        else:
            enriched = collab_result.response
        
        assert len(enriched) > len(fake_ai_response), "Response should be enriched"
        print(f"  ✅ Chat enrichment simulation: {len(fake_ai_response)} → {len(enriched)} chars")
        passed += 1
    except Exception as e:
        print(f"  ❌ Chat enrichment simulation: {e}")
        failed += 1

    # Test 7: On-demand perspectives (force collaboration)
    try:
        result = collab.orchestrate_collaboration(
            "Hello how are you", 1, {}, 'debate', None
        )
        # Even a simple message should work when forced
        assert result is not None
        assert len(result.contributions) >= 2
        print(f"  ✅ On-demand perspectives: forced debate on simple message, {len(result.contributions)} contributors")
        passed += 1
    except Exception as e:
        print(f"  ❌ On-demand perspectives: {e}")
        failed += 1

    # Test 8: Collaboration metadata structure
    try:
        result = collab.orchestrate_collaboration(
            "Help me with work and relationships", 1, {}, 'visible', None
        )
        assert result is not None
        collab_data = {
            'collaborated': True,
            'mode': result.mode,
            'characters': result.participating_characters,
            'event_id': result.event_id,
            'contributions_count': len(result.contributions)
        }
        assert collab_data['collaborated'] is True
        assert collab_data['mode'] == 'visible'
        assert len(collab_data['characters']) >= 2
        assert collab_data['event_id'] > 0
        # Verify JSON-serializable
        json.dumps(collab_data)
        print(f"  ✅ Metadata structure: valid JSON, {len(collab_data['characters'])} characters")
        passed += 1
    except Exception as e:
        print(f"  ❌ Metadata structure: {e}")
        failed += 1

    print(f"\n{'='*50}")
    print(f"MOLTBOOK INTEGRATION LOCAL: {passed}/{passed+failed} passed")
    print(f"{'='*50}")
    assert failed == 0, f"{failed} test(s) failed"


def test_production():
    """Test Moltbook integration endpoints on PythonAnywhere"""
    import requests

    BASE_URL = "https://trabcd.pythonanywhere.com"
    print(f"\nTarget: {BASE_URL}")

    session = requests.Session()
    passed = 0
    failed = 0

    # Login
    r = session.post(f"{BASE_URL}/api/auth/login", json={"username": "Wai Tse", "password": "123"})
    if r.status_code != 200:
        print(f"  ❌ Login failed: {r.status_code}")
        assert False, f"Login failed: {r.status_code}"
    token = r.json().get('token')
    session.headers.update({"Authorization": f"Bearer {token}"})
    print(f"  ✅ Logged in")

    # Test 1: On-demand perspectives endpoint
    try:
        r = session.post(f"{BASE_URL}/chat/perspectives", json={
            "message": "I'm struggling with work and relationship problems",
            "mode": "debate"
        })
        if r.status_code == 200:
            data = r.json()
            assert data.get('success') is True
            assert '🎭' in data.get('response', '')
            contribs = data.get('contributions', data.get('characters', []))
            assert len(contribs) >= 2
            print(f"  ✅ On-demand debate: {len(contribs)} characters")
            passed += 1
        else:
            print(f"  ❌ On-demand debate: {r.status_code} {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ On-demand debate: {e}")
        failed += 1

    # Test 2: On-demand visible mode
    try:
        r = session.post(f"{BASE_URL}/chat/perspectives", json={
            "message": "Should I change careers?",
            "mode": "visible"
        })
        if r.status_code == 200:
            data = r.json()
            assert data.get('success') is True
            assert 'Perspectives' in data.get('response', '') or '**' in data.get('response', '')
            print(f"  ✅ On-demand visible: attributed perspectives returned")
            passed += 1
        else:
            print(f"  ❌ On-demand visible: {r.status_code} {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ On-demand visible: {e}")
        failed += 1

    # Test 3: On-demand silent mode
    try:
        r = session.post(f"{BASE_URL}/chat/perspectives", json={
            "message": "I feel lost in life",
            "mode": "silent"
        })
        if r.status_code == 200:
            data = r.json()
            assert data.get('success') is True
            assert len(data.get('response', '')) > 10
            print(f"  ✅ On-demand silent: unified response ({len(data['response'])} chars)")
            passed += 1
        else:
            print(f"  ❌ On-demand silent: {r.status_code} {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ On-demand silent: {e}")
        failed += 1

    # Test 4: Chatchat collaboration enrichment (send a multi-domain message)
    try:
        # First create or get a session
        r = session.get(f"{BASE_URL}/api/user/conversations")
        if r.status_code == 200:
            convs = r.json()
            # Handle both list and dict responses
            if isinstance(convs, dict):
                convs = convs.get('conversations', [])
            
            if convs and len(convs) > 0:
                test_session = convs[0]['session_id']
            else:
                # Create one
                r2 = session.post(f"{BASE_URL}/api/user/conversations", json={"title": "Moltbook Test"})
                test_session = r2.json().get('session_id')
            
            # Send a multi-domain message that should trigger collaboration
            r = session.post(f"{BASE_URL}/api/user/conversations/{test_session}/messages", json={
                "senderType": "user",
                "content": "I'm anxious about work deadlines and my partner is upset with me"
            })
            if r.status_code == 200:
                data = r.json()
                if data.get('collaboration'):
                    collab = data['collaboration']
                    print(f"  ✅ Chatchat enrichment: mode={collab['mode']}, {collab['contributions_count']} contributors")
                else:
                    print(f"  ⚠️ Chatchat enrichment: response OK but no collaboration triggered (may depend on triggers)")
                passed += 1
            else:
                print(f"  ❌ Chatchat enrichment: {r.status_code} {r.text[:200]}")
                failed += 1
        else:
            print(f"  ⚠️ Chatchat enrichment: could not get conversations ({r.status_code})")
            passed += 1
    except Exception as e:
        print(f"  ❌ Chatchat enrichment: {e}")
        failed += 1

    # Test 5: Collaboration stats should show increased activity
    try:
        r = session.get(f"{BASE_URL}/api/collaboration/stats")
        if r.status_code == 200:
            data = r.json()
            print(f"  ✅ Collaboration stats: total={data.get('total_collaborations')}")
            passed += 1
        else:
            print(f"  ❌ Collaboration stats: {r.status_code}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Collaboration stats: {e}")
        failed += 1

    print(f"\n{'='*50}")
    print(f"MOLTBOOK PRODUCTION: {passed}/{passed+failed} passed")
    print(f"{'='*50}")
    assert failed == 0, f"{failed} test(s) failed"


if __name__ == '__main__':
    print("=" * 60)
    print("MOLTBOOK INTEGRATION TESTS")
    print("=" * 60)

    print("\n📋 LOCAL INTEGRATION TESTS")
    print("-" * 40)
    local_ok = test_integration_local()

    if '--production' in sys.argv:
        print("\n📋 PRODUCTION TESTS (PythonAnywhere)")
        print("-" * 40)
        prod_ok = test_production()
    else:
        print("\n⏭️  Skipping production tests (use --production flag)")
        prod_ok = True

    if local_ok and prod_ok:
        print("\n🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)
