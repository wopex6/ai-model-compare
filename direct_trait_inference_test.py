"""
Direct Trait Inference Test
Tests trait inference engine directly without HTTP
"""

from integrated_database import IntegratedDatabase
from smart_response.trait_inference import TraitInferenceEngine
import time

# Test messages (MIXED_PROFILE from TEST_MESSAGES.txt)
TEST_MESSAGES = [
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
    "I feel anxious when things are uncertain.",
    "Let me imagine some different scenarios here.",
    "I tend to procrastinate when I'm not motivated."
]

def print_section(title):
    """Print section header"""
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)
    print()

def check_inferred_traits(db, user_id):
    """Check current inferred traits"""
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

def simulate_conversation(db, trait_engine, user_id, messages):
    """Simulate a conversation by adding messages"""
    
    character = 'coach'
    
    for i, message in enumerate(messages, 1):
        # Store user message
        db.store_user_message(
            user_id=user_id,
            character=character,
            message=message
        )
        
        # Store AI response (simulated)
        ai_response = "I understand. Let me help you with that."
        db.store_ai_message(
            user_id=user_id,
            character=character,
            message=ai_response
        )
        
        print(f"[{i}/{len(messages)}] User: {message[:60]}...")
        
        # Run inference after every 5 messages
        if i % 5 == 0:
            print(f"   🔍 Running trait inference...")
            result = trait_engine.run_inference_if_needed(user_id)
            if result:
                print(f"   ✅ Inference updated: confidence={result['confidence']:.2f}")
            else:
                print(f"   ⏭️  Inference skipped (not enough messages)")

def main():
    print_section("DIRECT TRAIT INFERENCE TEST")
    
    # Initialize
    print("📦 Initializing database and trait engine...")
    db = IntegratedDatabase()
    trait_engine = TraitInferenceEngine(db)
    user_id = 1  # Wai Tse
    print("✅ Initialized")
    
    # Check initial state
    print_section("INITIAL STATE")
    traits = check_inferred_traits(db, user_id)
    
    if traits:
        print("📊 Existing inferred traits found:")
        print(f"   Message count: {traits['message_count']}")
        print(f"   Confidence: {traits['confidence']:.2f}")
        print(f"   Last updated: {traits['last_updated']}")
    else:
        print("📭 No inferred traits yet")
    
    # Simulate conversation
    print_section(f"SIMULATING CONVERSATION ({len(TEST_MESSAGES)} messages)")
    print("Sending test messages from MIXED_PROFILE...")
    print()
    
    simulate_conversation(db, trait_engine, user_id, TEST_MESSAGES)
    
    # Force final inference
    print()
    print("🔍 Running final trait inference...")
    result = trait_engine.run_inference_if_needed(user_id, force=True)
    
    if result:
        print(f"✅ Final inference completed: confidence={result['confidence']:.2f}")
    
    # Check final state
    print_section("FINAL RESULTS")
    traits = check_inferred_traits(db, user_id)
    
    if traits:
        print("✅ TRAIT INFERENCE WORKING!")
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
        
        print("📋 Expected (MIXED_PROFILE):")
        print("   Openness:          60-70% (creative, curious)")
        print("   Conscientiousness: 45-55% (mixed)")
        print("   Extraversion:      50-60% (balanced)")
        print("   Agreeableness:     55-65% (caring but direct)")
        print("   Neuroticism:       50-60% (some stress)")
        print("   Confidence:        50-60%")
        print()
        
        # Compare
        print("📊 Analysis:")
        if 0.60 <= traits['openness'] <= 0.70:
            print("   ✅ Openness in expected range")
        else:
            print(f"   ⚠️  Openness {traits['openness']:.2f} outside expected 0.60-0.70")
            
        if 0.45 <= traits['conscientiousness'] <= 0.55:
            print("   ✅ Conscientiousness in expected range")
        else:
            print(f"   ⚠️  Conscientiousness {traits['conscientiousness']:.2f} outside expected 0.45-0.55")
            
        if 0.50 <= traits['extraversion'] <= 0.60:
            print("   ✅ Extraversion in expected range")
        else:
            print(f"   ⚠️  Extraversion {traits['extraversion']:.2f} outside expected 0.50-0.60")
            
        if 0.55 <= traits['agreeableness'] <= 0.65:
            print("   ✅ Agreeableness in expected range")
        else:
            print(f"   ⚠️  Agreeableness {traits['agreeableness']:.2f} outside expected 0.55-0.65")
            
        if 0.50 <= traits['neuroticism'] <= 0.60:
            print("   ✅ Neuroticism in expected range")
        else:
            print(f"   ⚠️  Neuroticism {traits['neuroticism']:.2f} outside expected 0.50-0.60")
            
        print_section("✅ TEST COMPLETE")
        
    else:
        print("❌ TRAIT INFERENCE FAILED - No traits found")
        print_section("❌ TEST FAILED")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print()
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
