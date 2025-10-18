#!/usr/bin/env python3

import os
from dotenv import load_dotenv

print("=== Testing Environment Variable Loading ===")

# Test 1: Check current environment
print(f"1. Current env OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', 'NOT FOUND')[:20]}..." if os.getenv('OPENAI_API_KEY') else "1. Current env OPENAI_API_KEY: NOT FOUND")

# Test 2: Load .env without override
load_dotenv()
print(f"2. After load_dotenv(): {os.getenv('OPENAI_API_KEY', 'NOT FOUND')[:20]}..." if os.getenv('OPENAI_API_KEY') else "2. After load_dotenv(): NOT FOUND")

# Test 3: Load .env with override
load_dotenv(override=True)
print(f"3. After load_dotenv(override=True): {os.getenv('OPENAI_API_KEY', 'NOT FOUND')[:20]}..." if os.getenv('OPENAI_API_KEY') else "3. After load_dotenv(override=True): NOT FOUND")

# Test 4: Check if .env file exists
env_path = '.env'
if os.path.exists(env_path):
    print(f"4. .env file exists at: {os.path.abspath(env_path)}")
    with open(env_path, 'r') as f:
        content = f.read()
        if 'OPENAI_API_KEY' in content:
            print("   - OPENAI_API_KEY found in .env file")
        else:
            print("   - OPENAI_API_KEY NOT found in .env file")
else:
    print("4. .env file NOT found")

# Test 5: Test the get_api_key function
def get_api_key(key_name: str):
    key = os.getenv(key_name)
    return key if key and key.strip() else None

api_key = get_api_key('OPENAI_API_KEY')
print(f"5. get_api_key result: {api_key[:20]}..." if api_key else "5. get_api_key result: None")
