"""
Test all AI providers (Google, Anthropic, OpenAI)
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("🧪 TESTING ALL AI PROVIDERS")
print("=" * 70)
print()

# Test Google (Gemini) with automatic fallback
print("1️⃣ Testing Google Gemini API with auto-fallback...")
print("-" * 70)
google_key = os.getenv('GOOGLE_API_KEY')

if google_key:
    try:
        import google.generativeai as genai
        from ai_compare.model_config import get_fallback_models
        
        genai.configure(api_key=google_key)
        
        # Try models in order until one works
        models_to_try = get_fallback_models('google')
        last_error = None
        
        for model_name in models_to_try:
            try:
                print(f"   Trying {model_name}...")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content("Say 'Google works!' in 2 words")
                print(f"✅ Google Response ({model_name}): {response.text.strip()}")
                print("✅ GOOGLE API IS WORKING!")
                break
            except Exception as e:
                last_error = e
                continue
        else:
            # All models failed
            print(f"❌ All Google models failed. Last error: {last_error}")
        
    except Exception as e:
        print(f"❌ Google Error: {str(e)}")
else:
    print("⚠️  Google API key not found")

print()

# Test Anthropic (Claude)
print("2️⃣ Testing Anthropic Claude API...")
print("-" * 70)
anthropic_key = os.getenv('ANTHROPIC_API_KEY')

if anthropic_key:
    try:
        from anthropic import Anthropic
        
        client = Anthropic(api_key=anthropic_key)
        
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[
                {"role": "user", "content": "Say 'Claude works!' in 2 words"}
            ]
        )
        
        print(f"✅ Anthropic Response: {message.content[0].text}")
        print("✅ ANTHROPIC API IS WORKING!")
        
    except Exception as e:
        print(f"❌ Anthropic Error: {str(e)}")
else:
    print("⚠️  Anthropic API key not found")

print()

# Test OpenAI
print("3️⃣ Testing OpenAI API...")
print("-" * 70)
openai_key = os.getenv('OPENAI_API_KEY')

if openai_key:
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=openai_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'OpenAI works!' in 2 words"}
            ],
            max_tokens=10
        )
        
        print(f"✅ OpenAI Response: {response.choices[0].message.content}")
        print("✅ OPENAI API IS WORKING!")
        
    except Exception as e:
        error_msg = str(e)
        if "insufficient_quota" in error_msg:
            print(f"⚠️  OpenAI: Quota issue (billing needed)")
            print("   API key is valid, but account needs billing setup")
        else:
            print(f"❌ OpenAI Error: {error_msg}")
else:
    print("⚠️  OpenAI API key not found")

print()
print("=" * 70)
print("🎯 SUMMARY")
print("=" * 70)
print()
print("Your app can work with:")
print("  - ✅ Google Gemini (if it passed)")
print("  - ✅ Anthropic Claude (if it passed)")
print("  - ⏳ OpenAI GPT (needs billing)")
print()
print("You can deploy and use Google/Anthropic while fixing OpenAI billing!")
print()
print("=" * 70)
