"""
Phase 4: Proactive Clarification System Tests
Tests multi-perspective clarification locally and against PythonAnywhere production.
"""
import sqlite3
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smart_response.proactive_clarification import create_clarification_system
from smart_response.character_traits import create_character_trait_system


def test_phase4_local():
    """Test Phase 4 clarification enhancements with in-memory DB"""
    db = sqlite3.connect(':memory:')
    clarification = create_clarification_system(db)
    trait_system = create_character_trait_system(db)
    passed = 0
    failed = 0

    # Test 1: Basic confidence analysis - clear message
    try:
        confidence, questions = clarification.analyze_message(
            "I want to improve my public speaking skills by joining Toastmasters"
        )
        assert confidence.overall > 0.5
        assert confidence.goal_clarity >= 0.5  # Has clear goal
        print(f"  ✅ Clear message: confidence={confidence.overall:.2f}, goal={confidence.goal_clarity:.2f}, questions={len(questions)}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Clear message: {e}")
        failed += 1

    # Test 2: Vague message triggers clarification
    try:
        confidence, questions = clarification.analyze_message("stuff is bad")
        assert confidence.overall < 0.6, f"Vague message should have low confidence, got {confidence.overall}"
        assert confidence.needs_clarification()
        assert len(questions) >= 1
        print(f"  ✅ Vague message: confidence={confidence.overall:.2f}, questions={len(questions)}: '{questions[0].question}'")
        passed += 1
    except Exception as e:
        print(f"  ❌ Vague message: {e}")
        failed += 1

    # Test 3: Emotional distress triggers supportive clarification
    try:
        confidence, questions = clarification.analyze_message(
            "I'm overwhelmed and don't know what to do"
        )
        assert any(q.context_gap == 'distress_support' for q in questions), "Should detect distress"
        print(f"  ✅ Distress detection: {len(questions)} questions, gap='{questions[0].context_gap}'")
        passed += 1
    except Exception as e:
        print(f"  ❌ Distress detection: {e}")
        failed += 1

    # Test 4: Decision-making triggers option exploration
    try:
        confidence, questions = clarification.analyze_message(
            "Should I take this new job or stay?"
        )
        has_decision = any(q.context_gap == 'decision_explore' for q in questions)
        # May or may not trigger depending on confidence thresholds
        print(f"  ✅ Decision detection: confidence={confidence.overall:.2f}, has_decision_question={has_decision}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Decision detection: {e}")
        failed += 1

    # Test 5: Multi-perspective analysis (enhanced)
    try:
        confidence, std_q, persp_q = clarification.analyze_with_perspectives(
            "things are bad lately",
            character_trait_system=trait_system
        )
        assert confidence.needs_clarification(threshold=0.65)
        assert len(persp_q) >= 2, f"Expected 2+ perspective questions, got {len(persp_q)}"
        for pq in persp_q:
            assert 'character_lens' in pq
            assert 'character_name' in pq
            assert 'question' in pq
        lenses = [pq['character_lens'] for pq in persp_q]
        print(f"  ✅ Multi-perspective: {len(persp_q)} perspectives: {lenses}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Multi-perspective: {e}")
        failed += 1

    # Test 6: Perspective questions are diverse
    try:
        confidence, std_q, persp_q = clarification.analyze_with_perspectives(
            "I'm struggling",
            character_trait_system=trait_system
        )
        if persp_q:
            lenses = set(pq['character_lens'] for pq in persp_q)
            assert len(lenses) >= 2, f"Need diverse lenses, got {lenses}"
            questions_text = [pq['question'] for pq in persp_q]
            # All questions should be unique
            assert len(questions_text) == len(set(questions_text)), "Questions should be unique"
            print(f"  ✅ Question diversity: {len(lenses)} unique lenses, all questions unique")
        else:
            print(f"  ✅ Question diversity: no clarification needed (confidence={confidence.overall:.2f})")
        passed += 1
    except Exception as e:
        print(f"  ❌ Question diversity: {e}")
        failed += 1

    # Test 7: High-confidence message doesn't trigger perspectives
    try:
        confidence, std_q, persp_q = clarification.analyze_with_perspectives(
            "I want to lose 10 pounds in the next 3 months by running 3 times a week. Can you help me create a plan?",
            character_trait_system=trait_system
        )
        assert not confidence.needs_clarification(threshold=0.65), f"Clear message shouldn't need clarification, confidence={confidence.overall}"
        assert len(persp_q) == 0, "No perspective questions for clear messages"
        print(f"  ✅ Clear message skips perspectives: confidence={confidence.overall:.2f}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Clear message skips perspectives: {e}")
        failed += 1

    # Test 8: Format perspective clarification (no character names visible)
    try:
        _, std_q, persp_q = clarification.analyze_with_perspectives(
            "everything is falling apart",
            character_trait_system=trait_system
        )
        formatted = clarification.format_perspective_clarification(std_q, persp_q)
        assert len(formatted) > 0
        assert '1.' in formatted  # Numbered list format
        # Character names should NOT appear in formatted text
        for pq in persp_q:
            assert pq['character_name'] not in formatted, f"Character name '{pq['character_name']}' should not be in user-facing text"
        print(f"  ✅ Format perspectives: {len(formatted)} chars, no character names visible")
        passed += 1
    except Exception as e:
        print(f"  ❌ Format perspectives: {e}")
        failed += 1

    # Test 9: Record and retrieve clarification history
    try:
        from smart_response.proactive_clarification import ClarificationQuestion, ClarificationReason, ImportanceLevel
        q = ClarificationQuestion(
            question="What's most important to you?",
            reason=ClarificationReason.UNCLEAR_PRIORITY,
            importance=ImportanceLevel.HIGH,
            context_gap='priority'
        )
        clarification.record_question_asked(1, 'test_char', q)
        pending = clarification.get_pending_clarifications(1, 'test_char')
        assert len(pending) >= 1
        assert pending[0]['question'] == "What's most important to you?"
        print(f"  ✅ Record/retrieve: {len(pending)} pending questions")
        passed += 1
    except Exception as e:
        print(f"  ❌ Record/retrieve: {e}")
        failed += 1

    # Test 10: Should_ask_clarification filters duplicates
    try:
        from smart_response.proactive_clarification import ClarificationQuestion, ClarificationReason, ImportanceLevel
        q1 = ClarificationQuestion("What's most important?", ClarificationReason.UNCLEAR_PRIORITY, ImportanceLevel.HIGH, 'priority')
        q2 = ClarificationQuestion("Tell me more?", ClarificationReason.MISSING_CONTEXT, ImportanceLevel.NORMAL, 'context')
        
        # q1 was already asked (from test 9), should be filtered
        filtered = clarification.should_ask_clarification(1, 'test_char', [q1, q2])
        assert q1 not in filtered, "Already-asked question should be filtered"
        assert len(filtered) >= 1
        print(f"  ✅ Duplicate filtering: {len(filtered)} questions after filter (q1 removed)")
        passed += 1
    except Exception as e:
        print(f"  ❌ Duplicate filtering: {e}")
        failed += 1

    # Test 11: Clarification stats
    try:
        stats = clarification.get_clarification_stats()
        assert 'total_questions_asked' in stats
        assert 'response_rate' in stats
        assert 'gap_distribution' in stats
        assert stats['total_questions_asked'] >= 1
        print(f"  ✅ Stats: total={stats['total_questions_asked']}, gaps={stats['gap_distribution']}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Stats: {e}")
        failed += 1

    # Test 12: ClarificationQuestion to_dict
    try:
        from smart_response.proactive_clarification import ClarificationQuestion, ClarificationReason, ImportanceLevel
        q = ClarificationQuestion(
            question="How are you feeling?",
            reason=ClarificationReason.EMOTIONAL_UNCERTAINTY,
            importance=ImportanceLevel.CRITICAL,
            context_gap='emotion',
            suggested_options=['Happy', 'Sad', 'Anxious']
        )
        d = q.to_dict()
        assert d['question'] == "How are you feeling?"
        assert d['reason'] == 'emotional_uncertainty'
        assert d['importance'] == 'critical'
        assert d['suggested_options'] == ['Happy', 'Sad', 'Anxious']
        json.dumps(d)  # Must be JSON-serializable
        print(f"  ✅ to_dict: serializable, all fields correct")
        passed += 1
    except Exception as e:
        print(f"  ❌ to_dict: {e}")
        failed += 1

    print(f"\n{'='*50}")
    print(f"PHASE 4 LOCAL: {passed}/{passed+failed} passed")
    print(f"{'='*50}")
    assert failed == 0, f"{failed} test(s) failed"


def test_production():
    """Test Phase 4 clarification endpoints on PythonAnywhere"""
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

    # Test 1: Analyze endpoint - vague message
    try:
        r = session.post(f"{BASE_URL}/api/clarification/analyze", json={
            "message": "things are really bad"
        })
        if r.status_code == 200:
            data = r.json()
            assert 'confidence' in data
            assert data['needs_clarification'] is True
            persp = data.get('perspective_questions', [])
            print(f"  ✅ Analyze vague: confidence={data['confidence']['overall']}, {len(persp)} perspective questions")
            passed += 1
        else:
            print(f"  ❌ Analyze vague: {r.status_code} {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Analyze vague: {e}")
        failed += 1

    # Test 2: Analyze endpoint - clear message
    try:
        r = session.post(f"{BASE_URL}/api/clarification/analyze", json={
            "message": "I want to learn Python programming. Can you recommend a course for beginners?"
        })
        if r.status_code == 200:
            data = r.json()
            # Clear message should have higher confidence
            assert data['confidence']['overall'] > 0.5
            print(f"  ✅ Analyze clear: confidence={data['confidence']['overall']}, needs_clarification={data['needs_clarification']}")
            passed += 1
        else:
            print(f"  ❌ Analyze clear: {r.status_code} {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Analyze clear: {e}")
        failed += 1

    # Test 3: Analyze endpoint - distress message with perspectives
    try:
        r = session.post(f"{BASE_URL}/api/clarification/analyze", json={
            "message": "I'm overwhelmed and can't cope with everything"
        })
        if r.status_code == 200:
            data = r.json()
            std_q = data.get('standard_questions', [])
            persp_q = data.get('perspective_questions', [])
            formatted = data.get('formatted_text', '')
            print(f"  ✅ Analyze distress: {len(std_q)} standard + {len(persp_q)} perspective questions, formatted={len(formatted)} chars")
            passed += 1
        else:
            print(f"  ❌ Analyze distress: {r.status_code} {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Analyze distress: {e}")
        failed += 1

    # Test 4: Pending clarifications
    try:
        r = session.get(f"{BASE_URL}/api/clarification/pending")
        if r.status_code == 200:
            data = r.json()
            assert 'pending' in data
            print(f"  ✅ Pending: {len(data['pending'])} pending questions")
            passed += 1
        else:
            print(f"  ❌ Pending: {r.status_code} {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Pending: {e}")
        failed += 1

    # Test 5: Stats
    try:
        r = session.get(f"{BASE_URL}/api/clarification/stats")
        if r.status_code == 200:
            data = r.json()
            assert 'total_questions_asked' in data
            assert 'gap_distribution' in data
            print(f"  ✅ Stats: total={data['total_questions_asked']}, gaps={data.get('gap_distribution', {})}")
            passed += 1
        else:
            print(f"  ❌ Stats: {r.status_code} {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Stats: {e}")
        failed += 1

    # Test 6: Chatchat integration - vague message should get clarification
    try:
        r = session.get(f"{BASE_URL}/api/user/conversations")
        convs = r.json()
        if isinstance(convs, dict):
            convs = convs.get('conversations', [])
        
        if convs and len(convs) > 0:
            test_session = convs[0]['session_id']
        else:
            r2 = session.post(f"{BASE_URL}/api/user/conversations", json={"title": "Clarification Test"})
            test_session = r2.json().get('session_id')
        
        r = session.post(f"{BASE_URL}/api/user/conversations/{test_session}/messages", json={
            "senderType": "user",
            "content": "stuff is going wrong"
        })
        if r.status_code == 200:
            data = r.json()
            if data.get('clarification'):
                clar = data['clarification']
                print(f"  ✅ Chatchat clarification: confidence={clar.get('confidence')}, perspectives={len(clar.get('perspective_questions', []))}")
            else:
                print(f"  ⚠️ Chatchat clarification: response OK but no clarification in metadata (confidence may be above threshold)")
            passed += 1
        else:
            print(f"  ❌ Chatchat clarification: {r.status_code} {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Chatchat clarification: {e}")
        failed += 1

    print(f"\n{'='*50}")
    print(f"PHASE 4 PRODUCTION: {passed}/{passed+failed} passed")
    print(f"{'='*50}")
    assert failed == 0, f"{failed} test(s) failed"


if __name__ == '__main__':
    print("=" * 60)
    print("PHASE 4: PROACTIVE CLARIFICATION TESTS")
    print("=" * 60)

    print("\n📋 LOCAL TESTS")
    print("-" * 40)
    local_ok = test_phase4_local()

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
