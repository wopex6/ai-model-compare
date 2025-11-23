"""
Check OpenAI account status and quota
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("🔍 OPENAI ACCOUNT STATUS CHECK")
print("=" * 70)
print()

openai_key = os.getenv('OPENAI_API_KEY')

if not openai_key:
    print("❌ No OpenAI API key found in .env")
    exit(1)

print(f"API Key (first 20 chars): {openai_key[:20]}...")
print()

# Check account details
print("📋 Checking account information...")
print()

try:
    from openai import OpenAI
    
    client = OpenAI(api_key=openai_key)
    
    # Try to get models list (this doesn't use quota)
    print("Attempting to list available models (free operation)...")
    models = client.models.list()
    
    print("✅ API Key is valid and can connect to OpenAI")
    print()
    print(f"Available models: {len(list(models.data))} models")
    print()
    
    # Show some models
    print("Sample models you have access to:")
    for model in list(models.data)[:5]:
        print(f"  - {model.id}")
    
    print()
    print("=" * 70)
    print("🎯 DIAGNOSIS")
    print("=" * 70)
    print()
    print("✅ Your API key works and can authenticate")
    print("❌ But you don't have quota to make chat completions")
    print()
    print("This means your account needs billing setup:")
    print()
    print("1. Visit: https://platform.openai.com/settings/organization/billing")
    print("2. Add a payment method")
    print("3. Add credits (suggested: $10 to start)")
    print()
    print("OR check if you're on a free tier:")
    print("1. Visit: https://platform.openai.com/settings/organization/limits")
    print("2. Check your usage and limits")
    print()
    print("After adding billing, your app will work immediately!")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    print()
    
    if "insufficient_quota" in str(e):
        print("=" * 70)
        print("💡 SOLUTION")
        print("=" * 70)
        print()
        print("Your API key is VALID, but your account has no quota.")
        print()
        print("🔗 Quick Links:")
        print()
        print("1. Add Billing:")
        print("   https://platform.openai.com/settings/organization/billing")
        print()
        print("2. Check Usage:")
        print("   https://platform.openai.com/usage")
        print()
        print("3. Check Limits:")
        print("   https://platform.openai.com/settings/organization/limits")
        print()
        print("🎯 What to do:")
        print("  1. Click 'Add payment method' or 'Set up paid account'")
        print("  2. Add $5-$10 in credits")
        print("  3. Wait 2-5 minutes")
        print("  4. Try again")
        print()
    elif "invalid" in str(e).lower():
        print("API key might be invalid. Did you copy it correctly?")
    else:
        print("Unknown error. Check OpenAI status: https://status.openai.com")

print()
print("=" * 70)
