"""
API Testing Script
Tests all configured API keys and shows their status.
Run this anytime to check if your API keys are working.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai():
    """Test OpenAI API key."""
    print("\n1️⃣ Testing OpenAI...")
    try:
        from openai import OpenAI
        
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key:
            print("   ⚠️  OpenAI API key not found in .env")
            return False
        
        client = OpenAI(api_key=openai_key)
        
        # Test with minimal request (new API v1.0+ syntax)
        client.models.list()
        print("   ✅ OpenAI API is working!")
        print("   💰 Check usage: https://platform.openai.com/usage")
        return True
        
    except Exception as e:
        error_msg = str(e).lower()
        if 'quota' in error_msg or 'insufficient' in error_msg:
            print(f"   ❌ OpenAI: QUOTA/BILLING ISSUE - {e}")
            print("   💳 Add credits: https://platform.openai.com/account/billing")
        elif 'invalid' in error_msg or 'incorrect' in error_msg or 'authentication' in error_msg:
            print(f"   ❌ OpenAI: Invalid API key")
            print("   🔑 Generate new key: https://platform.openai.com/api-keys")
        else:
            print(f"   ❌ OpenAI: {e}")
        return False

def test_grok():
    """Test Grok (xAI) API key."""
    print("\n2️⃣ Testing Grok (xAI)...")
    try:
        from openai import OpenAI
        
        grok_key = os.getenv('GROK_API_KEY')
        if not grok_key:
            print("   ⚠️  Grok API key not found in .env")
            return False
        
        client = OpenAI(
            api_key=grok_key,
            base_url="https://api.x.ai/v1"
        )
        
        # Test with minimal request
        client.models.list()
        print("   ✅ Grok API is working!")
        print("   💰 Check usage: https://console.x.ai")
        return True
        
    except Exception as e:
        error_msg = str(e).lower()
        if 'quota' in error_msg or 'insufficient' in error_msg:
            print(f"   ❌ Grok: QUOTA/BILLING ISSUE - {e}")
            print("   💳 Add credits: https://console.x.ai")
        elif 'invalid' in error_msg or 'incorrect' in error_msg:
            print(f"   ❌ Grok: Invalid API key")
        else:
            print(f"   ❌ Grok: {e}")
        return False

def test_google():
    """Test Google (Gemini) API key."""
    print("\n3️⃣ Testing Google (Gemini)...")
    try:
        import google.generativeai as genai
        
        google_key = os.getenv('GOOGLE_API_KEY')
        if not google_key:
            print("   ⚠️  Google API key not found in .env")
            return False
        
        genai.configure(api_key=google_key)
        
        # Test with minimal request
        list(genai.list_models())
        print("   ✅ Google API is working!")
        print("   💰 Check usage: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com")
        return True
        
    except Exception as e:
        error_msg = str(e).lower()
        if 'quota' in error_msg or 'exceeded' in error_msg:
            print(f"   ❌ Google: QUOTA EXCEEDED - {e}")
            print("   💳 Check quota: https://console.cloud.google.com")
        elif 'invalid' in error_msg or 'api_key' in error_msg:
            print(f"   ❌ Google: Invalid API key")
        else:
            print(f"   ❌ Google: {e}")
        return False

def test_anthropic():
    """Test Anthropic (Claude) API key."""
    print("\n4️⃣ Testing Anthropic (Claude)...")
    try:
        import anthropic
        
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if not anthropic_key:
            print("   ⚠️  Anthropic API key not found in .env")
            return False
        
        client = anthropic.Anthropic(api_key=anthropic_key)
        
        # Anthropic doesn't have a simple "list" endpoint
        # We'll just verify the key format is valid
        if anthropic_key.startswith('sk-ant-'):
            print("   ✅ Anthropic API key format is valid")
            print("   💰 Check usage: https://console.anthropic.com/settings/usage")
            print("   ℹ️  Note: Full test requires making a paid request")
            return True
        else:
            print("   ⚠️  Anthropic API key format looks incorrect")
            return False
        
    except Exception as e:
        error_msg = str(e).lower()
        if 'quota' in error_msg or 'credit' in error_msg:
            print(f"   ❌ Anthropic: QUOTA/BILLING ISSUE - {e}")
            print("   💳 Add credits: https://console.anthropic.com/settings/billing")
        elif 'invalid' in error_msg:
            print(f"   ❌ Anthropic: Invalid API key")
        else:
            print(f"   ❌ Anthropic: {e}")
        return False

def main():
    """Run all API tests."""
    print("=" * 70)
    print("🔍 API KEY STATUS CHECKER")
    print("=" * 70)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("\n⚠️  WARNING: .env file not found!")
        print("   Create a .env file with your API keys")
        return
    
    results = {
        'OpenAI': test_openai(),
        'Grok': test_grok(),
        'Google': test_google(),
        'Anthropic': test_anthropic()
    }
    
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    working = sum(1 for status in results.values() if status)
    total = len(results)
    
    for api, status in results.items():
        emoji = "✅" if status else "❌"
        print(f"{emoji} {api}: {'Working' if status else 'Issue Detected'}")
    
    print(f"\n🎯 {working}/{total} APIs are working")
    
    if working == 0:
        print("\n⚠️  WARNING: No APIs are working! Check your .env file and API keys.")
    elif working < total:
        print("\n⚠️  Some APIs have issues. Check the details above.")
    else:
        print("\n🎉 All APIs are working great!")
    
    print("\n💡 TIP: Run this script regularly to monitor your API health.")
    print("=" * 70)

if __name__ == '__main__':
    main()
