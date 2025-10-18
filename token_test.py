#!/usr/bin/env python3
"""Simple test for token management system."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from ai_compare.token_manager import TokenManager

def test_basic_functionality():
    """Test basic token manager functionality."""
    print("=== Testing Token Manager ===")
    
    try:
        # Initialize token manager
        tm = TokenManager()
        print("✓ Token Manager initialized successfully")
        
        # Test getting limits
        gpt4_limit = tm.get_model_limit("openai", "gpt-4")
        claude_limit = tm.get_model_limit("anthropic", "claude-3-opus")
        
        print(f"✓ GPT-4 limit: {gpt4_limit:,} tokens")
        print(f"✓ Claude limit: {claude_limit:,} tokens")
        
        # Test short text (should not truncate)
        short_text = "What is machine learning?"
        result, truncated = tm.validate_and_truncate(short_text, "openai", "gpt-4")
        print(f"✓ Short text test - Truncated: {truncated}")
        
        # Test long text (should truncate)
        long_text = "This is a test. " * 1000  # Create long text
        result, truncated = tm.validate_and_truncate(long_text, "openai", "gpt-4")
        print(f"✓ Long text test - Truncated: {truncated}")
        print(f"  Original length: {len(long_text)} chars")
        print(f"  Result length: {len(result)} chars")
        
        print("\n=== All Tests Passed! ===")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)
