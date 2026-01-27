#!/usr/bin/env python3
"""
User Intelligence System - Interactive Test Script
===================================================

Run this script to test all User Intelligence functions with your own data.

Usage:
    python test_user_intelligence.py [user_id]
    
    If no user_id provided, defaults to user 23 (Wai Tse)
"""

import sqlite3
import json
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, '.')

from smart_response.user_intelligence import get_intelligence_system

def print_section(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)

def print_result(name, result):
    print(f"\n📊 {name}:")
    if isinstance(result, dict):
        for k, v in result.items():
            if isinstance(v, dict):
                print(f"   {k}:")
                for k2, v2 in v.items():
                    print(f"      {k2}: {v2}")
            else:
                print(f"   {k}: {v}")
    elif isinstance(result, list):
        for item in result[:5]:  # Show first 5
            print(f"   - {item}")
    else:
        print(f"   {result}")

def test_all_functions(user_id):
    """Test all User Intelligence System functions."""
    
    print(f"\n🧪 Testing User Intelligence System for User ID: {user_id}")
    print(f"   Timestamp: {datetime.now().isoformat()}")
    
    # Connect to database
    conn = sqlite3.connect('integrated_users.db')
    intel = get_intelligence_system(conn)
    
    # =========================================================================
    # 1. ENGAGEMENT TRACKING
    # =========================================================================
    print_section("1. ENGAGEMENT TRACKING")
    
    # Record some test engagements
    print("\n📝 Recording test engagement signals...")
    
    test_signals = [
        ('message_sent', {'test': True}, 'coordinator', 'general'),
        ('long_message', {'chars': 150}, 'domain_work', 'career'),
        ('suggestion_clicked', {}, 'domain_relationships', 'communication'),
        ('positive_feedback', {'rating': 5}, 'domain_mental_health', 'anxiety'),
    ]
    
    for signal_type, context, character, topic in test_signals:
        intel.record_engagement(user_id, signal_type, context, character, topic)
        print(f"   ✓ Recorded: {signal_type} → {character}/{topic}")
    
    # Get engagement summary
    summary = intel.get_engagement_summary(user_id, days=30)
    print_result("Engagement Summary (30 days)", summary)
    
    # =========================================================================
    # 2. BEHAVIORAL PATTERNS
    # =========================================================================
    print_section("2. BEHAVIORAL PATTERNS")
    
    temporal = intel.analyze_temporal_patterns(user_id)
    print_result("Temporal Patterns", temporal)
    
    comm_style = intel.analyze_communication_style(user_id)
    print_result("Communication Style", comm_style)
    
    topic_patterns = intel.analyze_topic_patterns(user_id)
    print_result("Topic Patterns", topic_patterns)
    
    # =========================================================================
    # 3. INTEREST GRAPH
    # =========================================================================
    print_section("3. INTEREST GRAPH")
    
    interests = intel.get_interest_profile(user_id)
    print_result("Interest Profile", interests)
    
    # =========================================================================
    # 4. CHARACTER RECOMMENDATIONS
    # =========================================================================
    print_section("4. CHARACTER RECOMMENDATIONS")
    
    recs = intel.get_character_recommendations(user_id)
    print_result("Character Recommendations", recs)
    
    # =========================================================================
    # 5. PREDICTIONS
    # =========================================================================
    print_section("5. PREDICTIONS & PROACTIVE SUGGESTIONS")
    
    predictions = intel.predict_user_needs(user_id)
    print_result("Predicted User Needs", predictions)
    
    proactive = intel.get_proactive_suggestions(user_id)
    print_result("Proactive Suggestions", proactive)
    
    # =========================================================================
    # 6. CONVERSATION-SPECIFIC METRICS (Our Unique Advantage)
    # =========================================================================
    print_section("6. CONVERSATION-SPECIFIC METRICS")
    
    depth = intel.analyze_conversation_depth(user_id)
    print_result("Conversation Depth (like YouTube watch time)", depth)
    
    emotional = intel.analyze_emotional_journey(user_id)
    print_result("Emotional Journey (sentiment tracking)", emotional)
    
    resolution = intel.get_resolution_rate(user_id)
    print_result("Resolution Rate (like video completion)", resolution)
    
    # =========================================================================
    # 7. FUTURE MEDIA HANDLERS (Ready for videos/images)
    # =========================================================================
    print_section("7. FUTURE MEDIA HANDLERS (Extensibility Test)")
    
    # Simulate video engagement (when videos are added)
    print("\n📹 Simulating future video engagement...")
    intel.record_media_engagement(
        user_id=user_id,
        content_id='intro_video_001',
        media_type='video',
        engagement_type='video_started',
        progress_percent=0,
        context={'source': 'test'}
    )
    intel.record_media_engagement(
        user_id=user_id,
        content_id='intro_video_001',
        media_type='video',
        engagement_type='video_50_percent',
        progress_percent=50
    )
    intel.record_media_engagement(
        user_id=user_id,
        content_id='intro_video_001',
        media_type='video',
        engagement_type='video_completed',
        progress_percent=100
    )
    print("   ✓ Recorded: video_started → video_50_percent → video_completed")
    
    # Simulate image engagement
    print("\n🖼️ Simulating future image engagement...")
    intel.record_media_engagement(
        user_id=user_id,
        content_id='inspiration_image_001',
        media_type='image',
        engagement_type='image_viewed'
    )
    intel.record_media_engagement(
        user_id=user_id,
        content_id='inspiration_image_001',
        media_type='image',
        engagement_type='image_saved'
    )
    print("   ✓ Recorded: image_viewed → image_saved")
    
    media_summary = intel.get_media_engagement_summary(user_id)
    print_result("Media Engagement Summary", media_summary)
    
    # =========================================================================
    # 8. AI PROMPT CONTEXT (What the AI sees)
    # =========================================================================
    print_section("8. AI PROMPT CONTEXT (What the AI receives)")
    
    ai_context = intel.get_ai_prompt_context(user_id)
    print("\n📝 Context injected into AI prompts:")
    if ai_context:
        for line in ai_context.split('\n'):
            print(f"   {line}")
    else:
        print("   (No context generated yet - need more interaction data)")
    
    # =========================================================================
    # 9. FULL INTELLIGENCE CONTEXT
    # =========================================================================
    print_section("9. FULL INTELLIGENCE CONTEXT (Complete Profile)")
    
    full_context = intel.build_intelligence_context(user_id)
    print_result("Complete User Intelligence", {
        'engagement_signals': full_context.get('engagement', {}).get('total_signals', 0),
        'active_days': full_context.get('engagement', {}).get('active_days', 0),
        'patterns_analyzed': list(full_context.get('patterns', {}).keys()),
        'interest_types': list(full_context.get('interests', {}).keys()),
        'predictions_made': bool(full_context.get('predictions', {}).get('likely_topics')),
        'recommendations_count': len(full_context.get('recommendations', []))
    })
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print_section("✅ TEST SUMMARY")
    
    print(f"""
    User ID: {user_id}
    
    Functions Tested: 15
    ├── record_engagement()              ✓
    ├── get_engagement_summary()         ✓
    ├── analyze_temporal_patterns()      ✓
    ├── analyze_communication_style()    ✓
    ├── analyze_topic_patterns()         ✓
    ├── get_interest_profile()           ✓
    ├── get_character_recommendations()  ✓
    ├── predict_user_needs()             ✓
    ├── get_proactive_suggestions()      ✓
    ├── analyze_conversation_depth()     ✓
    ├── analyze_emotional_journey()      ✓
    ├── get_resolution_rate()            ✓
    ├── record_media_engagement()        ✓
    ├── get_media_engagement_summary()   ✓
    ├── get_ai_prompt_context()          ✓
    └── build_intelligence_context()     ✓
    
    All tests completed successfully!
    """)
    
    conn.close()
    return True

def interactive_mode():
    """Interactive testing mode."""
    print("\n" + "="*60)
    print(" USER INTELLIGENCE SYSTEM - INTERACTIVE TEST MODE")
    print("="*60)
    
    conn = sqlite3.connect('integrated_users.db')
    
    # List available users
    cursor = conn.cursor()
    cursor.execute('SELECT id, username FROM users ORDER BY id LIMIT 20')
    users = cursor.fetchall()
    
    print("\n📋 Available Users:")
    for uid, name in users:
        print(f"   {uid}: {name}")
    
    user_id = input("\nEnter user ID to test (or press Enter for 23): ").strip()
    user_id = int(user_id) if user_id else 23
    
    conn.close()
    test_all_functions(user_id)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '-i' or sys.argv[1] == '--interactive':
            interactive_mode()
        else:
            user_id = int(sys.argv[1])
            test_all_functions(user_id)
    else:
        # Default: test with user 23
        test_all_functions(23)
