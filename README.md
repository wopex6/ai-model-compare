# AI Model Compare

Compare responses from multiple AI models (ChatGPT, Claude, Gemini, Meta, and Grok) and get summarized insights.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your available API keys. You only need to add the keys you have:
```
# Add only the keys you have available
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
META_API_KEY=your_key_here
GROK_API_KEY=your_key_here
```

The module will automatically use only the models for which you have valid API keys.

## Usage Example

```python
from ai_compare import AICompare
import asyncio

async def main():
    comparer = AICompare()
    
    # Check which models are available
    available_models = comparer.get_available_models()
    print(f"Available models: {', '.join(available_models)}")
    
    # Ask all available models
    responses = await comparer.ask_all("What is the future of AI?")
    
    # Print individual responses
    for model, response in responses.items():
        print(f"\n{model.upper()}:")
        print(response)
    
    # Get a summary using any available model
    summary = comparer.summarize_responses(responses)
    print("\nSUMMARY:")
    print(summary)

if __name__ == "__main__":
    asyncio.run(main())
```


Last updated: 2025-10-23 15:40:23