"""
Fix for production: Ensure .env loads with absolute path
This should be run to test the fix before applying to app.py
"""
import os
from pathlib import Path

print("=" * 70)
print("TESTING ABSOLUTE PATH FIX")
print("=" * 70)

# Get the directory where THIS script is located
# This will be the same directory as app.py
script_dir = Path(__file__).parent.absolute()
env_path = script_dir / '.env'

print(f"\n1. Script directory: {script_dir}")
print(f"2. .env path: {env_path}")
print(f"3. .env exists: {env_path.exists()}")
print(f"4. Current working directory: {os.getcwd()}")

# Load dotenv with ABSOLUTE path
from dotenv import load_dotenv

print(f"\n5. Loading with absolute path...")
result = load_dotenv(env_path, override=True)
print(f"   Result: {result}")

# Check if loaded
openai_key = os.getenv('OPENAI_API_KEY')
if openai_key:
    print(f"\n✅ SUCCESS! API key loaded: {openai_key[:20]}...")
else:
    print(f"\n❌ FAILED! API key not loaded")

print("\n" + "=" * 70)
print("RECOMMENDED FIX:")
print("=" * 70)
print("""
In app.py, BEFORE any other imports, add:

from pathlib import Path
from dotenv import load_dotenv

# Load .env with ABSOLUTE path (critical for WSGI)
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

Then remove the load_dotenv() call on line 40.
""")
