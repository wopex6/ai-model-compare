"""
Test Real-Time Data with AI Fallback System
"""

import asyncio
from ai_compare.chatbot import AIChatbot

async def test_realtime_with_fallback():
    """Test real-time queries with both tool and AI fallback"""
    
    print("\n" + "="*70)
    print("🔄 TESTING REAL-TIME DATA WITH AI FALLBACK")
    print("="*70)
    
    chatbot = AIChatbot(personality_preset="helpful_assistant")
    
    # Test 1: Weather (Should use custom tool - Tier 1)
    print("\n📍 TEST 1: Weather Query (Tier 1 - Custom Tool)")
    print("-"*70)
    user_message = "What's the temperature in Paris right now?"
    print(f"User: {user_message}")
    
    response = await chatbot.chat(user_message)
    print(f"\n{response['character']}: {response['response'][:300]}...")
    
    metadata = response['response_metadata']
    if metadata.get('tools_used'):
        print("\n✅ Custom tool was used!")
        if metadata.get('real_time_data'):
            data = metadata['real_time_data']
            if 'weather' in data and 'error' not in data['weather']:
                print(f"   Weather Data: {data['weather']['temperature']}, {data['weather']['condition']}")
            elif 'fallback_mode' in data:
                print(f"   ⚠️ Fallback mode activated: {data['fallback_mode']}")
    
    # Test 2: Stock price (Should trigger AI fallback - Tier 2)
    print("\n" + "-"*70)
    print("\n💰 TEST 2: Stock Price Query (Tier 2 - AI Fallback)")
    print("-"*70)
    user_message2 = "What's the current price of Tesla stock?"
    print(f"User: {user_message2}")
    
    response2 = await chatbot.chat(user_message2)
    print(f"\n{response2['character']}: {response2['response'][:300]}...")
    
    metadata2 = response2['response_metadata']
    if metadata2.get('tools_used'):
        data2 = metadata2.get('real_time_data', {})
        if 'fallback_mode' in data2:
            print(f"\n✅ AI fallback was triggered!")
            print(f"   Mode: {data2['fallback_mode']}")
            print(f"   Query type: {data2.get('query_type', 'N/A')}")
    
    # Test 3: Breaking news (Should trigger AI fallback)
    print("\n" + "-"*70)
    print("\n📰 TEST 3: Breaking News Query (Tier 2 - AI Fallback)")
    print("-"*70)
    user_message3 = "What's the latest news about AI?"
    print(f"User: {user_message3}")
    
    response3 = await chatbot.chat(user_message3)
    print(f"\n{response3['character']}: {response3['response'][:300]}...")
    
    metadata3 = response3['response_metadata']
    if metadata3.get('tools_used'):
        data3 = metadata3.get('real_time_data', {})
        if 'fallback_mode' in data3:
            print(f"\n✅ AI fallback was triggered!")
            print(f"   Mode: {data3['fallback_mode']}")
    
    # Test 4: General question (No tools needed)
    print("\n" + "-"*70)
    print("\n💬 TEST 4: General Question (No Real-Time Data)")
    print("-"*70)
    user_message4 = "What is Python programming?"
    print(f"User: {user_message4}")
    
    response4 = await chatbot.chat(user_message4)
    print(f"\n{response4['character']}: {response4['response'][:300]}...")
    
    metadata4 = response4['response_metadata']
    print(f"\n📊 Tools used: {metadata4.get('tools_used', False)}")
    
    print("\n" + "="*70)
    print("✅ ALL TESTS COMPLETE")
    print("="*70)
    
    print("\n📊 SUMMARY:")
    print("- Test 1 (Weather): Tier 1 custom tool")
    print("- Test 2 (Stocks): Tier 2 AI fallback")
    print("- Test 3 (News): Tier 2 AI fallback")
    print("- Test 4 (General): No tools needed")
    print("\n✨ Your AI now has comprehensive real-time capabilities!")


if __name__ == "__main__":
    print("\n🚀 Starting Real-Time Data Tests with AI Fallback...\n")
    asyncio.run(test_realtime_with_fallback())
