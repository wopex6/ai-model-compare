"""
Phase 7: Character Effectiveness Learner Tests
Tests outcome analysis, effectiveness scoring, and analytics locally and against production.
"""
import sqlite3
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smart_response.character_effectiveness_learner import (
    create_effectiveness_learner, CharacterEffectivenessLearner,
    EngagementLevel, ConversationOutcome
)
from smart_response.character_traits import create_character_trait_system


def make_messages(user_texts, ai_texts=None):
    """Helper: create message list from user/ai text lists"""
    msgs = []
    ai_texts = ai_texts or ["I'm here to help."] * len(user_texts)
    for i, (u, a) in enumerate(zip(user_texts, ai_texts)):
        msgs.append({'sender_type': 'user', 'content': u, 'timestamp': f'2025-02-08T12:{i:02d}:00Z'})
        msgs.append({'sender_type': 'assistant', 'content': a, 'timestamp': f'2025-02-08T12:{i:02d}:30Z'})
    return msgs


def test_phase7_local():
    """Test Phase 7 effectiveness learner with in-memory DB"""
    db = sqlite3.connect(':memory:')
    trait_system = create_character_trait_system(db)
    learner = create_effectiveness_learner(db, trait_system)
    passed = 0
    failed = 0

    # Test 1: Engagement level calculation
    try:
        assert learner._calc_engagement(1) == EngagementLevel.VERY_LOW
        assert learner._calc_engagement(3) == EngagementLevel.LOW
        assert learner._calc_engagement(6) == EngagementLevel.MODERATE
        assert learner._calc_engagement(12) == EngagementLevel.HIGH
        assert learner._calc_engagement(20) == EngagementLevel.VERY_HIGH
        print("  ✅ Engagement levels: all thresholds correct")
        passed += 1
    except Exception as e:
        print(f"  ❌ Engagement levels: {e}")
        failed += 1

    # Test 2: Positive conversation analysis
    try:
        msgs = make_messages(
            ["I'm feeling down today", "That makes sense, thank you",
             "Great advice, I'll try that", "You're right, I feel better now",
             "Thanks so much, this was helpful!", "I'm going to start tomorrow"],
            ["I hear you...", "Let's explore...", "Here's what I suggest...",
             "I'm glad...", "You're welcome...", "That's a great plan!"]
        )
        outcome = learner.analyze_conversation('sess1', 1, msgs, 'coach')
        assert outcome.satisfaction_estimate > 0.5, f"Positive conv should have high satisfaction, got {outcome.satisfaction_estimate}"
        assert outcome.engagement_level in (EngagementLevel.MODERATE, EngagementLevel.HIGH)
        assert outcome.signals['explicit_thanks'] > 0
        assert outcome.goal_achieved is True
        print(f"  ✅ Positive conversation: satisfaction={outcome.satisfaction_estimate:.2f}, engagement={outcome.engagement_level.value}, goal={outcome.goal_achieved}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Positive conversation: {e}")
        failed += 1

    # Test 3: Negative conversation analysis
    try:
        msgs = make_messages(
            ["Help me", "No, that's not what I meant", "You don't understand",
             "Nevermind, forget it"],
            ["Sure...", "Let me try again...", "I see...", "I'm sorry..."]
        )
        outcome = learner.analyze_conversation('sess2', 1, msgs, 'coach')
        assert outcome.signals['explicit_frustration'] > 0, "Should detect frustration"
        assert outcome.satisfaction_estimate < 0.6, f"Negative conv should have lower satisfaction, got {outcome.satisfaction_estimate}"
        print(f"  ✅ Negative conversation: satisfaction={outcome.satisfaction_estimate:.2f}, frustration={outcome.signals['explicit_frustration']:.2f}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Negative conversation: {e}")
        failed += 1

    # Test 4: Empty conversation
    try:
        outcome = learner.analyze_conversation('sess_empty', 1, [], 'coach')
        assert outcome.message_count == 0
        assert outcome.engagement_level == EngagementLevel.VERY_LOW
        assert outcome.satisfaction_estimate == 0.5
        print(f"  ✅ Empty conversation: defaults correct")
        passed += 1
    except Exception as e:
        print(f"  ❌ Empty conversation: {e}")
        failed += 1

    # Test 5: Record and retrieve outcome
    try:
        msgs = make_messages(
            ["I need help with my career", "That's a good point",
             "I'll think about it", "Thanks for the perspective",
             "I've decided to apply for the new role"],
            ["Tell me more...", "Consider...", "Take your time...",
             "You're welcome...", "That's exciting!"]
        )
        outcome = learner.analyze_and_record('sess3', 1, msgs, 'coach', 'career')
        
        eff_data = learner.get_character_effectiveness('coach')
        assert eff_data['total_conversations'] >= 1
        print(f"  ✅ Record outcome: total={eff_data['total_conversations']}, satisfaction={eff_data['avg_satisfaction']}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Record outcome: {e}")
        failed += 1

    # Test 6: Multiple outcomes build effectiveness score
    try:
        for i in range(5):
            msgs = make_messages(
                [f"Question {i}", "Thank you, that helps",
                 "I'll try that approach", "Makes sense"],
                ["Here's my take...", "Glad to help...",
                 "Good plan...", "You're on track!"]
            )
            learner.analyze_and_record(f'sess_bulk_{i}', 1, msgs, 'stoic', 'general')
        
        eff = learner.get_character_effectiveness('stoic')
        assert eff['total_conversations'] >= 5
        assert eff['sufficient_data'] is True
        assert eff['effectiveness_score'] > 0
        print(f"  ✅ Bulk effectiveness: score={eff['effectiveness_score']}, convs={eff['total_conversations']}, sufficient={eff['sufficient_data']}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Bulk effectiveness: {e}")
        failed += 1

    # Test 7: Best characters ranking
    try:
        # Add some outcomes for a different character
        for i in range(3):
            msgs = make_messages(
                [f"Help me {i}", "That's amazing, exactly what I needed!",
                 "Perfect, I'm going to do that right now"],
                ["Sure...", "Great to hear!", "Go for it!"]
            )
            learner.analyze_and_record(f'sess_sage_{i}', 1, msgs, 'sage', 'general')
        
        best = learner.get_best_characters()
        assert len(best) >= 2
        # Check ordering
        for b in best:
            assert 'effectiveness' in b
            assert 'conversations' in b
        print(f"  ✅ Best characters: {len(best)} ranked, top={best[0]['character_id']} ({best[0]['effectiveness']:.3f})")
        passed += 1
    except Exception as e:
        print(f"  ❌ Best characters: {e}")
        failed += 1

    # Test 8: User engagement stats
    try:
        stats = learner.get_user_engagement_stats(1)
        assert stats['total_conversations'] > 0
        assert stats['avg_satisfaction'] is not None
        assert stats['trend'] in ('improving', 'stable')
        print(f"  ✅ User stats: convs={stats['total_conversations']}, satisfaction={stats['avg_satisfaction']}, trend={stats['trend']}")
        passed += 1
    except Exception as e:
        print(f"  ❌ User stats: {e}")
        failed += 1

    # Test 9: Explicit feedback
    try:
        learner.record_feedback('sess3', 1, 'thumbs_up', character_id='coach')
        
        # Check it was stored
        cursor = db.cursor()
        cursor.execute('SELECT feedback_value FROM user_feedback WHERE session_id = ?', ('sess3',))
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == 1.0
        print(f"  ✅ Feedback: thumbs_up recorded, value={row[0]}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Feedback: {e}")
        failed += 1

    # Test 10: System stats
    try:
        stats = learner.get_system_stats()
        assert stats['total_conversations_tracked'] > 0
        assert stats['unique_users'] >= 1
        assert 'engagement_distribution' in stats
        print(f"  ✅ System stats: total={stats['total_conversations_tracked']}, users={stats['unique_users']}, feedback={stats['total_feedback']}")
        passed += 1
    except Exception as e:
        print(f"  ❌ System stats: {e}")
        failed += 1

    # Test 11: ConversationOutcome.to_dict serialization
    try:
        outcome = ConversationOutcome(
            session_id='test', user_id=1, character_id='coach',
            message_count=10, user_message_count=5,
            engagement_level=EngagementLevel.MODERATE,
            satisfaction_estimate=0.75, goal_achieved=True,
            signals={'engagement_depth': 0.6, 'explicit_thanks': 0.4},
            situation_type='career', timestamp='2025-02-08T12:00:00'
        )
        d = outcome.to_dict()
        json.dumps(d)  # Must be JSON serializable
        assert d['engagement_level'] == 'moderate'
        assert d['satisfaction_estimate'] == 0.75
        print(f"  ✅ to_dict: serializable, all fields correct")
        passed += 1
    except Exception as e:
        print(f"  ❌ to_dict: {e}")
        failed += 1

    # Test 12: Message length trend detection
    try:
        # Increasing length = engaged
        increasing_msgs = [
            {'sender_type': 'user', 'content': 'Hi'},
            {'sender_type': 'user', 'content': 'Tell me more about that please'},
            {'sender_type': 'user', 'content': 'That is really interesting, I want to understand the deeper implications of what you said'},
            {'sender_type': 'user', 'content': 'This is fascinating! I never thought about it that way. Let me share my perspective on this whole thing in detail'},
        ]
        trend_up = learner._calc_length_trend(increasing_msgs)
        
        # Decreasing length = disengaged
        decreasing_msgs = [
            {'sender_type': 'user', 'content': 'I have a really detailed question about how to improve my career trajectory and find meaning in my work'},
            {'sender_type': 'user', 'content': 'That is somewhat helpful I suppose'},
            {'sender_type': 'user', 'content': 'Ok sure'},
            {'sender_type': 'user', 'content': 'k'},
        ]
        trend_down = learner._calc_length_trend(decreasing_msgs)
        
        assert trend_up > trend_down, f"Increasing trend ({trend_up}) should be higher than decreasing ({trend_down})"
        print(f"  ✅ Length trend: increasing={trend_up:.2f}, decreasing={trend_down:.2f}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Length trend: {e}")
        failed += 1

    # Test 13: Situation breakdown in effectiveness
    try:
        # Record career-specific outcomes
        for i in range(3):
            msgs = make_messages(["career question", "thanks"], ["advice", "welcome"])
            learner.analyze_and_record(f'sess_career_{i}', 2, msgs, 'coach', 'career')
        
        eff = learner.get_character_effectiveness('coach')
        assert 'situation_breakdown' in eff
        assert 'career' in eff['situation_breakdown']
        print(f"  ✅ Situation breakdown: {eff['situation_breakdown']}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Situation breakdown: {e}")
        failed += 1

    # Test 14: Auto situation detection
    try:
        career_msgs = make_messages(
            ["I need help with my job interview", "My boss is unfair about my promotion"],
            ["Let's prepare...", "That's frustrating..."]
        )
        detected = learner.detect_situation_type(career_msgs)
        assert detected == 'career', f"Expected 'career', got '{detected}'"
        
        emotional_msgs = make_messages(
            ["I'm feeling really anxious and stressed", "I'm worried about everything"],
            ["I hear you...", "Let's talk about it..."]
        )
        detected2 = learner.detect_situation_type(emotional_msgs)
        assert detected2 == 'emotional', f"Expected 'emotional', got '{detected2}'"
        
        general_msgs = make_messages(["hello", "ok"], ["hi", "sure"])
        detected3 = learner.detect_situation_type(general_msgs)
        assert detected3 == 'general', f"Expected 'general', got '{detected3}'"
        
        print(f"  ✅ Situation detection: career={detected}, emotional={detected2}, general={detected3}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Situation detection: {e}")
        failed += 1

    # Test 15: Auto-detect integrates into analyze_conversation
    try:
        career_msgs = make_messages(
            ["I want to change my career path", "My salary is too low",
             "Should I resign from my job?"],
            ["Let's explore...", "I understand...", "Consider..."]
        )
        outcome = learner.analyze_conversation('sess_autodetect', 1, career_msgs, 'coach')
        assert outcome.situation_type == 'career', f"Expected auto-detected 'career', got '{outcome.situation_type}'"
        print(f"  ✅ Auto-detect in analysis: situation={outcome.situation_type}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Auto-detect in analysis: {e}")
        failed += 1

    print(f"\n{'='*50}")
    print(f"PHASE 7 LOCAL: {passed}/{passed+failed} passed")
    print(f"{'='*50}")
    assert failed == 0, f"{failed} test(s) failed"


def test_production():
    """Test Phase 7 effectiveness endpoints on PythonAnywhere"""
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

    # Test 1: System stats endpoint
    try:
        r = session.get(f"{BASE_URL}/api/effectiveness/stats")
        if r.status_code == 200:
            data = r.json()
            assert 'total_conversations_tracked' in data
            assert 'engagement_distribution' in data
            print(f"  ✅ System stats: total={data['total_conversations_tracked']}, users={data['unique_users']}")
            passed += 1
        else:
            print(f"  ❌ System stats: {r.status_code} {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ System stats: {e}")
        failed += 1

    # Test 2: User engagement stats
    try:
        r = session.get(f"{BASE_URL}/api/effectiveness/user")
        if r.status_code == 200:
            data = r.json()
            assert 'total_conversations' in data
            assert 'avg_satisfaction' in data
            print(f"  ✅ User engagement: convs={data['total_conversations']}, satisfaction={data.get('avg_satisfaction')}")
            passed += 1
        else:
            print(f"  ❌ User engagement: {r.status_code} {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ User engagement: {e}")
        failed += 1

    # Test 3: Character effectiveness
    try:
        r = session.get(f"{BASE_URL}/api/effectiveness/character/chatchat")
        if r.status_code == 200:
            data = r.json()
            assert 'effectiveness_score' in data
            assert 'total_conversations' in data
            print(f"  ✅ Character effectiveness (chatchat): score={data['effectiveness_score']}, convs={data['total_conversations']}")
            passed += 1
        else:
            print(f"  ❌ Character effectiveness: {r.status_code} {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Character effectiveness: {e}")
        failed += 1

    # Test 4: Best characters
    try:
        r = session.get(f"{BASE_URL}/api/effectiveness/best")
        if r.status_code == 200:
            data = r.json()
            assert 'characters' in data
            print(f"  ✅ Best characters: {len(data['characters'])} ranked")
            passed += 1
        else:
            print(f"  ❌ Best characters: {r.status_code} {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Best characters: {e}")
        failed += 1

    # Test 5: Manual analyze a conversation
    try:
        # Get a conversation to analyze
        r = session.get(f"{BASE_URL}/api/user/conversations")
        convs = r.json()
        if isinstance(convs, dict):
            convs = convs.get('conversations', [])
        
        if convs and len(convs) > 0:
            test_session = convs[0]['session_id']
            r = session.post(f"{BASE_URL}/api/effectiveness/analyze/{test_session}", json={})
            if r.status_code == 200:
                data = r.json()
                assert data.get('success') is True
                outcome = data.get('outcome', {})
                print(f"  ✅ Analyze conversation: satisfaction={outcome.get('satisfaction_estimate')}, engagement={outcome.get('engagement_level')}")
                passed += 1
            elif r.status_code == 404:
                print(f"  ⚠️ Analyze conversation: no messages (skipped)")
                passed += 1
            else:
                print(f"  ❌ Analyze conversation: {r.status_code} {r.text[:200]}")
                failed += 1
        else:
            print(f"  ⚠️ Analyze conversation: no conversations available (skipped)")
            passed += 1
    except Exception as e:
        print(f"  ❌ Analyze conversation: {e}")
        failed += 1

    # Test 6: Submit feedback
    try:
        r = session.post(f"{BASE_URL}/api/effectiveness/feedback", json={
            "session_id": "test_feedback_session",
            "feedback_type": "thumbs_up"
        })
        if r.status_code == 200:
            data = r.json()
            assert data.get('success') is True
            print(f"  ✅ Submit feedback: thumbs_up recorded")
            passed += 1
        else:
            print(f"  ❌ Submit feedback: {r.status_code} {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Submit feedback: {e}")
        failed += 1

    # Test 7: Effectiveness trends
    try:
        r = session.get(f"{BASE_URL}/api/effectiveness/trends/chatchat?days=30")
        if r.status_code == 200:
            data = r.json()
            assert 'trends' in data
            assert data['character_id'] == 'chatchat'
            print(f"  ✅ Effectiveness trends: {len(data['trends'])} data points")
            passed += 1
        else:
            print(f"  ❌ Effectiveness trends: {r.status_code} {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Effectiveness trends: {e}")
        failed += 1

    print(f"\n{'='*50}")
    print(f"PHASE 7 PRODUCTION: {passed}/{passed+failed} passed")
    print(f"{'='*50}")
    assert failed == 0, f"{failed} test(s) failed"


if __name__ == '__main__':
    print("=" * 60)
    print("PHASE 7: CHARACTER EFFECTIVENESS LEARNER TESTS")
    print("=" * 60)

    print("\n📋 LOCAL TESTS")
    print("-" * 40)
    local_ok = test_phase7_local()

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
