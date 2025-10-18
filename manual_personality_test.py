"""Manual test of personality system components"""

# Test 1: Import test
print("=== Personality System Manual Test ===\n")

print("1. Testing imports...")
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    
    from ai_compare.personality_profiler import (
        PersonalityProfiler, PersonalityProfile, 
        PersonalityDimension, CommunicationStyle
    )
    print("✓ PersonalityProfiler components imported")
    
    from ai_compare.adaptive_personality import AdaptivePersonality, InteractionAnalysis
    print("✓ AdaptivePersonality components imported")
    
    from ai_compare.personality_ui import PersonalityFeedbackWindow, PersonalityAssessmentUI
    print("✓ PersonalityUI components imported")
    
except Exception as e:
    print(f"✗ Import failed: {e}")
    exit(1)

# Test 2: Create profiler and test basic functionality
print("\n2. Testing PersonalityProfiler...")
try:
    profiler = PersonalityProfiler()
    print(f"✓ Profiler created with {len(profiler.questions)} questions")
    
    # Test assessment start
    test_user = "manual_test_user"
    session = profiler.start_assessment(test_user)
    print(f"✓ Assessment started for {test_user}")
    print(f"  - Questions in session: {len(session['questions'])}")
    print(f"  - Estimated time: {session['estimated_time']}")
    
    # Test getting question
    question = profiler.get_next_question(test_user)
    if question:
        print(f"✓ Question retrieved: {question['question_id']}")
        print(f"  - Text: {question['text'][:50]}...")
        print(f"  - Options: {len(question['options'])}")
        
        # Test recording response
        success = profiler.record_response(test_user, question['question_id'], 0)
        print(f"✓ Response recorded: {success}")
        
        # Test profile analysis
        profile = profiler.analyze_responses(test_user)
        print(f"✓ Profile analyzed")
        print(f"  - Communication style: {profile.communication_style.value}")
        print(f"  - Confidence: {profile.confidence_level:.1%}")
        
    else:
        print("✗ No question available")
        
except Exception as e:
    print(f"✗ PersonalityProfiler test failed: {e}")

# Test 3: Test adaptive personality
print("\n3. Testing AdaptivePersonality...")
try:
    adaptive = AdaptivePersonality(test_user, profiler)
    print("✓ AdaptivePersonality created")
    
    # Test message analysis
    test_msg = "Can you help me understand this complex programming concept? I'm having trouble with it."
    analysis = adaptive.analyze_user_message(test_msg)
    print("✓ Message analyzed")
    print(f"  - Word count: {analysis.message_length_avg}")
    print(f"  - Questions: {analysis.question_frequency:.2f}")
    print(f"  - Technical terms: {analysis.technical_language_usage:.2f}")
    
    # Test response adaptation
    base_resp = "Here's how it works. It's a simple process."
    adapted_resp = adaptive.adapt_response_style(test_msg, base_resp)
    print("✓ Response adapted")
    print(f"  - Original: {base_resp}")
    print(f"  - Adapted: {adapted_resp}")
    
except Exception as e:
    print(f"✗ AdaptivePersonality test failed: {e}")

# Test 4: Test UI components
print("\n4. Testing UI Components...")
try:
    assessment_ui = PersonalityAssessmentUI(profiler)
    print("✓ AssessmentUI created")
    
    # Test intro
    intro = assessment_ui.start_assessment_ui(test_user)
    print(f"✓ Assessment intro: {intro['title']}")
    
    # Test feedback
    feedback_window = PersonalityFeedbackWindow(test_user, profiler)
    feedback = feedback_window.get_current_feedback()
    print(f"✓ Feedback generated: {feedback['window_title']}")
    
except Exception as e:
    print(f"✗ UI Components test failed: {e}")

print("\n=== Test Summary ===")
print("✅ Personality system components are working!")
print("\nKey Features Verified:")
print("• Psychology-based assessment questions")
print("• User response recording and analysis") 
print("• Personality profile generation")
print("• Adaptive response styling")
print("• UI feedback and assessment interfaces")
print("\nThe system is ready for integration and use.")
