"""Migrate existing assessment from psychology_traits to assessment_history"""

from integrated_database import IntegratedDatabase
from datetime import datetime

db = IntegratedDatabase()
conn = db.get_connection()
cursor = conn.cursor()

print("\n" + "="*60)
print("📦 MIGRATING EXISTING ASSESSMENT TO HISTORY")
print("="*60)

# Get current assessment from psychology_traits
cursor.execute("""
    SELECT trait_name, trait_value, updated_at
    FROM psychology_traits
    WHERE user_id = 1
    ORDER BY trait_name
""")

traits = cursor.fetchall()

if not traits:
    print("\n❌ No assessment found to migrate!")
    conn.close()
    exit()

# Build trait scores dict
trait_scores = {}
last_updated = None

for trait_name, trait_value, updated_at in traits:
    # Normalize trait names to match Big 5
    trait_key = trait_name.lower()
    trait_scores[trait_key] = trait_value
    
    if updated_at and (not last_updated or updated_at > last_updated):
        last_updated = updated_at

print(f"\n✅ Found existing assessment (dated: {last_updated}):")
for trait, value in trait_scores.items():
    print(f"   • {trait.title()}: {value*100:.1f}%")

# Map to Big 5 format
big5_scores = {
    'openness': trait_scores.get('openness', 0.5),
    'conscientiousness': trait_scores.get('conscientiousness', 0.5),
    'extraversion': trait_scores.get('extraversion', 0.5),
    'agreeableness': trait_scores.get('agreeableness', 0.5),
    'neuroticism': trait_scores.get('neuroticism', 0.5)
}

# Save to assessment_history
try:
    history_id = db.save_assessment_to_history(
        user_id=1,
        trait_scores=big5_scores,
        started_at=last_updated,  # Use the updated_at as started_at
        completion_time_seconds=None,  # Unknown for old assessment
        notes="Migrated from existing assessment (completed before history feature)"
    )
    
    if history_id:
        print(f"\n✅ Successfully migrated to assessment_history!")
        print(f"   History ID: {history_id}")
        print("\n" + "="*60)
        print("✨ READY FOR NEXT ASSESSMENT")
        print("="*60)
        print("\nNow when you complete another assessment:")
        print("1. It will be saved to history ✅")
        print("2. It will auto-compare to this baseline ✅")
        print("3. You'll see changes over time ✅")
        print("\nGo ahead and retake the assessment!")
        print("Visit: http://localhost:5000/personality-test")
    else:
        print("\n❌ Failed to save to history!")
        
except Exception as e:
    print(f"\n❌ Error during migration: {e}")

conn.close()
print("\n" + "="*60 + "\n")
