"""
Synthetic Data Generator for Character Expansion & Effectiveness Testing

Generates realistic conversation outcomes, user feedback, and character usage
data across multiple users, situations, and time periods.

Design principles:
- Some situations have STRONG character coverage (high satisfaction)
- Some situations have WEAK coverage (low satisfaction) → triggers gap detection
- Usage frequency varies by situation → tests demand prioritization
- Data spans 60 days to test time-based analytics
"""

import sqlite3
import json
import random
import uuid
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# === Configuration ===

# Characters available in the system
CHARACTERS = ['stoic', 'coach', 'sage', 'therapist', 'strategist', 
              'cheerleader', 'mentor', 'realist']

# Situation types and their properties:
#   character_affinity: which characters handle this well
#   weak_characters: which characters struggle here
#   frequency: relative frequency (higher = more common)
#   base_satisfaction: baseline satisfaction (before character fit modifier)
SITUATIONS = {
    'career_guidance': {
        'character_affinity': ['coach', 'mentor', 'strategist'],
        'weak_characters': ['cheerleader', 'sage'],
        'frequency': 25,
        'base_satisfaction': 0.65,
    },
    'emotional': {
        'character_affinity': ['therapist', 'cheerleader'],
        'weak_characters': ['strategist', 'realist', 'stoic'],
        'frequency': 30,
        'base_satisfaction': 0.55,  # Hard situation → lower baseline
    },
    'relationship': {
        'character_affinity': ['therapist', 'cheerleader', 'mentor'],
        'weak_characters': ['strategist', 'stoic'],
        'frequency': 20,
        'base_satisfaction': 0.60,
    },
    'skill_development': {
        'character_affinity': ['coach', 'mentor', 'sage'],
        'weak_characters': ['cheerleader', 'therapist'],
        'frequency': 15,
        'base_satisfaction': 0.70,
    },
    'existential': {
        'character_affinity': ['sage', 'stoic'],
        'weak_characters': ['coach', 'cheerleader', 'strategist'],
        'frequency': 8,
        'base_satisfaction': 0.45,  # Very hard → poor coverage (should trigger gap)
    },
    'financial': {
        'character_affinity': ['strategist', 'realist'],
        'weak_characters': ['cheerleader', 'sage', 'therapist'],
        'frequency': 12,
        'base_satisfaction': 0.60,
    },
    'health': {
        'character_affinity': ['therapist', 'coach'],
        'weak_characters': ['realist', 'strategist'],
        'frequency': 10,
        'base_satisfaction': 0.50,  # Weak coverage (should trigger gap)
    },
    'creative': {
        'character_affinity': ['sage', 'mentor'],
        'weak_characters': ['realist', 'strategist', 'stoic'],
        'frequency': 6,
        'base_satisfaction': 0.40,  # Very weak coverage (should trigger gap)
    },
    'grief': {
        'character_affinity': ['therapist'],
        'weak_characters': ['coach', 'strategist', 'realist', 'cheerleader'],
        'frequency': 5,
        'base_satisfaction': 0.35,  # Worst coverage (should trigger gap)
    },
    'general': {
        'character_affinity': ['mentor', 'coach', 'therapist'],
        'weak_characters': [],
        'frequency': 20,
        'base_satisfaction': 0.65,
    },
}

# Simulated users
USERS = [
    {'id': 1, 'name': 'Wai Tse', 'preferred_chars': ['coach', 'mentor']},
    {'id': 2, 'name': 'Test User', 'preferred_chars': ['therapist', 'sage']},
    {'id': 3, 'name': 'Alex', 'preferred_chars': ['strategist', 'realist']},
    {'id': 4, 'name': 'Sam', 'preferred_chars': ['cheerleader', 'therapist']},
    {'id': 5, 'name': 'Jordan', 'preferred_chars': ['stoic', 'mentor']},
]

ENGAGEMENT_LEVELS = ['low', 'moderate', 'high', 'very_high']


def generate_satisfaction(situation_config, character_id):
    """Generate a realistic satisfaction score based on character-situation fit"""
    base = situation_config['base_satisfaction']
    
    if character_id in situation_config['character_affinity']:
        # Good fit: satisfaction boost
        satisfaction = base + random.uniform(0.15, 0.35)
    elif character_id in situation_config['weak_characters']:
        # Poor fit: satisfaction penalty
        satisfaction = base - random.uniform(0.10, 0.25)
    else:
        # Neutral fit: slight random variation
        satisfaction = base + random.uniform(-0.10, 0.10)
    
    # Add noise and clamp
    satisfaction += random.gauss(0, 0.05)
    return max(0.05, min(0.95, round(satisfaction, 3)))


def generate_engagement(satisfaction):
    """Derive engagement level from satisfaction"""
    if satisfaction > 0.7:
        return random.choice(['high', 'very_high'])
    elif satisfaction > 0.5:
        return random.choice(['moderate', 'high'])
    elif satisfaction > 0.3:
        return random.choice(['low', 'moderate'])
    else:
        return random.choice(['low', 'low', 'moderate'])


def generate_message_count(engagement):
    """Generate realistic message count based on engagement"""
    counts = {
        'low': (2, 4),
        'moderate': (4, 8),
        'high': (6, 14),
        'very_high': (10, 25),
    }
    low, high = counts.get(engagement, (3, 8))
    return random.randint(low, high)


def generate_signals(satisfaction, engagement, situation_type):
    """Generate realistic conversation signal indicators"""
    signals = {
        'message_length_trend': random.choice(['increasing', 'stable', 'decreasing']),
        'question_count': random.randint(0, 5),
        'gratitude_expressed': satisfaction > 0.6 and random.random() > 0.3,
        'frustration_detected': satisfaction < 0.35 and random.random() > 0.4,
        'topic_shifts': random.randint(0, 3),
        'follow_up_questions': random.randint(0, 4),
        'action_items_discussed': situation_type in ['career_guidance', 'skill_development', 'financial'],
        'emotional_disclosure': situation_type in ['emotional', 'relationship', 'grief'],
    }
    return signals


def pick_character(user, situation_config):
    """Pick which character handled this conversation"""
    # 40% chance user's preferred character, 60% system-matched
    if random.random() < 0.4 and user['preferred_chars']:
        return random.choice(user['preferred_chars'])
    
    # System matching: weighted toward affinity characters
    pool = []
    for char in CHARACTERS:
        if char in situation_config['character_affinity']:
            pool.extend([char] * 3)  # 3x weight for good matches
        elif char in situation_config['weak_characters']:
            pool.append(char)  # 1x weight for poor matches
        else:
            pool.extend([char] * 2)  # 2x weight for neutral
    return random.choice(pool)


def generate_synthetic_data(db_path='integrated_users.db', days=60, 
                            conversations_per_day=8, clear_existing=False,
                            db_connection=None):
    """
    Generate comprehensive synthetic data.
    
    Args:
        db_path: Database path (ignored if db_connection provided)
        days: How many days of historical data
        conversations_per_day: Average conversations per day across all users
        clear_existing: If True, clear existing synthetic data first
        db_connection: Optional existing connection (for in-memory sharing)
    """
    db = db_connection or sqlite3.connect(db_path)
    cursor = db.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation_outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            character_id TEXT NOT NULL,
            message_count INTEGER DEFAULT 0,
            user_message_count INTEGER DEFAULT 0,
            engagement_level TEXT,
            satisfaction_estimate REAL,
            goal_achieved BOOLEAN,
            signals_json TEXT,
            situation_type TEXT DEFAULT 'general',
            analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(session_id, character_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            character_id TEXT,
            feedback_type TEXT NOT NULL,
            feedback_value REAL,
            feedback_text TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS character_usage_outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            character_id TEXT NOT NULL,
            situation_json TEXT,
            conversation_length INTEGER,
            user_satisfaction REAL,
            goal_achieved BOOLEAN,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    if clear_existing:
        cursor.execute("DELETE FROM conversation_outcomes WHERE session_id LIKE 'synth_%'")
        cursor.execute("DELETE FROM user_feedback WHERE session_id LIKE 'synth_%'")
        cursor.execute("DELETE FROM character_usage_outcomes WHERE situation_json LIKE '%synthetic%'")
        print(f"  Cleared existing synthetic data")
    
    now = datetime.now()
    total_conversations = 0
    total_feedback = 0
    total_usage = 0
    situation_counts = {}
    character_counts = {}
    satisfaction_by_situation = {}
    
    # Build weighted situation pool based on frequency
    situation_pool = []
    for sit_name, config in SITUATIONS.items():
        situation_pool.extend([sit_name] * config['frequency'])
    
    print(f"\n  Generating {days} days of data...")
    
    for day_offset in range(days, 0, -1):
        day = now - timedelta(days=day_offset)
        
        # Vary conversations per day (weekdays more active)
        weekday = day.weekday()
        daily_count = conversations_per_day
        if weekday < 5:  # Weekday
            daily_count = int(daily_count * random.uniform(1.0, 1.5))
        else:  # Weekend
            daily_count = int(daily_count * random.uniform(0.5, 1.0))
        
        for _ in range(daily_count):
            user = random.choice(USERS)
            situation_type = random.choice(situation_pool)
            situation_config = SITUATIONS[situation_type]
            character = pick_character(user, situation_config)
            
            # Generate conversation metrics
            satisfaction = generate_satisfaction(situation_config, character)
            engagement = generate_engagement(satisfaction)
            msg_count = generate_message_count(engagement)
            user_msg_count = msg_count // 2 + random.randint(0, 2)
            goal_achieved = satisfaction > 0.6 and random.random() > 0.3
            signals = generate_signals(satisfaction, engagement, situation_type)
            
            # Randomize time within the day
            hour = random.randint(7, 23)
            minute = random.randint(0, 59)
            timestamp = day.replace(hour=hour, minute=minute)
            
            session_id = f"synth_{uuid.uuid4().hex[:12]}"
            
            # 1. Insert conversation_outcomes
            try:
                cursor.execute('''
                    INSERT INTO conversation_outcomes
                    (session_id, user_id, character_id, message_count, user_message_count,
                     engagement_level, satisfaction_estimate, goal_achieved, signals_json,
                     situation_type, analyzed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (session_id, user['id'], character, msg_count, user_msg_count,
                      engagement, satisfaction, goal_achieved, json.dumps(signals),
                      situation_type, timestamp.isoformat()))
                total_conversations += 1
            except sqlite3.IntegrityError:
                continue
            
            # 2. Insert character_usage_outcomes (for character_traits learning)
            cursor.execute('''
                INSERT INTO character_usage_outcomes
                (user_id, character_id, situation_json, conversation_length, 
                 user_satisfaction, goal_achieved, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user['id'], character, 
                  json.dumps({'situation_type': situation_type, 'synthetic': True}),
                  msg_count, satisfaction, goal_achieved, timestamp.isoformat()))
            total_usage += 1
            
            # 3. 30% chance of explicit user feedback
            if random.random() < 0.3:
                if satisfaction > 0.65:
                    fb_type = 'thumbs_up'
                    fb_value = 1.0
                elif satisfaction < 0.35:
                    fb_type = 'thumbs_down'
                    fb_value = 0.0
                else:
                    fb_type = random.choice(['thumbs_up', 'thumbs_down'])
                    fb_value = 1.0 if fb_type == 'thumbs_up' else 0.0
                
                cursor.execute('''
                    INSERT INTO user_feedback
                    (session_id, user_id, character_id, feedback_type, feedback_value, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (session_id, user['id'], character, fb_type, fb_value, timestamp.isoformat()))
                total_feedback += 1
            
            # Track stats
            situation_counts[situation_type] = situation_counts.get(situation_type, 0) + 1
            character_counts[character] = character_counts.get(character, 0) + 1
            if situation_type not in satisfaction_by_situation:
                satisfaction_by_situation[situation_type] = []
            satisfaction_by_situation[situation_type].append(satisfaction)
    
    db.commit()
    
    # Print summary
    print(f"\n  📊 Data Generation Summary")
    print(f"  {'='*50}")
    print(f"  Total conversations: {total_conversations}")
    print(f"  Total feedback entries: {total_feedback}")
    print(f"  Total usage outcomes: {total_usage}")
    
    print(f"\n  📋 Situation Distribution:")
    for sit, count in sorted(situation_counts.items(), key=lambda x: -x[1]):
        avg_sat = sum(satisfaction_by_situation[sit]) / len(satisfaction_by_situation[sit])
        marker = "🔴" if avg_sat < 0.45 else "🟡" if avg_sat < 0.6 else "🟢"
        print(f"     {marker} {sit:20s}: {count:4d} convos, avg_satisfaction={avg_sat:.3f}")
    
    print(f"\n  👤 Character Usage:")
    for char, count in sorted(character_counts.items(), key=lambda x: -x[1]):
        print(f"     {char:15s}: {count:4d} conversations")
    
    print(f"\n  🎯 Expected Gap Detection:")
    for sit, sats in sorted(satisfaction_by_situation.items(), key=lambda x: sum(x[1])/len(x[1])):
        avg = sum(sats) / len(sats)
        if avg < 0.5:
            print(f"     🔴 {sit}: avg_sat={avg:.3f} → Should trigger expansion")
    
    if not db_connection:
        db.close()
    return {
        'conversations': total_conversations,
        'feedback': total_feedback,
        'usage': total_usage,
        'situations': situation_counts,
        'satisfaction': {k: round(sum(v)/len(v), 3) for k, v in satisfaction_by_situation.items()},
        'db': db if db_connection else None
    }


def verify_expansion_with_data(db_path='integrated_users.db', db_connection=None):
    """After generating data, verify expansion system detects gaps"""
    db = db_connection or sqlite3.connect(db_path)
    
    from smart_response.character_expansion import create_character_expansion_system
    from smart_response.character_traits import create_character_trait_system
    
    trait_system = create_character_trait_system(db)
    expansion = create_character_expansion_system(db)
    
    print(f"\n  🔍 Running Gap Analysis with Synthetic Data")
    print(f"  {'='*50}")
    
    # Show effectiveness and demand data
    eff = expansion._get_effectiveness_gaps()
    demand = expansion._get_demand_scores()
    threshold = expansion._get_adaptive_threshold(len(trait_system.characters))
    
    print(f"\n  Adaptive threshold: {threshold:.2f}")
    print(f"  Characters in system: {len(trait_system.characters)}")
    
    print(f"\n  📉 Effectiveness Weaknesses (high = poor performance):")
    for sit, score in sorted(eff.items(), key=lambda x: -x[1]):
        marker = "🔴" if score > 0.5 else "🟡" if score > 0.3 else "🟢"
        print(f"     {marker} {sit:20s}: weakness={score:.3f}")
    
    print(f"\n  📈 Usage Demand (high = frequently needed):")
    for sit, score in sorted(demand.items(), key=lambda x: -x[1]):
        print(f"     {sit:20s}: demand={score:.3f}")
    
    # Run actual gap analysis
    gaps = expansion.analyze_trait_space_coverage(trait_system)
    
    print(f"\n  🎯 Gaps Detected: {len(gaps)}")
    for g in gaps:
        print(f"     Gap: score={g.gap_score:.3f}, nearest={g.nearest_character}, "
              f"dist={g.nearest_distance:.3f}")
        print(f"           situations={g.situation_types}, eff_weakness={g.effectiveness_score:.3f}, "
              f"demand={g.demand_score:.3f}")
    
    # Try filling gaps
    if gaps:
        print(f"\n  🔧 Attempting to fill top gap...")
        candidate = expansion.generate_character_for_gap(gaps[0])
        if candidate:
            print(f"     Generated: {candidate.name} (inspired by {candidate.inspiration})")
            print(f"     Domain: {candidate.domain}")
            print(f"     Lens: {candidate.philosophical_lens}")
    
    stats = expansion.get_expansion_stats()
    print(f"\n  📊 Final Stats: {json.dumps(stats, indent=2, default=str)}")
    
    if not db_connection:
        db.close()
    return gaps


if __name__ == '__main__':
    print("=" * 60)
    print("SYNTHETIC DATA GENERATOR")
    print("=" * 60)
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           'integrated_users.db')
    
    if '--clear' in sys.argv:
        print("\n⚠️  Clearing existing synthetic data first...")
        clear = True
    else:
        clear = False
    
    use_memory = '--memory' in sys.argv
    shared_conn = None
    
    if use_memory:
        shared_conn = sqlite3.connect(':memory:')
        db_path = ':memory:'
        print("\n📝 Using in-memory database (test mode)")
    
    print(f"\n📦 Database: {db_path}")
    
    result = generate_synthetic_data(
        db_path=db_path,
        days=60,
        conversations_per_day=8,
        clear_existing=clear,
        db_connection=shared_conn
    )
    
    if '--verify' in sys.argv or True:
        verify_expansion_with_data(db_path, db_connection=shared_conn)
    
    if shared_conn:
        shared_conn.close()
    
    print("\n✅ Done!")
