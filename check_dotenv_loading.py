#!/usr/bin/env python3.10
"""
Test if .env file loads correctly on production
"""
from dotenv import load_dotenv
import os
from pathlib import Path

print("=" * 70)
print("DOTENV LOADING TEST")
print("=" * 70)

# 1. Check .env file
env_path = Path('.env')
print(f"\n1. .env file check:")
print(f"   Exists: {env_path.exists()}")
if env_path.exists():
    print(f"   Size: {env_path.stat().st_size} bytes")
    print(f"   Location: {env_path.absolute()}")

# 2. Clear environment first
print(f"\n2. Clearing existing environment variables...")
for key in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY']:
    if key in os.environ:
        print(f"   Removing existing {key}")
        os.environ.pop(key)

# 3. Try to load .env
print(f"\n3. Loading .env file...")
try:
    # Explicitly specify .env path
    result = load_dotenv('.env', override=True, verbose=True)
    print(f"   load_dotenv() returned: {result}")
except Exception as e:
    print(f"   ❌ Error loading .env: {e}")
    import traceback
    traceback.print_exc()

# 4. Check what was loaded
print(f"\n4. Checking loaded variables:")
keys_to_check = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY', 'GROK_API_KEY']

for key in keys_to_check:
    value = os.getenv(key)
    if value:
        print(f"   ✅ {key}: {value[:15]}... ({len(value)} chars)")
    else:
        print(f"   ❌ {key}: NOT LOADED")

# 5. Analyze .env file format
print(f"\n5. Analyzing .env file format:")
if env_path.exists():
    with open('.env', 'rb') as f:
        raw_content = f.read()
    
    # Check line endings
    has_crlf = b'\r\n' in raw_content
    has_lf = b'\n' in raw_content
    
    print(f"   Line endings: ", end="")
    if has_crlf:
        print("CRLF (Windows) ⚠️")
    elif has_lf:
        print("LF (Unix) ✅")
    else:
        print("Unknown")
    
    # Parse lines
    with open('.env', 'r') as f:
        lines = f.readlines()
    
    print(f"   Total lines: {len(lines)}")
    print(f"\n   Line-by-line analysis:")
    
    for i, line in enumerate(lines, 1):
        if line.strip() and not line.strip().startswith('#'):
            # Show sanitized version
            if '=' in line:
                key_part = line.split('=', 1)[0]
                val_part = line.split('=', 1)[1]
                
                issues = []
                if line.rstrip() != line.rstrip('\n').rstrip('\r'):
                    issues.append("trailing whitespace")
                if ' = ' in line:
                    issues.append("space around =")
                if val_part.strip().startswith('"') or val_part.strip().startswith("'"):
                    issues.append("quoted value")
                if key_part != key_part.strip():
                    issues.append("space before key")
                
                status = "⚠️" if issues else "✅"
                print(f"   Line {i:2d}: {status} {key_part.strip()} = <{len(val_part.strip())} chars>", end="")
                if issues:
                    print(f" - Issues: {', '.join(issues)}")
                else:
                    print()

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
