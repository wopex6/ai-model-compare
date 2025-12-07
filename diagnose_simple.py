"""
Simple Production Diagnostic - No dependencies
"""
import sys
import os

print("=" * 70)
print("SIMPLE DIAGNOSTIC")
print("=" * 70)

# 1. Check API keys from environment
print("\n1. Checking environment variables...")
openai_key = os.environ.get('OPENAI_API_KEY', '')
anthropic_key = os.environ.get('ANTHROPIC_API_KEY', '')

if openai_key:
    print(f"   ✅ OPENAI_API_KEY found ({len(openai_key)} chars)")
else:
    print("   ❌ OPENAI_API_KEY not in environment!")
    print("   Check: ~/.bashrc or PythonAnywhere Web tab > Environment variables")

if anthropic_key:
    print(f"   ✅ ANTHROPIC_API_KEY found ({len(anthropic_key)} chars)")
else:
    print("   ⚠️  ANTHROPIC_API_KEY not in environment")

# 2. Check if .env file exists
print("\n2. Checking .env file...")
if os.path.exists('.env'):
    print("   ✅ .env file exists")
    # Try to read it
    try:
        with open('.env', 'r') as f:
            lines = [l.strip() for l in f.readlines() if l.strip() and not l.startswith('#')]
            print(f"   Found {len(lines)} config lines")
            for line in lines:
                if 'API_KEY' in line and '=' in line:
                    key_name = line.split('=')[0]
                    print(f"   - {key_name}")
    except Exception as e:
        print(f"   ⚠️  Can't read .env: {e}")
else:
    print("   ⚠️  .env file not found!")
    print("   You need to create it or set environment variables in PythonAnywhere")

# 3. Test imports
print("\n3. Testing Python imports...")
try:
    import httpx
    print(f"   ✅ httpx: {httpx.__version__}")
except ImportError:
    print("   ❌ httpx not installed!")
    sys.exit(1)

try:
    from openai import AsyncOpenAI
    print("   ✅ openai library installed")
except ImportError as e:
    print(f"   ❌ openai not installed: {e}")

try:
    import anthropic
    print("   ✅ anthropic library installed")
except ImportError as e:
    print(f"   ⚠️  anthropic not installed: {e}")

try:
    from dotenv import load_dotenv
    print("   ✅ python-dotenv installed")
except ImportError:
    print("   ⚠️  python-dotenv not installed")
    print("   This might be why .env isn't loading!")
    print("   Install: pip3.10 install --user python-dotenv")

# 4. Quick OpenAI test (if key available)
if openai_key:
    print("\n4. Testing OpenAI API with timeout...")
    try:
        import asyncio
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=openai_key,
            timeout=5.0,
            http_client=httpx.AsyncClient(timeout=5.0)
        )
        print("   ✅ Client created with timeout")
        
        # Try listing models
        async def test():
            try:
                models = await client.models.list()
                return "SUCCESS"
            except Exception as e:
                return str(e)
        
        import time
        start = time.time()
        result = asyncio.run(test())
        elapsed = time.time() - start
        
        if "SUCCESS" in result:
            print(f"   ✅ API call successful ({elapsed:.2f}s)")
        else:
            print(f"   ⚠️  API call failed: {result[:100]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
else:
    print("\n4. ⏭️  Skipping API test (no OPENAI_API_KEY)")

# 5. Check error log
print("\n5. Checking recent error log...")
log_file = '/var/log/trabcd.pythonanywhere.com.error.log'
if os.path.exists(log_file):
    try:
        # Read last 20 lines
        with open(log_file, 'r') as f:
            lines = f.readlines()[-20:]
        
        print(f"   Last {len(lines)} lines from error log:")
        print("   " + "-" * 60)
        for line in lines:
            print(f"   {line.rstrip()}")
        print("   " + "-" * 60)
    except Exception as e:
        print(f"   ⚠️  Can't read log: {e}")
else:
    print(f"   ⚠️  Log file not found: {log_file}")

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)

# Summary
print("\nSUMMARY:")
if not openai_key and not anthropic_key:
    print("❌ CRITICAL: No API keys found!")
    print("   Action: Set environment variables in PythonAnywhere Web tab")
elif openai_key:
    print("✅ API keys configured")
    print("✅ Timeout code present")
    print("✅ httpx installed")
    print("\nIf still hanging, check the error log above for specific errors.")
else:
    print("⚠️  Partial configuration - may have issues")

print("\nNext: Check error log for actual hang location")
