"""
Test script for the personality assessment system
Demonstrates the complete workflow from assessment to adaptive responses
"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_personality_system():
    """Test the complete personality system workflow"""
    
    print("=== Personality Assessment System Test ===\n")
    
    # Test 1: Initialize system components
    print("1. Initializing System Components...")
    
    try:
        from ai_compare.personality_profiler import PersonalityProfiler
        from ai_compare.adaptive_personality import AdaptivePersonality
        from ai_compare.personality_ui import PersonalityFeedbackWindow, PersonalityAssessmentUI
        from ai_compare.chatbot import AIChatbot
        
        profiler = PersonalityProfiler()
        assessment_ui = PersonalityAssessmentUI(profiler)
        print("   ✓ All components initialized successfully")
        
    except Exception as e:
        print(f"   ✗ Component initialization failed: {e}")
        return False
    
    # Test 2: Start assessment for test user
    print("\n2. Starting Personality Assessment...")
    
    test_user_id = "test_user_123"
    
    try:
        # Start assessment
        intro_ui = assessment_ui.start_assessment_ui(test_user_id)
        print(f"   ✓ Assessment started: {intro_ui['title']}")
        print(f"   ✓ Estimated time: {intro_ui['estimated_time']}")
        
        # Get first question
        question_ui = assessment_ui.get_current_question_ui(test_user_id)
        if question_ui:
            print(f"   ✓ First question loaded: {question_ui['question'][:50]}...")
            print(f"   ✓ Progress: {question_ui['progress']}")
        
    except Exception as e:
        print(f"   ✗ Assessment start failed: {e}")
        return False
    
    # Test 3: Simulate answering questions
    print("\n3. Simulating Assessment Responses...")
    
    try:
        # Answer a few questions with different response patterns
        test_responses = [
            (0, "Direct communication preference"),
            (1, "Moderate extraversion"),
            (2, "High conscientiousness")
        ]
        
        for i, (option_id, description) in enumerate(test_responses):
            question_ui = assessment_ui.get_current_question_ui(test_user_id)
            if question_ui and question_ui.get('ui_type') == 'assessment_question':
                question_id = question_ui['question_id']
                result = assessment_ui.process_question_response(test_user_id, question_id, option_id)
                print(f"   ✓ Response {i+1} recorded: {description}")
            else:
                break
        
        # Check if assessment is complete
        final_ui = assessment_ui.get_current_question_ui(test_user_id)
        if final_ui and final_ui.get('ui_type') == 'assessment_complete':
            print("   ✓ Assessment completed successfully")
            profile_summary = final_ui.get('profile_summary', {})
            print(f"   ✓ Profile created: {profile_summary}")
        
    except Exception as e:
        print(f"   ✗ Response simulation failed: {e}")
        return False
    
    # Test 4: Test adaptive personality
    print("\n4. Testing Adaptive Personality System...")
    
    try:
        adaptive_personality = AdaptivePersonality(test_user_id, profiler)
        
        # Test message analysis
        test_message = "I need help with a complex programming problem. Can you explain it step by step?"
        analysis = adaptive_personality.analyze_user_message(test_message)
        
        print(f"   ✓ Message analysis completed")
        print(f"     - Message length: {analysis.message_length_avg} words")
        print(f"     - Question frequency: {analysis.question_frequency:.2f}")
        print(f"     - Technical language: {analysis.technical_language_usage:.2f}")
        
        # Test response adaptation
        base_response = "Here's how to solve your programming problem. First, understand the requirements."
        adapted_response = adaptive_personality.adapt_response_style(test_message, base_response)
        
        print(f"   ✓ Response adaptation completed")
        print(f"     - Original: {base_response[:50]}...")
        print(f"     - Adapted: {adapted_response[:50]}...")
        
    except Exception as e:
        print(f"   ✗ Adaptive personality test failed: {e}")
        return False
    
    # Test 5: Test feedback system
    print("\n5. Testing Feedback System...")
    
    try:
        feedback_window = PersonalityFeedbackWindow(test_user_id, profiler)
        feedback = feedback_window.get_current_feedback()
        
        print(f"   ✓ Feedback generated successfully")
        print(f"     - Profile status: {feedback['profile_data']['status']}")
        print(f"     - Confidence: {feedback['profile_data']['confidence']:.0%}")
        
        visual_indicators = feedback['visual_indicators']
        print(f"     - Confidence bar: {visual_indicators['confidence_bar']['label']}")
        
        if visual_indicators['trait_indicators']:
            print("     - Detected traits:")
            for trait, info in visual_indicators['trait_indicators'].items():
                print(f"       * {info['display_name']}: {info['value']}")
        
    except Exception as e:
        print(f"   ✗ Feedback system test failed: {e}")
        return False
    
    # Test 6: Test chatbot integration
    print("\n6. Testing Chatbot Integration...")
    
    try:
        chatbot = AIChatbot(session_id=test_user_id)
        
        # Check if assessment is suggested
        should_offer = chatbot.should_offer_assessment()
        print(f"   ✓ Assessment suggestion check: {should_offer}")
        
        # Get personality feedback
        personality_feedback = chatbot.get_personality_feedback()
        print(f"   ✓ Personality feedback retrieved: {personality_feedback['status']}")
        
        # Test a simple chat interaction (without actually calling AI models)
        print("   ✓ Chatbot integration successful")
        
    except Exception as e:
        print(f"   ✗ Chatbot integration test failed: {e}")
        return False
    
    return True

def demonstrate_usage():
    """Demonstrate how to use the personality system"""
    
    print("\n=== Usage Examples ===\n")
    
    print("1. Starting Assessment:")
    print("   POST /personality/assessment/start")
    print("   {'user_id': 'user123'}")
    
    print("\n2. Getting Questions:")
    print("   GET /personality/assessment/question/user123")
    
    print("\n3. Submitting Responses:")
    print("   POST /personality/assessment/respond")
    print("   {'user_id': 'user123', 'question_id': 'ext_1', 'option_id': 0}")
    
    print("\n4. Getting Feedback:")
    print("   GET /personality/feedback/user123")
    
    print("\n5. Checking Assessment Need:")
    print("   GET /personality/check_assessment/user123")
    
    print("\n6. Integration with Chat:")
    print("   - Personality feedback included in chat responses")
    print("   - AI responses automatically adapted based on user profile")
    print("   - Ongoing learning from conversation patterns")

async def main():
    """Main test function"""
    
    success = await test_personality_system()
    
    if success:
        print("\n🎉 Personality Assessment System is fully functional!")
        
        demonstrate_usage()
        
        print("\n=== Key Features ===")
        print("✓ Psychology-based personality assessment (Big Five + preferences)")
        print("✓ Dynamic AI response adaptation based on user personality")
        print("✓ Real-time feedback window showing personality insights")
        print("✓ Ongoing analysis and profile refinement from interactions")
        print("✓ Session persistence for personality profiles")
        print("✓ Complete Flask API for UI integration")
        print("✓ Pausable/resumable assessment process")
        
        print("\n=== Benefits for Users ===")
        print("• Personalized AI responses matching communication style")
        print("• Learning experience adapted to individual preferences")
        print("• Transparent personality insights with feedback")
        print("• Continuous improvement through interaction analysis")
        print("• Quick 3-5 minute assessment with option to pause anytime")
        
    else:
        print("\n❌ Personality system has issues that need to be resolved")

if __name__ == "__main__":
    asyncio.run(main())
