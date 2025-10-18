"""Test script to demonstrate token limit functionality."""

import asyncio
from ai_compare.token_manager import TokenManager

async def test_token_limits():
    """Test the token management system with various input sizes."""
    
    token_manager = TokenManager()
    
    # Test 1: Short text (should not be truncated)
    short_text = "What is machine learning?"
    print("=== Test 1: Short Input ===")
    print(f"Original: {short_text}")
    result, truncated = token_manager.validate_and_truncate(short_text, "openai", "gpt-4")
    print(f"Processed: {result}")
    print(f"Was truncated: {truncated}")
    print(f"Token count: {token_manager.token_counter.count_tokens(result)}")
    print()
    
    # Test 2: Very long text (should be truncated)
    long_text = """
    This is a very long question about machine learning that goes into extensive detail about various aspects of the field. 
    Machine learning is a subset of artificial intelligence that focuses on the development of algorithms and statistical models 
    that enable computer systems to improve their performance on a specific task through experience, without being explicitly 
    programmed for every scenario. The field encompasses various approaches including supervised learning, unsupervised learning, 
    and reinforcement learning. Supervised learning involves training algorithms on labeled datasets where the correct output 
    is known, allowing the model to learn patterns and make predictions on new, unseen data. Common supervised learning 
    algorithms include linear regression, logistic regression, decision trees, random forests, support vector machines, 
    and neural networks. Unsupervised learning, on the other hand, deals with finding hidden patterns in data without 
    labeled examples, using techniques such as clustering, dimensionality reduction, and association rule learning. 
    Reinforcement learning involves training agents to make decisions in an environment to maximize cumulative reward, 
    often used in game playing, robotics, and autonomous systems. Deep learning, a subset of machine learning, uses 
    neural networks with multiple layers to model and understand complex patterns in data, leading to breakthroughs 
    in computer vision, natural language processing, and speech recognition. The applications of machine learning are 
    vast and growing, including recommendation systems, fraud detection, medical diagnosis, autonomous vehicles, 
    natural language translation, image recognition, and predictive analytics. However, machine learning also faces 
    challenges such as data quality issues, algorithmic bias, interpretability concerns, and the need for large 
    amounts of training data. As the field continues to evolve, researchers are working on developing more efficient 
    algorithms, addressing ethical considerations, and making machine learning more accessible to practitioners across 
    various domains. The future of machine learning holds promise for even more sophisticated applications and 
    integration into everyday technology, potentially transforming industries and society as a whole.
    """ * 10  # Multiply to make it very long
    
    print("=== Test 2: Long Input (GPT-4) ===")
    print(f"Original length: {len(long_text)} characters")
    print(f"Original tokens: {token_manager.token_counter.count_tokens(long_text)}")
    result, truncated = token_manager.validate_and_truncate(long_text, "openai", "gpt-4")
    print(f"Processed length: {len(result)} characters")
    print(f"Processed tokens: {token_manager.token_counter.count_tokens(result)}")
    print(f"Was truncated: {truncated}")
    print(f"Processed text preview: {result[:200]}...")
    print()
    
    # Test 3: Same long text with Claude (higher limit)
    print("=== Test 3: Long Input (Claude) ===")
    result, truncated = token_manager.validate_and_truncate(long_text, "anthropic", "claude-3-opus")
    print(f"Claude limit: {token_manager.get_model_limit('anthropic', 'claude-3-opus')}")
    print(f"Was truncated: {truncated}")
    print()
    
    # Test 4: Show all configured limits
    print("=== Test 4: All Model Limits ===")
    limits = token_manager.get_all_limits()
    for provider, models in limits.items():
        print(f"{provider.upper()}:")
        for model, limit in models.items():
            print(f"  {model}: {limit:,} tokens")
    print()

if __name__ == "__main__":
    asyncio.run(test_token_limits())
