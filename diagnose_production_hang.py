"""
Production Hang Diagnostic Script
Run this on PythonAnywhere to identify where the hang occurs
"""
import sys
import time
import traceback
from datetime import datetime

def log(msg):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")
    sys.stdout.flush()

log("=" * 70)
log("PRODUCTION HANG DIAGNOSTIC")
log("=" * 70)

# Test 1: Import httpx
log("\n1. Testing httpx import...")
try:
    import httpx
    log(f"   ✅ httpx version: {httpx.__version__}")
except ImportError as e:
    log(f"   ❌ httpx NOT installed: {e}")
    log("   FIX: pip3.10 install --user httpx")
    sys.exit(1)

# Test 2: Check timeout in models.py
log("\n2. Checking models.py timeout configuration...")
try:
    with open('ai_compare/models.py', 'r') as f:
        content = f.read()
        if 'timeout=20.0' in content:
            log("   ✅ models.py has timeout=20.0")
        else:
            log("   ❌ models.py missing timeout!")
        
        if 'import httpx' in content:
            log("   ✅ models.py imports httpx")
        else:
            log("   ❌ models.py doesn't import httpx!")
except Exception as e:
    log(f"   ❌ Error reading models.py: {e}")

# Test 3: Check timeout in model_discovery.py
log("\n3. Checking model_discovery.py timeout configuration...")
try:
    with open('ai_compare/model_discovery.py', 'r') as f:
        content = f.read()
        if 'timeout=10.0' in content:
            log("   ✅ model_discovery.py has timeout=10.0")
        else:
            log("   ❌ model_discovery.py missing timeout!")
        
        if 'import httpx' in content:
            log("   ✅ model_discovery.py imports httpx")
        else:
            log("   ❌ model_discovery.py doesn't import httpx!")
except Exception as e:
    log(f"   ❌ Error reading model_discovery.py: {e}")

# Test 4: Check API keys
log("\n4. Checking API keys...")
import os
from dotenv import load_dotenv
load_dotenv()

openai_key = os.getenv('OPENAI_API_KEY')
anthropic_key = os.getenv('ANTHROPIC_API_KEY')

if openai_key and openai_key.strip():
    log(f"   ✅ OPENAI_API_KEY found ({len(openai_key)} chars)")
else:
    log("   ⚠️  OPENAI_API_KEY missing or empty")

if anthropic_key and anthropic_key.strip():
    log(f"   ✅ ANTHROPIC_API_KEY found ({len(anthropic_key)} chars)")
else:
    log("   ⚠️  ANTHROPIC_API_KEY missing or empty")

# Test 5: Test AsyncOpenAI with timeout
log("\n5. Testing AsyncOpenAI with timeout...")
if openai_key:
    try:
        import asyncio
        from openai import AsyncOpenAI
        
        log("   Creating AsyncOpenAI client with 5s timeout...")
        client = AsyncOpenAI(
            api_key=openai_key,
            timeout=5.0,
            http_client=httpx.AsyncClient(
                timeout=5.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        )
        log("   ✅ Client created successfully")
        
        # Try a simple API call
        log("   Testing model list (5s timeout)...")
        start = time.time()
        
        async def test_list():
            try:
                models = await client.models.list()
                return list(models.data)[:3]  # First 3 models
            except Exception as e:
                return str(e)
        
        result = asyncio.run(test_list())
        elapsed = time.time() - start
        
        log(f"   ✅ API call completed in {elapsed:.2f}s")
        log(f"   Result: {result}")
        
    except Exception as e:
        log(f"   ❌ Error: {e}")
        traceback.print_exc()
else:
    log("   ⏭️  Skipped (no API key)")

# Test 6: Test model discovery
log("\n6. Testing ModelDiscovery...")
try:
    from ai_compare.model_discovery import ModelDiscovery
    log("   ✅ ModelDiscovery imported")
    
    discovery = ModelDiscovery()
    log("   ✅ ModelDiscovery instantiated")
    
    if openai_key:
        log("   Testing get_openai_models...")
        start = time.time()
        
        async def test_discovery():
            return await discovery.get_openai_models(openai_key)
        
        models = asyncio.run(test_discovery())
        elapsed = time.time() - start
        
        log(f"   ✅ Discovery completed in {elapsed:.2f}s")
        log(f"   Found {len(models)} models: {models}")
    
except Exception as e:
    log(f"   ❌ Error: {e}")
    traceback.print_exc()

# Test 7: Test ChatGPTModel
log("\n7. Testing ChatGPTModel...")
try:
    from ai_compare.models import ChatGPTModel
    log("   ✅ ChatGPTModel imported")
    
    if openai_key:
        log("   Creating ChatGPTModel instance...")
        model = ChatGPTModel()
        log("   ✅ Instance created")
        
        log("   Testing get_response with 'Hello' (20s timeout)...")
        start = time.time()
        
        async def test_chat():
            return await model.get_response("Say 'Hi' in one word")
        
        response = asyncio.run(test_chat())
        elapsed = time.time() - start
        
        log(f"   ✅ Response in {elapsed:.2f}s: {response[:50]}...")
    
except Exception as e:
    log(f"   ❌ Error: {e}")
    traceback.print_exc()

# Test 8: Database check
log("\n8. Testing database access...")
try:
    from integrated_database import IntegratedDatabase
    db = IntegratedDatabase()
    log("   ✅ Database connected")
    
    # Quick test query
    start = time.time()
    result = db.execute_query("SELECT COUNT(*) FROM users", fetch_one=True)
    elapsed = time.time() - start
    log(f"   ✅ Query completed in {elapsed:.2f}s")
    log(f"   User count: {result[0] if result else 'N/A'}")
    
except Exception as e:
    log(f"   ❌ Error: {e}")
    traceback.print_exc()

log("\n" + "=" * 70)
log("DIAGNOSTIC COMPLETE")
log("=" * 70)
log("\nIf all tests pass, the issue might be:")
log("1. Smart Response system")
log("2. Context manager")
log("3. Session/cookie handling")
log("4. Frontend timeout (check browser console)")
log("5. PythonAnywhere worker limits")
log("\nNext: Check PythonAnywhere error logs:")
log("  tail -50 /var/log/trabcd.pythonanywhere.com.error.log")
