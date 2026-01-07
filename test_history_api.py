"""
Test the assessment history API endpoint
Simulates what the frontend receives
"""

from integrated_database import IntegratedDatabase

print("=" * 80)
print("SIMULATING API RESPONSE")
print("=" * 80)
print()

db = IntegratedDatabase()
user_id = 23

# Get history (as the API does)
history = db.get_assessment_history(user_id, limit=20)

print(f"Raw database response: {len(history)} items")
print()

# Flatten and normalize (as the updated API does)
flattened_history = []
for item in history:
    # Detect if values are on 0-10 scale (any value > 1.0)
    traits = item['traits']
    needs_normalization = any(v > 1.0 for v in traits.values())
    
    flat_item = {
        'id': item['id'],
        'completed_at': item['completed_at'],
        'openness': traits['openness'] / 10.0 if needs_normalization else traits['openness'],
        'conscientiousness': traits['conscientiousness'] / 10.0 if needs_normalization else traits['conscientiousness'],
        'extraversion': traits['extraversion'] / 10.0 if needs_normalization else traits['extraversion'],
        'agreeableness': traits['agreeableness'] / 10.0 if needs_normalization else traits['agreeableness'],
        'neuroticism': traits['neuroticism'] / 10.0 if needs_normalization else traits['neuroticism'],
    }
    
    print(f"Assessment {item['id']} ({item['completed_at']}):")
    print(f"  Normalized: {needs_normalization}")
    print(f"  O={flat_item['openness']:.2f}, C={flat_item['conscientiousness']:.2f}, " +
          f"E={flat_item['extraversion']:.2f}, A={flat_item['agreeableness']:.2f}, N={flat_item['neuroticism']:.2f}")
    print(f"  As percentages: O={flat_item['openness']*100:.0f}%, C={flat_item['conscientiousness']*100:.0f}%, " +
          f"E={flat_item['extraversion']*100:.0f}%, A={flat_item['agreeableness']*100:.0f}%, N={flat_item['neuroticism']*100:.0f}%")
    print()
    
    flattened_history.append(flat_item)

print("=" * 80)
print(f"✅ API would return {len(flattened_history)} assessments")
print("=" * 80)
print()

print("Chart will display:")
for i, item in enumerate(flattened_history, 1):
    print(f"{i}. {item['completed_at']}: O={item['openness']*100:.0f}% C={item['conscientiousness']*100:.0f}% " +
          f"E={item['extraversion']*100:.0f}% A={item['agreeableness']*100:.0f}% N={item['neuroticism']*100:.0f}%")
