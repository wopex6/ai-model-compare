"""
AI Chatbot Demo Script
Demonstrates the chatbot functionality with different personalities
"""
import asyncio
from ai_compare.chatbot import AIChatbot, PERSONALITY_PRESETS

async def demo_chatbot():
    """Demonstrate chatbot functionality"""
    print("🤖 AI Chatbot Demo - Personality-Driven Conversations")
    print("=" * 60)
    
    # Initialize chatbot with helpful assistant personality
    chatbot = AIChatbot(personality_preset="helpful_assistant", user_preset="casual_learner")
    
    # Sample questions to demonstrate different responses
    sample_questions = [
        "What is artificial intelligence?",
        "How can I learn programming?",
        "Tell me a creative story about robots",
        "What's the best way to solve complex problems?"
    ]
    
    print("\n🎭 Available Personality Presets:")
    for preset_name, traits in PERSONALITY_PRESETS.items():
        print(f"  • {preset_name}: {traits.character} ({traits.mood.value}, {traits.goal.value})")
    
    print("\n" + "=" * 60)
    print("💬 Sample Conversations with Different Personalities")
    print("=" * 60)
    
    for question in sample_questions:
        print(f"\n❓ Question: {question}")
        print("-" * 40)
        
        # Get responses from different personalities
        personality_responses = await chatbot.get_personality_comparison(question)
        
        for preset_name, response in personality_responses.items():
            character_name = PERSONALITY_PRESETS[preset_name].character
            mood = PERSONALITY_PRESETS[preset_name].mood.value
            
            print(f"\n🎭 {character_name} ({preset_name.replace('_', ' ').title()}) - {mood}:")
            print(f"   {response[:200]}{'...' if len(response) > 200 else ''}")
    
    print("\n" + "=" * 60)
    print("🔄 Interactive Chat Session")
    print("=" * 60)
    
    # Interactive session
    print("\nStarting interactive chat with Alex (Helpful Assistant)")
    print("Type 'quit' to exit, 'change [personality]' to switch personalities")
    print("Available personalities: helpful_assistant, creative_mentor, technical_expert, curious_explorer")
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() == 'quit':
                break
            
            if user_input.lower().startswith('change '):
                preset = user_input[7:].strip()
                if chatbot.change_personality(preset):
                    print(f"✅ Personality changed to {preset}")
                    continue
                else:
                    print("❌ Invalid personality preset")
                    continue
            
            if not user_input:
                continue
            
            # Get chatbot response
            response_data = await chatbot.chat(user_input, include_context=True)
            
            character = response_data.get('character', 'Bot')
            mood = response_data.get('mood', 'neutral')
            response = response_data.get('response', 'Sorry, I could not generate a response.')
            models_used = response_data.get('response_metadata', {}).get('models_used', 0)
            
            print(f"\n🤖 {character} ({mood}): {response}")
            print(f"   📊 Generated using {models_used} AI models")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Show conversation summary
    print("\n" + "=" * 60)
    print("📊 Conversation Summary")
    print("=" * 60)
    
    summary = chatbot.get_conversation_summary()
    if 'message' not in summary:
        print(f"Session ID: {summary['session_id']}")
        print(f"Total Exchanges: {summary['total_exchanges']}")
        print(f"Average Response Length: {summary['avg_response_length']} characters")
        print(f"Current Character: {summary['current_personality']['character']}")
        print(f"Current Mood: {summary['current_personality']['mood']}")
        print(f"User Communication Style: {summary['user_profile']['communication_style']}")
        print(f"User Expertise Level: {summary['user_profile']['expertise_level']}")
        print(f"User Interests: {', '.join(summary['user_profile']['interests'])}")
    
    print("\n🎉 Demo completed! Thank you for trying the AI Chatbot.")

if __name__ == "__main__":
    asyncio.run(demo_chatbot())
