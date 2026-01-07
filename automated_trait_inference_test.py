"""
Automated Trait Inference Test
Sends test messages from TEST_MESSAGES.txt to the chat API
"""

import requests
import time
import json

BASE_URL = "http://localhost:5000"
USER_ID = 1  # Wai Tse

# Test messages from TEST_MESSAGES.txt
TEST_SETS = {
    "HIGH_OPENNESS": [
        "I love trying new things and exploring new ideas!",
        "What if we approached this problem from a completely different angle?",
        "I'm really curious about how this works under the hood.",
        "Let me brainstorm some creative solutions here.",
        "I wonder what would happen if we combined these two concepts?",
        "I enjoy abstract thinking and philosophical discussions.",
        "That's an interesting perspective I hadn't considered before.",
        "I like to imagine different possibilities and scenarios.",
        "Tell me about some unconventional ways to solve this.",
        "I appreciate innovative and original approaches.",
        "What's the most creative solution you can think of?",
        "I'm open to exploring alternative methods here.",
        "Let's think outside the box on this one.",
        "I find novel ideas really exciting and inspiring.",
        "I prefer flexibility over strict routines most of the time."
    ],
    "MIXED_PROFILE": [
        "I'm feeling a bit stressed about this deadline.",
        "Let me plan out how to tackle this project step by step.",
        "I love brainstorming creative solutions!",
        "I forgot to follow up on that email, oops.",
        "I'm excited to meet with the team tomorrow.",
        "I need some quiet time alone to recharge after this.",
        "I really want to help you figure this out.",
        "Honestly, I disagree with that approach.",
        "I'm curious about trying a completely new method here.",
        "I prefer having a clear schedule and routine.",
        "Sometimes I worry about whether I'm doing enough.",
        "I think it's important to be direct and truthful.",
        "I enjoy exploring new ideas and possibilities.",
        "I need to organize my thoughts before our meeting.",
        "I feel anxious when things are uncertain."
    ]
}

def check_server():
    """Check if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=2)
        return response.status_code == 200
    except:
        return False

def send_message(character, message, user_id):
    """Send a chat message to the API"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "character": character,
                "message": message,
                "user_id": user_id
            },
            timeout=30
        )
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except Exception as e:
        return False, str(e)

def check_inferred_traits(user_id):
    """Check inferred traits from database"""
    from integrated_database import IntegratedDatabase
    db = IntegratedDatabase()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT openness, conscientiousness, extraversion, agreeableness, neuroticism,
               confidence, message_count, last_updated
        FROM inferred_personality
        WHERE user_id = ?
    ''', (user_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'openness': row[0],
            'conscientiousness': row[1],
            'extraversion': row[2],
            'agreeableness': row[3],
            'neuroticism': row[4],
            'confidence': row[5],
            'message_count': row[6],
            'last_updated': row[7]
        }
    return None

def run_test(test_name, messages, character="coach"):
    """Run a test set"""
    print("=" * 80)
    print(f"TEST: {test_name}")
    print("=" * 80)
    print()
    
    print(f"📝 Sending {len(messages)} messages to {character}...")
    print()
    
    success_count = 0
    
    for i, message in enumerate(messages, 1):
        print(f"[{i}/{len(messages)}] Sending: {message[:50]}...")
        
        success, response = send_message(character, message, USER_ID)
        
        if success:
            success_count += 1
            print(f"   ✅ Response received")
        else:
            print(f"   ❌ Failed: {response}")
        
        # Small delay between messages
        time.sleep(1)
    
    print()
    print(f"✅ Sent {success_count}/{len(messages)} messages successfully")
    print()
    
    # Check inferred traits
    print("🔍 Checking inferred traits...")
    traits = check_inferred_traits(USER_ID)
    
    if traits:
        print("✅ Traits found!")
        print()
        print("📊 Inferred Personality Profile:")
        print(f"   Openness:          {traits['openness']:.2f} ({int(traits['openness']*100)}%)")
        print(f"   Conscientiousness: {traits['conscientiousness']:.2f} ({int(traits['conscientiousness']*100)}%)")
        print(f"   Extraversion:      {traits['extraversion']:.2f} ({int(traits['extraversion']*100)}%)")
        print(f"   Agreeableness:     {traits['agreeableness']:.2f} ({int(traits['agreeableness']*100)}%)")
        print(f"   Neuroticism:       {traits['neuroticism']:.2f} ({int(traits['neuroticism']*100)}%)")
        print()
        print(f"   Confidence:        {traits['confidence']:.2f} ({int(traits['confidence']*100)}%)")
        print(f"   Message count:     {traits['message_count']}")
        print(f"   Last updated:      {traits['last_updated']}")
        print()
        
        return traits
    else:
        print("❌ No inferred traits found")
        return None


if __name__ == '__main__':
    print("=" * 80)
    print("AUTOMATED TRAIT INFERENCE TEST")
    print("=" * 80)
    print()
    
    # Check server
    print("🔍 Checking if server is running...")
    if not check_server():
        print("❌ Server not running at http://localhost:5000")
        print("   Please start server: python app.py")
        exit(1)
    
    print("✅ Server is running!")
    print()
    
    # Run MIXED_PROFILE test (more realistic)
    print("Running MIXED_PROFILE test (15 messages)...")
    print("This will take about 15-30 seconds...")
    print()
    
    traits = run_test("MIXED_PROFILE", TEST_SETS["MIXED_PROFILE"], character="coach")
    
    if traits:
        print()
        print("=" * 80)
        print("✅ TEST COMPLETE - TRAIT INFERENCE WORKING!")
        print("=" * 80)
        print()
        print("Expected for MIXED_PROFILE:")
        print("   Openness:          60-70%")
        print("   Conscientiousness: 45-55%")
        print("   Extraversion:      50-60%")
        print("   Agreeableness:     55-65%")
        print("   Neuroticism:       50-60% (some stress)")
        print("   Confidence:        50-60%")
    else:
        print()
        print("=" * 80)
        print("❌ TEST FAILED - NO TRAIT INFERENCE")
        print("=" * 80)
        print()
        print("Check server console for errors")
