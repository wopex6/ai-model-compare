"""
Seed script: Populate Wai Tse's health profile from Google AI conversation (June 2026).
Run once: python health_profiles/seed_wai_tse.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_compare.medical_advisor_health_context import HealthContextManager

# Use user_id "1" as default for Wai Tse (primary user)
profile = HealthContextManager.get_profile("1")

# --- Personal Info ---
profile.name = "Wai Tse"
profile.set_personal(
    gender="male",
    location="Berwick, Victoria, Australia"
)

# --- Conditions ---
profile.add_condition(
    name="Urge Incontinence",
    details="Triggered by sound of running tap water (conditioned bladder reflex). Not stress incontinence - no leaks from lifting/coughing.",
    status="active",
    diagnosed_date="2026-01"
)
profile.add_condition(
    name="Rapid Hair Whitening",
    details="Rapid greying over short period, started a few months after bladder symptoms. Likely linked to overstimulated sympathetic nervous system.",
    status="active",
    diagnosed_date="2026-03"
)
profile.add_condition(
    name="Possible Subclinical Hypothyroidism",
    details="TSH jumped from baseline 2.3/2.9 to 5.1. GP says under 5.5 limit but individual trend is significant. Needs full thyroid panel.",
    status="investigating"
)
profile.add_condition(
    name="Nighttime Dry Mouth",
    details="Particularly after sexual activity and during sleep. Related to overstimulated SNS and late bedtime.",
    status="active"
)

# --- Symptoms ---
profile.add_symptom(
    description="Bladder leaks triggered by sound of running tap water",
    triggers=["running water sound", "tap water", "faucet"],
    severity="moderate",
    onset="~6 months ago"
)
profile.add_symptom(
    description="Rapid hair whitening/greying",
    triggers=["chronic stress", "possible B12/thyroid issue"],
    severity="moderate",
    onset="~3 months ago (after bladder symptoms)"
)
profile.add_symptom(
    description="Dry mouth at night, especially post-sexual activity",
    triggers=["late bedtime", "post-sex autonomic shift"],
    severity="mild-moderate"
)

# --- Test Results ---
profile.add_test_result("TSH", "5.1 mIU/L", reference_range="0.4-5.5", date="2026-05",
                        notes="Jumped from baseline 2.3/2.9. Biotin from seeds may falsely lower reading.")
profile.add_test_result("TSH (historical)", "2.3 mIU/L", reference_range="0.4-5.5", date="2025",
                        notes="Previous baseline")
profile.add_test_result("TSH (historical)", "2.9 mIU/L", reference_range="0.4-5.5", date="2025",
                        notes="Previous baseline")

# --- Diet ---
profile.update_diet(
    daily_foods=[
        "oats", "Greek yogurt", "a2 milk", "eggs",
        "psyllium husk", "coconut shreds", "honey",
        "black mulberries", "blueberries", "raspberries", "sultanas",
        "apple (1 daily)", "turmeric", "black pepper",
        "walnuts", "almonds", "flaxseeds", "linseeds",
        "chia seeds", "pumpkin seeds", "black sesame seeds",
        "salmon", "barramundi", "prawns", "loin", "skirt steak", "bananas"
    ],
    preferences=["whole foods", "anti-inflammatory", "high omega-3", "nutrient-dense"],
    restrictions=[
        "no cooking oil added (steams only)",
        "no caffeine",
        "no fried food",
        "STOP daily orange (bladder irritant - citric acid)"
    ],
    cooking_methods=["steaming only"],
    notes=[
        "No added cooking oil needed - gets all fats from whole foods",
        "Seeds are high in biotin - must pause 48hrs before thyroid blood tests",
        "Eggs also high in biotin - pause before tests",
        "Daily orange should be replaced with apple/berries (bladder acid irritant)",
        "Red meat (loin/skirt) limited to 2-3x/week to prevent constipation pressing on bladder",
        "Seeds should be limited to ~30g combined daily; soak overnight to improve zinc absorption"
    ]
)

# --- Supplements/Herbs ---
profile.add_supplement("Schisandra (Wu Wei Zi)", purpose="Adaptogen - calms SNS, reduces bladder spasms, stimulates saliva, protects hair follicles")
profile.add_supplement("Salvia (Dan Shen)", purpose="Blood circulation, nervous system calming. WARNING: natural blood thinner - disclose to GP")
profile.add_supplement("Turmeric + Black Pepper", purpose="Anti-inflammatory (curcumin absorption enhanced by piperine)")
profile.add_supplement("Psyllium Husk", purpose="Soluble fiber - prevents constipation/bladder pressure")

# --- Lifestyle ---
profile.update_lifestyle(
    sleep={
        "current_bedtime": "12:40 AM (shifted from 11 PM - needs to return to 11 PM)",
        "target_bedtime": "11:00 PM",
        "issue": "Late sleep worsens cortisol, TSH accuracy, bladder urgency, and dry mouth",
        "strategy": "Move bedtime back in 15-minute steps over 2 weeks"
    },
    exercise=["jogging/running (beneficial for SNS calming but use caution re: bladder impact)",
              "empty bladder before running", "engage pelvic floor during runs",
              "prefer soft surfaces over concrete"],
    stress_factors=["overstimulated sympathetic nervous system",
                    "late bedtime contributing to cortisol cycle"],
    habits=["no caffeine", "no alcohol mentioned", "no smoking mentioned",
            "steams all food", "stop fluids 2hrs before bed"]
)

# --- Action Plans ---
profile.add_action_plan(
    title="Bladder Retraining - Urge Suppression",
    steps=[
        "When hearing running water: STOP, stand still",
        "Deep belly breaths to calm SNS",
        "5-6 fast pelvic floor squeezes (Kegels)",
        "Distract mind (count backwards, read something)",
        "Wait 30-60 seconds for urge to pass",
        "Walk slowly to toilet - never run",
        "Gradually extend hold time to 5, 10, 15 minutes"
    ],
    status="active",
    priority="high"
)
profile.add_action_plan(
    title="GP Blood Test Panel",
    steps=[
        "Request: TSH, Free T4 (FT4), Free T3 (FT3)",
        "Request: Anti-TPO Thyroid Antibodies",
        "Request: Vitamin B12 & Serum Folate",
        "Request: Iron Studies (Ferritin)",
        "Request: Vitamin D",
        "PREP: Stop seeds/nuts/eggs 48 hours before",
        "PREP: Sleep before 11pm for 3 nights prior",
        "PREP: Fast morning of test (water only)",
        "PREP: Blood draw before 9:00 AM",
        "Mention salvia & schisandra to GP"
    ],
    status="active",
    priority="high"
)
profile.add_action_plan(
    title="Sleep Schedule Correction",
    steps=[
        "Move bedtime from 12:40 AM back to 11 PM",
        "Use 15-minute increments over 2 weeks",
        "Stop all fluids at 10 PM",
        "Critical for accurate TSH test results"
    ],
    status="active",
    priority="medium"
)
profile.add_action_plan(
    title="Pelvic Floor Strengthening",
    steps=[
        "Quick squeezes: 1 sec hold × 10 reps",
        "Slow holds: 3-5 sec hold × 5-10 reps",
        "Practice daily",
        "Consider pelvic floor physiotherapist referral (Berwick area)"
    ],
    status="active",
    priority="high"
)

# --- Key Conversation Insights ---
profile.add_conversation_insight(
    "Bladder leaks NOT caused by oil/fat deficiency - diet provides excellent fats from whole foods",
    category="diagnosis"
)
profile.add_conversation_insight(
    "Running-water trigger is nerve-reflex based (conditioned bladder reflex), not mechanical",
    category="diagnosis"
)
profile.add_conversation_insight(
    "Hair whitening + bladder symptoms together suggest overstimulated Sympathetic Nervous System",
    category="diagnosis"
)
profile.add_conversation_insight(
    "TSH 5.1 jumped from 2.3/2.9 baseline - significant individual trend even if within lab 'normal'",
    category="test_results"
)
profile.add_conversation_insight(
    "Biotin from daily seeds/nuts/eggs may falsely LOWER TSH readings on lab equipment",
    category="test_preparation"
)
profile.add_conversation_insight(
    "Hair whitening may be REVERSIBLE if caused by B12 deficiency or thyroid dysfunction",
    category="prognosis"
)
profile.add_conversation_insight(
    "Vitamin D deficiency is likely (hard to get from food alone) - drives pelvic floor weakness and hair greying",
    category="potential_deficiency"
)
profile.add_conversation_insight(
    "Zinc absorption may be impaired due to phytic acid in raw seeds - soaking overnight helps",
    category="nutrition"
)

print(f"✓ Health profile seeded for {profile.name}")
print(f"  Conditions: {len(profile.data['conditions'])}")
print(f"  Symptoms: {len(profile.data['symptoms'])}")
print(f"  Test results: {len(profile.data['test_results'])}")
print(f"  Action plans: {len(profile.data['action_plans'])}")
print(f"  Supplements: {len(profile.data['supplements'])}")
print(f"  Conversation insights: {len(profile.data['conversation_insights'])}")
print(f"  Saved to: {profile.file_path}")
