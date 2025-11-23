"""
Test script to demonstrate real-time data access in AI chatbot
"""

import asyncio
from ai_compare.chatbot import AIChatbot
from ai_compare.tools import AITools

async def test_weather_query():
    """Test weather queries with real-time data"""
    
    print("\n" + "="*70)
    print("🌤️  TESTING REAL-TIME WEATHER DATA")
    print("="*70)
    
    chatbot = AIChatbot(personality_preset="helpful_assistant")
    
    # Test 1: Weather query
    print("\n📍 TEST 1: Weather Query")
    print("-"*70)
    user_message = "What's the temperature in Tokyo right now?"
    print(f"User: {user_message}")
    
    response = await chatbot.chat(user_message)
    print(f"\n{response['character']}: {response['response']}")
    
    # Show metadata
    if response['response_metadata'].get('tools_used'):
        print("\n✅ Real-time data was used!")
        if response['response_metadata'].get('real_time_data'):
            print(f"📊 Data fetched: {response['response_metadata']['real_time_data']}")
    else:
        print("\n❌ No real-time data used (generic response)")
    
    # Test 2: Another location
    print("\n" + "-"*70)
    print("\n📍 TEST 2: Different Location")
    print("-"*70)
    user_message2 = "How's the weather in London?"
    print(f"User: {user_message2}")
    
    response2 = await chatbot.chat(user_message2)
    print(f"\n{response2['character']}: {response2['response']}")
    
    if response2['response_metadata'].get('real_time_data'):
        weather_data = response2['response_metadata']['real_time_data'].get('weather', {})
        if weather_data and 'error' not in weather_data:
            print("\n📊 Real-time weather data:")
            print(f"   - Temperature: {weather_data.get('temperature')}")
            print(f"   - Condition: {weather_data.get('condition')}")
            print(f"   - Humidity: {weather_data.get('humidity')}")
            print(f"   - Wind: {weather_data.get('wind_speed')}")
    
    # Test 3: Time query
    print("\n" + "-"*70)
    print("\n🕐 TEST 3: Current Time")
    print("-"*70)
    user_message3 = "What time is it now?"
    print(f"User: {user_message3}")
    
    response3 = await chatbot.chat(user_message3)
    print(f"\n{response3['character']}: {response3['response']}")
    
    # Test 4: Non-real-time query (should work without tools)
    print("\n" + "-"*70)
    print("\n💬 TEST 4: General Question (No Real-Time Data Needed)")
    print("-"*70)
    user_message4 = "What is Python programming?"
    print(f"User: {user_message4}")
    
    response4 = await chatbot.chat(user_message4)
    print(f"\n{response4['character']}: {response4['response']}")
    print(f"\n📊 Tools used: {response4['response_metadata'].get('tools_used', False)}")
    
    print("\n" + "="*70)
    print("✅ TESTING COMPLETE")
    print("="*70)


async def test_direct_tools():
    """Test tools directly"""
    
    print("\n" + "="*70)
    print("🛠️  TESTING TOOLS DIRECTLY")
    print("="*70)
    
    tools = AITools()
    
    # Test weather
    print("\n1. Testing weather API...")
    weather = tools.get_weather("Sydney")
    print(f"   Sydney: {weather.get('temperature', 'N/A')}, {weather.get('condition', 'N/A')}")
    
    # Test time
    print("\n2. Testing time API...")
    time_data = tools.get_current_time("America/New_York")
    print(f"   New York: {time_data.get('datetime', 'N/A')}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    print("\n🚀 Starting Real-Time Data Tests...\n")
    
    # Test direct tools first
    asyncio.run(test_direct_tools())
    
    # Then test chatbot integration
    asyncio.run(test_weather_query())
    
    print("\n✨ All tests completed!\n")
