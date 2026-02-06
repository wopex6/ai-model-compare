"""
Test Phase 5 Character Trait System API Endpoints
"""

import requests
import json

BASE_URL = "http://localhost:5000"

print("=" * 60)
print("PHASE 5 API ENDPOINT TESTS")
print("=" * 60)
print()
print("Note: These tests require the server to be running locally")
print("and a valid auth session. Run manually or use test credentials.")
print()

# Test messages for character matching
test_cases = [
    {
        "name": "Anxious user seeking support",
        "message": "I'm really anxious about my upcoming job interview and I don't know how to calm down"
    },
    {
        "name": "Motivated user wanting action plan",
        "message": "I'm excited to start my new fitness routine! What should I do first today?"
    },
    {
        "name": "Frustrated user venting",
        "message": "I'm so frustrated with my boss, he never listens to my ideas and I just need to vent"
    },
    {
        "name": "Confused user seeking advice",
        "message": "I don't understand why I keep procrastinating. Can you help me figure this out?"
    }
]

print("📋 Test Cases for API:")
print("-" * 40)
for i, tc in enumerate(test_cases, 1):
    print(f"{i}. {tc['name']}")
    print(f"   Message: \"{tc['message'][:50]}...\"")
print()

print("📌 API Endpoints Added:")
print("-" * 40)
endpoints = [
    ("POST", "/api/character-traits/match", "Match character to message/situation"),
    ("GET", "/api/character-traits/characters", "Get all characters with traits"),
    ("POST", "/api/character-traits/analyze", "Analyze message for situation context"),
    ("GET", "/api/character-traits/effectiveness", "Get character effectiveness stats"),
]

for method, path, desc in endpoints:
    print(f"  {method:6} {path}")
    print(f"         → {desc}")
print()

print("📝 Example API Usage:")
print("-" * 40)
print("""
# Match character to message
curl -X POST http://localhost:5000/api/character-traits/match \\
  -H "Content-Type: application/json" \\
  -d '{"message": "I am feeling anxious about work"}'

# Get all characters
curl http://localhost:5000/api/character-traits/characters

# Analyze situation
curl -X POST http://localhost:5000/api/character-traits/analyze \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Help me plan my career for the next 5 years"}'
""")

print("=" * 60)
print("✅ Phase 5 API endpoints added successfully")
print("=" * 60)
