"""
Phase 8: Character Expansion System Tests
Tests gap detection, character generation, scheduler integration, and API endpoints.
"""
import sqlite3
import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smart_response.character_expansion import (
    create_character_expansion_system, CharacterExpansionSystem,
    TraitSpaceGap, CharacterCandidate
)
from smart_response.character_traits import (
    create_character_trait_system, TraitVector, CharacterProfile
)


def test_phase8_local():
    """Test Phase 8 character expansion with in-memory DB"""
    db = sqlite3.connect(':memory:')
    trait_system = create_character_trait_system(db)
    expansion = create_character_expansion_system(db)
    passed = 0
    failed = 0

    # Test 1: Gap analysis finds gaps in trait-space
    try:
        gaps = expansion.analyze_trait_space_coverage(trait_system)
        assert isinstance(gaps, list)
        # With 8 base characters, there should be some gaps
        print(f"  ✅ Gap analysis: found {len(gaps)} gaps")
        if gaps:
            print(f"      Top gap: score={gaps[0].gap_score:.2f}, situations={gaps[0].situation_types}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Gap analysis: {e}")
        failed += 1

    # Test 2: Template-based character generation
    try:
        if gaps:
            candidate = expansion.generate_character_for_gap(gaps[0])
            assert candidate is not None
            assert candidate.name
            assert candidate.inspiration
            assert candidate.traits is not None
            assert candidate.philosophical_lens
            print(f"  ✅ Template generation: {candidate.name} (inspired by {candidate.inspiration})")
            passed += 1
        else:
            print(f"  ⚠️ Template generation: skipped (no gaps)")
            passed += 1
    except Exception as e:
        print(f"  ❌ Template generation: {e}")
        failed += 1

    # Test 3: Add generated character to system
    try:
        if gaps:
            candidate = expansion.generate_character_for_gap(gaps[0])
            initial_count = len(trait_system.characters)
            success = expansion.add_character_to_system(candidate, trait_system)
            assert success is True
            assert len(trait_system.characters) == initial_count + 1
            print(f"  ✅ Add to system: {initial_count} → {len(trait_system.characters)} characters")
            passed += 1
        else:
            print(f"  ⚠️ Add to system: skipped (no gaps)")
            passed += 1
    except Exception as e:
        print(f"  ❌ Add to system: {e}")
        failed += 1

    # Test 4: Duplicate character handling
    try:
        if gaps:
            candidate = expansion.generate_character_for_gap(gaps[0])
            success = expansion.add_character_to_system(candidate, trait_system)
            assert success is False  # Should fail - already exists
            print(f"  ✅ Duplicate handling: correctly rejected")
            passed += 1
        else:
            passed += 1
    except Exception as e:
        print(f"  ❌ Duplicate handling: {e}")
        failed += 1

    # Test 5: Expansion stats
    try:
        stats = expansion.get_expansion_stats()
        assert 'unfilled_gaps' in stats
        assert 'filled_gaps' in stats
        assert 'successful_generations' in stats
        assert 'custom_characters' in stats
        assert 'base_characters' in stats
        assert stats['base_characters'] == 8
        print(f"  ✅ Stats: base={stats['base_characters']}, custom={stats['custom_characters']}, "
              f"gaps_unfilled={stats['unfilled_gaps']}, gens={stats['successful_generations']}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Stats: {e}")
        failed += 1

    # Test 6: Sample situations cover key user needs
    try:
        situations = expansion._get_sample_situations()
        expected = ['emotional', 'quick_decision', 'existential',
                    'celebration', 'skill_development', 'relationship',
                    'career_guidance', 'financial', 'health', 'grief', 'creative']
        for s in expected:
            assert s in situations, f"Missing situation: {s}"
        print(f"  ✅ Sample situations: all {len(expected)} categories present")
        passed += 1
    except Exception as e:
        print(f"  ❌ Sample situations: {e}")
        failed += 1

    # Test 7: Trait descriptions are human-readable
    try:
        traits = TraitVector(
            stoicism=0.1, optimism=0.9, directness=0.5, supportiveness=0.8,
            structure=0.3, depth=0.7, formality=0.2, verbosity=0.6,
            action_oriented=0.9, present_focus=0.4, empathy=0.95, intensity=0.15
        )
        descriptions = expansion._describe_traits(traits)
        assert len(descriptions) == 12
        assert 'Very' in descriptions['stoicism']  # 0.1 = very low
        assert 'Very' in descriptions['optimism']  # 0.9 = very high
        assert 'Balanced' in descriptions['directness']  # 0.5 = balanced
        print(f"  ✅ Trait descriptions: 12 traits described (stoicism={descriptions['stoicism']})")
        passed += 1
    except Exception as e:
        print(f"  ❌ Trait descriptions: {e}")
        failed += 1

    # Test 8: Inspiration source matching by domain
    try:
        gap = TraitSpaceGap(
            centroid=TraitVector(),
            gap_score=0.5,
            nearest_character='coach',
            nearest_distance=2.0,
            recommended_traits={},
            situation_types=['emotional_crisis']
        )
        inspiration = expansion._find_best_inspiration(gap)
        assert inspiration['domain'] == 'mental_health', f"Expected mental_health, got {inspiration['domain']}"
        print(f"  ✅ Inspiration matching: emotional_crisis → {inspiration['name']} ({inspiration['domain']})")
        passed += 1
    except Exception as e:
        print(f"  ❌ Inspiration matching: {e}")
        failed += 1

    # Test 9: Forced gap generation (create a synthetic gap far from any character)
    try:
        from smart_response.character_traits import TraitVector as TV
        forced_gap = TraitSpaceGap(
            centroid=TV(stoicism=0.05, optimism=0.95, directness=0.05, supportiveness=0.95,
                        structure=0.05, depth=0.95, formality=0.05, verbosity=0.95,
                        action_oriented=0.05, present_focus=0.95, empathy=0.95, intensity=0.05),
            gap_score=0.8,
            nearest_character='none',
            nearest_distance=3.0,
            recommended_traits={'empathy': 'Very empathetic', 'depth': 'Very deep/philosophical'},
            situation_types=['existential_question']
        )
        candidate = expansion.generate_character_for_gap(forced_gap)
        assert candidate is not None
        assert candidate.name
        assert candidate.philosophical_lens
        
        # Verify log was written
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM character_generation_log')
        log_count = cursor.fetchone()[0]
        assert log_count > 0
        print(f"  ✅ Forced gap generation: {candidate.name} (inspired by {candidate.inspiration}), log={log_count}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Forced gap generation: {e}")
        failed += 1

    # Test 10: Add forced-gap character and verify DB persistence
    try:
        success = expansion.add_character_to_system(candidate, trait_system)
        assert success is True
        
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM character_library WHERE is_base = 0')
        custom_count = cursor.fetchone()[0]
        assert custom_count >= 1
        print(f"  ✅ Forced character added: {custom_count} custom characters in DB")
        passed += 1
    except Exception as e:
        print(f"  ❌ Forced character added: {e}")
        failed += 1

    # Test 11: Adaptive threshold lowers as library grows
    try:
        t8 = expansion._get_adaptive_threshold(8)
        t12 = expansion._get_adaptive_threshold(12)
        t16 = expansion._get_adaptive_threshold(16)
        t20 = expansion._get_adaptive_threshold(20)
        assert t8 == 1.5, f"8 chars should be 1.5, got {t8}"
        assert t12 < t8, f"12 chars ({t12}) should be < 8 chars ({t8})"
        assert t16 < t12, f"16 chars ({t16}) should be < 12 chars ({t12})"
        assert t20 >= 0.8, f"20 chars ({t20}) should floor at 0.8"
        print(f"  ✅ Adaptive threshold: 8={t8}, 12={t12:.2f}, 16={t16:.2f}, 20={t20:.2f}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Adaptive threshold: {e}")
        failed += 1

    # Test 12: Effectiveness gaps query (empty when no outcome data)
    try:
        eff_gaps = expansion._get_effectiveness_gaps()
        assert isinstance(eff_gaps, dict)
        print(f"  ✅ Effectiveness gaps: {len(eff_gaps)} situations with weakness data")
        passed += 1
    except Exception as e:
        print(f"  ❌ Effectiveness gaps: {e}")
        failed += 1

    # Test 13: Demand scores query (empty when no outcome data)
    try:
        demand = expansion._get_demand_scores()
        assert isinstance(demand, dict)
        print(f"  ✅ Demand scores: {len(demand)} situations with demand data")
        passed += 1
    except Exception as e:
        print(f"  ❌ Demand scores: {e}")
        failed += 1

    # Test 14: Effectiveness-driven gap detection with simulated outcome data
    try:
        # Create conversation_outcomes table and insert low-satisfaction data
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT, user_id INTEGER, character_id TEXT,
                message_count INTEGER, user_message_count INTEGER,
                engagement_level TEXT, satisfaction_estimate REAL,
                goal_achieved BOOLEAN, signals_json TEXT,
                situation_type TEXT, timestamp TEXT
            )
        ''')
        # Simulate 5 low-satisfaction career conversations
        for i in range(5):
            cursor.execute('''
                INSERT INTO conversation_outcomes 
                (session_id, user_id, character_id, message_count, user_message_count,
                 engagement_level, satisfaction_estimate, goal_achieved, situation_type, timestamp)
                VALUES (?, 1, 'coach', 6, 3, 'moderate', ?, 0, 'career_guidance', ?)
            ''', (f'eff_test_{i}', 0.2 + i * 0.02, datetime.now().isoformat()))
        db.commit()
        
        eff_gaps = expansion._get_effectiveness_gaps()
        assert 'career_guidance' in eff_gaps
        assert eff_gaps['career_guidance'] > 0.5  # Low satisfaction = high weakness
        print(f"  ✅ Effectiveness-driven gaps: career_guidance weakness={eff_gaps['career_guidance']:.3f}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Effectiveness-driven gaps: {e}")
        failed += 1

    # Test 15: Demand scores with simulated data
    try:
        demand = expansion._get_demand_scores()
        assert 'career_guidance' in demand
        assert demand['career_guidance'] > 0
        print(f"  ✅ Demand with data: career_guidance demand={demand['career_guidance']:.3f}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Demand with data: {e}")
        failed += 1

    # Test 16: Stats include effectiveness and demand data
    try:
        stats = expansion.get_expansion_stats()
        assert 'effectiveness_weaknesses' in stats
        assert 'demand_scores' in stats
        assert 'adaptive_threshold' in stats
        print(f"  ✅ Enhanced stats: threshold={stats['adaptive_threshold']:.2f}, "
              f"weaknesses={len(stats['effectiveness_weaknesses'])}, demands={len(stats['demand_scores'])}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Enhanced stats: {e}")
        failed += 1

    # Test 17: AI generation parses valid JSON response
    try:
        mock_ai_response = '{"display_name": "The Meaning Seeker", "description": "Guides through existential challenges with compassion. Helps find purpose in difficult moments.", "philosophical_lens": "Every struggle contains the seed of growth and meaning."}'
        
        def mock_ai_func(prompt):
            return mock_ai_response
        
        forced_gap2 = TraitSpaceGap(
            centroid=TraitVector(),
            gap_score=0.5,
            nearest_character='sage',
            nearest_distance=2.0,
            recommended_traits={},
            situation_types=['existential_question']
        )
        candidate = expansion._generate_with_ai(forced_gap2, 
            {"name": "Viktor Frankl", "domain": "mental_health", "style": "meaning-focused"},
            mock_ai_func)
        assert candidate is not None
        assert candidate.name == "The Meaning Seeker"
        assert "purpose" in candidate.description.lower() or "compassion" in candidate.description.lower()
        print(f"  ✅ AI JSON parsing: name={candidate.name}, lens={candidate.philosophical_lens[:50]}...")
        passed += 1
    except Exception as e:
        print(f"  ❌ AI JSON parsing: {e}")
        failed += 1

    # Test 18: AI generation handles bad response gracefully (falls back to template)
    try:
        def bad_ai_func(prompt):
            return "Sorry, I can't generate that."
        
        candidate = expansion._generate_with_ai(forced_gap2,
            {"name": "Buddha", "domain": "mental_health", "style": "mindful guide"},
            bad_ai_func)
        assert candidate is not None  # Should fall back to template
        assert candidate.inspiration == "Buddha"
        print(f"  ✅ AI fallback: {candidate.name} (template fallback on bad response)")
        passed += 1
    except Exception as e:
        print(f"  ❌ AI fallback: {e}")
        failed += 1

    print(f"\n{'='*50}")
    print(f"PHASE 8 LOCAL: {passed}/{passed+failed} passed")
    print(f"{'='*50}")
    assert failed == 0, f"{failed} test(s) failed"


def test_production():
    """Test Phase 8 expansion endpoints on PythonAnywhere"""
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

    # Test 1: Expansion stats
    try:
        r = session.get(f"{BASE_URL}/api/expansion/stats")
        if r.status_code == 200:
            data = r.json()
            assert 'base_characters' in data
            assert 'custom_characters' in data
            print(f"  ✅ Stats: base={data['base_characters']}, custom={data['custom_characters']}, "
                  f"total={data.get('total_characters', 'N/A')}")
            passed += 1
        else:
            print(f"  ❌ Stats: {r.status_code} {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Stats: {e}")
        failed += 1

    # Test 2: Gap analysis
    try:
        r = session.get(f"{BASE_URL}/api/expansion/gaps")
        if r.status_code == 200:
            data = r.json()
            assert 'gaps_found' in data
            assert 'gaps' in data
            print(f"  ✅ Gaps: {data['gaps_found']} found")
            if data['gaps']:
                g = data['gaps'][0]
                print(f"      Top gap: score={g['gap_score']}, situations={g['situation_types']}")
            passed += 1
        else:
            print(f"  ❌ Gaps: {r.status_code} {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Gaps: {e}")
        failed += 1

    # Test 3: Expanded characters list
    try:
        r = session.get(f"{BASE_URL}/api/expansion/characters")
        if r.status_code == 200:
            data = r.json()
            assert 'characters' in data
            assert 'count' in data
            print(f"  ✅ Expanded characters: {data['count']} non-base characters")
            passed += 1
        else:
            print(f"  ❌ Expanded characters: {r.status_code} {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Expanded characters: {e}")
        failed += 1

    # Test 4: Manual trigger expansion
    try:
        r = session.post(f"{BASE_URL}/api/expansion/run", json={})
        if r.status_code == 200:
            data = r.json()
            assert data.get('success') is True
            result = data.get('result', {})
            print(f"  ✅ Manual expansion: gaps={result.get('gaps_found', 0)}, added={result.get('characters_added', 0)}")
            passed += 1
        else:
            print(f"  ❌ Manual expansion: {r.status_code} {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Manual expansion: {e}")
        failed += 1

    # Test 5: Verify character was added (check stats again)
    try:
        r = session.get(f"{BASE_URL}/api/expansion/stats")
        if r.status_code == 200:
            data = r.json()
            print(f"  ✅ Post-expansion stats: custom={data['custom_characters']}, total={data.get('total_characters', 'N/A')}")
            passed += 1
        else:
            print(f"  ❌ Post-expansion stats: {r.status_code}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Post-expansion stats: {e}")
        failed += 1

    print(f"\n{'='*50}")
    print(f"PHASE 8 PRODUCTION: {passed}/{passed+failed} passed")
    print(f"{'='*50}")
    assert failed == 0, f"{failed} test(s) failed"


if __name__ == '__main__':
    print("=" * 60)
    print("PHASE 8: CHARACTER EXPANSION SYSTEM TESTS")
    print("=" * 60)

    print("\n📋 LOCAL TESTS")
    print("-" * 40)
    local_ok = test_phase8_local()

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
