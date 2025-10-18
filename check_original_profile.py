#!/usr/bin/env python3
"""
Check the original comprehensive profile system
"""

from ai_compare.user_profile_manager import UserProfileManager
import json

def check_original_profile():
    print("🔍 Checking Original Profile System (/profile)")
    print("=" * 50)
    
    upm = UserProfileManager()
    
    # Load Wai Tse's comprehensive profile
    profile_id = 'eb049813-e28a-4ae6-8c7b-fa80250d0e51'
    profile = upm.load_user_profile(profile_id)
    
    if profile:
        print(f"✅ Found comprehensive profile:")
        print(f"   Name: {profile['personal_info']['name']}")
        print(f"   Email: {profile['personal_info']['email']}")
        print(f"   Age: {profile['personal_info']['age']}")
        print(f"   Location: {profile['personal_info']['location']}")
        print(f"   Occupation: {profile['personal_info']['occupation']}")
        print(f"   Profile completion: {profile['metadata']['profile_completion']}%")
        
        # Check what sections exist
        sections = []
        if profile['personal_info']['name']:
            sections.append("Personal Info (Page 1)")
        if profile['preferences']['personality_type']:
            sections.append("Preferences (Page 2)")
        if 'privacy_settings' in profile:
            sections.append("Privacy Settings (Page 3)")
        if 'jung_types' in profile['preferences']:
            sections.append("Carl Jung Psychology")
        if 'assessment_history' in profile['preferences']:
            sections.append("Assessment History")
            
        print(f"   Available sections: {', '.join(sections)}")
        
        print(f"\n📊 Psychology Data:")
        if 'jung_types' in profile['preferences']:
            jung = profile['preferences']['jung_types']
            print(f"   Carl Jung - E/I: {jung['extraversion_introversion']:.1f}")
            print(f"   Carl Jung - S/N: {jung['sensing_intuition']:.1f}")
            print(f"   Carl Jung - T/F: {jung['thinking_feeling']:.1f}")
            print(f"   Carl Jung - J/P: {jung['judging_perceiving']:.1f}")
        
        if 'assessment_history' in profile['preferences']:
            history = profile['preferences']['assessment_history']
            print(f"   Assessment history: {len(history)} assessments")
            for i, assessment in enumerate(history):
                print(f"     {i+1}. {assessment['timestamp']}")
        
        return True
    else:
        print("❌ Comprehensive profile not found")
        return False

def check_profile_access():
    """Check if the /profile endpoint can access this data"""
    print(f"\n🌐 Profile Access:")
    print(f"   Original system: http://localhost:5000/profile")
    print(f"   Multi-user system: http://localhost:5000/multi-user")
    print(f"   Psychology assessment: http://localhost:5000/psychological-assessment")
    print(f"   Psychology profile: http://localhost:5000/psychological-profile")

if __name__ == "__main__":
    success = check_original_profile()
    check_profile_access()
    
    if success:
        print(f"\n💡 SOLUTION:")
        print(f"   The comprehensive 3-page profile data exists in the original system")
        print(f"   Access it at: http://localhost:5000/profile")
        print(f"   This is separate from the multi-user login system")
    else:
        print(f"\n❌ Need to restore comprehensive profile data")
