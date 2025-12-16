"""
Demo Script: Test All New Features
Run this to see how the new systems work.

Features demonstrated:
1. Mirror User Language
2. Proactive Clarification System
3. Character Trait System (12D matching)
4. Developer Analytics

Usage:
    python demo_features.py
"""

import sqlite3
import json
from datetime import datetime

# Connect to database
conn = sqlite3.connect('integrated_users.db')

print("=" * 60)
print("DEMO: New Features Testing")
print("=" * 60)

# =============================================================================
# 1. MIRROR USER LANGUAGE
# =============================================================================
print("\n" + "=" * 60)
print("1. MIRROR USER LANGUAGE")
print("=" * 60)

from smart_response.user_context_manager import RuleBasedExtractor, UserContextManager

extractor = RuleBasedExtractor()

test_messages = [
    "Hey! Call me Alex. I prefer brief answers.",
    "G'day mate, help me save some money",
    "Hi there, I'm really really stressed about work deadlines",
    "yo what's up, i need to figure out this budget thing",
]

print("\nExtracting language patterns from messages:")
for msg in test_messages:
    result = extractor.extract_all(msg)
    patterns = result['language_patterns']
    prefs = result['preferences']
    
    print(f"\n  Message: \"{msg}\"")
    if patterns:
        print(f"    Language patterns: {[(p.pattern_type, p.user_phrase) for p in patterns]}")
    if prefs:
        print(f"    Preferences: {[(p.fact_type, p.content) for p in prefs]}")

# Show what AI will see
print("\n\nWhat AI sees in system prompt (example):")
ucm = UserContextManager(conn)
sample_context = {
    'user_facts': [
        {'type': 'name_preference', 'content': 'Alex', 'priority': 'critical'},
        {'type': 'preference', 'content': 'brief answers', 'priority': 'critical'},
    ],
    'user_language': {
        'greeting': 'Hey',
        'preferred_length': 'brief',
        'sign_off': 'cheers',
        'emphasis_words': ['really', 'super'],
    },
    'conversation_summary': 'User is working on budgeting and time management.',
    'user_goals': ['save money', 'reduce stress']
}

formatted = ucm.format_context_for_prompt(sample_context)
print("-" * 40)
print(formatted)
print("-" * 40)

# =============================================================================
# 2. PROACTIVE CLARIFICATION SYSTEM
# =============================================================================
print("\n" + "=" * 60)
print("2. PROACTIVE CLARIFICATION SYSTEM")
print("=" * 60)

from smart_response.proactive_clarification import ProactiveClarificationSystem

clarification = ProactiveClarificationSystem(conn)

test_messages_clarity = [
    ("Help me with something", "Vague - should trigger questions"),
    ("I need to improve my budget by saving $500/month", "Clear - should NOT trigger"),
    ("I'm stressed", "Vague emotion - should trigger"),
    ("Help me create a plan to learn Python in 3 months", "Clear goal - should NOT trigger"),
    ("Maybe I should do that thing soon", "Very vague - multiple triggers"),
]

print("\nAnalyzing message clarity and generating questions:")
for msg, description in test_messages_clarity:
    confidence, questions = clarification.analyze_message(msg)
    
    print(f"\n  Message: \"{msg}\"")
    print(f"    ({description})")
    print(f"    Confidence: overall={confidence.overall:.2f}, goal={confidence.goal_clarity:.2f}, action={confidence.action_clarity:.2f}")
    print(f"    Needs clarification: {confidence.needs_clarification()}")
    
    if questions:
        print(f"    Questions to ask:")
        for q in questions[:2]:
            print(f"      - [{q.importance.value}] {q.question}")
            print(f"        (reason: {q.reason.value}, gap: {q.context_gap})")

# Show formatted output
print("\n\nFormatted clarification (appended to AI response):")
_, sample_questions = clarification.analyze_message("Help me with something soon")
formatted_q = clarification.format_clarification_for_response(sample_questions)
print("-" * 40)
print(f"[AI Response would go here...]{formatted_q}")
print("-" * 40)

# =============================================================================
# 3. CHARACTER TRAIT SYSTEM
# =============================================================================
print("\n" + "=" * 60)
print("3. CHARACTER TRAIT SYSTEM (12D Matching)")
print("=" * 60)

from smart_response.character_traits import CharacterTraitSystem, SituationAnalysis

trait_system = CharacterTraitSystem(conn)

print("\nAvailable characters and their traits:")
for char in trait_system.get_all_characters():
    traits = char.traits
    print(f"\n  {char.display_name} ({char.character_id})")
    print(f"    Domain: {char.domain}")
    print(f"    Key traits: empathy={traits.empathy:.1f}, directness={traits.directness:.1f}, "
          f"action={traits.action_oriented:.1f}, support={traits.supportiveness:.1f}")
    print(f"    Lens: \"{char.philosophical_lens[:60]}...\"" if len(char.philosophical_lens) > 60 
          else f"    Lens: \"{char.philosophical_lens}\"")

test_situations = [
    "I'm really stressed about my job interview tomorrow",
    "I just need to vent - my boss is so unfair!",
    "Help me create a detailed 6-month savings plan",
    "I'm excited! I got promoted! What should I do next?",
    "I feel lost and don't know what to do with my life",
]

print("\n\nMatching characters to situations:")
for msg in test_situations:
    situation = trait_system.analyze_situation(msg)
    best_char, score, reasoning = trait_system.match_character(situation)
    
    print(f"\n  Situation: \"{msg}\"")
    print(f"    Detected: emotion={situation.emotional_state}, goal={situation.goal_type}, "
          f"needs_validation={situation.needs_validation}")
    print(f"    Best match: {best_char.display_name} (score: {score:.0%})")
    print(f"    Reasoning: {reasoning[:80]}...")

# =============================================================================
# 4. DEVELOPER ANALYTICS
# =============================================================================
print("\n" + "=" * 60)
print("4. DEVELOPER ANALYTICS")
print("=" * 60)

from smart_response.developer_analytics import DeveloperAnalytics

dev_analytics = DeveloperAnalytics(conn)

print("\nSystem Metrics:")
metrics = dev_analytics.get_system_metrics()
for key, value in metrics.items():
    print(f"  {key}: {value}")

print("\nUser Context Analysis (aggregate):")
context_analysis = dev_analytics.get_user_context_analysis()
print(f"  Fact distribution: {context_analysis.get('fact_distribution', [])}")
print(f"  Top language patterns: {context_analysis.get('top_language_patterns', [])[:5]}")

print("\nDebug Info (tables):")
debug = dev_analytics.get_debug_info('database')
for table, count in list(debug.get('tables', {}).items())[:10]:
    print(f"  {table}: {count} rows")

# =============================================================================
# API ENDPOINTS FOR DEVELOPER
# =============================================================================
print("\n" + "=" * 60)
print("DEVELOPER API ENDPOINTS (requires 'developer' role)")
print("=" * 60)

endpoints = [
    ("GET", "/api/developer/metrics", "System-wide metrics"),
    ("GET", "/api/developer/ai-calls", "Detailed AI call logs"),
    ("GET", "/api/developer/user-context", "User context analysis"),
    ("GET", "/api/developer/character-effectiveness", "Character effectiveness"),
    ("GET", "/api/developer/clarification-stats", "Clarification stats"),
    ("GET", "/api/developer/export/<table>", "Export data (JSON/CSV)"),
    ("POST", "/api/developer/query", "Custom SELECT queries"),
    ("GET", "/api/developer/debug", "Debug information"),
    ("POST", "/api/developer/health-snapshot", "Take health snapshot"),
    ("GET", "/api/developer/health-history", "Health history"),
    ("GET", "/api/developer/access-log", "Audit trail"),
]

print("\nAvailable endpoints:")
for method, path, desc in endpoints:
    print(f"  {method:4} {path:40} - {desc}")

print("\n" + "=" * 60)
print("To use developer endpoints:")
print("  1. Login as admin")
print("  2. Go to Admin > Users > [Your user] > Change Role > 'developer'")
print("  3. Re-login")
print("  4. Access /api/developer/* endpoints")
print("=" * 60)

conn.close()
print("\n✅ Demo complete!")
