"""
Test PersonalityResolver - Smart personality data resolution

This script demonstrates how to use PersonalityResolver for real-time decisions
"""

from integrated_database import IntegratedDatabase
from smart_response.personality_resolver import PersonalityResolver


def test_basic_usage():
    """Test basic PersonalityResolver usage"""
    print("=" * 80)
    print("TEST: Basic PersonalityResolver Usage")
    print("=" * 80)
    print()
    
    db = IntegratedDatabase()
    user_id = 1  # Wai Tse
    
    # Get personality profile using new v2 method
    profile = db.get_personality_profile_v2(user_id)
    
    print(f"📊 Personality Profile for User {user_id}:")
    print(f"   Source: {profile['source']}")
    print(f"   Confidence: {profile['confidence']:.2f}")
    print()
    
    print("🎯 Big 5 Traits:")
    for trait, value in profile['traits'].items():
        print(f"   {trait.capitalize():20} {value:.2f} ({int(value * 100)}%)")
    print()
    
    print("📋 Metadata:")
    for key, value in profile['metadata'].items():
        print(f"   {key:25} {value}")
    print()
    
    print("💡 Recommendations:")
    for key, value in profile['recommendations'].items():
        print(f"   {key:25} {value}")
    print()


def test_context_specific():
    """Test context-specific personality resolution"""
    print("=" * 80)
    print("TEST: Context-Specific Resolution")
    print("=" * 80)
    print()
    
    db = IntegratedDatabase()
    user_id = 1
    
    contexts = [
        'character_selection',
        'response_tone',
        'action_plan'
    ]
    
    for context in contexts:
        profile = db.get_personality_profile_v2(user_id, context=context)
        print(f"📌 Context: {context}")
        print(f"   Confidence: {profile['confidence']:.2f}")
        print(f"   Reliability: {profile['recommendations']['reliability']}")
        print(f"   Should reassess: {profile['recommendations']['should_reassess']}")
        print()


def test_character_selection_example():
    """Example: Using resolver for character selection"""
    print("=" * 80)
    print("EXAMPLE: Character Selection")
    print("=" * 80)
    print()
    
    db = IntegratedDatabase()
    user_id = 1
    
    # Get profile for character selection
    profile = db.get_personality_profile_v2(user_id, context='character_selection')
    
    print(f"🎭 Selecting character for user {user_id}...")
    print(f"   Confidence: {profile['confidence']:.2f}")
    print()
    
    # Decision logic
    if profile['confidence'] < 0.5:
        print("⚠️  Low confidence - using versatile default")
        character = 'coach'
        reason = 'Safe choice for unknown personality'
    else:
        # Use personality traits
        traits = profile['traits']
        
        # Example decision logic
        if traits['neuroticism'] > 0.6:
            character = 'psychologist'
            reason = f"High neuroticism ({traits['neuroticism']:.2f}) - needs emotional support"
        elif traits['openness'] > 0.7 and traits['conscientiousness'] < 0.5:
            character = 'sage'
            reason = f"High openness ({traits['openness']:.2f}), low structure - philosophical approach"
        elif traits['conscientiousness'] > 0.7:
            character = 'coach'
            reason = f"High conscientiousness ({traits['conscientiousness']:.2f}) - structured guidance"
        else:
            character = 'coach'
            reason = 'Balanced personality - versatile approach'
    
    print(f"✅ Selected: {character}")
    print(f"   Reasoning: {reason}")
    print(f"   Data source: {profile['source']}")
    print()


def test_response_tone_example():
    """Example: Using resolver for response tone"""
    print("=" * 80)
    print("EXAMPLE: Response Tone Selection")
    print("=" * 80)
    print()
    
    db = IntegratedDatabase()
    user_id = 1
    
    # Get profile for tone selection
    profile = db.get_personality_profile_v2(user_id, context='response_tone')
    
    print(f"🎨 Determining response tone for user {user_id}...")
    print(f"   Confidence: {profile['confidence']:.2f}")
    print()
    
    # Default tone
    tone = {
        'formality': 'casual',
        'verbosity': 'moderate',
        'directness': 'balanced',
        'empathy_level': 'medium'
    }
    
    # Adjust based on traits (if confidence is reasonable)
    if profile['confidence'] > 0.6:
        traits = profile['traits']
        
        # High Openness → More detailed, exploratory
        if traits['openness'] > 0.7:
            tone['verbosity'] = 'detailed'
            tone['formality'] = 'casual'
            print(f"   📚 High openness ({traits['openness']:.2f}) → detailed, casual")
        
        # High Conscientiousness → More structured, direct
        if traits['conscientiousness'] > 0.7:
            tone['directness'] = 'direct'
            tone['verbosity'] = 'concise'
            print(f"   📋 High conscientiousness ({traits['conscientiousness']:.2f}) → direct, concise")
        
        # High Extraversion → More enthusiastic
        if traits['extraversion'] > 0.7:
            tone['formality'] = 'friendly'
            print(f"   🎉 High extraversion ({traits['extraversion']:.2f}) → friendly")
        
        # High Neuroticism → More empathetic
        if traits['neuroticism'] > 0.6:
            tone['empathy_level'] = 'high'
            tone['directness'] = 'gentle'
            print(f"   🤲 High neuroticism ({traits['neuroticism']:.2f}) → empathetic, gentle")
    
    print()
    print(f"✅ Response Tone:")
    for key, value in tone.items():
        print(f"   {key:20} {value}")
    print()


def test_comparison_old_vs_new():
    """Compare old method vs new PersonalityResolver"""
    print("=" * 80)
    print("COMPARISON: Old vs New Method")
    print("=" * 80)
    print()
    
    db = IntegratedDatabase()
    user_id = 1
    
    # Old method
    print("📛 OLD METHOD (get_personality_profile):")
    old_profile = db.get_personality_profile(user_id)
    print(f"   Source: {old_profile['source']}")
    print(f"   Confidence: {old_profile['confidence']:.2f}")
    print(f"   Has assessment: {old_profile['has_assessment']}")
    print()
    
    # New method
    print("✅ NEW METHOD (get_personality_profile_v2):")
    new_profile = db.get_personality_profile_v2(user_id)
    print(f"   Source: {new_profile['source']}")
    print(f"   Confidence: {new_profile['confidence']:.2f}")
    print(f"   Reliability: {new_profile['recommendations']['reliability']}")
    print(f"   Should reassess: {new_profile['recommendations']['should_reassess']}")
    print(f"   Reasoning: {new_profile['recommendations']['reasoning']}")
    print()
    
    print("💡 NEW METHOD ADVANTAGES:")
    print("   ✅ Age-aware (considers assessment freshness)")
    print("   ✅ Blending (combines old assessment with recent inference)")
    print("   ✅ Context-aware (different contexts, different needs)")
    print("   ✅ Cached (fast lookups)")
    print("   ✅ Rich metadata (know exactly what you're using)")
    print()


def test_cache_performance():
    """Test cache performance"""
    print("=" * 80)
    print("TEST: Cache Performance")
    print("=" * 80)
    print()
    
    db = IntegratedDatabase()
    user_id = 1
    
    import time
    
    # First call (uncached)
    start = time.time()
    profile1 = db.get_personality_profile_v2(user_id)
    time1 = (time.time() - start) * 1000
    
    # Second call (cached)
    start = time.time()
    profile2 = db.get_personality_profile_v2(user_id)
    time2 = (time.time() - start) * 1000
    
    print(f"⏱️  First call (uncached):  {time1:.2f}ms")
    print(f"⏱️  Second call (cached):   {time2:.2f}ms")
    if time2 > 0:
        print(f"🚀 Speed improvement:      {time1 / time2:.1f}x faster")
    else:
        print(f"🚀 Speed improvement:      INSTANT (too fast to measure!)")
    print()
    
    # Clear cache
    db.clear_personality_cache(user_id)
    print("🧹 Cache cleared")
    
    # Call after clear (uncached again)
    start = time.time()
    profile3 = db.get_personality_profile_v2(user_id)
    time3 = (time.time() - start) * 1000
    
    print(f"⏱️  After clear (uncached): {time3:.2f}ms")
    print()


if __name__ == '__main__':
    try:
        # Run all tests
        test_basic_usage()
        test_context_specific()
        test_character_selection_example()
        test_response_tone_example()
        test_comparison_old_vs_new()
        test_cache_performance()
        
        print("=" * 80)
        print("✅ ALL TESTS COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
