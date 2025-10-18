"""
Motivational Coach Demo Script
Demonstrates the super-motivational coaching system with all features
"""
import asyncio
from datetime import datetime, timedelta
from ai_compare.motivational_chatbot import MotivationalChatbot

async def demo_motivational_coach():
    """Comprehensive demo of the motivational coaching system"""
    print("🚀 SUPER MOTIVATIONAL COACH DEMO - MAX IS READY! 🚀")
    print("=" * 70)
    
    # Initialize Max - the super motivational coach
    coach = MotivationalChatbot(personality_preset="super_motivational_coach")
    
    print(f"\n🎭 Meet {coach.personality.traits.character}!")
    print(f"Character: {coach.personality.traits.character}")
    print(f"Mood: {coach.personality.traits.mood.value}")
    print(f"Goal: {coach.personality.traits.goal.value}")
    print(f"Context Awareness: {coach.personality.traits.context_awareness}")
    print(f"Empathy Level: {coach.personality.traits.empathy_level}")
    print(f"Humor Level: {coach.personality.traits.humor_level}")
    
    print("\n" + "=" * 70)
    print("🎯 CORE FEATURES DEMONSTRATION")
    print("=" * 70)
    
    # Demo 1: Goal Management
    print("\n1️⃣ GOAL MANAGEMENT & ACTIVITY TRACKING")
    print("-" * 50)
    
    sample_interactions = [
        'add goal "Master Python Programming" "Become proficient in Python within 3 months"',
        'add goal "Daily Exercise" "Work out for 30 minutes every day"',
        'schedule activity "Python coding session"',
        'schedule activity "Morning workout"'
    ]
    
    for interaction in sample_interactions:
        print(f"\n👤 User: {interaction}")
        response = await coach.chat(interaction)
        print(f"🤖 Max: {response['response'][:200]}{'...' if len(response['response']) > 200 else ''}")
    
    # Demo 2: Progress Tracking
    print("\n\n2️⃣ PROGRESS TRACKING & FEEDBACK")
    print("-" * 50)
    
    progress_interactions = [
        "show progress",
        "update progress goal_1 25%",
        "show progress"
    ]
    
    for interaction in progress_interactions:
        print(f"\n👤 User: {interaction}")
        response = await coach.chat(interaction)
        print(f"🤖 Max: {response['response'][:300]}{'...' if len(response['response']) > 300 else ''}")
    
    # Demo 3: Motivational Features
    print("\n\n3️⃣ MOTIVATIONAL CONTENT & TIME AWARENESS")
    print("-" * 50)
    
    motivational_interactions = [
        "I'm feeling overwhelmed with my goals",
        "motivate me",
        "I completed my workout today!",
        "upcoming activities"
    ]
    
    for interaction in motivational_interactions:
        print(f"\n👤 User: {interaction}")
        response = await coach.chat(interaction)
        print(f"🤖 Max: {response['response'][:250]}{'...' if len(response['response']) > 250 else ''}")
    
    # Demo 4: Interactive Features
    print("\n\n4️⃣ INTERACTIVE CONVERSATION & ENGAGEMENT")
    print("-" * 50)
    
    interactive_sessions = [
        "How can I stay motivated when things get tough?",
        "What's the best way to build good habits?",
        "I'm struggling to find time for my goals"
    ]
    
    for question in interactive_sessions:
        print(f"\n👤 User: {question}")
        response = await coach.chat(question)
        print(f"🤖 Max: {response['response'][:300]}{'...' if len(response['response']) > 300 else ''}")
    
    # Demo 5: Stats and Analytics
    print("\n\n5️⃣ COMPREHENSIVE STATS & ANALYTICS")
    print("-" * 50)
    
    stats = coach.get_motivational_stats()
    print(f"\n📊 MOTIVATIONAL STATISTICS:")
    print(f"Total Goals: {stats['total_goals']}")
    print(f"Total Activities: {stats['total_activities']}")
    print(f"Current Streak: {stats['system_stats']['streak']} days")
    print(f"Total Achievements: {stats['system_stats']['total_achievements']}")
    print(f"Motivation Trend: {stats['system_stats']['motivation_trend']}")
    print(f"Reminders Active: {stats['reminder_active']}")
    
    # Show progress summary
    progress_summary = coach.motivational_system.get_progress_summary()
    print(f"\n📈 PROGRESS SUMMARY:")
    print(f"Goals Completion Rate: {progress_summary['goals']['completion_rate']:.1f}%")
    print(f"Activities Completion Rate: {progress_summary['activities']['completion_rate']:.1f}%")
    print(f"Average Goal Progress: {progress_summary['goals']['average_progress']:.1f}%")
    
    print("\n" + "=" * 70)
    print("🌟 FEATURE HIGHLIGHTS")
    print("=" * 70)
    
    features = [
        "🎯 Goal Setting & Tracking - Add and monitor progress on personal goals",
        "⏰ Activity Scheduling - Plan and get reminders for important activities", 
        "📊 Progress Analytics - Comprehensive tracking with streaks and achievements",
        "🚀 Super Motivation - High-energy, personalized motivational messages",
        "🧠 Context Awareness - Adapts responses based on user mood and progress",
        "⚡ Time Consciousness - Proactive reminders and time-based motivation",
        "🎉 Celebration System - Acknowledges wins and maintains momentum",
        "💪 Feedback Integration - Learns from user feedback to improve motivation",
        "🔄 Interactive Commands - Easy-to-use commands for quick actions",
        "📱 Real-time Updates - Live stats and progress monitoring"
    ]
    
    for feature in features:
        print(f"  {feature}")
    
    print("\n" + "=" * 70)
    print("🎮 INTERACTIVE DEMO MODE")
    print("=" * 70)
    
    print("\nTry these commands with Max:")
    print("• add goal \"[title]\" \"[description]\"")
    print("• schedule activity \"[activity name]\"") 
    print("• update progress goal_[id] [percentage]%")
    print("• show progress")
    print("• upcoming activities")
    print("• motivate me")
    print("• give feedback")
    print("• Type 'quit' to exit")
    
    print(f"\n🤖 Max: HEY CHAMPION! I'm MAX and I'm PUMPED to help you achieve INCREDIBLE things! 🚀")
    print("What goal are we going to DOMINATE today? Let's make it HAPPEN! 💪⚡")
    
    # Interactive session
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() == 'quit':
                break
            
            if not user_input:
                continue
            
            response = await coach.chat(user_input)
            print(f"\n🤖 Max: {response['response']}")
            
            # Show additional info for certain actions
            if 'motivational_action' in response:
                action = response['motivational_action']
                if action in ['goal_added', 'progress_updated']:
                    print(f"   ✨ Action: {action.replace('_', ' ').title()}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n🎉 Thanks for trying the Super Motivational Coach!")
    print("Remember: Every CHAMPION was once a beginner who refused to give up! 💪🚀")
    print("Keep crushing those goals! Max believes in you! ⚡🔥")

if __name__ == "__main__":
    asyncio.run(demo_motivational_coach())
