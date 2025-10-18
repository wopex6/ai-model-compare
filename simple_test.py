from ai_compare.simple_compare import SimpleAICompare
import asyncio

async def main():
    try:
        comparer = SimpleAICompare()
        
        # Check which models are available
        available_models = comparer.get_available_models()
        print(f"Available models: {', '.join(available_models)}")
        
        if not available_models:
            print("No models available. Please check your API keys in .env file.")
            return
        
        # Ask a simple question
        question = "What is artificial intelligence in one sentence?"
        print(f"\nAsking: {question}")
        
        responses = await comparer.ask_all(question)
        
        # Print responses
        for model, response in responses.items():
            print(f"\n{model.upper()}:")
            print(response)
        
        # Get summary if multiple models responded
        if len(responses) > 1:
            summary = await comparer.summarize_responses(responses)
            print("\nSUMMARY:")
            print(summary)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
