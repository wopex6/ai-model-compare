"""
Seed realistic quality score data into smart_response.db for the trend chart.
Generates 14 days of scores across multiple characters with natural variation.

Usage: python scripts/seed_quality_scores.py
"""
import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'smart_response.db')

CHARACTERS = [
    ('super_motivational_coach', 'philosophy'),
    ('stoic_philosopher', 'philosophy'),
    ('wise_sage', 'philosophy'),
    ('domain_work', 'domain'),
    ('domain_relationships', 'domain'),
    ('domain_finance', 'domain'),
    ('domain_health', 'domain'),
]

def seed():
    print(f"Seeding quality scores into: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)

    # Ensure table exists
    conn.execute('''
        CREATE TABLE IF NOT EXISTS conversation_quality_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            character_id TEXT DEFAULT '',
            character_type TEXT DEFAULT '',
            coherence REAL,
            helpfulness REAL,
            engagement REAL,
            resolution REAL,
            consistency REAL,
            overall REAL,
            flags TEXT,
            details TEXT,
            scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    now = datetime.utcnow()
    inserted = 0

    for day_offset in range(14, 0, -1):
        day = now - timedelta(days=day_offset)
        # Slight upward trend over time (improvement)
        trend_bonus = (14 - day_offset) * 0.003

        # 3-8 scores per day
        num_scores = random.randint(3, 8)
        for _ in range(num_scores):
            char_id, char_type = random.choice(CHARACTERS)
            session_id = f"seed_session_{day.strftime('%Y%m%d')}_{random.randint(1000, 9999)}"

            base = 0.72 + trend_bonus
            coherence = min(1.0, base + random.uniform(-0.08, 0.12))
            helpfulness = min(1.0, base + random.uniform(-0.06, 0.14))
            engagement = min(1.0, base + random.uniform(-0.10, 0.10))
            resolution = min(1.0, base + random.uniform(-0.12, 0.08))
            consistency = min(1.0, base + random.uniform(-0.05, 0.10))
            overall = round((coherence + helpfulness + engagement + resolution + consistency) / 5, 4)

            scored_at = day.replace(
                hour=random.randint(8, 22),
                minute=random.randint(0, 59),
                second=random.randint(0, 59),
            ).strftime('%Y-%m-%d %H:%M:%S')

            flags = '[]'
            if overall < 0.65:
                flags = '["low_overall"]'

            conn.execute(
                """INSERT INTO conversation_quality_scores
                   (session_id, character_id, character_type, coherence, helpfulness,
                    engagement, resolution, consistency, overall, flags, details, scored_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (session_id, char_id, char_type,
                 round(coherence, 4), round(helpfulness, 4), round(engagement, 4),
                 round(resolution, 4), round(consistency, 4), round(overall, 4),
                 flags, '{"source": "seed_script"}', scored_at)
            )
            inserted += 1

    conn.commit()
    conn.close()
    print(f"Inserted {inserted} quality scores across 14 days.")
    print("Trend chart should now display data on the admin dashboard.")


if __name__ == '__main__':
    seed()
