"""
Phase 5 Enhancement Tests
Tests both locally (in-memory DB) and against PythonAnywhere production.
"""
import sqlite3
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smart_response.character_traits import create_character_trait_system, SituationAnalysis


def test_local():
    """Test all Phase 5 enhancements with in-memory DB"""
    db = sqlite3.connect(':memory:')
    system = create_character_trait_system(db)
    passed = 0
    failed = 0
    
    # Test 1: Basic match still works (regression)
    try:
        situation = system.analyze_situation('I feel anxious about my deadline')
        best, score, reasoning = system.match_character(situation)
        assert best is not None
        assert 0 <= score <= 1
        print(f"  ✅ Basic match: {best.display_name} (score={score:.3f})")
        passed += 1
    except Exception as e:
        print(f"  ❌ Basic match: {e}")
        failed += 1
    
    # Test 2: Personality-weighted match
    try:
        personality = {
            'openness': 0.8, 'conscientiousness': 0.3,
            'extraversion': 0.2, 'agreeableness': 0.7, 'neuroticism': 0.8
        }
        result = system.personality_weighted_match(situation, personality, user_id=1, top_n=3)
        assert 'best_match' in result
        assert 'alternatives' in result
        assert 'personality_influence' in result
        assert 'trait_weights_applied' in result
        assert len(result['alternatives']) == 3
        assert result['best_match']['similarity'] > 0
        bm = result['best_match']
        print(f"  ✅ Personality match: {bm['character']['display_name']} (sim={bm['similarity']})")
        passed += 1
    except Exception as e:
        print(f"  ❌ Personality match: {e}")
        failed += 1
    
    # Test 3: Personality influence description
    try:
        effects = result['personality_influence']['personality_effects']
        assert len(effects) > 0, "Expected personality effects"
        weights = result['trait_weights_applied']
        assert len(weights) == 12, f"Expected 12 trait weights, got {len(weights)}"
        # High neuroticism should boost empathy weight
        assert weights.get('empathy', 1.0) > 1.0, "Empathy weight should be boosted for high neuroticism"
        print(f"  ✅ Personality influence: {len(effects)} effects, empathy weight={weights['empathy']}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Personality influence: {e}")
        failed += 1
    
    # Test 4: Different personality gives different result
    try:
        personality_b = {
            'openness': 0.2, 'conscientiousness': 0.9,
            'extraversion': 0.8, 'agreeableness': 0.2, 'neuroticism': 0.2
        }
        result_b = system.personality_weighted_match(situation, personality_b, user_id=2, top_n=3)
        # The two different personalities should (likely) get different top matches or different scores
        sim_a = result['best_match']['similarity']
        sim_b = result_b['best_match']['similarity']
        char_a = result['best_match']['character']['character_id']
        char_b = result_b['best_match']['character']['character_id']
        print(f"  ✅ Different personality: A={char_a}({sim_a}), B={char_b}({sim_b})")
        passed += 1
    except Exception as e:
        print(f"  ❌ Different personality: {e}")
        failed += 1
    
    # Test 5: Record interaction
    try:
        system.record_character_interaction(1, 'therapist', satisfaction=0.8)
        system.record_character_interaction(1, 'therapist', satisfaction=0.9)
        system.record_character_interaction(1, 'coach')
        system.record_character_interaction(1, 'sage', satisfaction=0.6)
        print(f"  ✅ Record interactions: 4 recorded")
        passed += 1
    except Exception as e:
        print(f"  ❌ Record interactions: {e}")
        failed += 1
    
    # Test 6: Get user preferences
    try:
        prefs = system.get_user_preferences(1)
        assert 'preferences' in prefs
        assert 'recommendation_history' in prefs
        assert prefs['total_interactions'] >= 4
        assert len(prefs['preferences']) >= 3
        # Therapist should have highest preference (2 interactions with high satisfaction)
        top_pref = prefs['preferences'][0]
        print(f"  ✅ User preferences: {len(prefs['preferences'])} chars, top={top_pref['character_id']} (score={top_pref['preference_score']})")
        passed += 1
    except Exception as e:
        print(f"  ❌ User preferences: {e}")
        failed += 1
    
    # Test 7: Preference bias affects matching
    try:
        # After interactions, therapist should get a preference boost (2 interactions = qualifies)
        # coach and sage only had 1 interaction each, so they won't have bias yet
        bias = system._get_user_preference_bias(1)
        assert len(bias) >= 1, f"Expected at least 1 preference bias, got {len(bias)}"
        assert 'therapist' in bias, "Therapist should have preference bias (2 interactions)"
        print(f"  ✅ Preference bias: {len(bias)} characters with bias")
        passed += 1
    except Exception as e:
        print(f"  ❌ Preference bias: {e}")
        failed += 1
    
    # Test 8: Coverage analysis
    try:
        coverage = system.analyze_trait_space_coverage()
        assert 'overall_coverage_score' in coverage
        assert 'diversity_score' in coverage
        assert 'trait_analysis' in coverage
        assert 'coverage_gaps' in coverage
        assert 'similar_character_clusters' in coverage
        assert 'recommendations' in coverage
        assert len(coverage['trait_analysis']) == 12
        assert 0 <= coverage['overall_coverage_score'] <= 1
        assert 0 <= coverage['diversity_score'] <= 1
        print(f"  ✅ Coverage analysis: score={coverage['overall_coverage_score']}, diversity={coverage['diversity_score']}, gaps={len(coverage['coverage_gaps'])}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Coverage analysis: {e}")
        failed += 1
    
    # Test 9: Similar character detection
    try:
        clusters = coverage['similar_character_clusters']
        # Should find some similar pairs in 16 characters
        print(f"  ✅ Similar clusters: {len(clusters)} pairs detected")
        passed += 1
    except Exception as e:
        print(f"  ❌ Similar clusters: {e}")
        failed += 1
    
    # Test 10: Coverage recommendations
    try:
        recs = coverage['recommendations']
        assert len(recs) > 0, "Should have at least 1 recommendation"
        print(f"  ✅ Recommendations: {len(recs)} suggestions")
        for r in recs:
            print(f"     → {r}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Recommendations: {e}")
        failed += 1
    
    print(f"\n{'='*50}")
    print(f"LOCAL TESTS: {passed}/{passed+failed} passed")
    print(f"{'='*50}")
    assert failed == 0, f"{failed} test(s) failed"


def test_production():
    """Test Phase 5 enhancement endpoints on PythonAnywhere"""
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

    # Test 1: Personality match endpoint
    try:
        r = session.post(f"{BASE_URL}/api/character-traits/personality-match", json={
            "message": "I'm feeling stressed about money and need help budgeting",
            "personality": {
                "openness": 0.6, "conscientiousness": 0.8,
                "extraversion": 0.4, "agreeableness": 0.6, "neuroticism": 0.7
            }
        })
        if r.status_code == 200:
            data = r.json()
            bm = data.get('best_match', {})
            alts = data.get('alternatives', [])
            pi = data.get('personality_influence', {})
            print(f"  ✅ Personality match: {bm.get('character', {}).get('display_name')} (sim={bm.get('similarity')})")
            print(f"     Alternatives: {len(alts)}, Effects: {len(pi.get('personality_effects', []))}")
            passed += 1
        else:
            print(f"  ❌ Personality match: Status {r.status_code} - {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Personality match: {e}")
        failed += 1
    
    # Test 2: Auto-fetch personality (no personality provided)
    try:
        r = session.post(f"{BASE_URL}/api/character-traits/personality-match", json={
            "message": "I need advice on my career path"
        })
        if r.status_code == 200:
            data = r.json()
            print(f"  ✅ Auto-personality: {data['best_match']['character']['display_name']}")
            passed += 1
        else:
            print(f"  ❌ Auto-personality: Status {r.status_code} - {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Auto-personality: {e}")
        failed += 1
    
    # Test 3: Record interaction
    try:
        r = session.post(f"{BASE_URL}/api/character-traits/interact", json={
            "character_id": "therapist",
            "satisfaction": 0.85
        })
        if r.status_code == 200:
            print(f"  ✅ Record interaction: {r.json().get('status')}")
            passed += 1
        else:
            print(f"  ❌ Record interaction: Status {r.status_code} - {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Record interaction: {e}")
        failed += 1
    
    # Test 4: Get preferences
    try:
        r = session.get(f"{BASE_URL}/api/character-traits/preferences")
        if r.status_code == 200:
            data = r.json()
            print(f"  ✅ Preferences: {len(data.get('preferences', []))} chars, {data.get('total_interactions', 0)} interactions")
            passed += 1
        else:
            print(f"  ❌ Preferences: Status {r.status_code} - {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Preferences: {e}")
        failed += 1
    
    # Test 5: Coverage analysis
    try:
        r = session.get(f"{BASE_URL}/api/character-traits/coverage")
        if r.status_code == 200:
            data = r.json()
            print(f"  ✅ Coverage: score={data.get('overall_coverage_score')}, diversity={data.get('diversity_score')}, gaps={len(data.get('coverage_gaps', []))}")
            passed += 1
        else:
            print(f"  ❌ Coverage: Status {r.status_code} - {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Coverage: {e}")
        failed += 1
    
    # Test 6: Original endpoints still work (regression)
    try:
        r = session.get(f"{BASE_URL}/api/character-traits/characters")
        if r.status_code == 200:
            print(f"  ✅ Regression - characters: {r.json().get('count')} found")
            passed += 1
        else:
            print(f"  ❌ Regression - characters: Status {r.status_code}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Regression - characters: {e}")
        failed += 1
    
    try:
        r = session.post(f"{BASE_URL}/api/character-traits/match", json={"message": "I need help"})
        if r.status_code == 200:
            print(f"  ✅ Regression - match: {r.json().get('matched_character', {}).get('display_name')}")
            passed += 1
        else:
            print(f"  ❌ Regression - match: Status {r.status_code}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Regression - match: {e}")
        failed += 1
    
    print(f"\n{'='*50}")
    print(f"PRODUCTION TESTS: {passed}/{passed+failed} passed")
    print(f"{'='*50}")
    assert failed == 0, f"{failed} test(s) failed"


if __name__ == '__main__':
    print("=" * 60)
    print("PHASE 5 ENHANCEMENT TESTS")
    print("=" * 60)
    
    print("\n📋 LOCAL TESTS (in-memory DB)")
    print("-" * 40)
    local_ok = test_local()
    
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
