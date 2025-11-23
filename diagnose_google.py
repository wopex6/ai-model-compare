"""
Diagnose Google API issues and list available models
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("🔍 GOOGLE API DIAGNOSTIC")
print("=" * 70)
print()

google_key = os.getenv('GOOGLE_API_KEY')

if not google_key:
    print("❌ GOOGLE_API_KEY not found in .env")
    exit(1)

print(f"✅ API Key found: {google_key[:15]}...")
print()

# Test 1: Check if we can import and configure
print("Test 1: Import and Configure...")
print("-" * 70)
try:
    import google.generativeai as genai
    genai.configure(api_key=google_key)
    print("✅ Successfully imported and configured")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

print()

# Test 2: List available models
print("Test 2: List Available Models...")
print("-" * 70)
try:
    print("Fetching available models from Google...")
    models = genai.list_models()
    
    available = []
    for model in models:
        # Filter for generative models
        if 'generateContent' in model.supported_generation_methods:
            available.append(model.name)
    
    if available:
        print(f"✅ Found {len(available)} available models:")
        print()
        for i, model_name in enumerate(available, 1):
            # Extract just the model name without 'models/' prefix
            clean_name = model_name.replace('models/', '')
            print(f"   {i}. {clean_name}")
        
        print()
        print("=" * 70)
        print("💡 SOLUTION")
        print("=" * 70)
        print()
        print("Update your model_config.py with these working models:")
        print()
        print("'google': [")
        for model_name in available[:5]:  # Show top 5
            clean_name = model_name.replace('models/', '')
            print(f"    '{clean_name}',")
        print("]")
        
    else:
        print("⚠️  No models found that support generateContent")
        print()
        print("This might mean:")
        print("1. API is not enabled in Google Cloud Console")
        print("2. API key doesn't have correct permissions")
        
except Exception as e:
    print(f"❌ Error listing models: {e}")
    print()
    print("=" * 70)
    print("💡 LIKELY ISSUE")
    print("=" * 70)
    print()
    print("Your Google API is not properly set up.")
    print()
    print("To fix:")
    print()
    print("1. Go to Google AI Studio:")
    print("   https://aistudio.google.com/app/apikey")
    print()
    print("2. Click 'Get API Key' (create new or use existing)")
    print()
    print("3. Make sure you're in a supported region")
    print()
    print("4. Copy the key to your .env file")
    print()
    print("Alternative: Use Google Cloud Console")
    print("1. https://console.cloud.google.com/apis/library")
    print("2. Search: 'Generative Language API'")
    print("3. Click 'Enable'")
    print("4. Create credentials (API key)")

print()
print("=" * 70)
