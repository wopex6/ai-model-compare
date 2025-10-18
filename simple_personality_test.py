"""
Simple test to verify personality system components work
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test if all personality modules can be imported"""
    print("Testing imports...")
    
    try:
        from ai_compare.personality_profiler import PersonalityProfiler, PersonalityProfile
        print("✓ PersonalityProfiler imported")
        
        from ai_compare.adaptive_personality import AdaptivePersonality
        print("✓ AdaptivePersonality imported")
        
        from ai_compare.personality_ui import PersonalityFeedbackWindow, PersonalityAssessmentUI
        print("✓ PersonalityUI imported")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality"""
    print("\nTesting basic functionality...")
    
    try:
        from ai_compare.personality_profiler import PersonalityProfiler
        
        # Create profiler
        profiler = PersonalityProfiler()
        print("✓ PersonalityProfiler created")
        
        # Start assessment
        session = profiler.start_assessment("test_user")
        print(f"✓ Assessment started: {session['estimated_time']}")
        
        # Get question
        question = profiler.get_next_question("test_user")
        if question:
            print(f"✓ Question retrieved: {question['text'][:50]}...")
            
            # Record response
            success = profiler.record_response("test_user", question['question_id'], 0)
            print(f"✓ Response recorded: {success}")
            
            # Analyze
            profile = profiler.analyze_responses("test_user")
            print(f"✓ Profile created: {profile.communication_style.value}")
        
        return True
    except Exception as e:
        print(f"✗ Basic functionality failed: {e}")
        return False

def test_adaptive_system():
    """Test adaptive personality system"""
    print("\nTesting adaptive system...")
    
    try:
        from ai_compare.personality_profiler import PersonalityProfiler
        from ai_compare.adaptive_personality import AdaptivePersonality
        
        profiler = PersonalityProfiler()
        adaptive = AdaptivePersonality("test_user", profiler)
        print("✓ AdaptivePersonality created")
        
        # Test message analysis
        message = "Can you help me with this programming problem?"
        analysis = adaptive.analyze_user_message(message)
        print(f"✓ Message analyzed: {analysis.message_length_avg} words")
        
        # Test response adaptation
        base_response = "Here's how to solve it."
        adapted = adaptive.adapt_response_style(message, base_response)
        print(f"✓ Response adapted: {len(adapted)} chars")
        
        return True
    except Exception as e:
        print(f"✗ Adaptive system failed: {e}")
        return False

def test_ui_components():
    """Test UI components"""
    print("\nTesting UI components...")
    
    try:
        from ai_compare.personality_profiler import PersonalityProfiler
        from ai_compare.personality_ui import PersonalityAssessmentUI, PersonalityFeedbackWindow
        
        profiler = PersonalityProfiler()
        ui = PersonalityAssessmentUI(profiler)
        print("✓ AssessmentUI created")
        
        # Test assessment start
        intro = ui.start_assessment_ui("test_user")
        print(f"✓ Assessment intro: {intro['title']}")
        
        # Test feedback window
        feedback_window = PersonalityFeedbackWindow("test_user", profiler)
        feedback = feedback_window.get_current_feedback()
        print(f"✓ Feedback generated: {feedback['window_title']}")
        
        return True
    except Exception as e:
        print(f"✗ UI components failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Simple Personality System Test ===\n")
    
    tests = [
        test_imports,
        test_basic_functionality,
        test_adaptive_system,
        test_ui_components
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Personality system is working.")
    else:
        print("❌ Some tests failed. Check the errors above.")
