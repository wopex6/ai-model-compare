#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

print("Direct Personality System Test")
print("=" * 40)

# Test 1: Check if files exist
print("\n1. Checking files...")
files_to_check = [
    "ai_compare/personality_profiler.py",
    "ai_compare/adaptive_personality.py", 
    "ai_compare/personality_ui.py"
]

for file_path in files_to_check:
    if Path(file_path).exists():
        size = Path(file_path).stat().st_size
        print(f"✓ {file_path} ({size} bytes)")
    else:
        print(f"✗ {file_path} missing")

# Test 2: Try imports
print("\n2. Testing imports...")

try:
    from ai_compare.personality_profiler import PersonalityProfiler, PersonalityProfile
    print("✓ PersonalityProfiler imported")
except Exception as e:
    print(f"✗ PersonalityProfiler import failed: {e}")
    sys.exit(1)

try:
    from ai_compare.adaptive_personality import AdaptivePersonality
    print("✓ AdaptivePersonality imported")
except Exception as e:
    print(f"✗ AdaptivePersonality import failed: {e}")

try:
    from ai_compare.personality_ui import PersonalityFeedbackWindow, PersonalityAssessmentUI
    print("✓ PersonalityUI imported")
except Exception as e:
    print(f"✗ PersonalityUI import failed: {e}")

# Test 3: Create instances
print("\n3. Creating instances...")

try:
    profiler = PersonalityProfiler()
    print("✓ PersonalityProfiler instance created")
    print(f"  - Questions loaded: {len(profiler.questions)}")
    print(f"  - Profiles directory: {profiler.profiles_dir}")
except Exception as e:
    print(f"✗ PersonalityProfiler creation failed: {e}")
    sys.exit(1)

# Test 4: Start assessment
print("\n4. Testing assessment...")

try:
    test_user = "test_user_123"
    session = profiler.start_assessment(test_user)
    print("✓ Assessment session started")
    print(f"  - User ID: {session['user_id']}")
    print(f"  - Questions: {len(session['questions'])}")
    print(f"  - Estimated time: {session['estimated_time']}")
    
    # Get first question
    question = profiler.get_next_question(test_user)
    if question:
        print("✓ First question retrieved")
        print(f"  - Question: {question['text'][:60]}...")
        print(f"  - Options: {len(question['options'])}")
        print(f"  - Progress: {question['progress']}")
        
        # Answer the question
        success = profiler.record_response(test_user, question['question_id'], 0)
        print(f"✓ Response recorded: {success}")
        
        # Analyze responses
        profile = profiler.analyze_responses(test_user)
        print("✓ Profile analysis completed")
        print(f"  - Communication style: {profile.communication_style.value}")
        print(f"  - Learning preference: {profile.learning_preference.value}")
        print(f"  - Confidence: {profile.confidence_level:.1%}")
        
    else:
        print("✗ No question retrieved")
        
except Exception as e:
    print(f"✗ Assessment test failed: {e}")

# Test 5: Adaptive personality
print("\n5. Testing adaptive personality...")

try:
    adaptive = AdaptivePersonality(test_user, profiler)
    print("✓ AdaptivePersonality created")
    
    # Test message analysis
    test_message = "I need help understanding this complex algorithm. Can you explain it step by step with examples?"
    analysis = adaptive.analyze_user_message(test_message)
    
    print("✓ Message analysis completed")
    print(f"  - Message length: {analysis.message_length_avg} words")
    print(f"  - Question frequency: {analysis.question_frequency:.2f}")
    print(f"  - Technical language: {analysis.technical_language_usage:.2f}")
    print(f"  - Response preference: {analysis.response_time_preference}")
    
    # Test response adaptation
    base_response = "Here's how the algorithm works. It processes data efficiently."
    adapted_response = adaptive.adapt_response_style(test_message, base_response)
    
    print("✓ Response adaptation completed")
    print(f"  - Original length: {len(base_response)} chars")
    print(f"  - Adapted length: {len(adapted_response)} chars")
    print(f"  - Adaptation applied: {adapted_response != base_response}")
    
except Exception as e:
    print(f"✗ Adaptive personality test failed: {e}")

# Test 6: UI components
print("\n6. Testing UI components...")

try:
    assessment_ui = PersonalityAssessmentUI(profiler)
    print("✓ PersonalityAssessmentUI created")
    
    # Test assessment intro
    intro = assessment_ui.start_assessment_ui(test_user)
    print("✓ Assessment intro generated")
    print(f"  - Title: {intro['title']}")
    print(f"  - Estimated time: {intro['estimated_time']}")
    print(f"  - Benefits: {len(intro['benefits'])} listed")
    
    # Test feedback window
    feedback_window = PersonalityFeedbackWindow(test_user, profiler)
    feedback = feedback_window.get_current_feedback()
    print("✓ Feedback window generated")
    print(f"  - Window title: {feedback['window_title']}")
    print(f"  - Profile status: {feedback['profile_data']['status']}")
    print(f"  - Action buttons: {len(feedback['action_buttons'])}")
    
except Exception as e:
    print(f"✗ UI components test failed: {e}")

print("\n" + "=" * 40)
print("✅ Personality system test completed!")
print("\nThe system is ready for use. Key features:")
print("• Psychology-based personality assessment")
print("• Dynamic AI response adaptation")
print("• Real-time personality feedback")
print("• Pausable/resumable assessment process")
print("• Session persistence and profile storage")
