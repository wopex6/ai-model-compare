#!/usr/bin/env python3

print("Testing imports and model creation...")

try:
    # Test the import that app.py uses
    from ai_compare.simple_compare import SimpleAICompare
    print("✓ SimpleAICompare imported")
    
    # Test creating the comparer (this is what fails in app.py line 8)
    comparer = SimpleAICompare()
    print("✓ SimpleAICompare created")
    
    # Test getting available models
    models = comparer.get_available_models()
    print(f"✓ Available models: {models}")
    
    # Test asking a question (this is what fails in app.py line 27)
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    responses = loop.run_until_complete(comparer.ask_all("Hello"))
    loop.close()
    print(f"✓ Question asked successfully: {list(responses.keys())}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
