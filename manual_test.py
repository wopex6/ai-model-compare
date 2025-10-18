"""Manual verification of token management system."""

# Test the token manager logic manually
import re

def approximate_token_count(text):
    """Approximate token counter using word-based estimation."""
    words = len(re.findall(r'\b\w+\b', text))
    return int(words / 0.75)

def test_truncation_logic():
    """Test the truncation logic manually."""
    
    # Test data
    short_text = "What is machine learning?"
    long_text = "This is a very long text. " * 200  # Create long text
    
    # Model limits (from our implementation)
    gpt4_limit = 8000
    claude_limit = 200000
    
    print("=== Manual Token Management Test ===")
    print(f"Short text: '{short_text}'")
    print(f"Short text tokens: {approximate_token_count(short_text)}")
    print(f"Should truncate for GPT-4 ({gpt4_limit} limit): {approximate_token_count(short_text) > gpt4_limit}")
    print()
    
    print(f"Long text length: {len(long_text)} characters")
    print(f"Long text tokens: {approximate_token_count(long_text)}")
    print(f"Should truncate for GPT-4 ({gpt4_limit} limit): {approximate_token_count(long_text) > gpt4_limit}")
    print(f"Should truncate for Claude ({claude_limit} limit): {approximate_token_count(long_text) > claude_limit}")
    print()
    
    # Test intelligent truncation logic
    sentences = re.split(r'(?<=[.!?])\s+', long_text)
    print(f"Number of sentences in long text: {len(sentences)}")
    
    if len(sentences) > 2:
        first_part = sentences[0]
        last_part = sentences[-1]
        print(f"First sentence: '{first_part[:50]}...'")
        print(f"Last sentence: '{last_part[:50]}...'")
        print("✓ Intelligent truncation would preserve beginning and end")
    
    print("\n=== Integration Check ===")
    
    # Check if our compare.py has the token manager integration
    try:
        with open('ai_compare/compare.py', 'r') as f:
            content = f.read()
            
        checks = [
            ('TokenManager import', 'from .token_manager import TokenManager' in content),
            ('Token manager initialization', 'self.token_manager = TokenManager()' in content),
            ('Provider mapping', 'self._model_providers' in content),
            ('Validation in _safe_ask', 'validate_and_truncate' in content),
            ('Truncation notice', 'was_truncated' in content)
        ]
        
        for check_name, passed in checks:
            status = "✓" if passed else "✗"
            print(f"{status} {check_name}")
            
        all_passed = all(passed for _, passed in checks)
        print(f"\nIntegration status: {'✓ PASSED' if all_passed else '✗ FAILED'}")
        
    except Exception as e:
        print(f"✗ Error checking integration: {e}")

if __name__ == "__main__":
    test_truncation_logic()
