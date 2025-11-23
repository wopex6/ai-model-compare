"""
Test script to verify new API keys work correctly
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("🔑 API KEY VERIFICATION TEST")
print("=" * 60)
print()

# Check if keys are loaded
print("📋 Step 1: Checking if API keys are loaded from .env...")
print()

openai_key = os.getenv('OPENAI_API_KEY')
google_key = os.getenv('GOOGLE_API_KEY')
anthropic_key = os.getenv('ANTHROPIC_API_KEY')

if openai_key:
    print(f"✅ OpenAI API Key: Found (starts with: {openai_key[:15]}...)")
else:
    print("❌ OpenAI API Key: NOT FOUND in .env")

if google_key:
    print(f"✅ Google API Key: Found (starts with: {google_key[:10]}...)")
else:
    print("⚠️  Google API Key: NOT FOUND (optional)")

if anthropic_key:
    print(f"✅ Anthropic API Key: Found (starts with: {anthropic_key[:15]}...)")
else:
    print("⚠️  Anthropic API Key: NOT FOUND (optional)")

print()
print("=" * 60)
print("🧪 Step 2: Testing OpenAI API Connection...")
print("=" * 60)
print()

if openai_key:
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=openai_key)
        
        print("Sending test request to OpenAI...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'API key works!' in exactly 3 words."}
            ],
            max_tokens=10
        )
        
        result = response.choices[0].message.content
        print(f"✅ OpenAI Response: {result}")
        print("✅ OpenAI API Key is WORKING!")
        
    except Exception as e:
        print(f"❌ OpenAI API Error: {str(e)}")
        print()
        print("Common issues:")
        print("  - Key might be invalid or revoked")
        print("  - Check permissions (needs 'Model capabilities: Request')")
        print("  - Verify key was copied correctly (no spaces)")
else:
    print("❌ Cannot test - OpenAI key not found")

print()
print("=" * 60)
print("🎯 SUMMARY")
print("=" * 60)

if openai_key and 'API key works' in str(locals().get('result', '')):
    print("✅ All systems ready for deployment!")
    print("✅ Your new OpenAI API key is working correctly")
    print()
    print("Next steps:")
    print("1. Run: .\\fix_security.bat (to clean git)")
    print("2. Follow: DEPLOY_CHECKLIST.md")
else:
    print("⚠️  Please check your .env file configuration")
    print()
    print("Your .env file should look like:")
    print("OPENAI_API_KEY=sk-proj-YOUR_NEW_KEY_HERE")
    print("GOOGLE_API_KEY=AIza_YOUR_KEY_HERE")
    print("ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE")

print()
print("=" * 60)
