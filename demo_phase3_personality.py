"""
Phase 3 Personality Integration - Visual Demo
Demonstrates how the same message is interpreted differently based on personality
"""

import sqlite3
from smart_response.personality_interpreter import PersonalityAwareContextInterpreter
from smart_response.explicit_context_handler import ExplicitContextHandler
from smart_response.conversation_context import ConversationContextManager

print("="*80)
print("PHASE 3: PERSONALITY INTERPRETATION - VISUAL DEMO")
print("="*80)
print()
print("This demo shows how the SAME user message is interpreted DIFFERENTLY")
print("based on the user's personality traits.")
print()

# Initialize systems
conn = sqlite3.connect('integrated_users.db')
interpreter = PersonalityAwareContextInterpreter()

# Demo scenarios: Same message, different personalities
test_message = "I'm feeling stressed about my project deadline"

print("="*80)
print("TEST MESSAGE:")
print(f'  "{test_message}"')
print("="*80)
print()

# Create test personalities
personalities = [
    {
        'name': 'Alex (Perfectionist)',
        'traits': {
            'neuroticism': 0.85,
            'conscientiousness': 0.90,
            'openness': 0.60,
            'extraversion': 0.40,
            'agreeableness': 0.70
        },
        'description': 'High-achieving perfectionist, very organized, self-critical'
    },
    {
        'name': 'Jordan (Resilient Doer)',
        'traits': {
            'neuroticism': 0.25,
            'conscientiousness': 0.80,
            'openness': 0.65,
            'extraversion': 0.60,
            'agreeableness': 0.65
        },
        'description': 'Calm under pressure, practical problem-solver'
    },
    {
        'name': 'Sam (Overwhelmed Creative)',
        'traits': {
            'neuroticism': 0.80,
            'conscientiousness': 0.35,
            'openness': 0.85,
            'extraversion': 0.50,
            'agreeableness': 0.75
        },
        'description': 'Creative but scattered, feels overwhelmed easily'
    },
    {
        'name': 'Casey (Laid-back Explorer)',
        'traits': {
            'neuroticism': 0.30,
            'conscientiousness': 0.40,
            'openness': 0.80,
            'extraversion': 0.70,
            'agreeableness': 0.60
        },
        'description': 'Easy-going, adaptable, goes with the flow'
    }
]

# Function to manually interpret with specific traits
def interpret_with_traits(message, traits):
    """Manually run interpretation with specific trait values"""
    interpreter_instance = PersonalityAwareContextInterpreter()
    
    # Directly call the stress interpretation method
    return interpreter_instance._interpret_stress_event(message, traits)

# Show interpretations for each personality
for i, person in enumerate(personalities, 1):
    print(f"\n{'='*80}")
    print(f"PERSON {i}: {person['name']}")
    print(f"{'='*80}")
    print()
    
    # Show personality traits
    print("Personality Profile:")
    print(f"  Neuroticism (emotional sensitivity): {person['traits']['neuroticism']:.0%}")
    print(f"  Conscientiousness (organized):       {person['traits']['conscientiousness']:.0%}")
    print(f"  Openness (creative):                  {person['traits']['openness']:.0%}")
    print(f"  Extraversion (social):                {person['traits']['extraversion']:.0%}")
    print(f"  Agreeableness (cooperative):          {person['traits']['agreeableness']:.0%}")
    print()
    print(f"Description: {person['description']}")
    print()
    
    # Get interpretation
    interpretation = interpret_with_traits(test_message.lower(), person['traits'])
    
    # Display interpretation
    print("-" * 80)
    print("SYSTEM'S INTERPRETATION:")
    print("-" * 80)
    print()
    print(f"  Interpreted Meaning:")
    print(f"    '{interpretation['interpreted_meaning']}'")
    print()
    print(f"  Emotional Impact:")
    print(f"    {interpretation['emotional_impact']}")
    print()
    print(f"  Recommended Approach:")
    print(f"    {interpretation['recommended_approach']}")
    print()
    print(f"  Guidance for AI:")
    print(f"    {interpretation['guidance']}")
    print()
    print(f"  Confidence: {interpretation['confidence']:.0%}")
    print()

# Summary comparison
print("\n" + "="*80)
print("SUMMARY: HOW PERSONALITY AFFECTS INTERPRETATION")
print("="*80)
print()
print("Same message: 'I'm feeling stressed about my project deadline'")
print()
print("DIFFERENT INTERPRETATIONS:")
print()

for i, person in enumerate(personalities, 1):
    interpretation = interpret_with_traits(test_message.lower(), person['traits'])
    print(f"{i}. {person['name']}:")
    print(f"   Meaning: {interpretation['interpreted_meaning']}")
    print(f"   Approach: {interpretation['recommended_approach']}")
    print()

# Demonstrate integration with context extraction
print("="*80)
print("INTEGRATION TEST: Full Context Flow")
print("="*80)
print()

handler = ExplicitContextHandler(conn)

print("Simulating user message processing...")
print()
print(f"User message: '{test_message}'")
print()

# Extract explicit context (which triggers personality interpretation)
extracted = handler.extract_explicit_context(
    user_id=1,
    character='Coach Max',
    message=test_message
)

if extracted:
    print(f"Extracted {len(extracted)} context item(s):")
    for item in extracted:
        print()
        print(f"  Context Type: {item['type']}")
        print(f"  Value: {item['value']}")
        print(f"  Priority: {item['priority']}")
        
        if 'personality_interpretation' in item:
            print()
            print("  Personality Interpretation:")
            interp = item['personality_interpretation']
            print(f"    - Meaning: {interp['interpreted_meaning']}")
            print(f"    - Approach: {interp['recommended_approach']}")
            print(f"    - Source: {interp['personality_source']}")
            print(f"    - Confidence: {interp['confidence']:.0%}")

# Show how it appears in AI prompt
print()
print("="*80)
print("HOW IT APPEARS IN AI PROMPT")
print("="*80)
print()

context_mgr = ConversationContextManager(conn)
context = context_mgr.get_context_for_ai(1, 'Coach Max', [])
formatted = context_mgr.format_context_for_prompt(context)

if formatted:
    print("Context sent to AI:")
    print("-" * 80)
    print(formatted)
    print("-" * 80)
else:
    print("(No context to format - this is first message)")

conn.close()

print()
print("="*80)
print("DEMO COMPLETE")
print("="*80)
print()
print("Key Takeaways:")
print("  1. Same message → Different interpretations based on personality")
print("  2. System automatically detects and uses personality traits")
print("  3. AI receives personality-aware guidance in every response")
print("  4. Fully integrated into existing context extraction flow")
print()
print("Try it yourself:")
print("  - Chat with any character in the app")
print("  - System will interpret your messages through your personality lens")
print("  - AI responses will be tailored to your personality traits")
print()
