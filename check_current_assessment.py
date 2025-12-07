"""Check if assessment exists in the current system (psychology_traits table)"""

from integrated_database import IntegratedDatabase

db = IntegratedDatabase()
conn = db.get_connection()
cursor = conn.cursor()

print("\n" + "="*60)
print("🔍 CHECKING CURRENT ASSESSMENT DATA")
print("="*60)

# Check psychology_traits table (current assessment)
cursor.execute("""
    SELECT trait_name, trait_value, updated_at 
    FROM psychology_traits 
    WHERE user_id = 1 
    ORDER BY trait_name
""")

traits = cursor.fetchall()

if traits:
    print(f"\n✅ Found current assessment in psychology_traits:")
    print(f"   User: Wai Tse (user_id=1)\n")
    
    for trait_name, trait_value, updated_at in traits:
        percentage = trait_value * 100 if trait_value <= 1 else trait_value
        print(f"   • {trait_name}: {percentage:.1f}%")
    
    print(f"\n   Source: assessment")
    print(f"   Last updated: {updated_at}")
    
    print("\n" + "="*60)
    print("⚠️  ISSUE IDENTIFIED")
    print("="*60)
    print("\nYour assessment IS saved in the current profile,")
    print("but it was NOT copied to assessment_history.")
    print("\nThis happened because:")
    print("1. You completed the assessment")
    print("2. It saved to psychology_traits (old system) ✅")
    print("3. But assessment_history wasn't updated ❌")
    print("\nSOLUTION:")
    print("I need to manually migrate your current assessment")
    print("to the history table, or you can retake the assessment")
    print("with the updated code.")
    
else:
    print("\n❌ No assessment found in psychology_traits either!")
    print("   It seems no assessment has been completed yet.")

conn.close()

# Also check inferred traits
print("\n" + "="*60)
print("🧠 CHECKING INFERRED TRAITS")
print("="*60)

cursor = conn.cursor()
cursor.execute("""
    SELECT openness, conscientiousness, extraversion, agreeableness, 
           neuroticism, confidence, message_count, last_updated
    FROM inferred_traits
    WHERE user_id = 1
""")

inferred = cursor.fetchone()
conn.close()

if inferred:
    print("\n✅ Found inferred traits from conversations:")
    traits_names = ['Openness', 'Conscientiousness', 'Extraversion', 'Agreeableness', 'Emotional Stability']
    for i, name in enumerate(traits_names):
        print(f"   • {name}: {inferred[i]*100:.1f}%")
    print(f"\n   Confidence: {inferred[5]*100:.1f}%")
    print(f"   Based on: {inferred[6]} messages")
    print(f"   Last updated: {inferred[7]}")
else:
    print("\n❌ No inferred traits found")

print("\n" + "="*60 + "\n")
