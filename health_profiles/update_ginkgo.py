"""Update Wai Tse's health profile with new Ginkgo/diet/Vitamin D info from June 1 conversation."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_compare.medical_advisor_health_context import HealthContextManager

profile = HealthContextManager.get_profile("1")

# --- Vitamin D (already taking) ---
profile.add_supplement("Vitamin D", dose="2 tablets daily",
                       purpose="Pelvic floor muscle support, hair follicle health, bone density")

# --- Ginkgo consideration ---
profile.add_conversation_insight(
    "Ginkgo biloba: POTENTIAL BENEFIT for hair pigmentation (improves micro-capillary blood flow "
    "to follicles) and dry mouth (supports salivary glands). RISK: can stimulate bladder muscle "
    "(detrusor) worsening urgency. CRITICAL: DO NOT combine with Salvia - both are potent blood "
    "thinners, excessive bleeding risk. HOLD until GP consultation and blood test results.",
    category="herb_consideration"
)

# --- Updated daily foods (add chicken tenderloin, pork loin explicitly) ---
profile.data["diet"]["daily_foods"] = [
    "oats", "Greek yogurt", "a2 milk", "eggs",
    "psyllium husk", "coconut shreds", "honey (1 tsp only)",
    "black mulberries", "blueberries", "raspberries", "sultanas (small sprinkle)",
    "apple (1 daily)", "turmeric", "black pepper",
    "walnuts", "almonds", "flaxseeds", "linseeds",
    "chia seeds", "pumpkin seeds", "black sesame seeds",
    "salmon", "barramundi", "prawns",
    "chicken tenderloin", "pork loin", "beef skirt steak",
    "bananas"
]

# --- Updated diet notes ---
profile.data["diet"]["notes"] = [
    "No added cooking oil needed - gets all fats from whole foods",
    "Seeds are high in biotin - must pause 48hrs before thyroid blood tests",
    "Eggs also high in biotin - pause before tests",
    "STOP daily orange - citric acid + fructose irritate bladder lining causing involuntary spasms",
    "Alternate meats through week: chicken tenderloin, pork loin, beef skirt, salmon, barramundi, prawns",
    "Red meat (skirt steak) limited to 2-3x/week to prevent sluggish digestion pressing on bladder",
    "Seeds limited to ~30g combined daily; soak overnight to deactivate phytic acid and maximize zinc absorption",
    "Limit honey to 1 teaspoon and sultanas to small sprinkle - excess sugars alter urine acidity and irritate bladder wall",
    "Chicken/pork/beef are biotin-FREE and safe during 48-hr pre-test break",
    "Chicken tenderloin and pork loin are lighter and easier to digest than beef - less bladder pressure",
]

# --- Updated restrictions ---
profile.data["diet"]["restrictions"] = [
    "no cooking oil added (steams only)",
    "no caffeine",
    "no fried food",
    "STOP daily orange (citric acid + fructose = bladder irritant)",
    "DO NOT start Ginkgo biloba until after GP blood test and consultation (bleeding risk with Salvia)",
]

# --- Update GP blood test plan ---
for plan in profile.data["action_plans"]:
    if plan["title"] == "GP Blood Test Panel":
        plan["steps"] = [
            "Request: TSH, Free T4 (FT4), Free T3 (FT3)",
            "Request: Anti-TPO Thyroid Antibodies",
            "Request: Vitamin B12 & Serum Folate",
            "Request: Iron Studies (Ferritin)",
            "NOTE: Skip Vitamin D test - already supplementing 2 tablets daily",
            "PREP: Stop seeds/nuts/eggs 48 hours before (biotin interference)",
            "PREP: Sleep before 11pm for 3 nights prior",
            "PREP: Fast morning of test (water only)",
            "PREP: Blood draw before 9:00 AM",
            "TELL GP: Taking Salvia (Dan Shen) daily - blood thinner",
            "TELL GP: Taking Schisandra (Wu Wei Zi) daily",
            "TELL GP: Considering Ginkgo biloba - ask about bleeding risk with Salvia",
            "TELL GP: Ask about blood clotting factors if concerned",
        ]
        break

# --- Additional insights ---
profile.add_conversation_insight(
    "Fluid timing: stop ALL liquids 2hrs before bed. After sex, take small rolling sips (not gulps) to avoid overfilling bladder.",
    category="lifestyle"
)
profile.add_conversation_insight(
    "Ginkgo does NOT contain biotin - safe to take during 48-hr pre-test seed break. But fast completely morning of test.",
    category="test_preparation"
)
profile.add_conversation_insight(
    "Excess honey and sultanas can alter urine acidity and irritate bladder wall - keep minimal.",
    category="nutrition"
)

# --- Updated exercise notes ---
profile.data["lifestyle"]["exercise"] = [
    "jogging/running (beneficial for SNS calming)",
    "CAUTION: downward impact can temporarily worsen bladder leaks",
    "engage pelvic floor muscles while running",
    "consider switching to brisk walking or cycling temporarily",
    "empty bladder before any exercise",
    "prefer soft surfaces over concrete",
]

profile.save()

print(f"Profile updated for {profile.name}")
print(f"  Supplements: {len(profile.data['supplements'])}")
print(f"  Insights: {len(profile.data['conversation_insights'])}")
print(f"  Diet foods: {len(profile.data['diet']['daily_foods'])}")
print(f"  Diet notes: {len(profile.data['diet']['notes'])}")
print(f"  GP steps: {len([p for p in profile.data['action_plans'] if p['title'] == 'GP Blood Test Panel'][0]['steps'])}")
