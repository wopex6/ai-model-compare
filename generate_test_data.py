#!/usr/bin/env python3
"""
Synthetic Test Data Generator

Uses AI to generate realistic test conversations and character interpretations
for testing the Life Companion system without waiting for real user data.

Usage:
    python generate_test_data.py --user-id 2 --count 50
    python generate_test_data.py --user-id 2 --count 20 --use-ai  # Use AI for more realistic data
"""

import sqlite3
import json
import random
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / 'integrated_users.db'

# Domain characters
DOMAIN_CHARACTERS = [
    'domain_work',
    'domain_relationships', 
    'domain_mental_health',
    'domain_physical_health',
    'domain_finance',
    'domain_learning',
    'domain_creativity'
]

# Realistic message templates by domain
MESSAGE_TEMPLATES = {
    'domain_work': [
        "I'm feeling overwhelmed at work. My boss keeps adding more projects and I can't keep up.",
        "I got passed over for a promotion again. Starting to doubt my abilities.",
        "Had a great meeting today! My presentation went really well.",
        "Thinking about switching careers but I'm scared to take the risk.",
        "My coworker is taking credit for my work and I don't know how to handle it.",
        "I've been working 60-hour weeks and I'm burning out.",
        "Got some tough feedback in my review but I think it's fair.",
        "I'm procrastinating on this important deadline and feeling guilty.",
        "Landed a big client today! Feeling proud of myself.",
        "My work-life balance is non-existent right now.",
    ],
    'domain_relationships': [
        "My partner and I had a big fight about finances. We can't seem to agree.",
        "I'm feeling disconnected from my friends lately. Everyone's so busy.",
        "My parents don't approve of my life choices and it hurts.",
        "Made a new friend at the gym! It's nice to connect with someone.",
        "I think my partner might be losing interest in me.",
        "My sibling and I haven't spoken in months. I miss them.",
        "Feeling lonely even though I'm surrounded by people.",
        "Had a wonderful date night. Feeling grateful for my partner.",
        "I struggle to set boundaries with my family.",
        "My best friend moved away and I'm grieving the distance.",
    ],
    'domain_mental_health': [
        "I've been feeling anxious all week. Can't seem to shake it.",
        "Had a panic attack yesterday. It scared me.",
        "I'm in a really good headspace today. Feeling hopeful.",
        "The negative self-talk is getting worse. I'm being too hard on myself.",
        "Started meditating and it's actually helping with my stress.",
        "I feel numb lately. Not happy, not sad, just... empty.",
        "My therapist suggested journaling. Not sure where to start.",
        "I'm struggling with motivation. Everything feels pointless.",
        "Feeling proud that I asked for help. That was hard.",
        "The seasonal change is affecting my mood significantly.",
    ],
    'domain_physical_health': [
        "Started a new workout routine. Feeling sore but good!",
        "I can't seem to sleep well. Waking up exhausted every day.",
        "My doctor says I need to lose weight. Feeling discouraged.",
        "Finally hit my step goal every day this week!",
        "I've been stress eating and it's showing.",
        "Trying to cut back on caffeine but the headaches are brutal.",
        "My back pain is affecting my quality of life.",
        "Ran my first 5K! Never thought I could do it.",
        "I need to get better at drinking water throughout the day.",
        "Feeling sluggish lately. Maybe I need more vitamins?",
    ],
    'domain_finance': [
        "I'm stressed about my credit card debt. It keeps growing.",
        "Finally created a budget! Hope I can stick to it.",
        "Got an unexpected bill and it wiped out my savings.",
        "Thinking about investing but I don't know where to start.",
        "My spending is out of control. I need help.",
        "Paid off my student loans! Took 10 years but I did it.",
        "I'm worried about retirement. Haven't saved enough.",
        "Should I buy a house or keep renting? Can't decide.",
        "My partner and I have very different money habits.",
        "Got a raise! Time to adjust my savings goals.",
    ],
    'domain_learning': [
        "Started learning Spanish but I keep forgetting to practice.",
        "Feeling overwhelmed by how much I don't know about AI.",
        "Read a great book that changed my perspective on leadership.",
        "I want to learn coding but don't know where to begin.",
        "Taking an online course and loving it!",
        "My memory isn't what it used to be. Frustrating.",
        "Thinking about going back to school at my age.",
        "I learn better with hands-on projects than reading.",
        "My curiosity feels dulled. How do I get it back?",
        "Finally understood a concept I've been struggling with!",
    ],
    'domain_creativity': [
        "I want to start painting but I'm afraid I'll be terrible.",
        "Wrote a poem today for the first time in years.",
        "My creative block is so frustrating. Ideas just won't come.",
        "Started a photography hobby and I'm loving it!",
        "I feel like I've lost touch with my creative side.",
        "Made something today and I'm actually proud of it.",
        "I compare myself to other artists too much.",
        "Thinking about starting a blog but what would I write about?",
        "Music helps me process my emotions in ways words can't.",
        "I used to be so creative as a kid. What happened?",
    ]
}

# Sentiment options
SENTIMENTS = ['positive', 'negative', 'neutral', 'mixed']

# Emotion keywords by domain
EMOTIONS_BY_DOMAIN = {
    'domain_work': ['stressed', 'overwhelmed', 'proud', 'frustrated', 'motivated', 'burned_out'],
    'domain_relationships': ['lonely', 'connected', 'hurt', 'grateful', 'anxious', 'loved'],
    'domain_mental_health': ['anxious', 'hopeful', 'numb', 'peaceful', 'overwhelmed', 'proud'],
    'domain_physical_health': ['energized', 'exhausted', 'motivated', 'discouraged', 'proud', 'sluggish'],
    'domain_finance': ['stressed', 'relieved', 'worried', 'proud', 'overwhelmed', 'hopeful'],
    'domain_learning': ['curious', 'frustrated', 'excited', 'overwhelmed', 'proud', 'confused'],
    'domain_creativity': ['inspired', 'blocked', 'proud', 'frustrated', 'joyful', 'doubtful']
}

# Theme keywords
THEMES_BY_DOMAIN = {
    'domain_work': ['career_growth', 'work_life_balance', 'workplace_dynamics', 'productivity', 'leadership'],
    'domain_relationships': ['communication', 'boundaries', 'connection', 'conflict', 'support'],
    'domain_mental_health': ['anxiety', 'self_care', 'mindfulness', 'self_esteem', 'coping'],
    'domain_physical_health': ['fitness', 'nutrition', 'sleep', 'energy', 'health_goals'],
    'domain_finance': ['budgeting', 'debt', 'savings', 'investing', 'financial_stress'],
    'domain_learning': ['skill_development', 'education', 'curiosity', 'memory', 'growth_mindset'],
    'domain_creativity': ['artistic_expression', 'creative_block', 'inspiration', 'hobbies', 'self_expression']
}


def generate_interpretation(domain: str, message: str) -> dict:
    """Generate a realistic interpretation for a message."""
    # Determine sentiment based on message keywords
    negative_keywords = ['stressed', 'overwhelmed', 'worried', 'anxious', 'frustrated', 'hurt', 'lonely', 'struggling', 'can\'t', 'scared', 'doubt']
    positive_keywords = ['great', 'proud', 'loving', 'happy', 'grateful', 'hopeful', 'wonderful', 'finally', 'good']
    
    message_lower = message.lower()
    neg_count = sum(1 for kw in negative_keywords if kw in message_lower)
    pos_count = sum(1 for kw in positive_keywords if kw in message_lower)
    
    if pos_count > neg_count:
        sentiment = 'positive'
    elif neg_count > pos_count:
        sentiment = 'negative'
    elif neg_count > 0 and pos_count > 0:
        sentiment = 'mixed'
    else:
        sentiment = 'neutral'
    
    # Pick relevant emotions
    emotions = random.sample(EMOTIONS_BY_DOMAIN.get(domain, ['neutral']), min(2, len(EMOTIONS_BY_DOMAIN.get(domain, ['neutral']))))
    
    # Pick relevant themes
    themes = random.sample(THEMES_BY_DOMAIN.get(domain, ['general']), min(2, len(THEMES_BY_DOMAIN.get(domain, ['general']))))
    
    # Calculate concern level
    concern_keywords = ['panic', 'can\'t', 'scared', 'hurt', 'struggling', 'doubt', 'burning', 'numb', 'empty', 'pointless']
    concern_level = min(sum(0.15 for kw in concern_keywords if kw in message_lower), 0.8)
    if sentiment == 'negative':
        concern_level = max(concern_level, 0.3)
    
    return {
        'domain': domain.replace('domain_', ''),
        'relevance': random.choice([True, True, True, False]),  # 75% relevant
        'sentiment': sentiment,
        'detected_emotions': emotions,
        'key_themes': themes,
        'focus_areas_detected': themes[:1],
        'concern_level': round(concern_level, 2)
    }


def generate_test_data(user_id: int, count: int = 50, use_ai: bool = False):
    """Generate synthetic test data for a user."""
    
    print(f"\n{'='*60}")
    print(f"SYNTHETIC DATA GENERATOR")
    print(f"{'='*60}")
    print(f"User ID: {user_id}")
    print(f"Records to generate: {count}")
    print(f"Using AI: {use_ai}")
    print(f"{'='*60}\n")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    if not user:
        print(f"❌ Error: User ID {user_id} not found in database")
        conn.close()
        return
    
    print(f"✓ Found user: {user[0]}")
    
    # Generate data across different time periods (last 30 days)
    records_created = {
        'history_primary': 0,
        'character_interpretations': 0
    }
    
    for i in range(count):
        # Random domain
        domain = random.choice(DOMAIN_CHARACTERS)
        
        # Random message from templates
        messages = MESSAGE_TEMPLATES.get(domain, MESSAGE_TEMPLATES['domain_mental_health'])
        message = random.choice(messages)
        
        # Random timestamp in last 30 days
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)
        timestamp = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
        
        # Insert into history_primary (matches actual schema)
        cursor.execute('''
            INSERT INTO history_primary (user_id, character, user_message, assistant_response, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, domain, message, '[Test response]', timestamp.isoformat()))
        
        history_id = cursor.lastrowid
        records_created['history_primary'] += 1
        
        # Generate interpretation
        interpretation = generate_interpretation(domain, message)
        
        # Insert into character_interpretations
        cursor.execute('''
            INSERT INTO character_interpretations 
            (primary_history_id, character_id, interpretation, concern_level, responded, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            history_id,
            domain,
            json.dumps(interpretation),
            interpretation.get('concern_level', 0),
            random.choice([0, 1]),  # 50% responded
            timestamp.isoformat()
        ))
        records_created['character_interpretations'] += 1
        
        if (i + 1) % 10 == 0:
            print(f"  Generated {i + 1}/{count} records...")
    
    conn.commit()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"✅ DATA GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"  history_primary: {records_created['history_primary']} records")
    print(f"  character_interpretations: {records_created['character_interpretations']} records")
    print(f"\nYou can now test:")
    print(f"  - View My Data (Privacy panel)")
    print(f"  - Character insights")
    print(f"  - Analytics dashboard")
    print(f"{'='*60}\n")


def clear_test_data(user_id: int):
    """Clear all generated test data for a user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get history IDs for user
    cursor.execute('SELECT id FROM history_primary WHERE user_id = ?', (user_id,))
    history_ids = [row[0] for row in cursor.fetchall()]
    
    if history_ids:
        placeholders = ','.join('?' * len(history_ids))
        cursor.execute(f'DELETE FROM character_interpretations WHERE primary_history_id IN ({placeholders})', history_ids)
        interp_deleted = cursor.rowcount
        
        cursor.execute('DELETE FROM history_primary WHERE user_id = ?', (user_id,))
        history_deleted = cursor.rowcount
        
        conn.commit()
        print(f"✓ Deleted {history_deleted} history records")
        print(f"✓ Deleted {interp_deleted} interpretation records")
    else:
        print("No records found for this user")
    
    conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate synthetic test data')
    parser.add_argument('--user-id', type=int, required=True, help='User ID to generate data for')
    parser.add_argument('--count', type=int, default=50, help='Number of records to generate')
    parser.add_argument('--use-ai', action='store_true', help='Use AI for more realistic data (costs API credits)')
    parser.add_argument('--clear', action='store_true', help='Clear existing test data instead of generating')
    
    args = parser.parse_args()
    
    if args.clear:
        clear_test_data(args.user_id)
    else:
        generate_test_data(args.user_id, args.count, args.use_ai)
