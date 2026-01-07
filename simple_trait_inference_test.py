"""
Simple Trait Inference Test
Just call the trait inference engine directly
"""

from integrated_database import IntegratedDatabase
from smart_response.trait_inference import TraitInferenceEngine

print("=" * 80)
print("SIMPLE TRAIT INFERENCE TEST")
print("=" * 80)
print()

print("📦 Initializing...")
db = IntegratedDatabase()
trait_engine = TraitInferenceEngine(db)
user_id = 23  # User with conversation history

print("✅ Initialized")
print()

# Check current conversation history
conn = db.get_connection()
cursor = conn.cursor()

cursor.execute('''
    SELECT COUNT(*) FROM history_primary 
    WHERE user_id = ?
''', (user_id,))

message_count = cursor.fetchone()[0]
print(f"📊 Found {message_count} messages in conversation history")
print()

if message_count == 0:
    print("⚠️  No messages found - trait inference needs conversation data")
    print("   You need to chat with the AI first!")
    print()
    print("   How to generate messages:")
    print("   1. Visit http://localhost:5000/chatchat")
    print("   2. Send 10-15 messages to any character")
    print("   3. Run this test again")
    conn.close()
    exit(0)

print(f"✅ Good! {message_count} messages available for analysis")
print()

# Check if inference should run
should_run = trait_engine.should_run_inference(user_id)
print(f"🔍 Should run inference: {should_run}")
print()

# Run inference
print("🚀 Running trait inference...")
print()

try:
    result = trait_engine.run_inference_if_needed(user_id)
    
    if result:
        print("✅ TRAIT INFERENCE SUCCESSFUL!")
        print()
        print("📊 Results:")
        print(f"   Confidence: {result['confidence']:.2f} ({int(result['confidence']*100)}%)")
        print(f"   Message count: {result.get('message_count', 'N/A')}")
        print()
        
        # Check database
        cursor.execute('''
            SELECT openness, conscientiousness, extraversion, agreeableness, neuroticism,
                   confidence, message_count, last_updated
            FROM inferred_personality
            WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        
        if row:
            print("✅ Traits saved to database!")
            print()
            print("📊 Inferred Personality Profile:")
            print(f"   Openness:          {row[0]:.2f} ({int(row[0]*100)}%)")
            print(f"   Conscientiousness: {row[1]:.2f} ({int(row[1]*100)}%)")
            print(f"   Extraversion:      {row[2]:.2f} ({int(row[2]*100)}%)")
            print(f"   Agreeableness:     {row[3]:.2f} ({int(row[3]*100)}%)")
            print(f"   Neuroticism:       {row[4]:.2f} ({int(row[4]*100)}%)")
            print()
            print(f"   Confidence:        {row[5]:.2f}")
            print(f"   Message count:     {row[6]}")
            print(f"   Last updated:      {row[7]}")
            print()
            print("=" * 80)
            print("✅ TEST COMPLETE - TRAIT INFERENCE WORKING!")
            print("=" * 80)
        else:
            print("❌ Traits not saved to database")
    else:
        print("⚠️  Inference returned no result")
        print("   This might mean:")
        print("   - Not enough messages (need 10+)")
        print("   - Inference already run recently")
        print("   - Messages don't contain personality signals")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

finally:
    conn.close()
