"""
Phase 3 Interactive Demo
Try different messages and see how personality affects interpretation
"""

import sqlite3
from smart_response.personality_interpreter import PersonalityAwareContextInterpreter

def display_interpretation(message, personality_name, traits):
    """Display interpretation for a message with given traits"""
    interpreter = PersonalityAwareContextInterpreter()
    
    # Classify event type
    event_type = interpreter._classify_event_type(message)
    
    # Get interpretation
    if event_type == 'stress':
        interpretation = interpreter._interpret_stress_event(message.lower(), traits)
    elif event_type == 'failure':
        interpretation = interpreter._interpret_failure_event(message.lower(), traits)
    elif event_type == 'success':
        interpretation = interpreter._interpret_success_event(message.lower(), traits)
    elif event_type == 'goal':
        interpretation = interpreter._interpret_goal_event(message.lower(), traits)
    elif event_type == 'relationship':
        interpretation = interpreter._interpret_relationship_event(message.lower(), traits)
    elif event_type == 'learning':
        interpretation = interpreter._interpret_learning_event(message.lower(), traits)
    else:
        interpretation = interpreter._interpret_general_event(message.lower(), traits)
    
    # Display results
    print(f"\n{'='*70}")
    print(f"AS {personality_name.upper()}")
    print(f"{'='*70}")
    print(f"\nEvent Type: {event_type}")
    print(f"\nInterpretation: {interpretation['interpreted_meaning']}")
    print(f"Emotional Impact: {interpretation['emotional_impact']}")
    print(f"Recommended Approach: {interpretation['recommended_approach']}")
    print(f"\nGuidance for AI Response:")
    print(f"  {interpretation['guidance']}")
    print(f"\nConfidence: {interpretation['confidence']:.0%}")

# Define personality archetypes
PERSONALITIES = {
    '1': {
        'name': 'Perfectionist',
        'traits': {
            'neuroticism': 0.85,
            'conscientiousness': 0.90,
            'openness': 0.60,
            'extraversion': 0.40,
            'agreeableness': 0.70
        }
    },
    '2': {
        'name': 'Resilient Doer',
        'traits': {
            'neuroticism': 0.25,
            'conscientiousness': 0.80,
            'openness': 0.65,
            'extraversion': 0.60,
            'agreeableness': 0.65
        }
    },
    '3': {
        'name': 'Overwhelmed Creative',
        'traits': {
            'neuroticism': 0.80,
            'conscientiousness': 0.35,
            'openness': 0.85,
            'extraversion': 0.50,
            'agreeableness': 0.75
        }
    },
    '4': {
        'name': 'Laid-back Explorer',
        'traits': {
            'neuroticism': 0.30,
            'conscientiousness': 0.40,
            'openness': 0.80,
            'extraversion': 0.70,
            'agreeableness': 0.60
        }
    }
}

# Suggested test messages
EXAMPLE_MESSAGES = [
    "I'm feeling stressed about my deadlines",
    "I failed my exam today",
    "I just got promoted at work!",
    "My goal is to become a better leader",
    "I'm having conflict with my team",
    "I'm struggling to understand this concept",
    "I feel overwhelmed and don't know where to start",
    "I'm so proud of what I accomplished today"
]

print("="*70)
print("PHASE 3: INTERACTIVE PERSONALITY INTERPRETATION DEMO")
print("="*70)
print()
print("See how the SAME message is interpreted differently based on")
print("the user's personality traits!")
print()

while True:
    print("\n" + "="*70)
    print("CHOOSE A MESSAGE TO TEST")
    print("="*70)
    print()
    print("Quick examples:")
    for i, msg in enumerate(EXAMPLE_MESSAGES, 1):
        print(f"  {i}. {msg}")
    print()
    print("Or type your own message, or 'quit' to exit")
    print()
    
    user_input = input("Enter number (1-8) or your message: ").strip()
    
    if user_input.lower() in ['quit', 'exit', 'q']:
        print("\nThanks for trying Phase 3! 🎉")
        break
    
    # Get message
    if user_input.isdigit() and 1 <= int(user_input) <= len(EXAMPLE_MESSAGES):
        message = EXAMPLE_MESSAGES[int(user_input) - 1]
    else:
        message = user_input
    
    if not message:
        continue
    
    print(f"\n{'='*70}")
    print(f"YOUR MESSAGE: '{message}'")
    print(f"{'='*70}")
    
    # Show all personality interpretations
    for key, person in PERSONALITIES.items():
        display_interpretation(message, person['name'], person['traits'])
    
    print(f"\n{'='*70}")
    print("COMPARE THE DIFFERENCES!")
    print(f"{'='*70}")
    print()
    print("Notice how the SAME message gets interpreted in 4 DIFFERENT ways")
    print("based on personality traits:")
    print()
    print("  1. Perfectionist     → More validation, structured support")
    print("  2. Resilient Doer    → Problem-solving focus, action-oriented")
    print("  3. Overwhelmed       → Emotional support first, then structure")
    print("  4. Laid-back         → Balanced, gentle guidance")
    print()
    
    input("Press Enter to try another message...")

print()
print("="*70)
print("KEY INSIGHT")
print("="*70)
print()
print("Phase 3 makes the AI truly UNDERSTAND the user by considering:")
print("  ✓ What they said (explicit context)")
print("  ✓ WHO they are (personality traits)")
print("  ✓ How to best support them (tailored approach)")
print()
print("Result: More effective, personalized coaching!")
print("="*70)
