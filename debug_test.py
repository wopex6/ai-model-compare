#!/usr/bin/env python3

try:
    print("=== Testing AI Compare Import ===")
    
    # Test 1: Import simple_models
    print("1. Importing simple_models...")
    from ai_compare.simple_models import ChatGPTModel
    print("   ✓ simple_models imported successfully")
    
    # Test 2: Create ChatGPT model
    print("2. Creating ChatGPTModel...")
    model = ChatGPTModel()
    print("   ✓ ChatGPTModel created successfully")
    
    # Test 3: Import SimpleAICompare
    print("3. Importing SimpleAICompare...")
    from ai_compare.simple_compare import SimpleAICompare
    print("   ✓ SimpleAICompare imported successfully")
    
    # Test 4: Create comparer
    print("4. Creating SimpleAICompare...")
    comparer = SimpleAICompare()
    print("   ✓ SimpleAICompare created successfully")
    
    # Test 5: Get available models
    print("5. Getting available models...")
    models = comparer.get_available_models()
    print(f"   ✓ Available models: {models}")
    
    print("\n=== All tests passed! ===")
    
except Exception as e:
    print(f"✗ Sync call failed: {e}")

print("\n=== Testing Async OpenAI Call ===")
import asyncio

async def test_async():
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello World'"}
            ]
        )
        print(f"✓ Async call successful: {response.choices[0].message.content}")
    except Exception as e:
        print(f"✗ Async call failed: {e}")

asyncio.run(test_async())
