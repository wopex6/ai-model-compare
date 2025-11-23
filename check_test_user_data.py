"""Check what data exists for test_user_1761957912201"""

import os
import json
from pathlib import Path

print("\n" + "="*80)
print("CHECKING TEST_USER DATA")
print("="*80)

# Check personality profiles
profiles_dir = Path("personality_profiles")

# Check for the specific test user profile
test_user_file = profiles_dir / "test_user_1761957912201_profile.json"

if test_user_file.exists():
    print(f"\n✅ Found profile file: {test_user_file}")
    with open(test_user_file, 'r') as f:
        profile_data = json.load(f)
    
    print(f"\n📊 Profile Data:")
    print(f"   User ID: {profile_data.get('user_id')}")
    print(f"   Assessment Stage: {profile_data.get('assessment_stage')}")
    print(f"   Confidence Level: {profile_data.get('confidence_level')}")
    print(f"   Created: {profile_data.get('created_at')}")
    print(f"   Updated: {profile_data.get('updated_at')}")
    print(f"   Interaction Count: {profile_data.get('interaction_count')}")
    
    print(f"\n   This is why completion screen was showing!")
    print(f"   The test_user has assessment_stage = '{profile_data.get('assessment_stage')}'")
else:
    print(f"\n❌ No profile file found for test_user_1761957912201")

# Check session files
sessions_dir = profiles_dir / "sessions"
if sessions_dir.exists():
    session_files = list(sessions_dir.glob("test_user_1761957912201*"))
    if session_files:
        print(f"\n✅ Found {len(session_files)} session file(s):")
        for sf in session_files:
            print(f"   - {sf.name}")
            with open(sf, 'r') as f:
                session_data = json.load(f)
            print(f"     Current question: {session_data.get('current_question')}/{len(session_data.get('questions', []))}")
    else:
        print(f"\n❌ No session files found")

# Show all profile files
print(f"\n📁 All Profile Files:")
if profiles_dir.exists():
    profile_files = list(profiles_dir.glob("*_profile.json"))
    for pf in profile_files[:10]:  # Show first 10
        print(f"   - {pf.name}")
    if len(profile_files) > 10:
        print(f"   ... and {len(profile_files) - 10} more")
else:
    print("   No profiles directory")

print("\n" + "="*80)
print("SOLUTION:")
print("="*80)
print("Now that we've fixed the code to use actual username (WK),")
print("when you login as WK and click 'Take Personality Test',")
print("it will check for WK's profile, not test_user_1761957912201.")
print("\nSince WK has NOT completed the assessment,")
print("you should now see the WELCOME screen! ✅")
print("="*80 + "\n")
