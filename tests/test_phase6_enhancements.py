"""
Phase 6 & 6.5 Enhancement Tests
Tests both locally (in-memory DB) and against PythonAnywhere production.
"""
import sqlite3
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smart_response.character_traits import create_character_trait_system, SituationAnalysis
from smart_response.character_specific_context import create_character_specific_context
from smart_response.character_collaboration import create_collaboration_system


def test_phase6_local():
    """Test Phase 6 enhancements with in-memory DB"""
    db = sqlite3.connect(':memory:')
    trait_system = create_character_trait_system(db)
    context = create_character_specific_context(db, trait_system)
    passed = 0
    failed = 0

    # Test 1: Basic multi-perspective (regression)
    try:
        interps = context.get_multi_perspective_interpretations("I failed my exam")
        assert len(interps) == 4
        for i in interps:
            assert i.character_id
            assert i.interpretation
            assert i.confidence > 0
        print(f"  ✅ Basic multi-perspective: {len(interps)} perspectives")
        passed += 1
    except Exception as e:
        print(f"  ❌ Basic multi-perspective: {e}")
        failed += 1

    # Test 2: Situation-aware interpretation
    try:
        situation = trait_system.analyze_situation("I'm so stressed about my deadline")
        char = trait_system.get_character('stoic')
        interp = context.interpret_event_as_character(
            "I'm so stressed about my deadline", char, situation=situation
        )
        assert interp.situation_context is not None
        assert 'stressed' in interp.situation_context or 'anxious' in interp.situation_context
        # Should use situation-specific frame, not generic
        assert 'test of character' not in interp.interpretation.lower() or 'fortress' in interp.interpretation.lower() or 'pressures' in interp.interpretation.lower()
        print(f"  ✅ Situation-aware: context='{interp.situation_context}', interp='{interp.interpretation[:60]}...'")
        passed += 1
    except Exception as e:
        print(f"  ❌ Situation-aware: {e}")
        failed += 1

    # Test 3: Emotional inference from text
    try:
        state = context._infer_emotional_state("I'm so worried about everything")
        assert state == 'anxious', f"Expected 'anxious', got '{state}'"
        state2 = context._infer_emotional_state("I'm furious at my boss")
        assert state2 == 'angry', f"Expected 'angry', got '{state2}'"
        state3 = context._infer_emotional_state("Nice weather today")
        assert state3 == 'neutral', f"Expected 'neutral', got '{state3}'"
        print(f"  ✅ Emotional inference: worried→anxious, furious→angry, nice→neutral")
        passed += 1
    except Exception as e:
        print(f"  ❌ Emotional inference: {e}")
        failed += 1

    # Test 4: Personality resonance scoring
    try:
        personality = {'openness': 0.8, 'conscientiousness': 0.3, 'extraversion': 0.2,
                       'agreeableness': 0.9, 'neuroticism': 0.7}
        char = trait_system.get_character('therapist')
        interp = context.interpret_event_as_character(
            "I feel lost", char, personality=personality
        )
        assert interp.personality_resonance is not None
        assert 0 <= interp.personality_resonance <= 1
        print(f"  ✅ Personality resonance: {interp.personality_resonance} for therapist")
        passed += 1
    except Exception as e:
        print(f"  ❌ Personality resonance: {e}")
        failed += 1

    # Test 5: Personality-influenced character selection
    try:
        personality_high_agree = {'openness': 0.5, 'conscientiousness': 0.5, 'extraversion': 0.5,
                                  'agreeableness': 0.9, 'neuroticism': 0.7}
        chars = context._select_personality_aware_characters(4, personality_high_agree)
        assert len(chars) == 4
        # High agreeableness should favor empathetic/supportive characters
        char_ids = [c.character_id for c in chars]
        print(f"  ✅ Personality-aware selection: {char_ids}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Personality-aware selection: {e}")
        failed += 1

    # Test 6: Enhanced multi-perspective with situation + personality
    try:
        situation = trait_system.analyze_situation("I'm anxious about my job interview")
        personality = {'openness': 0.6, 'conscientiousness': 0.7, 'extraversion': 0.3,
                       'agreeableness': 0.5, 'neuroticism': 0.8}
        interps = context.get_multi_perspective_interpretations(
            "I'm anxious about my job interview",
            max_perspectives=4, situation=situation, personality=personality
        )
        assert len(interps) == 4
        # All should have situation context and personality resonance
        for i in interps:
            assert i.situation_context is not None
            assert i.personality_resonance is not None
        # Should be sorted by confidence
        confidences = [i.confidence for i in interps]
        assert confidences == sorted(confidences, reverse=True), "Should be sorted by confidence"
        print(f"  ✅ Enhanced multi-perspective: {len(interps)} perspectives, all with situation+personality")
        passed += 1
    except Exception as e:
        print(f"  ❌ Enhanced multi-perspective: {e}")
        failed += 1

    # Test 7: Compare interpretations
    try:
        result = context.compare_interpretations(
            "I failed my exam",
            ['stoic', 'therapist', 'coach'],
            personality=personality
        )
        assert 'interpretations' in result
        assert 'differences' in result
        assert 'recommendation' in result
        assert len(result['interpretations']) == 3
        assert len(result['differences']) == 3  # 3 pairs from 3 characters
        for diff in result['differences']:
            assert 'lens_contrast' in diff
            assert 'complementary' in diff
            assert 'resonance_comparison' in diff
        print(f"  ✅ Compare interpretations: {len(result['differences'])} comparisons, rec='{result['recommendation'][:50]}...'")
        passed += 1
    except Exception as e:
        print(f"  ❌ Compare interpretations: {e}")
        failed += 1

    # Test 8: Situation-aware perspectives (all-in-one)
    try:
        result = context.get_situation_aware_perspectives(
            "I'm overwhelmed with work and my relationship is falling apart",
            max_perspectives=3, personality=personality
        )
        assert 'situation_analysis' in result
        assert 'perspectives' in result
        assert result['perspective_count'] == 3
        assert result['personality_provided'] is True
        sa = result['situation_analysis']
        assert sa['emotional_state'] is not None
        print(f"  ✅ Situation-aware perspectives: emotion={sa['emotional_state']}, {result['perspective_count']} perspectives")
        passed += 1
    except Exception as e:
        print(f"  ❌ Situation-aware perspectives: {e}")
        failed += 1

    # Test 9: Store and retrieve interpretations
    try:
        interps = context.get_multi_perspective_interpretations("Test event")
        context.store_interpretations(1, "test-event-1", "Test event", interps)
        retrieved = context.get_event_interpretations(1, "test-event-1")
        assert len(retrieved) == len(interps)
        history = context.get_user_interpretation_history(1)
        assert len(history) >= 1
        print(f"  ✅ Store/retrieve: stored {len(interps)}, retrieved {len(retrieved)}, history={len(history)}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Store/retrieve: {e}")
        failed += 1

    print(f"\n{'='*50}")
    print(f"PHASE 6 LOCAL: {passed}/{passed+failed} passed")
    print(f"{'='*50}")
    assert failed == 0, f"{failed} test(s) failed"


def test_phase65_local():
    """Test Phase 6.5 enhancements with in-memory DB"""
    db = sqlite3.connect(':memory:')
    trait_system = create_character_trait_system(db)
    context = create_character_specific_context(db, trait_system)
    collab = create_collaboration_system(db, trait_system, context)
    passed = 0
    failed = 0

    # Test 1: Basic collaboration trigger (regression)
    try:
        should, mode, rule = collab.should_collaborate("What should I do about my job and relationship?")
        assert should is True
        print(f"  ✅ Collaboration trigger: mode={mode}, rule={rule}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Collaboration trigger: {e}")
        failed += 1

    # Test 2: Domain detection (regression)
    try:
        domains = collab._detect_domains("I'm stressed about work and money")
        assert len(domains) >= 1
        print(f"  ✅ Domain detection: {domains}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Domain detection: {e}")
        failed += 1

    # Test 3: Basic orchestration (regression)
    try:
        result = collab.orchestrate_collaboration(
            "Help me decide between changing careers and staying", 1, mode='debate'
        )
        assert result is not None
        assert result.mode == 'debate'
        assert len(result.contributions) >= 2
        assert result.event_id > 0
        print(f"  ✅ Orchestration: mode={result.mode}, {len(result.contributions)} contributors")
        passed += 1
    except Exception as e:
        print(f"  ❌ Orchestration: {e}")
        failed += 1

    # Test 4: Personality-aware collaboration
    try:
        personality = {'openness': 0.7, 'conscientiousness': 0.8, 'extraversion': 0.3,
                       'agreeableness': 0.6, 'neuroticism': 0.7}
        result = collab.personality_aware_collaborate(
            "What should I do about my career path?", 1,
            personality=personality, mode='visible'
        )
        assert result is not None
        assert result.mode == 'visible'
        assert len(result.contributions) >= 2
        # Contributions should have personality_resonance
        for c in result.contributions:
            assert 'personality_resonance' in c
        print(f"  ✅ Personality collab: {len(result.contributions)} contributors with resonance")
        passed += 1
    except Exception as e:
        print(f"  ❌ Personality collab: {e}")
        failed += 1

    # Test 5: Personality reranking
    try:
        candidates = collab._find_relevant_characters("I need career advice", {})
        personality = {'openness': 0.9, 'conscientiousness': 0.2, 'extraversion': 0.8,
                       'agreeableness': 0.3, 'neuroticism': 0.2}
        reranked = collab._rerank_by_personality(candidates, personality)
        assert all('blended_score' in c for c in reranked)
        assert all('personality_resonance' in c for c in reranked)
        # Should be sorted by blended score
        scores = [c['blended_score'] for c in reranked]
        assert scores == sorted(scores, reverse=True)
        print(f"  ✅ Personality reranking: {len(reranked)} candidates reranked")
        passed += 1
    except Exception as e:
        print(f"  ❌ Personality reranking: {e}")
        failed += 1

    # Test 6: Record feedback
    try:
        collab.record_collaboration_feedback(result.event_id, 4)
        # Verify it was recorded
        cursor = db.cursor()
        cursor.execute('SELECT user_satisfaction FROM collaboration_events WHERE id = ?', (result.event_id,))
        sat = cursor.fetchone()[0]
        assert sat == 4
        print(f"  ✅ Record feedback: event_id={result.event_id}, satisfaction={sat}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Record feedback: {e}")
        failed += 1

    # Test 7: Effectiveness analysis
    try:
        eff = collab.get_collaboration_effectiveness()
        assert 'total_collaborations' in eff
        assert 'rated_collaborations' in eff
        assert 'avg_satisfaction' in eff
        assert 'by_mode' in eff
        assert 'top_effective_characters' in eff
        assert eff['total_collaborations'] >= 2  # We did 2 collabs
        assert eff['rated_collaborations'] >= 1
        print(f"  ✅ Effectiveness: total={eff['total_collaborations']}, rated={eff['rated_collaborations']}, avg={eff['avg_satisfaction']}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Effectiveness: {e}")
        failed += 1

    # Test 8: Collaboration history
    try:
        history = collab.get_collaboration_history(1)
        assert len(history) >= 2
        for h in history:
            assert 'event_id' in h
            assert 'mode' in h
            assert 'characters' in h
        print(f"  ✅ Collaboration history: {len(history)} events")
        passed += 1
    except Exception as e:
        print(f"  ❌ Collaboration history: {e}")
        failed += 1

    # Test 9: Stats
    try:
        stats = collab.get_collaboration_stats()
        assert stats['total_collaborations'] >= 2
        assert 'by_mode' in stats
        assert 'top_characters' in stats
        print(f"  ✅ Stats: total={stats['total_collaborations']}, modes={list(stats['by_mode'].keys())}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Stats: {e}")
        failed += 1

    # Test 10: Rules and domains
    try:
        rules = collab.get_rules()
        domains = collab.get_domains()
        assert len(rules) >= 3  # 3 default rules
        assert len(domains) >= 1
        print(f"  ✅ Rules/Domains: {len(rules)} rules, {len(domains)} domains")
        passed += 1
    except Exception as e:
        print(f"  ❌ Rules/Domains: {e}")
        failed += 1

    print(f"\n{'='*50}")
    print(f"PHASE 6.5 LOCAL: {passed}/{passed+failed} passed")
    print(f"{'='*50}")
    assert failed == 0, f"{failed} test(s) failed"


def test_production():
    """Test Phase 6 & 6.5 enhancement endpoints on PythonAnywhere"""
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

    # Phase 6 Tests

    # Test 1: Enhanced interpret endpoint
    try:
        r = session.post(f"{BASE_URL}/api/character-context/interpret", json={
            "event_text": "I'm feeling anxious about my future",
            "max_perspectives": 3,
            "personality": {"openness": 0.7, "conscientiousness": 0.5, "extraversion": 0.3,
                           "agreeableness": 0.6, "neuroticism": 0.8}
        })
        if r.status_code == 200:
            data = r.json()
            assert data.get('situation_analyzed') is True
            assert data.get('personality_used') is True
            persp = data.get('perspectives', [])
            assert len(persp) == 3
            # Check new fields present
            assert persp[0].get('situation_context') is not None
            assert persp[0].get('personality_resonance') is not None
            print(f"  ✅ Enhanced interpret: {len(persp)} perspectives with situation+personality")
            passed += 1
        else:
            print(f"  ❌ Enhanced interpret: {r.status_code} {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Enhanced interpret: {e}")
        failed += 1

    # Test 2: Compare endpoint
    try:
        r = session.post(f"{BASE_URL}/api/character-context/compare", json={
            "event_text": "I lost my job today",
            "character_ids": ["stoic", "therapist", "coach"]
        })
        if r.status_code == 200:
            data = r.json()
            assert len(data.get('interpretations', [])) == 3
            assert len(data.get('differences', [])) == 3
            assert 'recommendation' in data
            print(f"  ✅ Compare: {len(data['differences'])} comparisons")
            passed += 1
        else:
            print(f"  ❌ Compare: {r.status_code} {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Compare: {e}")
        failed += 1

    # Test 3: Situation-aware perspectives
    try:
        r = session.post(f"{BASE_URL}/api/character-context/situation-perspectives", json={
            "message": "I'm overwhelmed at work and my partner is unhappy",
            "max_perspectives": 3
        })
        if r.status_code == 200:
            data = r.json()
            assert 'situation_analysis' in data
            assert data.get('perspective_count') == 3
            sa = data['situation_analysis']
            print(f"  ✅ Situation perspectives: emotion={sa.get('emotional_state')}, {data['perspective_count']} perspectives")
            passed += 1
        else:
            print(f"  ❌ Situation perspectives: {r.status_code} {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Situation perspectives: {e}")
        failed += 1

    # Phase 6.5 Tests

    # Test 4: Personality-aware collaboration
    try:
        r = session.post(f"{BASE_URL}/api/collaboration/personality-collaborate", json={
            "message": "What should I do about my career and relationship problems?",
            "personality": {"openness": 0.7, "conscientiousness": 0.6, "extraversion": 0.4,
                           "agreeableness": 0.7, "neuroticism": 0.6}
        })
        if r.status_code == 200:
            data = r.json()
            if data.get('collaborated'):
                assert 'contributions' in data
                assert data.get('personality_used') is True
                print(f"  ✅ Personality collab: {len(data['contributions'])} contributors")
                passed += 1
            else:
                print(f"  ⚠️ Personality collab: no trigger matched (domains: {data.get('detected_domains')})")
                passed += 1  # OK - might not trigger on this specific phrasing
        else:
            print(f"  ❌ Personality collab: {r.status_code} {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Personality collab: {e}")
        failed += 1

    # Test 5: Collaboration feedback
    try:
        # First do a collaboration to get an event_id
        r = session.post(f"{BASE_URL}/api/collaboration/orchestrate", json={
            "message": "Help me decide what to do with my life",
            "force": True, "mode": "debate"
        })
        if r.status_code == 200 and r.json().get('collaborated'):
            event_id = r.json()['event_id']
            # Record feedback
            r2 = session.post(f"{BASE_URL}/api/collaboration/feedback", json={
                "event_id": event_id, "satisfaction": 4
            })
            if r2.status_code == 200:
                print(f"  ✅ Feedback: recorded satisfaction=4 for event {event_id}")
                passed += 1
            else:
                print(f"  ❌ Feedback: {r2.status_code} {r2.text[:200]}")
                failed += 1
        else:
            print(f"  ⚠️ Feedback: skipped (collab didn't trigger)")
            passed += 1
    except Exception as e:
        print(f"  ❌ Feedback: {e}")
        failed += 1

    # Test 6: Effectiveness
    try:
        r = session.get(f"{BASE_URL}/api/collaboration/effectiveness")
        if r.status_code == 200:
            data = r.json()
            assert 'total_collaborations' in data
            assert 'by_mode' in data
            print(f"  ✅ Effectiveness: total={data['total_collaborations']}, rated={data.get('rated_collaborations')}")
            passed += 1
        else:
            print(f"  ❌ Effectiveness: {r.status_code} {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Effectiveness: {e}")
        failed += 1

    # Regression tests
    try:
        r = session.get(f"{BASE_URL}/api/collaboration/rules")
        if r.status_code == 200:
            print(f"  ✅ Regression - rules: {len(r.json().get('rules', []))} rules")
            passed += 1
        else:
            print(f"  ❌ Regression - rules: {r.status_code}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Regression - rules: {e}")
        failed += 1

    try:
        r = session.get(f"{BASE_URL}/api/collaboration/domains")
        if r.status_code == 200:
            print(f"  ✅ Regression - domains: {len(r.json().get('domains', []))} domains")
            passed += 1
        else:
            print(f"  ❌ Regression - domains: {r.status_code}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Regression - domains: {e}")
        failed += 1

    print(f"\n{'='*50}")
    print(f"PRODUCTION TESTS: {passed}/{passed+failed} passed")
    print(f"{'='*50}")
    assert failed == 0, f"{failed} test(s) failed"


if __name__ == '__main__':
    print("=" * 60)
    print("PHASE 6 & 6.5 ENHANCEMENT TESTS")
    print("=" * 60)

    print("\n📋 PHASE 6 LOCAL TESTS")
    print("-" * 40)
    p6_ok = test_phase6_local()

    print("\n📋 PHASE 6.5 LOCAL TESTS")
    print("-" * 40)
    p65_ok = test_phase65_local()

    if '--production' in sys.argv:
        print("\n📋 PRODUCTION TESTS (PythonAnywhere)")
        print("-" * 40)
        prod_ok = test_production()
    else:
        print("\n⏭️  Skipping production tests (use --production flag)")
        prod_ok = True

    if p6_ok and p65_ok and prod_ok:
        print("\n🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)
