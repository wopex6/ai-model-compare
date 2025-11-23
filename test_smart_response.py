#!/usr/bin/env python3
"""
Test Script for Smart Response System
Demonstrates how the system learns and adapts
"""

import sqlite3
from smart_response.handler import SmartResponseHandler
from pathlib import Path

def test_smart_response():
    """Test the smart response system"""
    print("=" * 80)
    print("SMART RESPONSE SYSTEM TEST")
    print("=" * 80)
    print()
    
    # Connect to database
    db_path = Path(__file__).parent / 'integrated_users.db'
    conn = sqlite3.connect(db_path)
    
    # Initialize handler
    handler = SmartResponseHandler(conn)
    
    # Test user ID (use a test user)
    test_user_id = 1
    character = 'coach'
    
    print(f"Testing with user_id={test_user_id}, character={character}")
    print()
    
    # Test cases
    test_messages = [
        ("hi", "greeting"),
        ("thanks for your help", "thanks"),
        ("I'm struggling with my motivation and feel lost about my goals", "complex"),
        ("ok", "acknowledgment"),
        ("that's interesting", "borderline"),
        ("yes", "agreement"),
        ("bye", "farewell"),
        ("how can I improve my productivity?", "complex"),
        ("got it", "acknowledgment"),
        ("thank you", "thanks"),
    ]
    
    print("🧪 Processing test messages...")
    print()
    
    for i, (message, expected_type) in enumerate(test_messages, 1):
        print(f"Test {i}: \"{message}\"")
        print("-" * 60)
        
        # Process message
        response_type, response_data = handler.process_message(
            test_user_id, message, character
        )
        
        print(f"   Response type: {response_type}")
        print(f"   Confidence: {response_data['confidence']:.2f}")
        
        if response_type == 'quick_reply':
            print(f"   Quick reply: \"{response_data['text']}\"")
        else:
            print(f"   → Sending to full AI")
        
        print(f"   Reasoning: {', '.join(response_data['reasoning'][:2])}")
        
        # Simulate tracking (for learning)
        # In real usage, this would be called after user responds
        handler.track_response(
            test_user_id,
            message,
            response_type,
            character,
            user_followup=None,  # Would be user's next message
            time_to_followup=None
        )
        
        print()
    
    # Show user stats
    print("=" * 80)
    print("USER LEARNING PROFILE")
    print("=" * 80)
    
    stats = handler.get_user_stats(test_user_id)
    
    print(f"Interactions: {stats['interaction_count']}")
    print(f"Quick reply rate: {stats['quick_reply_rate']:.1%}")
    print(f"Success rate: {stats['success_rate']:.1%}")
    print(f"Current threshold: {stats['threshold']:.2f}")
    print(f"Prefers detailed: {stats['prefer_detailed']}")
    
    if stats['character_preferences']:
        print("\nCharacter preferences:")
        for char, pref in stats['character_preferences'].items():
            print(f"   {char}: {pref:.2f}")
    
    print()
    print("✅ Test complete!")
    print()
    
    conn.close()

if __name__ == "__main__":
    test_smart_response()
