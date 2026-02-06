"""
Test Character Trait System (Phase 5)
"""

import sqlite3
from smart_response.character_trait_system import CharacterTraitSystem

print("=" * 60)
print("CHARACTER TRAIT SYSTEM TEST")
print("=" * 60)
print()

# Initialize
print("📦 Initializing...")
conn = sqlite3.connect('integrated_users.db')
trait_system = CharacterTraitSystem(conn)
print()

# Test 1: Get all characters
print("📊 Test 1: Character Library")
print("-" * 40)
characters = trait_system.get_all_characters()
print(f"Total characters: {len(characters)}")
for char in characters:
    print(f"  • {char['display_name']} ({char['character_id']})")
print()

# Test 2: Analyze situation
print("📊 Test 2: Situation Analysis")
print("-" * 40)
test_messages = [
    "I'm feeling really anxious about my job interview tomorrow",
    "I want to build a morning routine that sticks",
    "Why do I keep procrastinating on important things?",
    "I'm so frustrated with my boss, I might quit",
    "I need help planning my career for the next 5 years",
]

for msg in test_messages:
    context = trait_system.analyze_situation(msg)
    print(f"Message: \"{msg[:50]}...\"")
    print(f"  → Emotional: {context['user_emotional_state']}")
    print(f"  → Goal: {context['goal_type']}")
    print(f"  → Challenge: {context['challenge_type']}")
    print(f"  → Domain: {context['domain']}")
    print()

# Test 3: Character matching
print("📊 Test 3: Character Matching")
print("-" * 40)

test_situations = [
    {
        'user_emotional_state': 'anxious',
        'goal_type': 'emotional_support',
        'challenge_type': 'emotional'
    },
    {
        'user_emotional_state': 'motivated',
        'goal_type': 'immediate_action',
        'challenge_type': 'practical'
    },
    {
        'user_emotional_state': 'confused',
        'goal_type': 'long_term_growth',
        'challenge_type': 'philosophical'
    },
]

for i, situation in enumerate(test_situations, 1):
    print(f"\nSituation {i}: {situation['user_emotional_state']} + {situation['goal_type']}")
    result = trait_system.find_best_character(situation)
    
    print(f"  Best match: {result['character']['display_name']}")
    print(f"  Score: {result['match_score']}")
    print(f"  Reasoning: {result['reasoning'][:80]}...")
    
    if result['alternatives']:
        alt_names = [a['display_name'] for a in result['alternatives'][:2]]
        print(f"  Alternatives: {', '.join(alt_names)}")

# Test 4: Full flow - message to character
print()
print("📊 Test 4: End-to-End Flow")
print("-" * 40)
test_msg = "I'm overwhelmed with work deadlines and don't know how to prioritize"
print(f"User message: \"{test_msg}\"")
print()

context = trait_system.analyze_situation(test_msg)
print(f"Analyzed context:")
print(f"  • Emotional state: {context['user_emotional_state']}")
print(f"  • Goal type: {context['goal_type']}")
print(f"  • Challenge: {context['challenge_type']}")
print(f"  • Domain: {context['domain']}")
print()

result = trait_system.find_best_character(context)
print(f"Recommended character: {result['character']['display_name']}")
print(f"Match score: {result['match_score']}")
print(f"Reasoning: {result['reasoning']}")
print()

# Summary
conn.close()
print("=" * 60)
print("✅ CHARACTER TRAIT SYSTEM TEST COMPLETE")
print("=" * 60)
