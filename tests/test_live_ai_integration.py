"""
Live AI Integration Test
Tests that AI actually USES explicit context in its responses
"""

import sys
import os
import sqlite3
import requests
import time

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from smart_response.explicit_context_handler import ExplicitContextHandler
from smart_response.conversation_context import ConversationContextManager


class LiveAIIntegrationTest:
    """
    Test that AI responses actually use explicit context
    
    This is a MANUAL-VERIFICATION test - you must READ the AI responses
    and confirm they acknowledge the user's emotional state and goals.
    """
    
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.character = 'coach'  # Test with Coach Alex
        self.session_id = None
        
    def send_message(self, message):
        """Send message to character and get response"""
        url = f"{self.base_url}/{self.character}/chat"
        
        payload = {
            'message': message,
            'user_id': 999,  # Test user
            'session_id': self.session_id
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Store session ID for continuity
            if 'session_id' in data:
                self.session_id = data['session_id']
            
            return data.get('response', data.get('text', ''))
        except Exception as e:
            print(f"Error sending message: {e}")
            return None
    
    def test_context_awareness(self):
        """Test that AI uses explicit context in responses"""
        print("\n" + "="*80)
        print("LIVE AI INTEGRATION TEST")
        print("="*80)
        print("\nThis test sends messages to the AI and checks if it USES the context.")
        print("You must MANUALLY VERIFY the responses.\n")
        
        # Test scenario: User with stress and a goal
        test_messages = [
            "I'm feeling stressed",
            "I'm worried about my future",
            "I'm anxious about deadlines",
            "My goal is to become a data scientist",
            "How can you help me?"  # The critical test message
        ]
        
        print("Sending messages to AI:")
        print("-" * 80)
        
        responses = []
        for i, message in enumerate(test_messages, 1):
            print(f"\n{i}. USER: {message}")
            
            response = self.send_message(message)
            
            if response:
                print(f"   AI: {response[:150]}...")
                responses.append((message, response))
                time.sleep(1)  # Brief pause between messages
            else:
                print(f"   ERROR: No response received")
                return False
        
        # Analyze final response
        print("\n" + "="*80)
        print("ANALYSIS OF FINAL RESPONSE")
        print("="*80)
        
        final_response = responses[-1][1].lower()
        
        # Check for context usage
        checks = {
            "Mentions stress": any(word in final_response for word in ['stress', 'stressed']),
            "Mentions worry": any(word in final_response for word in ['worry', 'worried', 'anxious', 'anxiety']),
            "Mentions goal": any(phrase in final_response for phrase in ['data scientist', 'goal', 'your goal']),
            "Empathetic": any(word in final_response for word in ['understand', 'see', 'know', 'realize']),
            "Acknowledges feelings": any(word in final_response for word in ['feeling', 'feel', 'emotions']),
        }
        
        print("\nContext Usage Checks:")
        for check, passed in checks.items():
            status = "✓" if passed else "✗"
            print(f"  {status} {check}: {'YES' if passed else 'NO'}")
        
        passed_count = sum(checks.values())
        total_count = len(checks)
        
        print(f"\nScore: {passed_count}/{total_count} checks passed")
        
        if passed_count >= 3:
            print("\n✓ PASS: AI appears to be using explicit context")
            print("  The AI response acknowledges the user's emotional state and/or goals.")
            return True
        else:
            print("\n✗ FAIL: AI may not be using explicit context")
            print("  The AI response doesn't clearly acknowledge user's emotions or goals.")
            print("\n  MANUAL REVIEW NEEDED:")
            print(f"\n  Full Response:\n  {responses[-1][1]}")
            return False
    
    def run_test(self):
        """Run the live AI integration test"""
        print("\n" + "="*80)
        print("PRE-TEST CHECKLIST")
        print("="*80)
        print("\n1. Is the app running? (python app.py)")
        print("2. Can you access http://localhost:5000?")
        print("3. Do you have AI credits available?")
        
        input("\nPress ENTER to start the test...")
        
        try:
            result = self.test_context_awareness()
            
            print("\n" + "="*80)
            print("TEST COMPLETE")
            print("="*80)
            
            if result:
                print("\n✓ AI is using explicit context correctly!")
                print("  Context extraction → AI prompt → AI response is working end-to-end.")
            else:
                print("\n⚠ Manual verification needed.")
                print("  Please review the AI response above and check if it:")
                print("  - Acknowledges the user's stress/worry/anxiety")
                print("  - Mentions the user's goal (data scientist)")
                print("  - Shows empathy or understanding")
            
            return result
            
        except Exception as e:
            print(f"\n✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    tester = LiveAIIntegrationTest()
    success = tester.run_test()
    sys.exit(0 if success else 1)
