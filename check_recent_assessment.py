"""Check if there's a recent assessment we might have missed"""

from integrated_database import IntegratedDatabase

db = IntegratedDatabase()

print("\n" + "="*60)
print("🔍 CHECKING FOR RECENT ASSESSMENT")
print("="*60)

# Check assessment_history for any recent entries
history = db.get_assessment_history(user_id=1, limit=5)

print(f"\nTotal assessments in history: {len(history)}\n")

if len(history) > 1:
    print("✅ Multiple assessments found! Showing all:\n")
    for i, assessment in enumerate(history, 1):
        print(f"Assessment #{i} - {assessment['completed_at']}")
        for trait, value in assessment['traits'].items():
            print(f"  • {trait.title()}: {value*100:.1f}%")
        if assessment.get('notes'):
            print(f"  Notes: {assessment['notes']}")
        print()
    
    # Auto-compare latest two
    if len(history) >= 2:
        print("="*60)
        print("📈 AUTO-COMPARISON: Latest vs Previous")
        print("="*60)
        
        comparison = db.compare_assessments(
            user_id=1,
            assessment1_id=history[1]['id'],  # Older
            assessment2_id=history[0]['id']   # Newer
        )
        
        print(f"\nTime between: {comparison['time_between']}")
        print(f"Overall change: {comparison['overall_change']}%")
        print(f"Stability: {comparison['stability_assessment']}\n")
        
        print("Changes:")
        for trait, data in comparison['comparison'].items():
            emoji = "↑" if data['direction'] == 'increased' else "↓" if data['direction'] == 'decreased' else "→"
            print(f"  {emoji} {trait.title()}: {data['old_value']}% → {data['new_value']}% ({data['change']:+.1f}%)")

elif len(history) == 1:
    print("📍 Only baseline assessment found.")
    print("\n" + "="*60)
    print("💡 READY FOR NEXT ASSESSMENT")
    print("="*60)
    print("\nTo see comparison data:")
    print("1. Visit: http://localhost:5000/personality-test")
    print("2. Complete the 44 questions")
    print("3. Submit - you'll see comparison to your baseline!")
    print("\nThe system will automatically:")
    print("  ✅ Save as Assessment #2")
    print("  ✅ Compare to Sept 25 baseline")
    print("  ✅ Show changes in each trait")

print("\n" + "="*60 + "\n")
